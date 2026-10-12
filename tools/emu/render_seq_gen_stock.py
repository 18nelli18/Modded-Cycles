#!/usr/bin/env python3
"""Prototype Genie stock exécuté en RAM avec polices et dessin natifs.

Aucune image firmware exportée ; fixtures musicales et allocation simulées.
--cycles OS1.13.syx --output aperçu.png [--row 0..20]
"""
import argparse,pathlib,subprocess,tempfile,re,struct,json
import unicorn.m68k_const as mk
from unicorn import UC_HOOK_CODE
import build
from render_midi_bank import DrawingRig,png
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--row',type=int,default=0)
    ap.add_argument('--bundle',action='store_true',help='Exécuter le renderer et la vtable du bundle placé')
    a=ap.parse_args();root=pathlib.Path(__file__).resolve().parents[2]
    catalog=build.load_catalog()['model-cycles_OS1.13'][1]
    tweak=catalog['scale-gen-st-queued'];base=catalog['model-tg-st']
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    tg=symbols(cross,root.parent/'model-tg/build/_b.elf')
    r=DrawingRig(main_os_from_syx(a.cycles),base,tweak)
    r.stubs[0x400802ec]=lambda args:0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);src=(root/'tools/machines/seq_gen/stock_ui.s').read_text()
        inverse={'ne':'eq','eq':'ne','lt':'ge','gt':'le','le':'gt','ge':'lt','hi':'ls','ls':'hi','cc':'cs','cs':'cc','mi':'pl','pl':'mi'}
        serial=[0]
        def far(m):
            kind,target=m.groups()
            if kind=='ra':return '    jmp '+target
            serial[0]+=1;label='.Lf'+str(serial[0])
            return '    b'+inverse[kind]+'s '+label+'\n    jmp '+target+'\n'+label+':'
        src=re.sub(r'^[ \t]*b(ra|ne|eq|lt|gt|le|ge|hi|ls|cc|cs|mi|pl)w[ \t]+(\w+)[ \t]*(?:\|[^\n]*)?$',far,src,flags=re.M)
        (p/'ui.s').write_text(src)
        subprocess.run([cross+'as','-march=cfv4e',*sum((['--defsym',x+'=1'] for x in ['SG_SCROLL','SG_DYNAMICS','SG_ADVANCED','SG_SEQUENCE_ONLY','SG_QUEUE']),[]),'-o',str(p/'ui.o'),str(p/'ui.s')],check=True)
        undef=subprocess.check_output([cross+'nm','-u',str(p/'ui.o')],text=True)
        aliases={**{k:int(v,16) for k,v in tweak['symbols'].items()},**{'TG_'+k:v for k,v in tg.items()}}
        bindings='\n'.join(n+' = '+hex(aliases[n])+';' for n in (line.split()[-1] for line in undef.splitlines()))
        (p/'link.ld').write_text(bindings+'\nSECTIONS { .ui 0x93080000 : { *(.text*) *(.rodata*) *(.data*) } }')
        subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-o',str(p/'ui.elf'),str(p/'ui.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'ui.elf'),str(p/'ui.bin')],check=True)
        syms=symbols(cross,p/'ui.elf');r.u.mem_write(0x93080000,(p/'ui.bin').read_bytes())
    if a.bundle:
        bundle=json.loads((root/'tweaks/model-cycles_OS1.13/experimental/midi-bank/60-midi-bank-bundle.json').read_text())
        for part in bundle['append']['parts']:
            r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
        for write in bundle['writes']:
            r.u.mem_write(build.BASE+write['off'],bytes.fromhex(write['new']))
        syms={k:int(v,16) for k,v in bundle['symbols'].items()}
        r.call('sg_open');obj=r.r32(r.s['sg_obj'])
        assert obj and r.r32(r.r32(obj)+16)==syms['sg_render']
    r.w32(r.s['sg_intro'],0);r.w32(r.s['sg_row'],a.row)
    r.w32(r.s['sg_config']+4,80);r.w32(r.s['sg_config']+8,48);r.w32(r.s['sg_config']+12,72)
    r.u.mem_write(tg['scale_state'],b'\1');r.u.mem_write(tg['key_state'],b'\0')
    r.w32(r.s['sg_advanced']+32,1);r.w32(r.s['sg_advanced']+36,5)
    r.w32(r.s['sg_advanced']+28,35)
    r.call(0x400e7dbc)
    bitmap,fb=0x93006000,0x93090000
    r.u.mem_write(fb,bytes(1024));r.call(0x40070172,bitmap,128,64,fb,0)
    try:r.call(syms['sg_render'],0,bitmap)
    except Exception:
        pc=r.u.reg_read(mk.UC_M68K_REG_PC);print('PC',hex(pc),'code',bytes(r.u.mem_read(pc,16)).hex());raise
    data=bytes(r.u.mem_read(fb,1024));assert any(data)
    pixels=[]
    for y in range(63,-1,-1):
        for x in range(128):
            word=struct.unpack_from('>I',data,(x*2+y//32)*4)[0]
            pixels.append(0 if word&(1<<(31-y%32)) else 255)
    pathlib.Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    png(a.output,pixels)
    print('ok : rendu ColdFire, texte/rectangles/polices OS natifs ; renderer natif validé')
if __name__=='__main__':main()
