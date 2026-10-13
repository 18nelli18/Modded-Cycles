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
         'key','led','ui_hook','transport','worker','boot','banks','stock_display','keyboard','genie','genie_router','settings_present','genie_chance','clipboard', 'track_setup')
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



def fragment_slide_source(body,tag):
    """Placer le seul code slide dans les masques libres, branches absolues."""
    inverse={'ne':'eq','eq':'ne','lt':'ge','gt':'le','le':'gt','ge':'lt','hi':'ls','ls':'hi','cc':'cs','cs':'cc','mi':'pl','pl':'mi'}
    rows=[];part=0;count=0;serial=0;inside=False
    for line in body.splitlines():
        stripped=line.strip()
        if stripped=='.text' or stripped.startswith('.section .text'):
            inside=True;line='    .section .text.ms_'+tag+str(part)+',"ax"'
        elif stripped.startswith(('.data','.section .data','.rodata','.section .rodata')):
            inside=False
        instruction=inside and stripped and not stripped.startswith(('|','.')) and not stripped.endswith(':')
        if instruction and count>=20:
            part+=1;label='MS_'+tag+'_part'+str(part)
            rows+=['    jmp '+label,'    .section .text.ms_'+tag+str(part)+',"ax"',label+':'];count=0
        m=re.match(r'^(\s*)b(ra|sr|eq|ne|hi|ls|cc|cs|pl|mi|ge|lt)(?:[ws])?\s+(\.L\w+)\s*(?:\|.*)?$',line)
        if inside and m:
            pad,kind,target=m.groups()
            if kind in ('ra','sr'):line=pad+('jmp ' if kind=='ra' else 'jsr ')+target
            else:
                serial+=1;skip='.Lms_'+tag+'_far'+str(serial)
                line=pad+'b'+inverse[kind]+'.s '+skip+'\n'+pad+'jmp '+target+'\n'+skip+':'
        rows.append(line)
        if instruction:count+=1
    return '\n'.join(rows)+'\n'

def compile_code(cross,tg,next_key,start,limit,source,loader,merge_masks,pattern_banks=False,stock_display=False,lfo_cc=False,storage=False,repeat=False,conditions=False,extended_storage=False,audio_storage=False,working_storage=False,live_record=False,write_first=False,genie_chance=False,restore_saved=False,knob_cc=False,knob_locks=False,cc_storage=False,cc_slides=False,lfo_confirm=False,cost_compression=False):
    if cc_storage and not (knob_locks and storage and extended_storage):
        raise ValueError('cc_storage exige locks CC et stockage MIDI étendu')
    if working_storage and not audio_storage:
        raise ValueError('working_storage exige MBK3')
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);objects=[];slide_objects=[]
        for name in SOURCES + (STORAGE_SOURCES if storage else ()) + (('storage_audio_lfo',) if audio_storage else ()) + (('storage_autosave',) if working_storage else ()) + (('live_record_mode','live_record') if live_record else ()) + (('knob_cc','knob_cc_ui','knob_cc_scroll','knob_cc_assignment','knob_cc_scramble') if knob_cc else ()) + (('knob_cc_locks','knob_cc_lock_patterns','knob_cc_lock_edit','knob_cc_lock_queue','knob_cc_lock_clip') if knob_locks else ()) + (REPEAT_SOURCES if repeat else ()) + (CONDITION_SOURCES if conditions else ()) + (('knob_cc_slide_plan','knob_cc_slide_value','knob_cc_slide_arm','knob_cc_slide_tick') if cc_slides else ()) + (tuple('knob_cc_storage_'+n for n in ('codec','verify','path','journal','prepare','project','restore','rebind')) if cc_storage else ()):
            if name == 'banks' and not pattern_banks:
                continue
            if name == 'stock_display' and not stock_display:
                continue
            obj=p/(name+'.o');objects.append(str(obj))
            source_file=ROOT/'tools/machines/midi_lanes'/(name+'.s')
            if cc_slides and name.startswith('knob_cc_slide_'):
                asm=p/(name+'.s')
                asm.write_text(fragment_slide_source(source_file.read_text(),name.rsplit('_',1)[-1]))
                source_file=asm;slide_objects.append(obj)
            subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_CLIPBOARD=1','--defsym','ML_WORKER=1','--defsym','ML_GENIE=1','--defsym','ML_MERGE=1',
                            *(['--defsym','ML_PATTERN_BANKS=1'] if pattern_banks else []),
                            *(['--defsym','ML_STOCK_DISPLAY=1'] if stock_display else []),
                            *(['--defsym','ML_LFO_CC=1'] if lfo_cc else []),
                            *(['--defsym','ML_STORAGE=1'] if storage else []),
                            *(['--defsym','ML_STORAGE2=1'] if extended_storage else []),
                            *(['--defsym','ML_STORAGE3=1'] if audio_storage else []),
                            *(['--defsym','ML_WORKING=1'] if working_storage else []),
                            *(['--defsym','ML_LIVE_REC=1'] if live_record else []),
                            *(['--defsym','ML_SAVE_FIRST=1'] if write_first else []),
                            *(['--defsym','ML_RESTORE_SAVED=1'] if restore_saved else []),
                            *(['--defsym','ML_KNOB_CC=1'] if knob_cc else []),
                            *(['--defsym','ML_KNOB_LOCKS=1'] if knob_locks else []),
                            *(['--defsym','ML_CC_STORAGE=1'] if cc_storage else []),
                            *(['--defsym','ML_CC_SLIDES=1'] if cc_slides else []),
                            *(['--defsym','ML_GENIE_CHANCE=1'] if genie_chance else []),
                            *(['--defsym','ML_REPEAT=1'] if repeat else []),
                            *(['--defsym','ML_CHANCE=1','--defsym','ML_CONDITIONS=1','--defsym','ML_CONDITION_COMPACT=1'] if conditions else []),
                            '-o',str(obj),str(source_file)],check=True)
        if lfo_cc:
            from gen_midi_lfo_cc_page import sources
            extras={"cc_"+k:v for k,v in sources(confirm=lfo_confirm).items()}
            for name in ('frame','settings','queue','lane','rate','service','names','integration','depack'):
                extras['cc_'+name]=(ROOT/'tools/machines/midi_lanes'/('lfo_cc_'+name+'.s')).read_text()
            extras['cc_update']=(ROOT/'tools/machines/lfo_secondary/update.s').read_text()
            if lfo_confirm:
                # Déplacer aussi le getter UI dans un masque libre vérifié.
                page_body=extras['cc_page'];a=page_body.index('    .section .text.mlccp_raw_value,');b=page_body.index('    .section .text.mlccp_value,',a)
                extras['cc_read']='    .globl mlccp_raw_value\n'+page_body[a:b];extras['cc_page']=page_body[:a]+page_body[b:]
                support=extras['cc_support'];a=support.index('    .section .text.mlccp_confirm_write,');b=support.index('    .section .text.mlccp_confirm_validate,',a)
                extras['cc_write']='    .globl mlccp_confirm_write,mlccp_confirm_adjust\n'+support[a:b];extras['cc_support']=support[:a]+support[b:]
                scroll=extras['cc_scroll'];a=scroll.index('mlccp_tick:');extras['cc_tick']='    .text\n    .globl mlccp_tick\n'+scroll[a:];extras['cc_scroll']='    .globl mlccp_scroll_draw\n'+scroll[:a]
                page_body=extras['cc_page'];a=page_body.index('    .section .text.mlccp_pad,');b=page_body.index('    .section .text.mlccp_enc_navigation,',a);extras['cc_pad']='    .globl mlccp_pad\n'+page_body[a:b];extras['cc_page']=page_body[:a]+page_body[b:]
            for name,body in extras.items():
                asm=p/(name+'.s');asm.write_text(fragment_slide_source(body,'confirm'+name[3:]) if lfo_confirm and name in ('cc_write','cc_read','cc_tick','cc_pad') else body)
                obj=p/(name+'.o');objects.append(str(obj))
                if lfo_confirm and name in ('cc_write','cc_read','cc_tick','cc_pad'):slide_objects.append(obj)
                subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_STORAGE2=1'] if extended_storage else []),'-o',str(obj),str(asm)],check=True)
        if audio_storage:
            legacy=(ROOT/'tools/machines/midi_lanes/storage_codec.s').read_text()
            for name in ('ml_record_crc','ml_record_encode','ml_record_decode','ml_record_select'):
                legacy=legacy.replace(name,name+'_v2')
            if working_storage:
                # Migration lecture seule : encode/select MBK2 inutilisés.
                legacy=legacy.replace(',ml_record_encode_v2','')
                legacy_start=legacy.index('ml_record_encode_v2:')
                legacy_end=legacy.index('.Lenc_bad:',legacy_start)
                legacy=legacy[:legacy_start]+legacy[legacy_end:]
                legacy_start=legacy.index('    .globl ml_record_select_v2')
                legacy_end=legacy.index('    .section .rodata',legacy_start)
                # Garder le .ifdef qui encadre les tables finales.
                legacy=legacy[:legacy_start]+'    .ifdef ML_STORAGE2\n'+legacy[legacy_end:]
            asm=p/'codec_v2.s';asm.write_text(legacy)
            obj=p/'codec_v2.o';objects.append(str(obj))
            subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_STORAGE2=1','-o',str(obj),str(asm)],check=True)
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
        for slide_object in slide_objects:
            listing=subprocess.check_output([cross+'objdump','-h',str(slide_object)],text=True)
            sections += [(m.group(1),int(m.group(2),16)) for m in re.finditer(r'^\s*\d+\s+(\.text\.ms_[a-z]+\d+)\s+([0-9a-fA-F]+)',listing,re.M) if int(m.group(2),16)]
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
        alignment=4 if lfo_confirm else 2
        spans=[(va,(va+alignment-1)&~(alignment-1),sprites.MASKS[va][0]-(((va+alignment-1)&~(alignment-1))-va)) for va in available]
        owners={va:va for _,va in placements}
        for section,size in sorted(sections,key=lambda x:-x[1]):
            if conditions and section=='.data.mm_merge':continue
            fits=[span for span in spans if span[2]>=size]
            assert fits,(section,size,'aucun masque merger libre')
            base,at,capacity=min(fits,key=lambda span:(span[2],span[1]))
            spans.remove((base,at,capacity))
            used=(size+alignment-1)&~(alignment-1)
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
            if audio_storage:
                bindings+='\nLF2_context = '+lf['lf2_context']+';\nLF2_prepare = '+lf['lf2_prepare']+';'
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
TG_show_popup = {tg['show_popup']:#x}; TG_slide_phase = {tg['sld_phase']:#x};
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


def generate(stock,syntakt_path,model_tg,cross,pattern_banks=False,stock_display=False,usb6=True,cache_blocks=6,lfo_cc=False,storage=False,repeat=False,conditions=False,extended_storage=False,audio_storage=False,working_storage=False,live_record=False,write_first=False,genie_chance=False,restore_saved=False,knob_cc=False,knob_locks=False,cc_storage=False,cc_slides=False,lfo_confirm=False,cost_compression=False):
    if cc_slides:assert knob_locks
    if knob_locks:assert knob_cc and storage and extended_storage
    if genie_chance:assert conditions
    if restore_saved:assert write_first
    if write_first:assert storage and extended_storage and not working_storage
    # La capture live fonctionne aussi sans stockage disque.
    if audio_storage:assert extended_storage
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
    if live_record:cache_blocks=max(cache_blocks,9)
    assert blocks==6 and cache_blocks in (6,7,8,9)
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
    blob,stub,merge_code,syms=compile_code(cross,tg,next_key,start,limit,source,loader,merge_masks,pattern_banks,stock_display,lfo_cc,storage,repeat,conditions,extended_storage,audio_storage,working_storage,live_record,write_first,genie_chance,restore_saved,knob_cc,knob_locks,cc_storage,cc_slides,lfo_confirm)
    if lfo_cc:
        import aplib_grow
        if cost_compression:
            import aplib_cost
            packed=aplib_cost.pack(blob,depth=128,lazy=True)
        elif storage or repeat:
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
        for at,old,name in disk_hooks + ([(0x4000f762,'4fefffcc48d77c1c','ml_store_save_entry')] if write_first else []) + [
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
    assert image[0x4001c5da-build.BASE:0x4001c5e0-build.BASE].hex()=='4eb940077da8'
    write(0x4001c5da,b'\x4e\xb9'+struct.pack('>I',syms['ml_settings_toggle']))
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
