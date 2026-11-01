"""Dummy3.00 : moteur silencieux, icone native et choix confirme, base3.00 epinglee."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4692d200;BSS=0x46930800
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='05702ddea6d59174275b6008ce5395cc5ed7b3dbd9c5073d8f3c2b1e34d418f1');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
am=m['activity_masks'];ams=am['symbols'];prev=m['cpu_monitor'];previous=ams['am_boot_finish'];tiny=m['tiny_extra']['symbols'];ps=m['per_track_fx']['symbols']
optional='mb_display_count' in ams
full=am['full']
assert optional and full,'Dummy reserve a Optional Full'
order=(list(range(17))+list(range(18,28 if optional else 25))+[17,28]) if full else list(range(6))+[28]
from dummy300_assets import make
make(O,order)
aliases={k:ams[k] for k in ('mb_silent','mb_native_rotate','mb_native_key','rm_machine_valid','rm_machine_stamp','rm_machine_result')}
aliases.update(dy_gov_quiet=0x4673205e,dy_gov_cost=0x4673200a,dy_gov_peak=0x46732022,dy_qt_engines=m['complete_irq_accounting']['symbols']['qt_engines'],dy_side_on=ps['mf_side_on'])
body=(R/'tools/machines/track_fx/machine-confirm.c').read_text().replace('volatile u32 mb_silent=0,mb_pending,mb_candidate,mb_lane,mb_all,mb_view;','extern volatile u32 mb_silent;volatile u32 mb_pending,mb_candidate,mb_lane,mb_all,mb_view;')
body=body.replace('extern const u8 rm_order[];extern const u32 rm_count;','extern const u8 dy_order[];extern const u32 dy_count;extern u32 dy_allowed(u32);\n#define rm_order dy_order\n#define rm_count dy_count')
if optional:body=body.replace('if(machine==21)machine=4;','')
body=body.replace('if(delta>0&&pos+1<rm_count)pos++;if(delta<0&&pos)pos--;','if(delta)for(int i=(int)pos+(delta>0?1:-1);i>=0&&i<(int)rm_count;i+=delta>0?1:-1)if(dy_allowed(rm_order[i])){pos=(u32)i;break;}')
(O/'machine-confirm.c').write_text(body)
from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
end=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
def raw(at,n=32):
 if at<0x40200000:return bytes(image[at-BASE:at-BASE+n])
 for v in m.values():
  if isinstance(v,dict) and 'code' in v and 'loader' in v and v['code']<=at<v['code']+v.get('code_bytes',0):
   off=v['loader']+512-BASE+at-v['code'];return bytes(image[off:off+n])
 off=end+at-0x467ab360;return bytes(image[off:off+n])
late=[(0x400a7d96,'dy_voice'),(0x400a2612,'dy_names'),(tiny['tiny_left'],'dy_left'),(tiny['tiny_right'],'dy_right'),(tiny['shown'],'dy_shown'),(tiny['amp_gate'],'dy_amp_gate'),(tiny['lfo_gate'],'dy_lfo_gate'),(tiny['tiny_menu_increment'],'dy_increment'),(tiny['marks'],'dy_marks'),(0x4001477e,'dy_set'),(ams['mb_display_hook'],'dy_display_hook')]
tramp='.text\n'
for at,fn in late:
 if fn not in ('dy_names','dy_left','dy_right','dy_shown','dy_amp_gate','dy_lfo_gate','dy_set'):continue
 name='dy_old_'+fn[3:];v=raw(at)
 if v[:2]==b'\x4e\xf9':aliases[name]=int.from_bytes(v[2:6],'big')
 else:
  n=0;instructions=[]
  for ins in cs.disasm(v,at):
   assert 'pc' not in ins.op_str and not ins.mnemonic.startswith('j'),str(ins)
   instructions.append(ins);n+=ins.size
   if n>=6:break
  assert 6<=n<=16
  tramp+='\n.globl '+name+'\n'+name+':\n'
  inverse={'bne':'beq','beq':'bne','bhi':'bls','bls':'bhi','bcc':'bcs','bcs':'bcc','bpl':'bmi','bmi':'bpl','bge':'blt','blt':'bge','bgt':'ble','ble':'bgt'}
  for j,ins in enumerate(instructions):
   op=ins.mnemonic.split('.')[0]
   if op.startswith('b'):
    target=int(ins.op_str.replace('$','0x'),16);assert not at<=target<at+n
    assert op in inverse,str(ins)
    tramp+=f' {inverse[op]}.s .L_{name}_{j}\n jmp {target:#x}\n.L_{name}_{j}:\n'
   else:tramp+='.byte '+','.join(map(str,ins.bytes))+'\n'
  tramp+=f' jmp {at+n:#x}\n'
for name in ('mb_rotate','mb_step','mb_key','mb_display_machine','mb_cancel'):late.append((ams[name],name))
assert raw(0x400a7d96,6).hex()=='2005e4a07201'
assert raw(0x400147a4,2)[0]==0x70
assert int.from_bytes(raw(0x4683c800+41*56+12,4),'big') in (5<<8,24<<8,27<<8)
# Les helpers MD sont poses avant notre installateur tardif : capturer leur
# destination courante pour conserver leurs icones et pages de parametres.
links=[(at,fn,'dy_old_'+fn[3:]) for at,fn in late if 'dy_old_'+fn[3:] in aliases or 'dy_old_'+fn[3:]+':' in tramp]
for at,fn,old in links:
 tramp+='\n.globl dy_fallback_'+fn[3:]+'\ndy_fallback_'+fn[3:]+':\n move.l dy_next_'+fn[3:]+',-(%sp)\n rts\n'
tramp+='\n.bss\n.balign 4\n'
for at,fn,old in links:tramp+='.globl dy_next_'+fn[3:]+'\ndy_next_'+fn[3:]+': .skip 4\n'
tramp+='\n.text\n'
asm=tramp+'.globl dy_install\ndy_install:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n'
for i,(at,fn,old) in enumerate(links):
 pointer='dy_next_'+fn[3:]
 asm+=f' lea {pointer},%a1\n move.l #{old},(%a1)\n moveq #0,%d0\n move.w {at:#x},%d0\n cmpi.l #0x4ef9,%d0\n bne.s .Ldyn{i}\n move.l {at+2:#x},%d0\n cmpi.l #{fn},%d0\n beq.s .Ldyn{i}\n move.l %d0,(%a1)\n.Ldyn{i}:\n'
asm+=' move.l '+hex(0x4683c800+41*56+12)+',%d0\n cmpi.l #6912,%d0\n bne.s 1f\n lea dy_md_present,%a1\n move.l #1,(%a1)\n1:\n'
asm+=' lea 0x400147a4,%a1\n move.w #0x701c,(%a1)\n lea '+hex(0x4683c800+41*56+12)+',%a1\n move.l #7168,(%a1)\n'
for at,fn in late:asm+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)\n'
asm+=f' movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp {previous:#x}\n'
(O/'bridge.S').write_text(asm)
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) *(.rodata*) } .bss '+hex(BSS)+' (NOLOAD) : { *(.bss*) *(COMMON) } . = ALIGN(4); dy_end = .; }\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
objects=[]
for name,path in [('bridge',O/'bridge.S'),('engine',R/'tools/machines/track_fx/dummy300.S'),('ui',R/'tools/machines/track_fx/dummy300.c'),('assets',O/'dummy-assets.c'),('confirm',O/'machine-confirm.c')]:
 obj=O/(name+'.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',f'-DDY_FULL={int(full)}',f'-DDY_OPTIONAL={int(optional)}','-c',path,'-o',obj);objects.append(obj)
run('ld','-T',O/'module.ld','-o',O/'module.elf',*objects);run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=0x4692f000 and s['dy_end']<0x46931000
lo=prev['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+prev['code_bytes']]);assert chunk.count(old)==1;patchat=lo+chunk.index(old)+2;struct.pack_into('>I',image,patchat,s['dy_install']);relay_patch=BASE+patchat
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s["dy_end"]-BSS)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
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
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_3.00_Dummy_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['dummy300']=dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_end=s['dy_end'],symbols=s,aliases=aliases,loader=loader,boot_target=s['dy_install'],boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),machine=28,order=order,late_hooks=[dict(at=at,target=s[fn],function=fn) for at,fn in late],hardware_tested=False)
for k,v in s.items():
 if k.startswith('mb_') and k not in ('mb_native_rotate','mb_native_key','mb_silent'):m['activity_masks']['symbols'][k]=v
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT Dummy',len(blob),'code bytes',sha(result),flush=True)
