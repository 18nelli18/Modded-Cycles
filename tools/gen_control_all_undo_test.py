"""Patch UI prive sur la base2.94 : undo BACK natif et sortie double BACK."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4691f100;BSS=0x4691f900
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='eac5566104acb4edbbb2dd54fd8a5d9e5ae7da334a8b2c5b9d27e75181078465');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];oldcal=m['control_all_latch'];ig=m['complete_irq_accounting']
optional=am['code']>=0x4691c400
if optional:CODE=0x4692a000;BSS=0x4692f100
assert am['bss_end']<=CODE and oldcal['bss_end']<BSS
aliases={k:oldcal['symbols'][k] for k in ('fx_notice','menu','cal_old_key','cal_old_encoder','cal_old_held')}
aliases['cal_old_boot']=am['symbols']['am_boot_finish']
late=[(h['at'],fn,h['size']) for h,fn in zip(oldcal['late_hooks'],('cal_key','cal_encoder','cal_held'))]
asm='.text\n'
asm+='.globl cal_finish\ncal_finish:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n'
for at,fn,n in late:
 asm+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)+\n'+(' nop\n'*((n-6)//2))
asm+=' movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp cal_old_boot\n'
(O/'bridge.S').write_text(asm,encoding='utf-8');(O/'latch.c').write_text((R/'tools/machines/control_all_latch/latch.c').read_text(encoding='utf-8'),encoding='utf-8')
(O/'module.ld').write_text('SECTIONS { . = '+hex(CODE)+'; .text : { *(.text*) *(.rodata*) *(.data*) } . = '+hex(BSS)+'; .bss : { *(.bss*) *(COMMON) } . = ALIGN(4); cal_end = .; }\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
for name in ['latch.c','bridge.S']:run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',O/name,'-o',O/(Path(name).stem+'.o'))
run('ld','-T',O/'module.ld','-o',O/'module.elf',O/'latch.o',O/'bridge.o');run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert not (CODE<am['bss_end'] and CODE+len(blob)>am['bss']);assert CODE+len(blob)<=(0x4692a800 if optional else oldcal['bss']);assert s['cal_end']<(0x4692f800 if optional else 0x46920000)
# Modifier uniquement le relais de fin2.94, sans changer son DSP.
lo=ig['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',oldcal['boot_target']);chunk=bytes(image[lo:lo+ig['code_bytes']]);assert chunk.count(old)==1;at=lo+chunk.index(old)+2;struct.pack_into('>I',image,at,s['cal_finish']);relay_patch=BASE+at
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s["cal_end"]-BSS)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
(O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','cal_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=512
struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(512-len(stub))+blob
from title204_assets import apply
# Identifiant experimental distinct ; aucun push/flasher modifie.
def patch(at,old,new,buf):assert bytes(buf[at-BASE:at-BASE+len(old)])==old;buf[at-BASE:at-BASE+len(old)]=new
m['title_screen']=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,image,patch,'2.95',lite=not am['full'],previous=m['title_screen'])
# Tokens de compression officiels, comme les generateurs prives existants.
stockops=read(a.cycles)[3];dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,_=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for sec in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.95_Control_All_Undo_Estus_Audit_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
s.update(aliases)
m['control_all_undo']=dict(base_release='2.94',native_back_undo=True,double_back_exit=True,audio_unchanged=True,estus_audit='one voice per track; no synthesis changes')
m['control_all_latch']=dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_end=s['cal_end'],symbols=s,loader=loader,previous_loader=oldentry,late_hooks=[dict(at=at,target=s[fn],size=n) for at,fn,n in late],boot_target=s['cal_finish'],source_sha256=sha(a.source.read_bytes()),boot_relay_patch=relay_patch,hardware_tested=False,audio_hooks_added=False)
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT control-all latch',len(blob),'code bytes',sha(result),flush=True)
