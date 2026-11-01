"""ChordKeys3.00 Optional : stockage compact compatible Page Length et codec natif."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x46939000;BSS=0x4693fe00
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='6fcd5d9330dcde3843e5f521c5c2cb5e8b3eabe9f79703355ed68456537b14cd');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
assert not m.get('chordkeys_removed'),'Ne pas restaurer ChordKeys dans Main'
am=m['activity_masks'];prev=m.get('transfer300') or m.get('dummy300') or m['cpu_monitor'];previous=am['symbols']['am_boot_finish'];ck={k:int(v,0) for k,v in json.loads((R/'docs/flasher/source/integration-chord-keys.json').read_text())['symbols'].items()}
aliases={new:ck[old] for new,old in [('cs_valid','ck_storage_valid'),('cs_irq_save','ck_storage_irq_save'),('cs_irq_restore','ck_storage_irq_restore'),('cs_clear_header','ck_ui_clear_header'),('cs_clear_modifiers','ck_ui_clear_modifiers'),('cs_object','ui_header_object'),('cs_audio_header','audio_header'),('cs_ui_header','ck_ui_header')]}
late=[(ck[old],new) for old,new in [('ck_storage_read','cs_read'),('ck_storage_reset','cs_reset'),('ck_storage_load','cs_load'),('ck_ui_config_set','cs_set'),('ck_ui_midi_get','cs_ui_midi_get'),('ck_audio_midi_get','cs_audio_midi_get'),('ck_ui_midi_set','cs_ui_midi_set')]]
asm='.text\n.globl cs_install\ncs_install:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n'
for at,fn in late:asm+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)\n'
asm+=f' movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp {previous:#x}\n'
(O/'bridge.S').write_text(asm)
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) *(.rodata*) } .bss '+hex(BSS)+' (NOLOAD) : { *(.bss*) *(COMMON) } . = ALIGN(4); cs_end = .; }\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');run('gcc','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-common','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',R/'tools/machines/track_fx/chord-storage300.c','-o',O/'storage.o');run('ld','-T',O/'module.ld','-o',O/'module.elf',O/'bridge.o',O/'storage.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert prev['code']+prev['code_bytes']<=CODE and CODE+len(blob)<=0x4693e000 and prev['bss_end']<=BSS and s['cs_end']<=0x46940000
lo=prev['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+prev['code_bytes']]);assert chunk.count(old)==1;patchat=lo+chunk.index(old)+2;struct.pack_into('>I',image,patchat,s['cs_install']);relay_patch=BASE+patchat
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s["cs_end"]-BSS)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
(O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','cal_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
from title204_assets import apply
# Identifiant experimental distinct ; aucun push/flasher modifie.
def patch(at,old,new,buf):assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
m['title_screen']=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,patch,'3.00',lite=not am['full'],previous=m['title_screen'])
# Tokens de compression officiels, comme les generateurs prives existants.
stockops=read(a.cycles)[3];dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for sec in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_3.00_ChordKeys_Persistence_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['chord_storage300']=dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_end=s['cs_end'],symbols=s,aliases=aliases,loader=loader,boot_target=s['cs_install'],boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),format='CK4/6x26bits/header40..59',page_length_independent=True,late_hooks=[dict(at=at,target=s[fn],function=fn) for at,fn in late],hardware_tested=False)
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT ChordKeys persistence',len(blob),'code bytes',sha(result),flush=True)
