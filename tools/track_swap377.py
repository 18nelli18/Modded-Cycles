"""Track > Swap : construction privee, UI seule et noyau arrete, aucune IRQ ajoutee."""
from pathlib import Path
import os,struct,subprocess,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];BASE=0x46700000;CODE=0x4679d000;BSS=0x4679ef00;END=0x4679f000
def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);assert not meta.get('track_swap377')
 assert not any(runtime[CODE-BASE:END-BASE])
 assert any(e['kind']=='remove' and e['address']<=CODE and END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 aliases={};groups=['groove_strum','direct_jump','per_track_fx','fx_menu']
 for k in ['menu','row','gc_level','gc_tree_cursor','gc_page','sx_submenu','du_page','mq_page','sx_track']:
  for g in groups:
   v=meta[g].get('symbols',{}).get(k,meta[g].get('aliases',{}).get(k))
   if v is not None:aliases[k]=v;break
  assert k in aliases,k
 def sy(group,key):return meta[group]['symbols'][key]
 aliases.update(ts_notice=sy('fx_menu','fx_notice'),ts_fxp_capture=sy('fx_project','fxp_capture'),ts_scramble_masks=sy('scramble_mask','sx_masks'),ts_duck_config=sy('sidechain','du_config'),ts_duck_fx=sy('sidechain','du_fx'),ts_fxd_apply=sy('fx_project','fxd_apply'),ts_filter_get=sy('filter_pattern300','fp_get'),ts_filter_set=sy('filter_pattern300','fp_set'),ts_capture_lfo=sy('lfo_reload','capture'),ts_capture_extra=sy('four_lfos','capture'),ts_lfo_context=sy('lfo_polarity','lf2_context'),ts_lp_one=sy('lfo_polarity','lp_one'),ts_lp_two=sy('lfo_polarity','lp_two'),ts_extra_contexts=sy('four_lfos','mx_extra'),ts_extra_polarity=sy('four_lfos','mx_polarity'),ts_glide=sy('acid_articulation','aa_glide'),ts_legato=sy('acid_articulation','aa_legato'),ts_acid_initialized=sy('acid_articulation','aa_initialized'),ts_slot=meta['wizard_display']['aliases']['ws_track_slot'],ts_mode=meta['wizard_display']['aliases']['ws_mode'],ts_mf_live=sy('per_track_fx','mf_live'),ts_mf_choice=sy('per_track_fx','mf_choice'),ts_mf_choose=sy('per_track_fx','mf_choose'),ts_mf_capture=sy('per_track_fx','capture'),ts_mf_mode=sy('per_track_fx','mf_mode'),ts_song=sy('acid_articulation','sg_song'))

 stock_only=meta.get('edition')=='lite'
 chord=meta.get('chord_storage300')
 if chord:
  cs=chord['symbols'];aliases.update(ts_ck_read=cs['cs_read'],ts_ck_set=cs['cs_set'],ts_ck_midi_get=cs['cs_ui_midi_get'],ts_ck_midi_set=cs['cs_ui_midi_set'])
 # Les trois rows historiques appartiennent a notre renderer Groove/Strum.
 sys.path.insert(0,str(ROOT/'tools/emu'));from test_seq_gen_menu import Rig
 from unicorn import UC_HOOK_CODE,m68k_const as C
 r=Rig(bytes(native),{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(BASE,0x300000);r.u.mem_write(BASE,bytes(runtime));calls=[]
 def bind(at,fn):
  if at not in r.stubs:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 bind(sy('groove_strum','gc_tree_edit'),lambda a:0);bind(sy('groove_strum','gc_tree_row'),lambda a:0);bind(0x400423e4,lambda a:calls.append(a[0]) or 0)
 draw=sy('groove_strum','gc_track_draw');r.call(draw,0,0x93010000);obj=calls[-1];vt=r.r32(obj);assert r.call(r.r32(vt+12),obj)==3
 records=[]
 for i in range(3):
  r.u.reg_write(C.UC_M68K_REG_A0,0x931f0000);r.call(r.r32(vt+16),obj,i);records.append(bytes(r.u.mem_read(r.r32(0x931f0000),84)))
 template=(ROOT/'tools/machines/direct_jump/global.S').read_text();template=template[:template.index('.Llabel0:')]
 import re
 template=re.sub(r'    clrb %a0@\(\d+\)\n','',template)
 def view(name,title,count,getrow,getedit,rows):
  s=template.replace('mf_global_draw',name).replace('gc_tree_row',getrow).replace('ae_global_edit',getedit).replace('moveq #11,%d0',f'moveq #{count},%d0').replace('.Lts_title_header: .long 6,6,0',f'.Lts_title_header: .long {len(title)},{len(title)},0').replace('.asciz "Global"',f'.asciz "{title}"')
  s=s.replace('    jsr '+getrow,''.join(f'    clrb %a0@({80+84*i})\n' for i in range(count))+'    jsr '+getrow,1)
  return s+rows
 label='.Lswap: .asciz "Swap"\n.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'
 label+=''.join('.byte '+','.join(map(str,v))+'\n' for v in records)
 label+='.long 0,0,0,.Lswap,0,1,.Lts_label,0,0,0,0,0,0,1,ts_empty_value,0,0,0,0,0,0\n'
 (out/'track.S').write_text(view('ts_track_menu','Track',4,'gc_tree_row','ts_menu_edit',label))
 rows='.Lsource: .asciz "From"\n.Ltarget: .asciz "To"\n.Lswap: .asciz "Swap"\n.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'
 for label,fn in [('source','ts_source_value'),('target','ts_target_value'),('swap','ts_empty_value')]:rows+=f'.long 0,0,0,.L{label},0,1,.Lts_label,0,0,0,0,0,0,1,{fn},0,0,0,0,0,0\n'
 (out/'page.S').write_text(view('ts_page_menu','Swap',3,'ts_menu_row','ts_menu_edit',rows))
 aliases['gc_tree_row']=sy('groove_strum','gc_tree_row');tramp='.text\n';hooks=[];cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 aliases['ts_tree_edit']=sy('groove_strum','gc_tree_edit')
 for at,target,oldname in [(sy('gov_policy372','gp_key'),'ts_key','ts_old_key'),(sy('gov_policy372','gp_encoder'),'ts_encoder','ts_old_encoder'),(draw,'ts_draw',None)]:
  old=bytes(runtime[at-BASE:at-BASE+24]);n=0
  for ins in cs.disasm(old,at):
   assert not ins.mnemonic.startswith(('b','j')),(target,ins.mnemonic);n+=ins.size
   if n>=6:break
  assert n>=6;hooks.append((at,old[:n],target))
  if oldname:tramp+=f'.globl {oldname}\n{oldname}:\n.byte '+','.join(map(str,old[:n]))+f'\njmp {at+n:#x}\n'
 (out/'tramp.S').write_text(tramp)
 ld=out/'swap.ld';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); ts_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} ts_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 objects=[]
 for src in [ROOT/'tools/machines/track_fx/track-swap377.c',ROOT/'tools/machines/track_fx/track-swap-ui377.c',out/'track.S',out/'page.S',out/'tramp.S']:
  obj=out/(src.name+'.o');objects.append(obj);run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DTS_STOCK_ONLY'] if stock_only else []),*(['-DTS_CHORD'] if chord else []),'-c',src,'-o',obj)
 run('ld','-T',ld,'-o',out/'swap.elf',*objects);run('objcopy','-O','binary','-j','.text',out/'swap.elf',out/'swap.bin');raw=(out/'swap.bin').read_bytes()
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'swap.elf').splitlines() if len(v:=line.split())==3}
 # Le helper distant possede deja4679ec00..4679ee00 : ne jamais y emettre de code.
 assert symbols['ts_code_end']<=0x4679ec00 and symbols['ts_end']<=END
 patches=[]
 def write(at,new):
  off=at-BASE;old=bytes(runtime[off:off+len(new)]);runtime[off:off+len(new)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 write(CODE,raw)
 for at,old,target in hooks:
  assert bytes(runtime[at-BASE:at-BASE+len(old)])==old
  write(at,b'\x4e\xf9'+struct.pack('>I',symbols[target])+b'\x4e\x71'*((len(old)-6)//2))
 return dict(code=CODE,code_bytes=len(raw),symbols=symbols,aliases=aliases,patches=patches,UI_only=True,audio_hooks=False,hardware_tested=False,experimental=True)
