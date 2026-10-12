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
import struct
import subprocess
import tempfile
import build
import sprites
from gen_seq_gen import COMMIT, STOCK, symbols, main_os_from_syx

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'tweaks/model-cycles_OS1.13/experimental/midi-bank/60-midi-bank-bundle.json'
SOURCES=('runtime','pattern','clock','service','prepare','page','integration',
         'key','led','ui_hook','transport','worker','boot','banks','stock_display','keyboard')
IDS=('6ch-usbup','model-tg-st','sample-preview-st','trig-hold','arp','tempo-max',
     'boot-anim','multiline-browser','level-pan-values','trigless-dim',
     'midi-live-both','syntakt-tg-sd-cp-toy-bits-swarm-macro',
     'scale-gen-st-queued','lfo-secondary','scramble-st-gen-queued')


def compile_code(cross,tg,next_key,start,limit,source,loader,pattern_banks=False,stock_display=False):
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);objects=[]
        for name in SOURCES:
            if name == 'banks' and not pattern_banks:
                continue
            if name == 'stock_display' and not stock_display:
                continue
            obj=p/(name+'.o');objects.append(str(obj))
            subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_WORKER=1',
                            *(['--defsym','ML_PATTERN_BANKS=1'] if pattern_banks else []),
                            *(['--defsym','ML_STOCK_DISPLAY=1'] if stock_display else []),
                            '-o',str(obj),str(ROOT/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
        script=f'''TG_set_held = {tg['set_held']:#x}; TG_mod_used = {tg['mod_used']:#x};
TG_snap_note = {tg['snap_note']:#x};
ml_key_next = {next_key:#x}; ML_BANK_START = {start:#x};
ML_TG_START = {tg['blob_start']:#x}; ML_PAYLOAD_SRC = {source:#x};
SECTIONS {{
 .loader {loader:#x} : {{ *(.text.ml_loader) }}
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
        return *blobs,symbols(cross,elf)


def generate(stock,syntakt_path,model_tg,cross,pattern_banks=False,stock_display=False):
    assert hashlib.sha256(stock).hexdigest()==STOCK,'OS Cycles non officiel'
    assert subprocess.check_output(['git','-C',str(model_tg),'rev-parse','HEAD'],text=True).strip()==COMMIT
    subprocess.run(['git','-C',str(model_tg),'diff','--quiet','HEAD'],check=True)
    catalog=build.load_catalog()['model-cycles_OS1.13'][1]
    chosen=sorted((catalog[x] for x in IDS),key=lambda t:t['order'])
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
    limit=tg['blob_start']+blocks*16384
    assert blocks==6 and start<limit
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
    blob,stub,syms=compile_code(cross,tg,next_key,start,limit,source,loader,pattern_banks,stock_display)
    assert source>=start+len(blob) and source+len(blob)<=build.END_LIMIT
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
    redirect=sprites.redirect_write(loader)
    write(build.BASE+redirect['off'],bytes.fromhex(redirect['new']))
    write(loader,stub)
    write(chain[0],b'\x4e\xf9'+struct.pack('>I',syms['ml_boot_copy']))
    write(0x4007240c,b'\x4e\xf9'+struct.pack('>I',syms['ml_key']))
    write(0x40054686,b'\x4e\xf9'+struct.pack('>I',syms['ml_start_hook']))
    write(0x400594a8,b'\x4e\xb9'+struct.pack('>I',syms['ml_audio_hook']))
    write(0x40006a4a,b'\x4e\xf9'+struct.pack('>I',syms['ml_ui_hook'])+b'\x4e\x71')
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
               requires=list(IDS),conflicts=[],writes=writes,
               append=dict(at=hex(source),dest=hex(start),size=len(blob),
                           parts=[dict(dest=hex(start),hex=blob.hex())],reloc=[]),
               symbols={k:hex(v) for k,v in syms.items()})
    final,_=build.apply_writes(stock,chosen+[tweak])
    return tweak,chosen,final+payload+blob


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True)
    ap.add_argument('--model-tg',required=True);ap.add_argument('--cross',default='m68k-elf-')
    ap.add_argument('--output',type=pathlib.Path,default=OUT);ap.add_argument('--check',action='store_true')
    ap.add_argument('--pattern-banks',action='store_true',default=True,help='Banques RAM par pattern du candidat test')
    ap.add_argument('--stock-display',action='store_true',default=True,help='Rendu stock du candidat test')
    args=ap.parse_args()
    tweak,_,image=generate(main_os_from_syx(args.cycles),args.syntakt,args.model_tg,args.cross,args.pattern_banks,args.stock_display)
    body=json.dumps(tweak,indent=1,ensure_ascii=False)+'\n'
    if args.check:
        assert args.output and args.output.read_text()==body,'JSON candidat différent'
    elif args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(body)
    print('ok : candidat',tweak['append']['size'],'octets, fin image',hex(build.BASE+len(image)),
          'sha256',hashlib.sha256(image).hexdigest())
    print('NOTE : catalogue principal inchangé ; matériel et persistance à valider')


if __name__=='__main__':main()
