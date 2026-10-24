"""SPEAK dans les six slots natifs, commandes d evenement changeantes et isolement."""
import sys,json,struct
from boot_candidate import ROOT
from test_wizard_playback import fixtures
import mcengine as E
stem=sys.argv[1];m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());s=m['speak']['symbols'];e=fixtures(False,127,0,[stem],native_chordkeys=True,audit_count=False)[0]
stride=int.from_bytes(e.uc.mem_read(s['speak_track_bytes'],4),'big');size=int.from_bytes(e.uc.mem_read(s['speak_state_bytes'],4),'big');peaks=[0]*6
for lane in range(6):e.set(lane,machine=20,note=60+lane,pitch=64,color=64,shape=31,sweep=64,contour=80,decay=127)
for b in range(220):
 if b in (50,100,150):
  for lane in range(6):e.set(lane,shape=(b+lane)%128,pitch=64+lane,color=32+lane*8,sweep=40+lane*9,contour=20+lane*16)
 x=e.block(63 if b in (0,50,100,150) else 0)
 for lane in range(6):peaks[lane]=max(peaks[lane],int(abs(x[lane]).max()))
 if b in (2,52,102,152):
  for lane in range(6):
   base=s['speak_tracks']+lane*stride;wanted=31 if b==2 else (b-2+lane)%128
   assert int.from_bytes(e.uc.mem_read(base+8,4),'big')==wanted,(b,lane,wanted)
   assert int.from_bytes(e.uc.mem_read(E.VOICE0+lane*E.VSTRIDE,4),'big')==20
assert all(1000<p<0x7fffffff for p in peaks) and not e.unmapped
report=dict(candidate=stem,six_native_voices=True,event_word_changes=24,blocks=220,peaks=peaks,unmapped=e.unmapped,hardware_tested=False)
(ROOT/'output/firmware'/('speak-native-proof-'+stem.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('PASS six native SPEAK voices, changing word/pitch/tone/speed/articulation, per-track state, bounded PCM',report,flush=True)
