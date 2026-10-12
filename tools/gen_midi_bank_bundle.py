#!/usr/bin/env python3
"""Note 57 : placement candidat banque MIDI + bundle Select All TG-ST.

--cycles OS1.13.syx --syntakt OS1.42.syx --model-tg clone épinglé
[--cross m68k-elf-] [--output JSON] [--check]. Aucun catalogue ni flasher
principal modifié. Réglages RAM seulement, validation matérielle à faire.
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
from gen_seq_gen import COMMIT, STOCK, symbols, main_os_from_syx

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'tweaks/model-cycles_OS1.13/experimental/midi-bank/60-midi-bank-bundle.json'
SOURCES=('runtime','pattern','clock','service','prepare','page','integration',
         'key','led','ui_hook','transport','worker','boot','banks','stock_display','keyboard','genie','genie_router','clipboard', 'track_setup')
STORAGE_SOURCES=tuple('storage_'+name for name in (
    'prepare','guard','checked','directory','codec','io','path','verify','load',
    'commit','initial','snapshot','session','project','save_hook','load_hook',
    'restore','restore_step','publish','retire','ui_cancel','service','working_slot','bank','feedback','presence'))
CONDITION_SOURCES=('chance','conditions','condition_history','condition_decode','condition_run','chance_menu')
REPEAT_SOURCES=('retrigger','retrigger_locks','retrigger_service','retrigger_patterns',
                'retrigger_step','retrigger_menu','arp','arp_tick')

IDS=('6ch-usbup','model-tg-st','sample-preview-st','trig-hold','arp','tempo-max',
     'boot-anim','multiline-browser','level-pan-values','trigless-dim',
     'midi-live-both','syntakt-tg-sd-cp-toy-bits-swarm-macro-acid',
     'scale-gen-st-queued','lfo-secondary','scramble-st-gen-queued')


def compile_code(cross,tg,next_key,start,limit,source,loader,merge_masks,pattern_banks=False,stock_display=False,lfo_cc=False,storage=False,repeat=False,conditions=False,extended_storage=False):
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);objects=[]
        for name in SOURCES + (STORAGE_SOURCES if storage else ()) + (REPEAT_SOURCES if repeat else ()) + (CONDITION_SOURCES if conditions else ()):
            if name == 'banks' and not pattern_banks:
                continue
            if name == 'stock_display' and not stock_display:
                continue
            obj=p/(name+'.o');objects.append(str(obj))
            subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_CLIPBOARD=1','--defsym','ML_WORKER=1','--defsym','ML_GENIE=1','--defsym','ML_MERGE=1',
                            *(['--defsym','ML_PATTERN_BANKS=1'] if pattern_banks else []),
                            *(['--defsym','ML_STOCK_DISPLAY=1'] if stock_display else []),
                            *(['--defsym','ML_LFO_CC=1'] if lfo_cc else []),
                            *(['--defsym','ML_STORAGE=1'] if storage else []),
                            *(['--defsym','ML_STORAGE2=1'] if extended_storage else []),
                            *(['--defsym','ML_REPEAT=1'] if repeat else []),
                            *(['--defsym','ML_CHANCE=1','--defsym','ML_CONDITIONS=1','--defsym','ML_CONDITION_COMPACT=1'] if conditions else []),
                            '-o',str(obj),str(ROOT/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
        if lfo_cc:
            from gen_midi_lfo_cc_page import sources
            extras={"cc_"+k:v for k,v in sources().items()}
            for name in ('frame','settings','queue','lane','rate','service','names','integration','depack'):
                extras['cc_'+name]=(ROOT/'tools/machines/midi_lanes'/('lfo_cc_'+name+'.s')).read_text()
            extras['cc_update']=(ROOT/'tools/machines/lfo_secondary/update.s').read_text()
            for name,body in extras.items():
                asm=p/(name+'.s');asm.write_text(body)
                obj=p/(name+'.o');objects.append(str(obj))
                subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_STORAGE2=1'] if extended_storage else []),'-o',str(obj),str(asm)],check=True)
        # Petits fragments à sauts absolus : aucun masque libre ne dépasse280o.
        raw=(ROOT/'tools/machines/midi_thru/merge.s').read_text()
        inverse={'ne':'eq','eq':'ne','hi':'ls','ls':'hi','cc':'cs','cs':'cc','pl':'mi','mi':'pl','ge':'lt','lt':'ge'}
        lines=[];part=0;count=0;serial=0;in_text=False
        for line in raw.splitlines():
            if '.section .text.mm_merge' in line:
                line='    .section .text.mm_part'+str(part)+',"ax"'
                in_text=True
            elif '.section .data.mm_merge' in line:
                in_text=False
            stripped=line.strip()
            instruction=in_text and stripped and not stripped.startswith(('|','.')) and not stripped.endswith(':')
            if instruction and count>=20:
                part+=1
                lines+=['    jmp MM_part'+str(part),'    .section .text.mm_part'+str(part)+',"ax"','MM_part'+str(part)+':']
                count=0
            match=re.match(r'^(\s*)b(ra|sr|eq|ne|hi|ls|cc|cs|pl|mi|ge|lt)\s+(\.L\w+)\s*$',line)
            if match:
                pad,kind,target=match.groups()
                if kind in ('ra','sr'):line=pad+('jmp ' if kind=='ra' else 'jsr ')+target
                else:
                    serial+=1;skip='.Lmm_far_'+str(serial)
                    line=pad+'b'+inverse[kind]+'.s '+skip+'\n'+pad+'jmp '+target+'\n'+skip+':'
            lines.append(line)
            if instruction:count+=1
        asm=p/'merge.s';asm.write_text('\n'.join(lines)+'\n')
        merge=p/'merge.o';objects.append(str(merge))
        subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_MERGE=1','-o',str(merge),str(asm)],check=True)
        listing=subprocess.check_output([cross+'objdump','-h',str(merge)],text=True)
        sections=[(m.group(1),int(m.group(2),16)) for m in re.finditer(r'^\s*\d+\s+(\.(?:text\.mm_part\d+|data\.mm_merge))\s+([0-9a-fA-F]+)',listing,re.M) if int(m.group(2),16)]
        available=list(merge_masks);placements=[]
        if lfo_cc:
            decoder=next(va for va in sorted(available) if sprites.MASKS[va][0]>=240)
            available.remove(decoder);placements.append(('.text.ml_depack',decoder))
        if conditions:
            # Helper de décision dans un masque libre vérifié, hors image compressée.
            listing=subprocess.check_output([cross+'objdump','-h',str(p/'conditions.o')],text=True)
            match=re.search(r'\s+\d+\s+\.text.ml_condition_eval\s+([0-9a-fA-F]+)',listing)
            size=int(match.group(1),16)
            mask=next((va for va in sorted(available,key=lambda va:(sprites.MASKS[va][0],va)) if sprites.MASKS[va][0]>=size),None)
            assert mask is not None,('condition helper',size,'aucun masque libre')
            available.remove(mask);placements.append(('.text.ml_condition_eval',mask))
        if repeat:
            listing=subprocess.check_output([cross+'objdump','-h',str(p/'clipboard.o')],text=True)
            sections += [(m.group(1),int(m.group(2),16)) for m in re.finditer(r'^\s*\d+\s+(\.text\.ml_step_clip_[abcd])\s+([0-9a-fA-F]+)',listing,re.M)]
        # Plusieurs fragments peuvent partager les queues libres d'un masque.
        spans=[(va,va,sprites.MASKS[va][0]) for va in available]
        owners={va:va for _,va in placements}
        for section,size in sorted(sections,key=lambda x:-x[1]):
            if conditions and section=='.data.mm_merge':continue
            fits=[span for span in spans if span[2]>=size]
            assert fits,(section,size,'aucun masque merger libre')
            base,at,capacity=min(fits,key=lambda span:(span[2],span[1]))
            spans.remove((base,at,capacity))
            used=(size+1)&~1
            if capacity>used:spans.append((base,at+used,capacity-used))
            placements.append((section,at));owners[at]=base
        merge_script='\n'.join(f' {name} {mask:#x} : {{ *({name}) }}' for name,mask in placements)
        sg=build.load_catalog()['model-cycles_OS1.13'][1]['scale-gen-st-queued']['symbols']
        bindings='\n'.join(f"SG_{name[3:]} = {sg[name]};" for name in (
            'sg_action_generate','sg_action_undo','sg_config','sg_error','sg_generate',
            'sg_advanced_steps','sg_options','sg_advanced','sg_random','sg_random_range','sg_func','sg_pad','sg_undo_valid','sg_obj','sg_menu_key','sg_open'))
        if lfo_cc:
            lf=build.load_catalog()['model-cycles_OS1.13'][1]['lfo-secondary']['symbols']
            bindings+='\nMLCC_audio_next = '+lf['lf2_dispatch']+';'
        # Même source que l'aperçu natif ; garder ses branches locales hors des masques.
        ui=p/'genie_stock.s'
        body=(ROOT/'tools/machines/seq_gen/stock_ui.s').read_text()
        inverse={'ne':'eq','eq':'ne','lt':'ge','gt':'le','le':'gt','ge':'lt','hi':'ls','ls':'hi','cc':'cs','cs':'cc','mi':'pl','pl':'mi'}
        serial=[0]
        def far(m):
            kind,target=m.groups()
            if kind=='ra':return '    jmp '+target
            serial[0]+=1;label='.Lstock_far_'+str(serial[0])
            return '    b'+inverse[kind]+'s '+label+'\n    jmp '+target+'\n'+label+':'
        ui.write_text(re.sub(r'^[ \t]*b(ra|ne|eq|lt|gt|le|ge|hi|ls|cc|cs|mi|pl)w[ \t]+(\w+)[ \t]*(?:\|[^\n]*)?$',far,body,flags=re.M))
        obj=p/'genie_stock.o';objects.append(str(obj))
        subprocess.run([cross+'as','-march=cfv4e',*sum((['--defsym',x+'=1'] for x in ('SG_SCROLL','SG_DYNAMICS','SG_ADVANCED','SG_SEQUENCE_ONLY','SG_QUEUE')),[]),'-o',str(obj),str(ui)],check=True)
        undefined=subprocess.check_output([cross+'nm','-u',str(obj)],text=True)
        for line in undefined.splitlines():
            name=line.split()[-1]
            if name.startswith('sg_'):bindings+='\n'+name+' = '+sg[name]+';'
        script=f'''{bindings}
TG_scale_state = {tg['scale_state']:#x}; TG_key_state = {tg['key_state']:#x};
ML_original_key = {tg['key_hook']:#x};
TG_set_held = {tg['set_held']:#x}; TG_mod_used = {tg['mod_used']:#x};
TG_show_popup = {tg['show_popup']:#x};
TG_snap_note = {tg['snap_note']:#x}; TG_blk_clk = {tg['blk_clk']:#x};
ml_key_next = {next_key:#x}; ML_BANK_START = {start:#x};
ML_TG_START = {tg['blob_start']:#x}; ML_PAYLOAD_SRC = {source:#x};
SECTIONS {{
 .loader {loader:#x} : {{ *(.text.ml_loader) }}
{merge_script}
 .bank {start:#x} : {{ *(.text*) *(.rodata*) *(.data*) *(.bss*) . = ALIGN(16); }}
 ML_BANK_END = ADDR(.bank) + SIZEOF(.bank); ML_BANK_SIZE = SIZEOF(.bank);
 ASSERT(ML_BANK_END <= {limit:#x}, "banque hors des blocs TG retires")
 ASSERT(SIZEOF(.loader) <= {sprites.MASKS[loader][0]}, "masque chargeur plein")
}}
'''
        (p/'link.ld').write_text(script)
        elf=p/'bank.elf'
        subprocess.run([cross+'ld','--orphan-handling=error','-T',str(p/'link.ld'),
                        '-e','ml_boot_copy','-o',str(elf),*objects],check=True)
        blobs=[]
        for section in ('.bank','.loader'):
            out=p/(section[1:]+'.bin')
            subprocess.run([cross+'objcopy','-O','binary','--only-section='+section,str(elf),str(out)],check=True)
            blobs.append(out.read_bytes())
        collected={}
        for section,mask in placements:
            out=p/'fragment.bin'
            subprocess.run([cross+'objcopy','-O','binary','--only-section='+section,str(elf),str(out)],check=True)
            code=out.read_bytes();base=owners[mask];offset=mask-base
            buf=collected.setdefault(base,bytearray())
            if len(buf)<offset+len(code):buf.extend(bytes(offset+len(code)-len(buf)))
            buf[offset:offset+len(code)]=code
            assert len(buf)<=sprites.MASKS[base][0]
        fragments=[(base,bytes(buf)) for base,buf in collected.items()]
        return *blobs,fragments,symbols(cross,elf)


def generate(stock,syntakt_path,model_tg,cross,pattern_banks=False,stock_display=False,usb6=True,cache_blocks=6,lfo_cc=False,storage=False,repeat=False,conditions=False,extended_storage=False):
    if extended_storage:assert storage and repeat and lfo_cc
    if conditions:assert repeat, 'conditions requièrent les réglages privés'
    if storage:assert pattern_banks and lfo_cc, 'prototype stockage requiert banques et compression LFO CC'
    if repeat:assert pattern_banks and lfo_cc, 'prototype retrigger requiert banques et compression LFO CC'
    assert hashlib.sha256(stock).hexdigest()==STOCK,'OS Cycles non officiel'
    assert subprocess.check_output(['git','-C',str(model_tg),'rev-parse','HEAD'],text=True).strip()==COMMIT
    subprocess.run(['git','-C',str(model_tg),'diff','--quiet','HEAD'],check=True)
    catalog=build.load_catalog()['model-cycles_OS1.13'][1]
    chosen=sorted((catalog[x] for x in IDS if usb6 or x!='6ch-usbup'),key=lambda t:t['order'])
    build.check_conflicts(chosen)
    patched,_=build.apply_writes(stock,chosen)
    payload,_=build.build_payload(chosen,stock,syntakt_path)
    image=patched+payload;source=build.BASE+len(image)
    tg=symbols(cross,pathlib.Path(model_tg)/'build/_b.elf')
    tg_tweak=catalog['model-tg-st'];ap=tg_tweak['append']
    start=int(ap['at'],16)+ap['size']
    assert start==int(tg_tweak['symbols']['reserved_end'],16)==tg['reserved_end']
    assert tg['blob_start']==int(tg_tweak['symbols']['blob_start'],16)==0x401ab750
    # Six blocs retirés des listes natives ; aucune réserve supplémentaire.
    def word(at):return struct.unpack('>I',image[at-build.BASE:at-build.BASE+4])[0]
    assert word(0x400792f2)==0x401eb7c8 and word(0x400792bc)==0x401eb7ec
    blocks=(word(0x400792f2)-0x401eb750)//20
    if lfo_cc:cache_blocks=max(cache_blocks,8 if conditions else 7)
    assert blocks==6 and cache_blocks in (6,7,8)
    limit=tg['blob_start']+cache_blocks*16384
    assert start<limit
    oldkey=image[0x4007240c-build.BASE:0x40072412-build.BASE]
    assert oldkey[:2]==b'\x4e\xf9'
    next_key=struct.unpack('>I',oldkey[2:])[0]
    assert next_key==int(catalog['scramble-st-gen-queued']['symbols']['sc_key'],16)
    occupied=[(build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new'])))
              for t in catalog.values() for w in t['writes']]
    free=[va for va,row in sprites.MASKS.items() if len(row)==4 and
          not any(va<hi and lo<va+row[0] for lo,hi in occupied)]
    assert free,'aucun masque chargeur libre'
    loader=min(free,key=lambda va:(sprites.MASKS[va][0],va))
    size,ptr,_,kept=sprites.MASKS[loader]
    assert stock[loader-build.BASE:loader-build.BASE+size]==stock[kept-build.BASE:kept-build.BASE+size]
    needle=struct.pack('>I',loader)
    assert [build.BASE+i for i in range(0,len(stock)-3,2) if stock[i:i+4]==needle]==[ptr]
    merge_masks=[va for va in free if va!=loader]
    blob,stub,merge_code,syms=compile_code(cross,tg,next_key,start,limit,source,loader,merge_masks,pattern_banks,stock_display,lfo_cc,storage,repeat,conditions,extended_storage)
    if lfo_cc:
        import aplib_grow
        if storage or repeat:
            import aplib_dense
            packed=min((aplib_dense.pack(blob,depth=d) for d in ((32,128,512) if conditions else (32,))),key=len)
        else:packed=aplib_grow.pack(blob)
    else:packed=blob
    assert source>=start+len(blob), ("source/payload overlap",source,start,len(blob))
    assert source+len(packed)<=build.END_LIMIT, ("image overflow",source+len(packed)-build.END_LIMIT,"raw",len(blob),"packed",len(packed),"source",hex(source))
    st=catalog['syntakt-tg-sd-cp-toy-bits-swarm-macro']
    target=b'\x4e\xf9'+struct.pack('>I',int(tg_tweak['symbols']['boot_extra_hook'],16))
    chain=[]
    for w in st['writes']:
        data=bytes.fromhex(w['new'])
        for offset in range(0,len(data)-5,2):
            if data[offset:offset+6]==target:chain.append(build.BASE+w['off']+offset)
    assert len(chain)==1,'chaîne boot Syntakt ambiguë'
    writes=[]
    def write(at,new):
        old=patched[at-build.BASE:at-build.BASE+len(new)]
        assert len(old)==len(new)
        writes.append(dict(off=at-build.BASE,old=old.hex(),new=new.hex()))
    if repeat and not storage:
        at=0x4006a660
        assert image[at-build.BASE:at-build.BASE+8].hex()=="4cd7040c4fef0020"
        write(at,b"\x4e\xf9"+struct.pack(">I",syms["ml_repeat_project_hook"])+b"\x4e\x71")
    if storage:
        # Cibles natives exactes ; ordre boot/cache à valider avant publication.
        disk_hooks = [(0x4008b24a,'4fefffec48d7043c','ml_store_disk_read'),
                      (0x4008b3f6,'4fefffec48d7043c','ml_store_disk_write')] if extended_storage else [(0x400798c8,'4eb94008b24a','ml_store_disk_read')]
        for at,old,name in disk_hooks + [
            (0x4000f850,'4cd77c1c4fef0034','ml_store_save_hook'),
            (0x4006a660,'4cd7040c4fef0020','ml_store_load_hook')]:
            assert image[at-build.BASE:at-build.BASE+len(bytes.fromhex(old))].hex()==old
            op=b'\x4e\xb9' if at==0x400798c8 else b'\x4e\xf9'
            replacement=op+struct.pack('>I',syms[name])
            if len(bytes.fromhex(old))==8:replacement+=b'\x4e\x71'
            write(at,replacement)
    # Réserve optionnelle : sept blocs pour CC, huit pour conditions ; au moins huit blocs disque liés.
    if cache_blocks != blocks:
        write(0x400792f2,struct.pack('>I',0x401eb750+20*cache_blocks))
        write(0x400792bc,struct.pack('>I',0x401eb750+20*(cache_blocks+1)+16))
    redirect=sprites.redirect_write(loader)
    write(build.BASE+redirect['off'],bytes.fromhex(redirect['new']))
    write(loader,stub)
    for merge_mask,fragment in merge_code:
        redirect=sprites.redirect_write(merge_mask)
        write(build.BASE+redirect['off'],bytes.fromhex(redirect['new']))
        write(merge_mask,fragment)
    write(chain[0],b'\x4e\xf9'+struct.pack('>I',syms['ml_boot_copy']))
    assert image[0x4008e8c4-build.BASE:0x4008e8ce-build.BASE].hex()=='202f000441f94010abf8'
    write(0x4008e8c4,b'\x4e\xf9'+struct.pack('>I',syms['mlp_pulse_guard'])+b'\x4e\x71'*2)
    assert image[0x400012cc-build.BASE:0x400012d2-build.BASE].hex()=='2f02242f0008'
    write(0x400012cc,b'\x4e\xf9'+struct.pack('>I',syms['mm_rx']))
    if lfo_cc:
        expected=b'\x4e\xb9'+struct.pack('>I',int(catalog['lfo-secondary']['symbols']['lf2_dispatch'],16))
        assert image[0x400597c6-build.BASE:0x400597cc-build.BASE]==expected
        write(0x400597c6,b'\x4e\xb9'+struct.pack('>I',syms['mlcc_audio']))
    write(0x4007240c,b'\x4e\xf9'+struct.pack('>I',syms['ml_key']))
    write(0x40054686,b'\x4e\xf9'+struct.pack('>I',syms['ml_start_hook']))
    write(0x400594a8,b'\x4e\xb9'+struct.pack('>I',syms['ml_audio_hook']))
    write(0x40006a4a,b'\x4e\xf9'+struct.pack('>I',syms['ml_ui_hook'])+b'\x4e\x71')
    # Rediriger seulement les appels du menu ; les actions audio restent intactes.
    sg=catalog['scale-gen-st-queued']['symbols']
    for native,ours in (('sg_action_generate','ml_genie_generate'),('sg_action_undo','ml_genie_undo')):
        target=b'\x4e\xb9'+struct.pack('>I',int(sg[native],16))
        menu=int(sg['sg_menu_key'],16)
        sites=[at for at in range(menu,menu+0x400,2)
               if patched[at-build.BASE:at-build.BASE+6]==target]
        assert len(sites)==1,(native,sites)
        write(sites[0],b'\x4e\xb9'+struct.pack('>I',syms[ours]))
    for native,ours in (('sg_pad','ml_genie_pad'),('sg_menu_key','ml_genie_menu_key'),('sg_render','sg_render')):
        target=b'\x20\x3c'+struct.pack('>I',int(sg[native],16))
        sites=[build.BASE+i for i in range(0,len(patched)-5,2) if patched[i:i+6]==target]
        assert len(sites)==1,sites
        write(sites[0],b'\x20\x3c'+struct.pack('>I',syms[ours]))
    # Le constructeur MACHINES ajoute le groupe de fermeture 2 ; garder B dessous.
    lo=int(sg['sg_o_allocate'],16);hi=int(sg['sg_o_done'],16)
    target=b'\x4e\xb9'+struct.pack('>I',0x4007700e)
    sites=[at for at in range(lo,hi,2) if patched[at-build.BASE:at-build.BASE+6]==target]
    assert len(sites)==1,sites
    write(sites[0],b'\x4e\xb9'+struct.pack('>I',syms['ml_genie_present']))
    if stock_display:
        for at,expected,name in ((0x4001b28a,'4eb940012412','mlp_stock_track'),
                                 (0x4001b774,'4eb940009c5a','mlp_stock_volume'),
                                 (0x4001b722,'2068001c4e90','mlp_stock_pan')):
            assert image[at-build.BASE:at-build.BASE+6].hex()==expected
            write(at,b'\x4e\xb9'+struct.pack('>I',syms[name]))
        assert image[0x4001b6ba-build.BASE:0x4001b6c4-build.BASE].hex()=='486a0001283c401117e0'
        write(0x4001b6ba,b'\x4e\xf9'+struct.pack('>I',syms['mlp_stock_track_label'])+b'\x4e\x71'*2)
    tweak=dict(id='midi-bank-bundle',order=60,name='Banque MIDI : bundle candidat',
               description=['Six voies MIDI indépendantes, canaux fixes 7..12 ; réglages en RAM seulement.',
                            'Placement candidat TG-ST Select All ; tools/gen_midi_bank_bundle.py, note 57.'],
               device='Model:Cycles',os='1.13',section=3,status='experimental',
               requires=[x for x in IDS if x!='6ch-usbup'],conflicts=[],writes=writes,
               append=dict(at=hex(source),dest=hex(start),size=len(blob),
                           parts=[dict(dest=hex(start),hex=blob.hex())],reloc=[]),
               symbols={k:hex(v) for k,v in syms.items()})
    if lfo_cc:tweak['append']['compress']='aplib'
    if storage or repeat:tweak['append']['compressed_hex']=packed.hex()
    final,_=build.apply_writes(stock,chosen+[tweak])
    return tweak,chosen,final+payload+packed


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True)
    ap.add_argument('--model-tg',required=True);ap.add_argument('--cross',default='m68k-elf-')
    ap.add_argument('--output',type=pathlib.Path,default=OUT);ap.add_argument('--check',action='store_true')
    ap.add_argument('--pattern-banks',action='store_true',default=True,help='Banques RAM par pattern du candidat test')
    ap.add_argument('--stock-display',action='store_true',default=True,help='Rendu stock du candidat test')
    ap.add_argument('--cache-blocks',type=int,choices=(6,7,8),default=6,help='Réserve expérimentale ; huit blocs disque au minimum')
    ap.add_argument('--lfo-cc',action='store_true',help='Candidat LFO CC privé ; réserve sept blocs')
    ap.add_argument('--retrigger',action='store_true',help='Prototype retrigger/arp B intégré, non publié')
    args=ap.parse_args()
    tweak,_,image=generate(main_os_from_syx(args.cycles),args.syntakt,args.model_tg,args.cross,args.pattern_banks,args.stock_display,cache_blocks=args.cache_blocks,lfo_cc=args.lfo_cc,repeat=args.retrigger)
    body=json.dumps(tweak,indent=1,ensure_ascii=False)+'\n'
    if args.check:
        assert args.output and args.output.read_text()==body,'JSON candidat différent'
    elif args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(body)
    print('ok : candidat',tweak['append']['size'],'octets, fin image',hex(build.BASE+len(image)),
          'sha256',hashlib.sha256(image).hexdigest())
    print('NOTE : catalogue principal inchangé ; matériel et persistance à valider')


if __name__=='__main__':main()
