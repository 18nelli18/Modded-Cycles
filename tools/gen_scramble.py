#!/usr/bin/env python3
"""SCRAMBLE menu-less expérimental, quatre paramètres ; notes/55.

Sources originales, hooks Model-TG épinglés ; aucun firmware exporté au dépôt.
"""
import argparse,hashlib,json,pathlib,re,struct,subprocess,tempfile
import build,sprites
import gen_seq_gen as sg
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'tweaks/model-cycles_OS1.13/experimental/scramble'

def check_index_modes(disassembly):
    """Unicorn accepte ces modes 68000 interdits par ColdFire (vecteur 03)."""
    assert not re.search(r"%[da][0-7]:[wl]:8|%[da][0-7]:w",disassembly), "mode indexé interdit ColdFire"

def compile_code(cross,tg,next_hook):
    occupied=[]
    paths=list((ROOT/'tweaks/model-cycles_OS1.13').glob('*.json'))+list((ROOT/'tweaks/model-cycles_OS1.13/experimental/sequence-only').glob('*.json'))+list((ROOT/'tweaks/model-cycles_OS1.13/experimental/queued').glob('*.json'))
    for p in paths:
        t=json.loads(p.read_text())
        occupied.extend((build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for w in t.get('writes',[]))
    free=[(va,row) for va,row in sprites.MASKS.items() if len(row)==4 and not any(va<hi and lo<va+row[0] for lo,hi in occupied)]
    body=(ROOT/'tools/machines/scramble/scramble.s').read_text()
    inverse={'ne':'eq','eq':'ne','lt':'ge','gt':'le','hi':'ls','mi':'pl','cs':'cc','cc':'cs'}
    serial=0
    def far(m):
        nonlocal serial
        op,target=m.groups()
        if op=='ra':return '    jmp '+target
        serial+=1;label=f'.Lscfar{serial}'
        return f'    b{inverse[op]}s {label}\n    jmp {target}\n{label}:'
    body=re.sub(r'^[ \t]*b(ra|ne|eq|lt|gt|hi|mi|cs|cc)w[ \t]+(\w+)[ \t]*(?:\|[^\n]*)?$',far,body,flags=re.M)
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);(p/'sc.s').write_text(body)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'sc.o'),str(p/'sc.s')],check=True)
        sections=[]
        for line in subprocess.check_output([cross+'objdump','-h',str(p/'sc.o')],text=True).splitlines():
            cols=line.split()
            if len(cols)>3 and cols[0].isdigit() and cols[1].startswith(('.text.sc_','.data.sc_','.rodata.sc_')):
                sections.append((cols[1],int(cols[2],16)))
        slots=[]
        for section,size in sorted(sections,key=lambda x:-x[1]):
            fits=[(row[0]-size,va,row) for va,row in free if row[0]>=size]
            assert fits,(section,size)
            _,va,row=min(fits);free=[(v,r) for v,r in free if v!=va];slots.append((va,row,section))
        script='\n'.join(f'TG_{n} = {tg[n]};' for n in (*sg.TG_NAMES,'show_popup'))+f'\nSC_NEXT = {next_hook};\nSECTIONS {{\n'
        for i,(va,row,sec) in enumerate(slots):
            script+=f'.slot{i} {va:#x} : {{ *({sec}) }}\nASSERT(SIZEOF(.slot{i}) <= {row[0]}, "masque plein")\n'
        script+=' .unused : { *(.text) *(.data) *(.bss) }\nASSERT(SIZEOF(.unused) == 0, "section non placee")\n}\n'
        (p/'sc.ld').write_text(script)
        subprocess.run([cross+'ld','--orphan-handling=error','-T',str(p/'sc.ld'),'-o',str(p/'sc.elf'),str(p/'sc.o')],check=True)
        check_index_modes(subprocess.check_output([cross+'objdump','-d',str(p/'sc.elf')],text=True))
        syms=sg.symbols(cross,p/'sc.elf');blobs=[]
        for i in range(len(slots)):
            subprocess.run([cross+'objcopy','-O','binary',f'--only-section=.slot{i}',str(p/'sc.elf'),str(p/'sc.bin')],check=True)
            blobs.append((p/'sc.bin').read_bytes())
    return slots,blobs,syms

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',type=pathlib.Path,required=True)
    ap.add_argument('--cross',default='m68k-elf-');ap.add_argument('--check',action='store_true');a=ap.parse_args()
    assert subprocess.check_output(['git','-C',str(a.model_tg),'rev-parse','HEAD'],text=True).strip()==sg.COMMIT
    subprocess.run(['git','-C',str(a.model_tg),'diff','--quiet','HEAD'],check=True)
    stock=sg.main_os_from_syx(a.cycles);assert hashlib.sha256(stock).hexdigest()==sg.STOCK
    tg=sg.symbols(a.cross,a.model_tg/'build/_b.elf');OUT.mkdir(parents=True,exist_ok=True)
    for st in (False,True):
        dep='model-tg-st' if st else 'model-tg'
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        for gen in (False,True,"queued"):
            seqname='scale-gen-st' if st else 'scale-gen'
            folder='queued' if gen=='queued' else 'sequence-only'
            if gen=='queued':seqname+='-queued'
            seq=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/{folder}/49-{seqname}.json').read_text())
            next_hook=int(seq['symbols']['sg_key'],16) if gen else tg['key_hook']
            slots,blobs,syms=compile_code(a.cross,tg,next_hook)
            writes=[]
            def write(va,old,new):writes.append(dict(off=va-build.BASE,old=old.hex(),new=new.hex()))
            for (va,row,_),blob in zip(slots,blobs):
                size,ptr,_,kept=row
                raw=lambda v,n:stock[v-build.BASE:v-build.BASE+n]
                assert raw(va,size)==raw(kept,size)
                assert raw(ptr,4)==struct.pack('>I',va)
                assert [build.BASE+i for i in range(0,len(stock)-3,2) if stock[i:i+4]==struct.pack('>I',va)]==[ptr]
                write(ptr,raw(ptr,4),struct.pack('>I',kept));write(va,raw(va,len(blob)),blob)
            write(0x4007240c,b'\x4e\xf9'+struct.pack('>I',next_hook),b'\x4e\xf9'+struct.pack('>I',syms['sc_key']))
            name='scramble'+('-st' if st else '')+('-gen' if gen else '')+('-queued' if gen=='queued' else '')
            t=dict(id=name,order=50,name='SCRAMBLE — quatre paramètres (expérimental)',description=['SETTINGS + TRACK : popup SCRAMBLE et tirage des quatre contrôles machine.','Sans menu ni état du générateur ; Sampler exclu. Vérification matérielle attendue.','Code original ; dépend de Model-TG (TinyGregAudio, MIT). tools/gen_scramble.py, notes/55.'],device='Model:Cycles',os='1.13',section=3,requires=[dep]+([seqname] if gen else []),conflicts=[n for n in ['scramble','scramble-st','scramble-gen','scramble-st-gen','scramble-gen-queued','scramble-st-gen-queued'] if n!=name]+([] if gen else ['scale-gen','scale-gen-st','scale-gen-queued','scale-gen-st-queued']),writes=writes,symbols={n:hex(v) for n,v in syms.items() if n.startswith('sc_')})
            text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';p=OUT/f'50-{name}.json'
            if a.check:assert p.read_text()==text,p
            else:p.write_text(text)
            print('ok :',name,sum(len(b) for b in blobs),'octets,',len(slots),'masques')
if __name__=='__main__':main()
