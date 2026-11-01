"""Moniteur DX2.99 : SETTINGS BACK, UI4Hz, delegation native des controles, base2.98."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x46926c00;BSS=0x4692f800
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='f06cdebebd6e2d6b7899015261aabbedd06f4748cfac6d78395c465797f12021');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];ig=m['complete_irq_accounting'];prev=m['native_two_mix300'];fx=m['fx_menu']['symbols'];ps=m['per_track_fx']['symbols'];art=m['acid_articulation']['symbols'];previous=am['symbols']['am_boot_finish']
assert m['cpu_monitor']['code']+m['cpu_monitor']['code_bytes']<=CODE<0x46928000
aliases=dict(m['cpu_monitor']['aliases']);aliases['cpu_govern']=ps['mf_old_audio_end']
late=[(art['aa_face_key'],'cpu_key'),(art['aa_face_encoder'],'cpu_encoder'),(fx['fx_stack_overlay'],'cpu_stack'),(am['symbols']['mb_frame'],'cpu_frame'),(fx['fx_diag_gesture'],'cpu_legacy_gesture'),(ig['symbols']['dt_audio_end'],'cpu_audio_end')]
asm='.text\n.globl cpu_install\ncpu_install:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n'
for at,fn in late:asm+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)\n'+(' move.w #0x4e71,4(%a1)\n' if fn=='cpu_frame' else '')
asm+=f' movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp {previous:#x}\n'
(O/'bridge.S').write_text(asm);(O/'monitor.c').write_text((R/'tools/machines/track_fx/cpu-monitor.c').read_text())
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) *(.rodata*) } .bss '+hex(BSS)+' (NOLOAD) : { *(.bss*) *(COMMON) } . = ALIGN(4); cpu_end = .; }\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',O/'monitor.c','-o',O/'monitor.o');run('ld','-T',O/'module.ld','-o',O/'module.elf',O/'bridge.o',O/'monitor.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=0x46928000 and s['cpu_end']<=0x46930000
lo=prev['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+prev['code_bytes']]);assert chunk.count(old)==1;patchat=lo+chunk.index(old)+2;struct.pack_into('>I',image,patchat,s['cpu_install']);relay_patch=BASE+patchat
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s["cpu_end"]-BSS)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
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
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_3.00_Recent_Cuts_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['cpu_monitor']=dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_end=s['cpu_end'],symbols=s,aliases=aliases,loader=loader,boot_target=s['cpu_install'],boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),late_hooks=[dict(at=at,target=s[fn],function=fn) for at,fn in late],refresh_hz=4,global_dx_gated=True,legacy_func_popup_disabled=True,native_knobs_and_transport=True,irq_hooks_added=False,recent_cuts=6,pages=3,track5_focus=False,hardware_tested=False)
for h in m['control_all_latch']['late_hooks']:
 if h['at']==art['aa_face_key']:h['target']=s['cpu_key']
 if h['at']==art['aa_face_encoder']:h['target']=s['cpu_encoder']
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT live CPU monitor',len(blob),'code bytes',sha(result),flush=True)
