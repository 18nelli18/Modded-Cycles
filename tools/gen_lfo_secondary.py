#!/usr/bin/env python3
"""Note 58 : placement expérimental du LFO 2, sans image firmware distribuée.

--cycles OS1.13.syx [--cross m68k-elf-] [--check]. Réserve des masques
sans écriture d'aucun tweak principal, y compris Model-TG et ses variantes.
Sans --native-sound, réglages en RAM. Option native : cinq réglages sauvés avec le son,
les trois autres aux défauts au chargement ; candidat expérimental.
"""
import argparse
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import tempfile
import build
import sprites
from gen_seq_gen import STOCK, main_os_from_syx, symbols

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'tweaks/model-cycles_OS1.13/52-lfo-secondary.json'


def compile_code(cross,reserved_masks=(),preserve_main_abi=False,native_sound=False):
    occupied=[]
    for path in sorted((ROOT/'tweaks/model-cycles_OS1.13').glob('*.json')):
        tweak=json.loads(path.read_text())
        if tweak.get('id')=='lfo-secondary' or (native_sound and tweak.get('id') in ('lfo-plus','track-filter')):continue
        occupied.extend((build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for w in tweak.get('writes',[]))
    free=[(va,row) for va,row in sprites.MASKS.items() if len(row)==4 and va not in reserved_masks and not any(va<hi and lo<va+row[0] for lo,hi in occupied)]
    inverse={'ne':'eq','eq':'ne','lt':'ge','ge':'lt','gt':'le','le':'gt','hi':'ls','ls':'hi','mi':'pl','pl':'mi','cs':'cc','cc':'cs'}
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);objects=[];sections=[]
        for source in sorted((ROOT/'tools/machines/lfo_secondary').glob('*.s')):
            serial=0
            def far(match):
                nonlocal serial
                op,target=match.groups()
                if op=='ra':return '    jmp '+target
                if op=='sr':return '    jsr '+target
                serial+=1;label=f'.Lfar_{source.stem}_{serial}'
                return f'    b{inverse[op]}s {label}\n    jmp {target}\n{label}:'
            body=source.read_text()
            body=re.sub(r'^\s*\.text\s*$',f'    .section .text.lf2_{source.stem},"ax"',body,flags=re.M)
            body=re.sub(r'^\s*\.data\s*$',f'    .section .data.lf2_{source.stem},"aw"',body,flags=re.M)
            # Les branches internes restent courtes ; seules les références
            # entre masques requièrent un saut absolu (masques éloignés).
            labels={};section=None
            for line in body.splitlines():
                if line.strip().startswith('.section'):section=line.strip().split()[1].split(',')[0]
                match=re.match(r'^([.\w]+):',line)
                if match:labels[match[1]]=section
            lines=[];section=None
            for line in body.splitlines():
                if line.strip().startswith('.section'):section=line.strip().split()[1].split(',')[0]
                match=re.match(r'^[ \t]*b(ra|sr|ne|eq|lt|ge|gt|le|hi|ls|mi|pl|cs|cc)[sw]?[ \t]+([.\w]+)[ \t]*(?:\|[^\n]*)?$',line)
                lines.append(far(match) if match and labels.get(match[2])!=section else line)
            body='\n'.join(lines)+'\n'
            assembled=p/(source.stem+'.s');assembled.write_text(body)
            obj=p/(source.stem+'.o');objects.append(str(obj))
            subprocess.run([cross+'as','-march=cfv4e','--defsym','LF2_INTEGRATED=1',*(['--defsym','LF2_NATIVE_SOUND=1'] if native_sound else []),'-o',str(obj),str(assembled)],check=True)
            for line in subprocess.check_output([cross+'objdump','-h',str(obj)],text=True).splitlines():
                cols=line.split()
                if len(cols)>3 and cols[0].isdigit() and int(cols[2],16):
                    assert cols[1].startswith(('.text.lf2','.data.lf2','.rodata.lf2')),cols
                    sections.append((cols[1],int(cols[2],16)))
        # Partager les queues des masques ; alignement4 pour code et données.
        spans=[(va,va,row[0],row) for va,row in free]
        placed=[]
        # ABI conservée pour la banque MIDI déjà publiée sur main.
        fixed={'.data.lf2_dispatch':0x40184808,'.text.lf2_dispatch':0x40168a84,'.text.lf2_prepare':0x401795b0} if preserve_main_abi else {}
        for section,at in fixed.items():
            size=dict(sections)[section]
            span=next(span for span in spans if span[0]==at)
            base,_,capacity,row=span
            assert size<=capacity,(section,size,capacity)
            spans.remove(span);placed.append((base,at,capacity,row,section))
            used=(size+3)&~3
            if capacity>used:spans.append((base,at+used,capacity-used,row))
        for section,size in sorted(sections,key=lambda item:(-item[1],item[0])):
            if section in fixed:continue
            fits=[span for span in spans if span[2]>=size]
            assert fits,('aucun masque disponible',section,size)
            base,at,capacity,row=min(fits,key=lambda span:(span[2],span[1]))
            spans.remove((base,at,capacity,row))
            placed.append((base,at,capacity,row,section))
            used=(size+3)&~3
            if capacity>used:spans.append((base,at+used,capacity-used,row))
        script='SECTIONS {\n'
        for index,(base,at,capacity,row,section) in enumerate(placed):
            script+=f'.slot{index} {at:#x} : {{ *({section}) }}\nASSERT(SIZEOF(.slot{index}) <= {capacity}, "masque plein")\n'
        script+=' .unused : { *(.text) *(.data) *(.bss) }\nASSERT(SIZEOF(.unused) == 0, "section non placee")\n}\n'
        (p/'link.ld').write_text(script)
        elf=p/'lfo.elf'
        subprocess.run([cross+'ld','--orphan-handling=error','-T',str(p/'link.ld'),'-e','lf2_launch','-o',str(elf),*objects],check=True)
        disasm=subprocess.check_output([cross+'objdump','-d',str(elf)],text=True)
        assert not re.search(r'%[da][0-7]:[wl]:8|%[da][0-7]:w',disasm),'index interdit ColdFire'
        grouped={}
        for index,(base,at,capacity,row,section) in enumerate(placed):
            subprocess.run([cross+'objcopy','-O','binary',f'--only-section=.slot{index}',str(elf),str(p/'slot.bin')],check=True)
            body=(p/'slot.bin').read_bytes()
            if base not in grouped:grouped[base]=(row,bytearray(row[0]))
            grouped[base][1][at-base:at-base+len(body)]=body
        slots=[(base,row,'packed') for base,(row,body) in sorted(grouped.items())]
        blobs=[bytes(body) for base,(row,body) in sorted(grouped.items())]
        return slots,blobs,symbols(cross,elf)



def generate(stock,cross,reserved_masks=(),preserve_main_abi=False,native_sound=False):
    assert hashlib.sha256(stock).hexdigest()==STOCK,'OS non officiel'
    slots,blobs,syms=compile_code(cross,reserved_masks,preserve_main_abi,native_sound);writes=[]
    def raw(va,size):return stock[va-build.BASE:va-build.BASE+size]
    def write(va,new):writes.append(dict(off=va-build.BASE,old=raw(va,len(new)).hex(),new=new.hex()))
    for (va,row,section),blob in zip(slots,blobs):
        size,ptr,_,kept=row
        assert raw(va,size)==raw(kept,size),(section,'masques différents')
        assert raw(ptr,4)==struct.pack('>I',va),(section,'référence différente')
        assert [build.BASE+i for i in range(0,len(stock)-3,2) if stock[i:i+4]==struct.pack('>I',va)]==[ptr],section
        write(ptr,struct.pack('>I',kept));write(va,blob)
    for va,original,target in ((0x401016c8,0x40024e0c,'lf2_key'),(0x401016e4,0x40024e86,'lf2_key_sub')):
        assert raw(va,4)==struct.pack('>I',original)
        write(va,struct.pack('>I',syms[target]))
    assert raw(0x400597c6,6)==bytes.fromhex('4eb940091ab2')
    write(0x400597c6,b'\x4e\xb9'+struct.pack('>I',syms['lf2_dispatch']))
    if native_sound:
        for va,old,target in ((0x4005b028,'356b005e005c','lf2n_pack'),(0x4005b0dc,'356b005e005c','lf2n_pack'),(0x4005af1c,'41f94010eea8','lf2n_unpack'),(0x400618e2,'e18b35430026','lf2n_init')):
            assert raw(va,6)==bytes.fromhex(old)
            write(va,b'\x4e\xb9'+struct.pack('>I',syms[target]))
    tweak=dict(id='lfo-secondary',order=52,name='Second LFO',
        description=['Deuxième appui LFO : page secondaire, six états indépendants.',
            'Testé sur machine par AveyCole le 11/10/2026 ; réglages RAM uniquement.',
            'Sources et preuve : tools/gen_lfo_secondary.py, notes/58 ; page adaptée de Model-TG (MIT).'],
        device='Model:Cycles',os='1.13',section=3,requires=[],conflicts=['lfo-plus','track-filter'] if native_sound else [],writes=writes,
        symbols={name:hex(value) for name,value in syms.items() if name.startswith('lf2')})
    if native_sound:
        tweak['description']=['Sauvegarde native expérimentale de cinq réglages du LFO 2 audio.',
            'Fade, phase initiale et mode remis aux défauts au chargement.',
            'Format basé sur 18nelli18 (MIT), idée de DavidCaruso.']
    build.apply_writes(stock,[tweak])
    for path in (ROOT/'tweaks/model-cycles_OS1.13').glob('*.json'):
        other=json.loads(path.read_text())
        if other.get('id')=='lfo-secondary' or other.get('id') in tweak['conflicts'] or 'lfo-secondary' in other.get('conflicts',[]):continue
        for ours in writes:
            low=ours['off'];high=low+len(bytes.fromhex(ours['new']))
            for theirs in other.get('writes',[]):
                start=theirs['off'];end=start+len(bytes.fromhex(theirs['new']))
                assert not (low<end and start<high),('chevauchement',other['id'],hex(build.BASE+max(low,start)))
    return tweak


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-sound',action='store_true');ap.add_argument('--preserve-main-abi',action='store_true');ap.add_argument('--reserve-mask',action='append',type=lambda x:int(x,0),default=[]);ap.add_argument('--cycles',required=True);ap.add_argument('--output',default=str(OUT));ap.add_argument('--cross',default='m68k-elf-');ap.add_argument('--check',action='store_true')
    args=ap.parse_args();tweak=generate(main_os_from_syx(args.cycles),args.cross,args.reserve_mask,args.preserve_main_abi,args.native_sound)
    text=json.dumps(tweak,ensure_ascii=False,indent=1)+'\n'
    output=pathlib.Path(args.output)
    if args.check:assert output.read_text()==text,output
    else:output.parent.mkdir(parents=True,exist_ok=True);output.write_text(text)
    print('ok : LFO 2 placé sans chevauchement des mods principaux,',len(tweak['writes']),'écritures')


if __name__=='__main__':main()
