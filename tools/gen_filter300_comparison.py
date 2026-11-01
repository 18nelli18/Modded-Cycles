"""Filtre3.00 : types par pattern, resonance native0..15000, base2.99 epinglee."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
from bootstrap205_assets import pack
import aplib_grow
CODE=0x4692b000;BSS=0x4692f200
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--metadata',type=Path,required=True);p.add_argument('--cycles',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check',action='store_true');p.add_argument('--expected-sha256',default='9abe84ff10012a31097c57b09ba85be11ec52c514bdc23b4c540b24c72009f71');a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(a.source.read_bytes())==a.expected_sha256
m=json.loads(a.metadata.read_text(encoding='utf-8'));assert m['sha256']==sha(a.source.read_bytes())
assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
info,pkg,image,ops=read(a.source);image=bytearray(image);stock=read(a.cycles)[2];O=a.output;O.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
assert m['cpu_monitor']['code']+m['cpu_monitor']['code_bytes']<=CODE and m['cpu_monitor']['bss']==0x4692f800
assert m['native_second_mod']['code']+m['native_second_mod']['code_bytes']<=CODE
am=m['activity_masks'];previous=am['symbols']['am_boot_finish'];prev=m['cpu_monitor'];fm=m['filter_modes']['symbols'];ps=m['per_track_fx']['symbols']
aliases=dict(fc_type=fm['fc_type'],fc_native_table=fm['fc_native_table'],fp_open=fm['open'],fp_lane=fm['lane'],fp_cursor=fm['cursor'],fp_generation=0x468f6e80,fp_quiet=m['filter_modes']['aliases']['fc_input_quiet'],fp_crc=ps['mf_crc'],fp_low=fm['fc_low'],fp_modes=fm['fc_filter'])
aliases.update(wp_mask_pointer=m['acid_articulation']['symbols']['wp_mask_pointer'],aa_face_encoder=m['acid_articulation']['symbols']['aa_face_encoder'],aa_old_encoder=m['acid_articulation']['symbols']['aa_old_encoder'])
late=[(m['acid_articulation']['symbols']['wp_before'],'wp_before'),(m['acid_articulation']['symbols']['wp_after'],'wp_after'),(ps['fast_pf_coeff'],'fast_pf_coeff'),(ps['fast_fc_coeff'],'fast_fc_coeff'),(fm['fc_get_type_real'],'fp_get'),(fm['fc_set_type_real'],'fp_set'),(fm['fc_frame_real'],'fp_frame')]
ams=am['symbols'];aliases.update({k:ams[k] for k in ('mb_silent','mb_native_rotate','mb_native_key','rm_machine_valid','rm_machine_stamp','rm_machine_result')})
body=(R/'tools/machines/track_fx/machine-confirm.c').read_text().replace('volatile u32 mb_silent=0,mb_pending,mb_candidate,mb_lane,mb_all,mb_view;','extern volatile u32 mb_silent;volatile u32 mb_pending,mb_candidate,mb_lane,mb_all,mb_view;')
if 'mb_display_count' in ams:
 order=list(range(17))+list(range(18,28))+[17] if am['full'] else list(range(6))
 body=body.replace('if(machine==21)machine=4;','').replace('extern const u8 rm_order[];extern const u32 rm_count;','static const u8 rm_order[]={'+','.join(map(str,order))+'};static const u32 rm_count='+str(len(order))+';\nstatic u32 mb_enabled(u32 m){u32 md=*(volatile u32*)(0x4683c800+41*56+12)==(27u<<8),mask=md?*(volatile u32*)0x469c423c:*(volatile u32*)0x468d0ff0;if(!md&&!mask)mask=0x7ffff;return m<6||(m<28&&((mask>>(m-6))&1));}')
 body=body.replace('if(delta>0&&pos+1<rm_count)pos++;if(delta<0&&pos)pos--;','if(delta)for(int i=(int)pos+(delta>0?1:-1);i>=0&&i<(int)rm_count;i+=delta>0?1:-1)if(mb_enabled(rm_order[i])){pos=(u32)i;break;}')
else:aliases.update(rm_order=ams['rm_order'],rm_count=ams['rm_count'])
(O/'machine-confirm300.c').write_text(body)
for name in ('mb_rotate','mb_step','mb_key','mb_display_machine','mb_cancel'):late.append((ams[name],name))
# Rejouer des prologues complets : aucune adresse relative au PC dans ces stubs.
from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
tramp='.text\n'
for at,newname in [(ps['mf_pattern_copy'],'fp_copy'),(ps['mf_pattern_init'],'fp_init'),(ps['mf_project_encode'],'fp_encode'),(m['lfo_reload']['symbols']['xp_change'],'fp_change'),(m['lfo_reload']['symbols']['xp_sync'],'fp_lfosync')]:
 # Le module historique est stocke dans la queue decompressee467ab360.
 end=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 raw=bytes(image[end+at-0x467ab360:end+at-0x467ab360+32]);n=0
 if raw[:2]==b'\x4e\xf9':aliases['fp_old_'+newname[3:]]=int.from_bytes(raw[2:6],'big')
 else:
  for ins in cs.disasm(raw,at):
   assert 'pc' not in ins.op_str and not ins.mnemonic.startswith(('b','j')),str(ins)
   n+=ins.size
   if n>=6:break
  assert 6<=n<=16
  name='fp_old_'+newname[3:];tramp+='\n.globl '+name+'\n'+name+':\n.byte '+','.join(map(str,raw[:n]))+f'\n jmp {at+n:#x}\n'
 late.append((at,newname))
asm=tramp+'.globl fp_install\nfp_install:\n lea -8(%sp),%sp\n movem.l %d0/%a1,(%sp)\n'
for at,fn in late:asm+=f' lea {at:#x},%a1\n move.w #0x4ef9,(%a1)+\n move.l #{fn},(%a1)\n'
asm+=f' movem.l (%sp),%d0/%a1\n lea 8(%sp),%sp\n jmp {previous:#x}\n'
(O/'bridge.S').write_text(asm)
(O/'module.ld').write_text('SECTIONS { .text '+hex(CODE)+' : { *(.text*) *(.rodata*) } .bss '+hex(BSS)+' (NOLOAD) : { *(.bss*) *(COMMON) } . = ALIGN(4); fp_end = .; .wpbss 0x46930200 (NOLOAD) : { *(.wpbss) } . = ALIGN(4); wp_end = .; }\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
run('gcc','-mcpu=54418','-c',O/'bridge.S','-o',O/'bridge.o');objects=[O/'bridge.o']
for name in ('filter-low','filter-modes','filter-pattern300'):
 obj=O/(name+'.o');run('gcc','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-common','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',R/('tools/machines/track_fx/'+name+'.c'),'-o',obj);objects.append(obj)
obj=O/'machine-confirm300.o';run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',O/'machine-confirm300.c','-o',obj);objects.append(obj)
obj=O/'wizard-priority.o';run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',R/'tools/machines/wizard_priority/control.c','-o',obj);run('objcopy','--rename-section','.bss=.wpbss',obj);objects.append(obj)
run('ld','-T',O/'module.ld','-o',O/'module.elf',*objects);run('objcopy','-O','binary',O/'module.elf',O/'module.bin')
s={v[2]:int(v[0],16) for line in run('nm',O/'module.elf').splitlines() if len(v:=line.split())==3};blob=(O/'module.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=0x4692f000 and s['fp_end']<=0x4692f800 and s['wp_end']<0x46931000
lo=prev['loader']+512-BASE;old=b'\x4e\xf9'+struct.pack('>I',previous);chunk=bytes(image[lo:lo+prev['code_bytes']]);assert chunk.count(old)==1;patchat=lo+chunk.index(old)+2;struct.pack_into('>I',image,patchat,s['fp_install']);relay_patch=BASE+patchat
oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;source=loader+512
load=f'.text\n.globl cal_load\ncal_load:\n lea -12(%sp),%sp\n movem.l %d0/%a0-%a1,(%sp)\n lea {source:#x},%a0\n lea {CODE:#x},%a1\n move.l #{len(blob)//4},%d0\n1: move.l (%a0)+,(%a1)+\n subq.l #1,%d0\n bne.s 1b\n lea {BSS:#x},%a0\n move.l #{(s["fp_end"]-BSS)//4},%d0\n2: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 2b\n lea 0x46930200,%a0\n move.l #{(s["wp_end"]-0x46930200)//4},%d0\n3: clr.l (%a0)+\n subq.l #1,%d0\n bne.s 3b\n movem.l (%sp),%d0/%a0-%a1\n lea 12(%sp),%sp\n jmp {oldentry:#x}\n'
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
result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_3.00_Filter_Regression_Experimental.syx'
if a.check:assert target.read_bytes()==result
else:target.write_bytes(result)
m['filter_pattern300']=dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_end=s['fp_end'],wizard_bss=0x46930200,wizard_bss_end=s['wp_end'],symbols=s,aliases=aliases,loader=loader,boot_target=s['fp_install'],boot_relay_patch=relay_patch,source_sha256=sha(a.source.read_bytes()),late_hooks=[dict(at=at,target=s[fn],function=fn) for at,fn in late],hardware_tested=False)
for k,v in s.items():
 if k.startswith('mb_') and k not in ('mb_native_rotate','mb_native_key'):m['activity_masks']['symbols'][k]=v
m['silent_browse300']=dict(context_invalidation=True,hardware_tested=False)
m['wizard_priority']=dict(code=CODE,loader=loader,symbols=s,active_note_bitmap=True,hardware_tested=False)
m.update(sha256=sha(result),main_os_sha256=sha(image));(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('BUILT filter3.00',len(blob),'code bytes',s['fp_end']-BSS,'BSS bytes',sha(result),flush=True)
