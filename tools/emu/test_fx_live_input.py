"""Regressions v94 : copie Application native, replays pendant pads, quiet save."""
from pathlib import Path
import sys,struct,json
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/emu'),str(ROOT/'tools')]
import test_wizard_playback
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
NEW='staging/all-features-polivoks-cpu-trim-test-'+(sys.argv[1] if len(sys.argv)>1 else 'v94')
OLD='staging/all-features-polivoks-cpu-trim-test-v93'
report={}
for mode,knob,name,mods in [(9,14,'fx_ring_freq',set()),(9,14,'fx_ring_depth',{1}),(11,15,'fx_phase_rate',set()),(11,15,'fx_phase_depth',{1}),(11,15,'fx_phase_feedback',{1,2})]:
 changes=[]
 for stem in (OLD,NEW):
  r,s,h,log,files,key,turn,data,bind=fixture(stem);r.call('fx_service');r.w32(s['ch_mode' if mode==9 else 'cr_mode'],mode);h.update(mods);h.add(16)
  # Meme lecture exacte du delta que4006f73a(e,1,1), sans gain accelere.
  bind(0x4006f73a,lambda a:r.r32(a[0]+16));start=r.r32(s[name]);r.w32(s[name],60)
  raw=struct.pack('>6I',0x400fbebc,0,12345,knob,1,0);r.u.mem_write(EVENT,raw)
  for _ in range(8):r.call(0x40006158,0,EVENT)
  changes.append(r.r32(s[name])-60)
  if stem==NEW:
   assert len([x for x in log if x==('show',12 if name=='fx_ring_freq' else 13 if name=='fx_ring_depth' else 14 if name=='fx_phase_rate' else 15 if name=='fx_phase_depth' else 16)])==1
   # Nouveau mouvement physique de meme sens : meme pointeur, nouveau stamp.
   r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,12346,knob,1,0));r.call(0x40006158,0,EVENT);assert r.r32(s[name])==62
   r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,12347,knob,0,0));r.call(0x40006158,0,EVENT);assert r.r32(s[name])==62
   # La touche maintenue et les tours rapides ne doivent pas sauver de fichiers.
   h.clear();r.call('fx_service');assert '/ExtraFx.cfg' not in files
   r.w32(0xfc07000c,200000000);r.call('fx_service');assert '/ExtraFx.cfg' in files
 assert changes==[8,1],(name,changes)
 report[name]={'same_event_replay_old_new':changes,'fresh_event_accepted':True,'zero_delta_no_change':True,'writes_deferred':True}
print('PASS native Application EncoderEvent copies: held-pad replays apply once; fresh turns remain precise; zero input stops; writes wait for idle',flush=True)
(ROOT/'output/firmware'/('fx-input-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n')
