"""GOV Lod/Trk : rang seulement, seuils/eligibilite/fondu preserves."""
from pathlib import Path
import os,sys,struct,json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=0x46700000;NB=0x40000400
CODE=0x467a2200;BSS=0x467a2fc0;END=0x467a3000

def apply(meta,native,runtime,sram,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);assert not meta.get('gov_policy372')
 assert not any(runtime[CODE-BASE:END-BASE])
 assert any(e['kind']=='remove' and e['address']<=CODE and END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 sys.path.insert(0,str(ROOT/'tools/emu'));from test_seq_gen_menu import Rig
 from unicorn import UC_HOOK_CODE
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 sy=meta['activity_masks']['symbols'];r=Rig(bytes(native),{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(BASE,0x300000);r.u.mem_write(BASE,bytes(runtime));objects=[]
 def bind(at,fn):
  if at not in r.stubs:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 bind(sy['mb_tree_row'],lambda a:0);bind(sy['mb_edit'],lambda a:0);bind(0x400423e4,lambda a:objects.append(a[0]) or 0)
 r.call(sy['mb_global_draw'],0,0x93010000);obj=objects[-1];vt=r.r32(obj);count=r.call(r.r32(vt+12),obj);assert count in (12,13),count
 rows=[];rowbase=None
 for i in range(count):
  from unicorn import m68k_const as C
  r.u.reg_write(C.UC_M68K_REG_A0,0x931f0000);r.call(r.r32(vt+16),obj,i);item=r.r32(0x931f0000);rowbase=item if i==0 else rowbase;assert item==rowbase+84*i;rows.append(bytes(r.u.mem_read(item,84)))
 aliases={k:meta['direct_jump']['aliases'].get(k,meta['direct_jump']['symbols'].get(k)) for k in ['menu','row','gc_level','gc_tree_cursor','gc_page','sx_submenu','du_page','mq_page','gc_input_quiet']}
 for k in list(aliases):
  if aliases[k] is None:aliases[k]=meta['per_track_fx']['symbols'][k]
 aliases['gc_tree_row']=sy['mb_tree_row'];aliases['gp_native_rows']=rowbase
 view=(ROOT/'tools/machines/direct_jump/global.S').read_text().split('.Lts_rows:')[0]
 view=view.replace('mf_global_draw','gp_global_draw').replace('ae_global_edit','gp_edit').replace('moveq #11,%d0',f'moveq #{count+1},%d0')
 view=view.replace('    jsr gc_tree_row',''.join(f'    clrb %a0@({80+84*i})\n' for i in range(11,count+1))+'    jsr gc_tree_row',1)
 # Reutiliser les13records natifs ; seul GOV a un record supplementaire.
 view=view.replace('lea.l .Lts_rows,%a0','lea.l gp_native_rows,%a0')
 extra=''.join(f'    clrb %a0@({80+84*i})\n' for i in range(11,count+1))
 view=view.replace(extra,''.join(f'    clrb %a0@({80+84*i})\n' for i in range(11,count))+'    lea.l .Lgov_row,%a0\n    clrb %a0@(80)\n')
 view=view.replace('    muluw #84,%d0\n    lea.l gp_native_rows,%a0\n    addal %d0,%a0',f'    cmpil #{count},%d0\n    beq .Lgov_edit\n    muluw #84,%d0\n    lea.l gp_native_rows,%a0\n    addal %d0,%a0\n    bra .Lgov_edit_done\n.Lgov_edit:\n    lea.l .Lgov_row,%a0\n.Lgov_edit_done:')
 view=view.replace('    muluw #84,%d0\n    lea.l .Lts_rows,%a1\n    addal %d0,%a1',f'    cmpil #{count},%d0\n    beq .Lgov_item\n    muluw #84,%d0\n    lea.l gp_native_rows,%a1\n    addal %d0,%a1\n    bra .Lgov_item_done\n.Lgov_item:\n    lea.l .Lgov_row,%a1\n.Lgov_item_done:')
 view=view[:view.index('.Llabel0:')]+'.Lallocator: .byte 0\n'
 view=view.replace('.Lts_label','gp_label').replace('.text\n','.text\n.globl gp_label\n',1)
 view+='\n.Lgov_label: .asciz "GOV"\n.balign 4\n.Lgov_row:\n.long 0,0,0,.Lgov_label,0,1,gp_label,0,0,0,0,0,0,1,gp_value,0,0,0,0,0,0\n'
 (out/'global.S').write_text(view)
 md=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);hooks=[];tramp='.text\n'
 for old,new in [('mb_edit','gp_edit'),('mb_gc_key','gp_key'),('mb_gc_encoder','gp_encoder'),('mb_frame','gp_frame')]:
  at=sy[old];raw=bytes(runtime[at-BASE:at-BASE+24]);n=0
  for ins in md.disasm(raw,at):
   assert not ins.mnemonic.startswith('b') and 'pc' not in ins.op_str,(old,ins.mnemonic,ins.op_str)
   n+=ins.size
   if n>=6:break
  assert n>=6;name='gp_old_'+{'mb_edit':'edit','mb_gc_key':'key','mb_gc_encoder':'encoder','mb_frame':'frame'}[old]
  tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';hooks.append((at,raw[:n],new))
 (out/'old.S').write_text(tramp)
 ld=f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} gp_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items());(out/'gov.ld').write_text(ld)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 objs=[]
 for src in (out/'global.S',out/'old.S',ROOT/'tools/machines/track_fx/gov-policy372.c'):
  obj=out/(src.name+'.o');objs.append(obj);run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',f'-DGP_ROW={count}','-c',src,'-o',obj)
 run('ld','-T',out/'gov.ld','-o',out/'gov.elf',*objs);run('objcopy','-O','binary',out/'gov.elf',out/'gov.bin');blob=(out/'gov.bin').read_bytes();symbols={v[2]:int(v[0],16) for line in run('nm',out/'gov.elf').splitlines() if len(v:=line.split())==3};assert CODE+len(blob)<=BSS,(len(blob),BSS-CODE);assert symbols['gp_end']<=END
 patches=[]
 def patch(buf,origin,at,old,new):
  assert len(old)==len(new);off=at-origin;assert bytes(buf[off:off+len(old)])==old;buf[off:off+len(old)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex(),region='sram' if origin==0x80000000 else 'runtime'))
 for at,old,target in hooks:patch(runtime,BASE,at,old,b'\x4e\xf9'+struct.pack('>I',symbols[target])+b'\x4e\x71'*((len(old)-6)//2))
 at=sy['mb_global_draw'];old=bytes(runtime[at-BASE:at-BASE+6]);patch(runtime,BASE,at,old,b'\x4e\xf9'+struct.pack('>I',symbols['gp_global_draw']))
 # Les labels anciens deleguent au meme constructeur de string, reloge ici.
 for i in range(count):
  at=rowbase+84*i+24;old=bytes(runtime[at-BASE:at-BASE+4]);patch(runtime,BASE,at,old,struct.pack('>I',symbols['gp_label']))
 start=sy['mb_global_draw']+6;finish=sy['mb_callback0'];assert finish-start<512
 patch(runtime,BASE,start,bytes(runtime[start-BASE:finish-BASE]),bytes(finish-start))

 g=meta['governor_key_optimization'];entry=g['original_entry'];target=g['target'];stub=target+g['code_bytes'];assert stub+18<=target+g['free_bytes'];assert not any(sram[stub-0x80000000:stub-0x80000000+18]);assert sram[entry-0x80000000:entry-0x80000000+6]==b'\x4e\xf9'+struct.pack('>I',target)
 # TST mode ; BEQ Lod ; MOVE D0,D2 ; RTS ; JMP noyau courant.
 body=b'\x4a\xb9'+struct.pack('>I',symbols['gp_mode'])+b'\x67\x04\x24\x00\x4e\x75\x4e\xf9'+struct.pack('>I',target);assert len(body)==18
 patch(sram,0x80000000,stub,bytes(18),body);patch(sram,0x80000000,entry,b'\x4e\xf9'+struct.pack('>I',target),b'\x4e\xf9'+struct.pack('>I',stub))
 patch(runtime,BASE,CODE,bytes(len(blob)),blob)
 return dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_bytes=symbols['gp_end']-BSS,symbols=symbols,aliases=aliases,patches=patches,global_row=count,global_rows=count+1,storage='/Governor.cfg',default='Lod',thresholds_unchanged=True,eligibility_unchanged=True,fades_unchanged=True,rare_governor_path_only=True,SRAM_added=18,hardware_tested=False)
