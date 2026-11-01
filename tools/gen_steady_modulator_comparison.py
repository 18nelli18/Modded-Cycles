"""Comparaison privee2.96 : second operateur FM, profondeur stable et chemin sec exact sur la base2.95."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4691fa00;BSS=0x46920000
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='d0c1d2d710bf8b7a2f24174028fab726124b2049f26259f98a70e19e5a3dea75');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];cal=m['control_all_latch']
if am['code']>=0x4691c400:CODE=0x4692a800;BSS=0x4692b000
assert cal['code']+cal['code_bytes']<=CODE and (cal['bss_end']<=CODE or cal['bss']>=BSS)
previous=am['symbols']['am_boot_finish']
asm=(R/'tools/machines/track_fx/steady-mod-second.S').read_text()
asm+='\n.globl of_install\nof_install:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n lea 0x400a82cc,%a1\n move.w #0x4ef9,(%a1)+\n move.l #om_osc,(%a1)\n movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp '+hex(previous)+'\n'
(O/'bridge.S').write_text(asm)
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) } }\nom_native = '+hex(m['complete_irq_accounting']['symbols']['om_native'])+';\n')
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');run('ld','-T',O/'module.ld','-o',O/'module.elf',O/'bridge.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS
assert image[0x400a82cc-BASE:0x400a82d2-BASE]==b'\x4e\xf9'+struct.pack('>I',m['per_track_fx']['symbols']['dry_osc'])
lo=cal['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+cal['code_bytes']]);assert chunk.count(old)==1;at=lo+chunk.index(old)+2;struct.pack_into('>I',image,at,s['of_install']);relay_patch=BASE+at
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
(O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','cal_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
from title204_assets import apply
# Identifiant experimental distinct ; aucun push/flasher modifie.
def patch(at,old,new,buf):assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
m['title_screen']=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,patch,'2.96',lite=not am['full'],previous=m['title_screen'])
# Tokens de compression officiels, comme les generateurs prives existants.
stockops=read(a.cycles)[3];dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for sec in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.96_Steady_Modulator_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['native_second_mod']=dict(code=CODE,code_bytes=len(blob),symbols=s,target=s['om_osc'],loader=loader,previous_loader=oldentry,boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),depth_and_ramp_guards=True,steady_mod_depth_with_amp_ramp=True,direct_dry_path=True,first_operator_unchanged=True,governor_unchanged=True,hardware_tested=False)
for h in m['complete_irq_accounting']['late_hooks']:
 if h['at']==0x400a82cc:h['target']=s['om_osc']
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT steady second operator',len(blob),'code bytes',sha(result),flush=True)
