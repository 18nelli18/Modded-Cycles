"""Composition privee222 : routage FX par piste, controles historiques, MST/TRK.
Le socle215 est epingle et chaque detour verifie ses octets avant assemblage.
La nouvelle reservation46900000..46920000 precede GATED et WAVE.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,struct,subprocess,sys
WORK=Path(__file__).resolve().parent;HOME=WORK.parent
ROOT=Path(os.environ.get('CREATURE_ROOT','H:/CREATURE-source/retrosyn-integration-step-rec-solo'))
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu'),str(HOME)]
from gen_governor_recovery_test import read,BASE,START,RUNTIME,TAIL
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
import aplib_grow
CODE=0x46900000;BSS=0x46910000;END=0x46920000
POTS_LINE=0x46980000;POTS_LINE_BYTES=0x40000
SOURCE=ROOT/'output/firmware/staging/all-features-polivoks-cpu-trim-test-v215.syx'
SHA='c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6'

def main():
 global SOURCE,SHA
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--module-only',action='store_true');parser.add_argument('--edition',choices=('full','lite'),default='full');parser.add_argument('--chordkeys-audio-off',action='store_true');parser.add_argument('--remove-chordkeys',action='store_true');parser.add_argument('--eco24',action='store_true');parser.add_argument('--runtime-headroom',action='store_true');parser.add_argument('--destination',type=Path,default=HOME/'private-cpu-stock-parity'/'eco24-no-chordkeys')
 parser.add_argument('--legacy12',action='store_true');parser.add_argument('--chord-delta',action='store_true');parser.add_argument('--remove-legacy',action='store_true');parser.add_argument('--unique-punch',action='store_true');parser.add_argument('--no-vinyl',action='store_true');parser.add_argument('--macro-eco-only',action='store_true');args=parser.parse_args()
 assert not args.legacy12 or args.eco24,'--legacy12 requires --eco24'
 lite=args.edition=='lite';version=216 if lite else 215
 SOURCE=ROOT/f'output/firmware/staging/all-features-polivoks-cpu-trim-test-v{version}.syx'
 if lite:SHA='0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e'
 output=args.destination/args.edition/'build';output.mkdir(parents=True,exist_ok=True)
 meta=json.loads(SOURCE.with_suffix('.json').read_text(encoding='utf-8'));assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA
 info,pkg,main_image,ops=read(SOURCE);old_end=int.from_bytes(main_image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 raw=main_image[START:old_end];rt,rtops=aplib.depack(struct.pack('>II',len(raw),sum(raw)&0xffffffff)+raw)
 prefix=bytearray(main_image[:START]);rt=bytearray(rt);tail=bytearray(main_image[old_end:]);tg_anchor=bytes.fromhex('42b9401b72f44aba001c');tg_at=rt.find(tg_anchor);assert tg_at>=0 and rt.find(tg_anchor,tg_at+1)<0;tg_origin=0x401b72c8-tg_at;before=(bytes(prefix),bytes(rt),bytes(tail))
 assert TAIL+len(tail)<=CODE,(hex(TAIL+len(tail)),hex(CODE))
 tail.extend(bytes(END-TAIL-len(tail)))
 def section(at):
  if 0x401aa140<=at<0x401bf8c0:return rt,tg_origin
  for off,run,size in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):
   if run<=at<run+size:return rt,run-off
  return (prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
 def peek(at,n):a,b=section(at);return bytes(a[at-b:at-b+n])
 edits=[]
 def patch(at,data):
  a,b=section(at);old=peek(at,len(data));assert len(old)==len(data);a[at-b:at-b+len(data)]=data;storage=RUNTIME+at-tg_origin if 0x401aa140<=at<0x401bf8c0 else at
  for off,run,size in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):
   if run<=at<run+size:storage=RUNTIME+off+at-run
  edits.append(dict(at=storage,run=at,old=old.hex(),new=data.hex()))
 fold_specs=[('triangle',0x46743fb0,0x236,'_ZN6braids16AnalogOscillator18RenderTriangleFoldEPKhPsPhm'),('sine',0x467441e6,0x1e2,'_ZN6braids16AnalogOscillator14RenderSineFoldEPKhPsPhm')]
 if not lite:assert peek(0x467449be,8).hex()=='4fefff68206f009c'
 harmonic_target='_ZN6braids17DigitalOscillator15RenderHarmonicsEPKhPsm'
 cymbal_target='_ZN6braids17DigitalOscillator12RenderCymbalEPKhPsm'
 cymbal_guards={} if lite else json.loads((WORK/'cymbal-guards.json').read_text())
 for guard in cymbal_guards.values():assert hashlib.sha256(peek(guard['address'],guard['size'])).hexdigest()==guard['sha256']
 fold_guards={} if lite else json.loads((WORK/'macro-fold-guards.json').read_text())
 if lite:fold_specs=[]
 for name,at,n,target in fold_specs:assert hashlib.sha256(peek(at,n)).hexdigest()==fold_guards[name],name
 if not lite:
  for name,at in [('triangle_table',0x46755174),('sine_fold_table',0x46755376),('sine_table',0x4675779a)]:assert hashlib.sha256(peek(at,0x202)).hexdigest()==fold_guards[name],name
 aliases=dict(fc_type=meta['filter_modes']['symbols']['fc_type'],fc_native_table=meta['filter_modes']['symbols']['fc_native_table'])
 for name in ('symbols','capture_symbols','persist_symbols'):aliases.update(meta.get(name,{}))
 for name in ('fx_menu','groove_strum','fx_project','lfo_reload','sidechain','mute_quant'):
  aliases.update(meta[name].get('aliases',{}));aliases.update(meta[name].get('symbols',{}))
 # Seuls identifiants assembleur valides, sans collisions statiques locales.
 aliases={k:v for k,v in aliases.items() if k.replace('_','').isalnum() and isinstance(v,int)}
 aliases.update(_ZN6braids25lut_oscillator_incrementsE=0x46757f20,_ZN6braids12lut_svf_dampE=0x467599a2,_ZN6braids14lut_svf_cutoffE=0x46759ba4)
 aliases.update(_ZN6braids11ws_tri_foldE=0x46755174,_ZN6braids12ws_sine_foldE=0x46755376,_ZN6braids8wav_sineE=0x4675779a)
 fx=meta['fx_menu']['symbols'];gc=meta['groove_strum']['symbols'];fp=meta['fx_project']['symbols'];xp=meta['lfo_reload']['symbols']
 assert meta['fx_menu']['gate_buffer_address']+0x40000<=POTS_LINE and POTS_LINE+POTS_LINE_BYTES<=meta['wave_starter']['custom_buffer']
 aliases.update(fx_line=POTS_LINE,pots_native=fx['fx_delay_previous'])
 aliases.update(mf_shared_fx_reset=fx['fx_vinyl_reset'],mf_shared_ch_state=fx['ch_state'])
 aliases.update({name:meta['beat_repeat_symbols'][name] for name in ('br_keys','br_valid','br_wet','br_lane_wet','br_side','br_side_on','br_active','br_history')})
 aliases.update(idle_rev_active=fx['active'],idle_del_active=fx['nd_active']);aliases.update(gb_enabled=meta['dx_symbols']['dx_enabled'],gb_peak=meta['dx_symbols']['dx_peak'],gb_over=meta['dx_symbols']['dx_over'],gb_mask=meta['dx_symbols']['dx_before_mask'],gb_sum=meta['recovery_symbols']['gr_diag_sum'],gb_blocks=meta['recovery_symbols']['gr_diag_blocks']);aliases.update(mf_old_tree_edit=gc['gc_tree_edit'],mf_fx_selected=fx['fx_selected'],mf_show=fx['fx_show'],mf_redraw=fx['fx_redraw'],mf_wf_api=meta['symbols']['wf_api'],mf_side=fx['fx_side'],mf_side_on=fx['fx_side_on'],mf_crc=fp['fxp_crc'])
 lfo=meta['four_lfos'];aliases.update(ls_ready=xp['ready'],ls_current=xp['current'],ls_import_pending=xp['import_pending'],ls_epoch=lfo['aliases']['lf2n_epoch'],ls_seen=lfo['aliases']['lf2n_seen'],ls_restore=xp['restore'],ls_original=lfo['aliases']['lf2n_sync']);aliases.update(li_count=lfo['symbols']['mx_count'],li_context=lfo['aliases']['lf2_context'],li_extra=lfo['symbols']['mx_extra'],li_sync=lfo['aliases']['lf2n_sync'],li_update=lfo['aliases']['lf2_update'])
 if args.runtime_headroom:aliases.update(ls_storage=xp['storage'],ls_polarity=xp['xp_polarity'],ls_lp_one=xp['xp_lp_one'])
 if args.no_vinyl:aliases['build_no_vinyl']=1
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);tramp='.text\n';hooks=[]
 entries=[('filter_low',meta['recovery_symbols']['pf_coeff'],'fast_pf_coeff'),('filter_modes',meta['filter_modes']['symbols']['fc_coeff'],'fast_fc_coeff'),('native_delay',0x40057488,'idle_delay'),('native_reverb',0x400579c4,'idle_reverb'),('irq_start',0x40058ca0,'gb_irq_start'),('irq_end',0x400594ca,'gb_irq_end'),('audio_end',0x8000e6e0,'gb_audio_end'),('dx_before',meta['dx_symbols']['dx_before'],'gb_dx_before'),('lfo_dispatch',xp['xp_old_dispatch'],'li_dispatch'),('sum6',0x40056716,'mf_sum6'),('sum7',0x40056698,'mf_sum7'),('post',fx['fx_post'],'mf_post'),('fx_encoder',fx['fx_encoder'],'mf_fx_encoder'),('commit',fx['fx_commit'],'mf_commit'),('fx_key',fx['fx_key'],'mf_fx_key'),('value',fx['fx_value'],'mf_value'),('gc_key',gc['gc_key'],'mf_gc_key'),('gc_encoder',gc['gc_encoder'],'mf_gc_encoder'),('gc_draw',gc['gc_draw'],'mf_gc_draw'),('frame',xp['xp_frame'],'mf_frame'),('project_encode',fp['fxp_encode'],'mf_project_encode'),('pattern_copy',fp['fxs_copy'],'mf_pattern_copy'),('pattern_init',fp['fxs_init'],'mf_pattern_init')]
 entries.append(('repeat_render',meta['recovery_symbols']['rr_render'],'rt_render'))
 entries += [('pots_delay',fx['fx_delay'],'pots_slot_delay'),('fx_overlay',fx['fx_overlay'],'nv_overlay'),('fx_overlay_canvas',fx['fx_overlay.part.0'],'nv_overlay_canvas')]
 entries += [('panic_set',0x40058c04,'mf_panic_set'),('panic_transport',0x40059692,'mf_panic_transport')]
 aliases['mf_filter_set']=0x468d0120
 entries += [('filter_init',0x400618f2,'mf_filter_init'),('filter_new',meta['filter_modes']['symbols']['fc_new_sound'],'mf_filter_new'),('filter_get',0x468d0110,'mf_filter_get'),('filter_frame',0x468d0020,'mf_filter_frame')]
 if not lite:
  entries=[(name,at,{'gc_key':'ae_key','gc_encoder':'ae_encoder','gc_draw':'ae_draw','frame':'ae_frame'}.get(name,target)) for name,at,target in entries]
  entries += [('acid_update',meta['fundamentals']['symbols']['acid_update'],'ae_update'),('acid_render',meta['fundamentals']['symbols']['acid_render'],'ae_render')]
 if args.remove_legacy or args.unique_punch:entries.append(('voice_playability',0x400a7d4a,'pp_voice_loop'))
 if args.no_vinyl:entries += [('vinyl_bypass',fx['fx_vinyl'],'nv_bypass')]
 if args.remove_legacy:
  import no_legacy
  extra_aliases,extra_entries=no_legacy.setup(meta);aliases.update(extra_aliases);entries+=extra_entries
 if args.chord_delta:entries.append(('chord_render',0x400a8906,'chord_delta_fast'))
 if args.remove_chordkeys:
  import no_chordkeys
  extra_aliases,extra_entries=no_chordkeys.setup(meta);aliases.update(extra_aliases);entries+=extra_entries
 if args.eco24 or args.macro_eco_only:
  legacy=meta['legacy']['symbols'];aliases.update(sintab=legacy['sintab'],eco_macro_store=0x4675b000)
  if not args.remove_legacy and not args.macro_eco_only:entries += [('eco_dx_block',legacy['dx7_block_c'],'eco_dx_block'),('eco_dx_mod',legacy['_ZN10FmOpKernel7computeEPlPKlllllb'],'eco_dx_compute'),('eco_dx_pure',legacy['_ZN10FmOpKernel12compute_pureEPlllllb'],'eco_dx_pure'),('eco_dx_feedback',legacy['_ZN10FmOpKernel10compute_fbEPlllllS0_ib'],'eco_dx_feedback')]
  if not lite:entries.append(('eco_macro_update',0x46742000,'eco_macro_update'))
 for name,at,target in entries:
  raw=peek(at,64);alias='mf_old_'+name;n=0
  if raw[:2]==b'\x4e\xf9':n=6;aliases[alias]=int.from_bytes(raw[2:6],'big')
  elif name=='panic_transport':
   # Rejouer le branchement court hors de portee du nouveau module.
   assert raw[:6].hex()=='4aaf00046714'
   n=6;tramp+='\n.globl '+alias+'\n'+alias+':\n tst.l 4(%sp)\n bne.s .Lpanic_transport_on\n jmp 0x400596ac\n.Lpanic_transport_on:\n jmp 0x40059698\n'
  else:
   tramp+='\n.globl '+alias+'\n'+alias+':\n'
   for ins in cs.disasm(raw,at):
    data=bytes(ins.bytes)
    if data[:2]==b'\x4e\xba':
     to=ins.address+2+int.from_bytes(data[2:4],'big',signed=True);tramp+=f'jsr {to:#x}\n'
    elif data[:2]==b'\x4e\xb9':tramp+='jsr '+hex(int.from_bytes(data[2:6],'big'))+'\n'
    else:
     assert not ins.mnemonic.startswith(('b','j')) and 'pc' not in ins.op_str.lower(),(name,ins.mnemonic,ins.op_str)
     tramp+='.byte '+','.join(map(str,data))+'\n'
    n+=ins.size
    if n>=6:break
   assert n>=6 and n%2==0;tramp+=f'jmp {at+n:#x}\n'
  hooks.append(dict(name=name,at=at,old=raw[:n].hex(),target=target,bytes=n))
 if 'mf_old_repeat_render' in aliases:aliases['rt_old_render']=aliases['mf_old_repeat_render']
 else:tramp+='\n.globl rt_old_render\n.set rt_old_render,mf_old_repeat_render\n'
 (output/'tramp.S').write_text(tramp,encoding='utf-8')
 view=(ROOT/'output/firmware/governor-recovery-v215/gc_global.S').read_text(encoding='utf-8')
 view=view.replace('gc_global_draw','mf_global_draw').replace('gc_tree_edit','mf_tree_edit').replace('moveq #9,%d0','moveq #10,%d0').replace('    clrb %a0@(752)','    clrb %a0@(752)\n    clrb %a0@(836)').replace('.Lallocator: .byte 0','.Llabel9: .asciz "FX"\n.Lallocator: .byte 0')
 view+='\n.long 0,0,0,.Llabel9,0,1,.Lts_label,0,0,0,0,0,0,1,mf_global_value,0,0,0,0,0,0\n'
 (output/'global.S').write_text(view,encoding='utf-8');(output/'aliases.json').write_text(json.dumps(aliases,indent=2)+'\n')
 if not lite:
  view=view.replace('mf_tree_edit','ae_global_edit').replace('moveq #10,%d0','moveq #11,%d0').replace('    clrb %a0@(836)','    clrb %a0@(836)\n    clrb %a0@(920)').replace('.Lallocator: .byte 0','.Lacid_label: .asciz "ACID"\n.Lallocator: .byte 0')
  view+='\n.long 0,0,0,.Lacid_label,0,1,.Lts_label,0,0,0,0,0,0,1,ae_value,0,0,0,0,0,0\n'
  (output/'global.S').write_text(view,encoding='utf-8')
 (output/'roots.json').write_text(json.dumps([h['target'] for h in hooks]+['dry_osc','gv_fade_entry','idle_check','idle_voice_begin']+[f[3] for f in fold_specs]+([] if lite else [harmonic_target,cymbal_target])+(['li_store_gate'] if args.runtime_headroom else [])+(['rm_noop','rm_silence'] if args.remove_legacy else [])))
 command=[sys.executable,str(WORK/'build_light_lab.py'),'--code',hex(CODE),'--bss',hex(BSS),'--output',str(output),'--aliases',str(output/'aliases.json'),'--roots',str(output/'roots.json')]
 for source in ('slot-state.c','slot-controls.c','firmware-bridge.c','repeat-idle.c','lfo-idle.c','sparse.S','governor.c','governor-hooks.S','irq-budget.c','irq-budget.S','fx-idle.c','fx-idle.S','fx-panic.c','filter-startup.c','native-osc.S','filter-low.c','filter-modes.c','lfo-sync.c')+(() if lite else ('macro-fold.cc','macro-harmonics.cc','macro-cymbal.cc')):command+=['--extra',str(WORK/source)]
 for source in ('tramp.S','global.S'):command+=['--extra',str(output/source)]
 for source in (WORK/'pots-slot.c',WORK.parent/'pots/pots.c'):command+=['--extra',str(source)]
 order=list(struct.unpack('>7I',peek(fx['fx_del_order'],28)));assert order==[11,10,9,5,0,1,2]
 order.insert(3,12);labels=[]
 for i in range(12):
  ptr=int.from_bytes(peek(fx['fx_del_names']+4*i,4),'big');labels.append(peek(ptr,64).split(b'\0',1)[0].decode('ascii'))
 labels.append('POTS');(output/'pots-menu.c').write_text('const unsigned int pots_del_order[8]={'+','.join(map(str,order))+'};\nconst char*const pots_del_names[13]={'+','.join(json.dumps(s) for s in labels)+'};\n')
 command+=['--extra',str(output/'pots-menu.c')]
 (output/'no-vinyl.c').write_text(('#define MF_NO_VINYL 1\n' if args.no_vinyl else '')+(WORK/'no-vinyl.c').read_text())
 command+=['--extra',str(output/'no-vinyl.c')]
 if not lite:
  for source in ('acid-envelope.c','acid-envelope-dsp.c'):command+=['--extra',str(WORK/source)]
 if args.no_vinyl:
  order=list(struct.unpack('>9I',peek(fx['fx_rev_order'],36)));assert order.count(3)==1
  order.remove(3);(output/'no-vinyl-order.c').write_text('const unsigned int nv_rev_order[8]={'+','.join(map(str,order))+'};\n')
  command+=['--extra',str(output/'no-vinyl-order.c')]
  for name in ('slot-state.c','slot-controls.c'):
   (output/name).write_text('#define MF_NO_VINYL 1\n'+(WORK/name).read_text().replace('"Vinyl"','""'))
   command[command.index(str(WORK/name))]=str(output/name)
 if args.remove_legacy or args.unique_punch:
  (output/'voice-punch.c').write_text('#define PP_UNIQUE '+str(int(args.unique_punch))+'\n#define PP_REMOVE_LEGACY '+str(int(args.remove_legacy))+'\n'+(WORK/'voice-punch.c').read_text())
  command+=['--extra',str(output/'voice-punch.c')]
 if args.remove_legacy:
  for source in no_legacy.sources(WORK,output,meta):command+=['--extra',str(source)]
 if args.chord_delta:
  import chord_delta
  for source in chord_delta.sources(ROOT,output,peek,SOURCE,args.destination):command+=['--extra',str(source)]
 if args.runtime_headroom:
  at=command.index(str(WORK/'lfo-idle.c'));command[at]=str(WORK/'lfo-direct.c')
  for source in ('lfo-direct.S','lfo-restore.c'):command+=['--extra',str(WORK/source)]
 if args.remove_chordkeys:command+=['--extra',str(WORK/'midi-no-chordkeys.c')]
 if args.eco24 or args.macro_eco_only:
  for source in (() if args.remove_legacy or args.macro_eco_only else ('eco12.c','eco-dx12.S') if args.legacy12 else ('eco24.c','eco-dx.S'))+(() if lite else ('macro-eco.cc',)):command+=['--extra',str(WORK/source)]
 subprocess.run(command,check=True)
 lab=json.loads((output/'light.json').read_text());sy=lab['symbols'];blob=(output/'light.bin').read_bytes()
 assert CODE+len(blob)<=BSS and sy['lt_bss_end']<=END
 assert meta['fx_menu']['gate_buffer_address']>=END and END<=0x46a00000<=meta['wave_starter']['custom_buffer_end']
 assert not any(peek(CODE,END-CODE));patch(CODE,blob)
 for h in hooks:
  assert peek(h['at'],h['bytes']).hex()==h['old'];patch(h['at'],b'\x4e\xf9'+struct.pack('>I',sy[h['target']])+b'\x4e\x71'*((h['bytes']-6)//2))
 if not lite:
  patch(0x4674b9a0,b'\x4e\xf9'+struct.pack('>I',sy[cymbal_target]))
  patch(0x467449be,b'\x4e\xf9'+struct.pack('>I',sy[harmonic_target])+b'\x4e\x71')
 for name,at,n,target in fold_specs:patch(at,b'\x4e\xf9'+struct.pack('>I',sy[target]))
 if args.runtime_headroom:
  assert peek(0x40091d04,6).hex()=='7350d0816a04'
  patch(0x40091d04,b'\x4e\xf9'+struct.pack('>I',sy['li_store_gate']))
 # Restaurer le pipeline FX Model-TG contourne par les wrappers ajoutes.
 for at,old,data in (
  # Complete the Model-TG scheduling contract: fx_early already prepares once.
  # Replay only its required EMAC state at the old output-stage setup site.
  (0x400567d6,'2f0b4eb94005802e588f',bytes.fromhex('a93c00000020a1c0a3c0')),
  # Existing fx_c advances rings/writes DMA only when this block ran the FX.
  (0x40056a36,'4eb9400579424eb9400573fa',bytes.fromhex('4eb9401b74044e714e714e71')),
  (0x4005981e,'4eb9400a7d4a',b'\x4e\xb9'+struct.pack('>I',sy['idle_voice_begin'])),
  (0x401b731c,'41f980001858',b'\x4e\xf9'+struct.pack('>I',sy['idle_check'])),
  (0x401b7388,'4ef940057488',b'\x4e\xf9'+struct.pack('>I',sy['mf_old_native_delay'])),
  (0x401b73b0,'4eb9400579c4',b'\x4e\xb9'+struct.pack('>I',sy['mf_old_native_reverb']))):
  assert peek(at,len(bytes.fromhex(old))).hex()==old,(hex(at),peek(at,len(bytes.fromhex(old))).hex());patch(at,data)
 assert peek(0x401b7404,20).hex()=='4abafeea660c4eb9400579424ef9400573fa4e75','FX completion helper changed'
 removal={}
 if args.remove_chordkeys:removal=no_chordkeys.remove(peek,patch)
 legacy_removal=no_legacy.remove(meta,peek,patch,sy,lite) if args.remove_legacy else {}
 if args.chordkeys_audio_off and not args.remove_chordkeys:
  for at,old,new in [(0x400aae88,'4ef9401c50484e71','4fefffe448d71c3c'),(0x400ab0e4,'4ef9401875b8','d1fc4012142c')]:
   assert peek(at,len(bytes.fromhex(old))).hex()==old,hex(at)
   patch(at,bytes.fromhex(new))
 # Detour interne : uniquement le bloc deja en fondu, avant le scan natif.
 fade=0x800073a2;assert peek(fade,6).hex()=='77b108522803';patch(fade,b'\x4e\xf9'+struct.pack('>I',sy['gv_fade_entry']))
 assert peek(0x400a82cc,8).hex()=='a3072619a61a3804';patch(0x400a82cc,b'\x4e\xf9'+struct.pack('>I',sy['dry_osc'])+b'\x4e\x71')
 proof=dict(status='experimental',hardware_tested=False,source_build=215,source_sha256=SHA,code=CODE,bss=BSS,end=END,code_bytes=len(blob),bss_bytes=lab['bss_bytes'],symbols=sy,hooks=hooks,edits=edits,shared_reverb_delay=True,controls='Global FX MST/TRK; existing TRACK + SIZE/TIME selectors',storage='/MFX_<project UUID>.cfg',native_exports_include_sidecar=False,track_release_commit_guard=True,selection_track_latched=True,lfo_idle_copy_optimization=True,governor_thresholds_unchanged=True,governor_original_limits_restored=True,governor_fade_end_zero=True,irq_budget_includes_prelude=True,irq_budget_previous_tail=True,dx_near_complete_irq=True,irq_immediate_overload_guard=False,governor_spike_hysteresis_restored=True,fx_native_idle_pipeline_restored=True,fx_dma_prepare_before_voices=True,fx_idle_respects_sends=True)
 proof.update(cymbal_fixed_filter_path=True,cymbal_guards=cymbal_guards,harmonics_exact_target_cache=True,harmonics_zero_trailing_partials=True,ui_masked_word_capture=True,macro_fold_steady_parameter=True,macro_fold_guards=fold_guards,fx_startup_asleep_before_first_send=True,fx_post_send_tail_guard_preserved=True,native_osc_zero_modulation_fast_path=True,filter_exact_q30_division_reduction=True,filter_shared_coefficient_cache=True,master_mode_skips_track_scan=True,lfo_stable_bank_sync_optimization=True,shared_chorus_crusher_code_independent_state=True)
 proof.update(edition=args.edition,source_build=version,cymbal_fixed_filter_path=not lite,harmonics_exact_target_cache=not lite,harmonics_zero_trailing_partials=not lite,macro_fold_steady_parameter=not lite,fx_tail_scan_fused=True,ring_exact_endpoint_paths=True)
 proof.update(fx_output_duplicate_setup_removed=True,fx_sleep_skips_ring_and_dma_writeback=True,hardware_click_fix_verified=False)
 proof.update(native_send_zero_gain_fast_path=True)
 proof.update(filter_new_sound_deferred_low=True,filter_saved_load_cancels_pending=True)
 proof.update(pots_delay=True,pots_upstream='durchgemacht/model27',pots_revision='5badf6ad27d956e86d32ff331c480a84ef74db92',pots_loop_rate=12000,pots_line=POTS_LINE,pots_line_bytes=POTS_LINE_BYTES,pots_effect_id=12,pots_delay_order=[11,10,9,12,5,0,1,2],pots_native_time_feedback=True,pots_shared_heavy_delay=True)
 if not lite:proof.update(acid_envelope_modes=['A','F','AF'],acid_envelope_default='F',acid_envelope_storage='one global setting /AcidEnv.cfg',acid_envelope_menu='Mod Setup > Global > ACID')
 proof.update(retrig_idle_history_packed=True,retrig_active_and_fades_original=True)
 proof.update(lfo_direct_collection=args.runtime_headroom,unassigned_secondary_banks_pause=args.runtime_headroom,filter_fractional_divisions=4)
 proof.update(legacy_internal_samples=None if lite or args.remove_legacy else 8 if args.legacy12 else 16 if args.eco24 else 32,macro_eco_only=args.macro_eco_only)
 proof.update(chord_exact_delta_interpolation=args.chord_delta)
 proof.update(legacy_removed=args.remove_legacy,legacy_removal=legacy_removal,unique_machine_punch=args.unique_punch,vinyl_removed=args.no_vinyl)
 proof.update(chordkeys_audio_disabled=args.chordkeys_audio_off or args.remove_chordkeys,chordkeys_ui_midi_removed=args.remove_chordkeys,chordkeys_removal=removal,eco24=args.eco24,eco_machines=(([] if lite or args.remove_legacy else ['LEGACY'])+([] if lite else ['MACRO existing RATE-capable models'])) if args.eco24 else [],output_sample_rate=48000)
 (output/'integration.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('INTEGRATED MODULE',len(blob),'bytes code;',lab['bss_bytes'],'BSS;',len(hooks),'guarded hooks',flush=True)
 if args.module_only:return
 struct.pack_into('>I',prefix,0x40195ad8-BASE,len(tail))
 packed=aplib.repack(bytes(rt),rtops,bytes(a!=b for a,b in zip(rt,before[1])));assert aplib.depack(packed)[0]==bytes(rt)
 struct.pack_into('>I',prefix,0x40195ad0-BASE,BASE+START+len(packed)-8)
 newmain=bytes(prefix)+packed[8:]+bytes(tail)
 _,_,stock,stockops=read(ROOT/'firmware/model-cycles_OS1.13.syx');assert len(stock)==START
 dirty=bytes(a!=b for a,b in zip(prefix,stock))+b'\1'*(len(newmain)-START)
 section3=aplib_grow.repack_grow(newmain,stockops,dirty,START)
 from bootstrap205_assets import pack as safe_pack
 section3,packing=safe_pack(section3)
 spec=importlib.util.spec_from_file_location('verified_aplib',Path(os.environ.get('APLIB_VERIFIER','H:/Supermodel-Recovery-2026-10-27/Supermodel-public/tools/mtlib/aplib.py')));verified=importlib.util.module_from_spec(spec);spec.loader.exec_module(verified)
 assert verified.depack(section3,bootstrap_gap=0x1ffc00)[0]==newmain
 plains=[]
 for sec in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key
 rebuilt=container.rebuild(pkg,{3:section3},key);assert len(rebuilt)<=0x1c0000,(len(rebuilt),hex(0x1c0000))
 syx=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq'])
 delivery=args.destination/args.edition;delivery.mkdir(parents=True,exist_ok=True);name='Supermodel_CPU_'+args.edition.title()+('_Punch_No_Legacy_No_Vinyl_No_ChordKeys_Experimental.syx' if args.unique_punch and args.remove_legacy and args.no_vinyl and args.remove_chordkeys else '_LFO_Headroom_ECO12_No_ChordKeys_Experimental.syx' if args.runtime_headroom and args.legacy12 else '_ECO_No_ChordKeys_Experimental.syx' if args.eco24 and args.remove_chordkeys else '_No_ChordKeys_Experimental.syx' if args.remove_chordkeys else '_ChordKeys_Audio_Off_Diagnostic.syx' if args.chordkeys_audio_off else '_Machine_Experimental.syx');(delivery/name).write_bytes(syx)
 proof.update(sha256=hashlib.sha256(syx).hexdigest(),main_sha256=hashlib.sha256(newmain).hexdigest(),packing=packing,flash_bytes=len(rebuilt),syx_bytes=len(syx),firmware_hooks_installed=True)
 candidate={**meta,'governor_thresholds_unchanged':True,'irq_budget221':dict(original_limits_restored=True,fade_end_zero=True,irq_prelude_and_previous_tail_budget=True,dx_near_complete_irq=True,irq_immediate_overload_guard=False,governor_spike_hysteresis_restored=True,hardware_tested=False),'sha256':proof['sha256'],'main_os_sha256':proof['main_sha256'],'hardware_tested':False,'per_track_fx':proof}
 candidate['fx_menu']={**candidate['fx_menu'],'delay_selector_order':proof['pots_delay_order'],'delay_selector_count':8}
 if args.remove_chordkeys:
  # Do not export obsolete feature symbols/availability in the new manifest.
  def clean(value):
   if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if not k.startswith(('ck_','chord_audio_'))}
   if isinstance(value,list):return [clean(v) for v in value]
   return value
  candidate=clean(candidate);candidate['chord_names_external_midi']=False;candidate['chordkeys_removed']=True
 if args.remove_legacy:
  candidate.pop('legacy',None)
  roster=dict(candidate['tiny_extra']);roster['menu_order']=[m for m in roster['menu_order'] if m!=21];roster['installed_machine_count']=len(roster['menu_order']);candidate['tiny_extra']=roster
  identities=candidate.get('machine_identities')
  if isinstance(identities,dict):candidate['machine_identities']={k:v for k,v in identities.items() if str(k)!='21'}
  elif isinstance(identities,list):candidate['machine_identities']=[v for v in identities if v.get('machine')!=21 and (not lite or v.get('machine',25)<6)]
  candidate['legacy_removed']=True
 if args.no_vinyl:candidate['vinyl_removed']=True
 (delivery/'BUILD.json').write_text(json.dumps(candidate,indent=2)+'\n');(output/'integration.json').write_text(json.dumps(proof,indent=2)+'\n')
 print('BUILT PRIVATE CPU REPAIR',len(rebuilt),'flash bytes;',proof['sha256'],flush=True)

if __name__=='__main__':main()
