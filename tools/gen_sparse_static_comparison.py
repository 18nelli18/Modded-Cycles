"""Comparaison privee2.98 : mixeur natif6 a gains stables et sources nulles, base2.96."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x46922000;BSS=0x46924000
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='51f5845512c28c22134d1ccf5135bf68706330bb4bb9b2fd368717722ee8bd1d');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];osc=m['native_second_mod'];jp=m['direct_jump'];ig=m['complete_irq_accounting'];at=m['static_gain_mixer']['symbols']['sg_static6'];assert jp['code']+jp['code_bytes']<=CODE and CODE<BSS
previous=am['symbols']['am_boot_finish'];off=ig['loader']+512-BASE+at-ig['code'];oldprefix=bytes(image[off:off+8]);assert oldprefix.hex()=='4fefffe048d70cfc'
asm=(R/'tools/machines/track_fx/sparse-static-mix.S').read_text()
asm+=f'\n.globl sm_install\nsm_install:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #sm_dispatch,(%a1)+\n move.w #0x4e71,(%a1)\n movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp {previous:#x}\n'
(O/'bridge.S').write_text(asm);(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) } }\nsm_resume = '+hex(at+8)+';\n')
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');run('ld','-T',O/'module.ld','-o',O/'module.elf',O/'bridge.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS
lo=osc['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+osc['code_bytes']]);assert chunk.count(old)==1;patchat=lo+chunk.index(old)+2;struct.pack_into('>I',image,patchat,s['sm_install']);relay_patch=BASE+patchat
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
(O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','cal_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
from title204_assets import apply
# Identifiant experimental distinct ; aucun push/flasher modifie.
def patch(at,old,new,buf):assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
m['title_screen']=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,patch,'2.98',lite=not am['full'],previous=m['title_screen'])
# Tokens de compression officiels, comme les generateurs prives existants.
stockops=read(a.cycles)[3];dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for sec in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.98_Sparse_Static_Mixer_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['sparse_static_mixer']=dict(code=CODE,code_bytes=len(blob),symbols=s,target=s['sm_dispatch'],hook=at,original_prefix=oldprefix.hex(),loader=loader,boot_target=s['sm_install'],boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),governor_unchanged=True,stage_instrumentation=False,hardware_tested=False)
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT sparse static mixer',len(blob),'code bytes',sha(result),flush=True)
