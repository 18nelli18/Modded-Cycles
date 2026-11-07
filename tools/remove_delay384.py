"""Retire le delay telephone : sept choix, anciens ID12 convertis en Delay."""
from pathlib import Path
import os,struct,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
BASE,CODE,END=0x46700000,0x46705860,0x46707870
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
def apply(meta,runtime,out):
 assert meta.get('fx_live383') and not meta.get('remove_delay384')
 assert not any(runtime[CODE-BASE:END-BASE])
 assert any(e['kind']=='remove' and e['address']<=CODE and END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 out=Path(out);out.mkdir(parents=True,exist_ok=True);p=meta['per_track_fx'];sy=p['symbols'];aliases={**meta['fx_menu']['symbols'],**p.get('aliases',{}),**sy};patches=[]
 def patch(at,new):
  old=bytes(runtime[at-BASE:at-BASE+len(new)]);runtime[at-BASE:at-BASE+len(new)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 controls=(ROOT/'tools/machines/track_fx/slot-controls.c').read_text(encoding='utf-8').replace('pots_del_order[8]','nr_order[7]').replace('pots_del_order','nr_order').replace('slot?8:','slot?7:').replace('mf_fx_encoder(', 'nr_encoder(').replace('mf_commit(', 'nr_commit(')
 overlay=(ROOT/'tools/machines/track_fx/no-vinyl.c').read_text(encoding='utf-8').replace('pots_del_order[8]','nr_order[7]').replace('pots_del_order','nr_order').replace('slot?8:','slot?7:').replace('nv_overlay_canvas','nr_canvas').replace('nv_overlay','nr_overlay')
 state=(ROOT/'tools/machines/track_fx/slot-state.c').read_text(encoding='utf-8')
 def fn(name):
  a=state.index(name+'(');a=state.rfind('\n',0,a)+1;b=state.index('{',a);depth=1;c=b+1
  while depth:
   depth+=(state[c]=='{')-(state[c]=='}');c+=1
  return state[a:c]+'\n'
 header='typedef unsigned int u32;typedef unsigned char u8;extern volatile u32 mf_mode,ch_mode,cr_mode;extern volatile u8 mf_live[48];extern u32 ready,pending,current,lt_config[8][4];extern void seed(void),import_params(void),capture(void);\n'
 for k in ['fx_speed','fx_depth','fx_crackle','fx_warble','fx_wspeed','fx_ring_freq','fx_ring_depth','fx_phase_rate','fx_phase_depth','fx_phase_feedback','cr_rate','cr_bits','mf_requested']:header+='extern u32 '+k+';\n'
 clean='void nr_retired(void){if(cr_mode==12)cr_mode=0;if(mf_live[37]==12)mf_live[37]=0;if(mf_live[39]==12)mf_live[39]=0;'
 if p.get('vinyl_removed'):clean+='if(ch_mode==3)ch_mode=0;for(u32 t=0;t<6;t++)if(mf_live[t]==3)mf_live[t]=0;if(mf_live[36]==3)mf_live[36]=0;if(mf_live[38]==3)mf_live[38]=0;'
 clean+='}\n'
 statecode=header+''.join(fn(n) for n in ['pattern','rev_light','del_light','rev_ok','del_ok'])+clean+fn('runtime').replace('static void runtime','void nr_runtime').replace('retired_effects();','nr_retired();')+fn('mf_legacy_capture').replace('mf_legacy_capture','nr_capture').replace('{if(ready','{nr_retired();if(ready')
 statecode+='extern void mf_old_pots_delay(int*,const int*,const short*,const int*,const int*);void nr_delay(int*out,const int*in,const short*params,const int*dl,const int*dr){if(cr_mode==12)cr_mode=0;mf_old_pots_delay(out,in,params,dl,dr);}\n'
 (out/'controls.c').write_text(controls,encoding='utf-8');(out/'overlay.c').write_text(overlay,encoding='utf-8');(out/'state.c').write_text(statecode,encoding='utf-8');(out/'order.c').write_text('const unsigned int nr_order[7]={11,10,9,5,0,1,2};\n')
 os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ['PATH']
 def run(t,*args):return subprocess.check_output([CROSS+t+'.exe',*map(str,args)],text=True)
 objs=[]
 for name in ['controls','overlay','state','order']:
  obj=out/(name+'.o');objs.append(obj);run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-ffunction-sections','-fdata-sections',*(['-DMF_NO_VINYL'] if p.get('vinyl_removed') else []),'-c',out/(name+'.c'),'-o',obj)
 names=set()
 for obj in objs:names.update(line.split()[-1] for line in run('nm','-u',obj).splitlines())
 (out/'remove.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items() if k in names and not k.startswith('nr_')))
 elf=out/'remove.elf';binary=out/'remove.bin';roots=['nr_encoder','nr_commit','nr_overlay','nr_canvas','nr_runtime','nr_capture','nr_delay'];run('ld','--gc-sections',*['--undefined='+n for n in roots],'-T',out/'remove.ld','-o',elf,*objs);run('objcopy','-O','binary',elf,binary);raw=binary.read_bytes();assert CODE+len(raw)<END
 symbols={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3};assert max(symbols[k] for k in symbols if k.startswith('nr_'))<END
 patch(CODE,raw)
 for old,new in [('mf_fx_encoder','nr_encoder'),('mf_commit','nr_commit'),('nv_overlay','nr_overlay'),('nv_overlay_canvas','nr_canvas'),('runtime','nr_runtime'),('mf_legacy_capture','nr_capture'),('pots_slot_delay','nr_delay')]:patch(sy[old],b'\x4e\xf9'+struct.pack('>I',symbols[new]))
 # Effacer le noyau et ses tables ; les appels de reset encore partages deviennent RTS.
 lo,hi=sy['lg2'],sy['pots_reset']+8;patch(lo,bytes(hi-lo));patch(sy['pots_reset'],b'\x4e\x75')
 lo=sy['RX_C'];hi=min(struct.unpack_from('>13I',runtime,sy['pots_del_names']-BASE));assert lo<hi<sy['pots_del_names'];patch(lo,bytes(hi-lo))
 for pos in range(p['code']-BASE,p['code']-BASE+p['code_bytes']-4):
  if runtime[pos:pos+5]==b'POTS\0':patch(BASE+pos,bytes(5))
 for k in list(p):
  if k.startswith('pots_'):del p[k]
 p.update(delay_selector_count=7,delay_selector_order=[11,10,9,5,0,1,2])
 meta['fx_menu'].update(delay_selector_count=7,delay_selector_order=[11,10,9,5,0,1,2])
 return dict(code=CODE,code_bytes=len(raw),end=END,symbols=symbols,delay_order=[11,10,9,5,0,1,2],legacy_id12_maps_to=0,DSP_removed=True,hardware_tested=False,patches=patches)
