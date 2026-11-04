"""Commandes privees de banc sur UI ; transport et vrais gestes CTRL-ALL filtre."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];CODE=0x4679bc00;BSS=0x4679ec00;END=BSS+512
def apply(meta,native,runtime,out,machine_test=False):
 base=0x46700000;nb=0x40000400;out=Path(out);out.mkdir(parents=True,exist_ok=True);assert not meta.get('output_monitor_fast')
 if meta.get('remote_panel'):
  if meta.get('stage_profile'):
   from stage_profile320 import remove
   remove(meta,native,runtime);del meta['stage_profile']
  previous=meta['remote_panel'];assert hashlib.sha256(bytes(runtime[CODE-base:CODE-base+previous['code_bytes']])).hexdigest()==previous['sha256']
  for patch in previous['patches']:
   at=patch['at'];buf,offset=(native,at-nb) if at<base else (runtime,at-base);new=bytes.fromhex(patch['new']);assert buf[offset:offset+len(new)]==new;buf[offset:offset+len(new)]=bytes.fromhex(patch['old'])
  runtime[CODE-base:END-base]=bytes(END-CODE)
 assert not any(runtime[CODE-base:END-base])
 old=meta['upgrade_remote_data'];sy=old['symbols'];held=meta['control_all_latch']['symbols']['cal_held']
 aliases=dict(rp_old_request=sy['uk_request'],rp_old_send=sy['uk_send'],rp_queue_manager=sy['uk_manager'],rp_old_held=held,rp_ui_encoder=meta['acid_articulation']['symbols']['aa_face_encoder'],rp_params=meta['playability_symbols']['mm_params'],rp_menu=meta['fx_menu']['symbols']['menu'])
 aliases['rp_deep_stop']=meta.get('deep_idle_wake',{}).get('symbols',{}).get('rw_arm',0x40059692)
 aliases['rp_clear_counters']=meta['cpu_monitor']['symbols']['cpu_reset']
 flags=[]
 if meta.get('deep_idle_wake'):
  aliases['rp_wake_status']=meta['deep_idle_wake']['symbols']['rw_status'];flags=['-DRP_DEEP_WAKE']
 if meta.get('eco_fx351',{}).get('voice_first_pressure'):
  es=meta['eco_fx351']['hall_symbols'];aliases.update(rp_eco_calls=es['eco_calls'],rp_eco_shed=es['eco_shed'],rp_eco_max=es['eco_max_entry'],rp_eco_seen=es['eco_seenIRQ']);flags.append('-DRP_ECO')
 if machine_test:
  flags.append('-DRP_MACHINE_TEST');aliases['rp_fx_commit']=meta['per_track_fx']['symbols']['mf_commit']
  assert meta['activity_masks']['full'],'Machine test helper requires Full edition'
  ws=meta['wizard_display']['symbols'];aliases.update(rp_sample_slot=ws['ws_track_slot'],rp_sample_count=ws['ws_slot_count'],rp_sample_mode=ws['ws_mode'])
  if meta.get('gov_policy372'):
   flags.append('-DRP_GOV');gs=meta['gov_policy372']['symbols'];aliases.update(rp_gov_mode=gs['gp_mode'],rp_gov_set=gs['gp_set'])
  if meta.get('pattern_latch374'):
   flags.append('-DRP_PATTERN');aliases['rp_pattern_snapshot']=meta['pattern_latch374']['symbols']['pl_snapshot']
 (out/'remote-panel.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} rp_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 run('gcc','-mcpu=54418','-Os',*flags,'-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',ROOT/'tools/machines/track_fx/remote-panel318.c','-o',out/'remote-panel.o');run('ld','-T',out/'remote-panel.ld','-o',out/'remote-panel.elf',out/'remote-panel.o');run('objcopy','-O','binary',out/'remote-panel.elf',out/'remote-panel.bin');raw=(out/'remote-panel.bin').read_bytes()
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'remote-panel.elf').splitlines() if len(v:=line.split())==3};assert CODE+len(raw)<=BSS and symbols['rp_end']<=END
 patches=[]
 for oldfn,newfn in [('uk_request','rp_request'),('uk_send','rp_send')]:
  expected=b'\x4e\xb9'+struct.pack('>I',sy[oldfn]);sites=[p['at'] for p in old['patches'] if p['new']==expected.hex()];assert len(sites)==1
  at=sites[0];assert runtime[at-base:at-base+6]==expected;new=b'\x4e\xb9'+struct.pack('>I',symbols[newfn]);runtime[at-base:at-base+6]=new;patches.append(dict(at=at,old=expected.hex(),new=new.hex()))
 at=0x4007faf4;expected=b'\x4e\xf9'+struct.pack('>I',held);assert native[at-nb:at-nb+6]==expected;new=b'\x4e\xf9'+struct.pack('>I',symbols['rp_held']);native[at-nb:at-nb+6]=new;patches.append(dict(at=at,old=expected.hex(),new=new.hex()))
 runtime[CODE-base:CODE-base+len(raw)]=raw
 return dict(code=CODE,code_bytes=len(raw),bss=BSS,bss_bytes=symbols['rp_end']-BSS,symbols=symbols,aliases=aliases,patches=patches,sha256=hashlib.sha256(raw).hexdigest(),hardware_tested=False,audio_hooks=False,parameter_save=False,virtual_modifiers_UI_only=True,double_stop_native_panic=True,panic_api='soft-setter',play_clears_transport_mute=True,native_key_event_vtable=0x400fc20c,deep_stop_test=True,native_play_test=True,volume_readback=True,sequence_genie_open=True,stock_machine_test=machine_test)
