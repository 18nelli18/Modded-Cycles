"""Parcours voix+repeat+deux filtres : v21 vs candidat v25, memes vraies sorties.
Ce n'est pas l'interruption entiere : mix final/sendFX/UI/USB non mesures.
"""
import json,struct,sys
import numpy as np
from test_wizard_playback import fixtures,ROOT
import mcengine as E
STEM=sys.argv[1] if len(sys.argv)>1 else 'validation/all-features-polivoks-cpu-trim-test-v25'
BASELINE=sys.argv[2] if len(sys.argv)>2 else 'all-features-polivoks-cpu-test-v21'
def main():
 stems=[BASELINE,STEM];engines=fixtures(True,70,100,stems)
 shared=json.loads((ROOT/'output/firmware'/(STEM+'.json')).read_text())['shared_filter_enabled']
 states=[]
 for e,stem in zip(engines,stems):
  m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());s=m['beat_repeat_symbols'];states.append(s)
  for at,v in [(0x40149310,57600),(0x40a7883c,1),(0x40a78888,0x41400000),(0x40a78840,1)]:e.uc.mem_write(at,struct.pack('>I',v))
 results=[]
 for mode in ('off','armed','active'):
  totals=[0,0];blocks=[[],[]]
  for e,s in zip(engines,states):
   for key,v in [('br_history',0 if mode=='off' else 0x41000000),('br_blocks',4096),('br_keys',0 if mode=='off' else 3),('br_requested',0 if mode=='active' else -1),('br_wet',0),('br_valid',0),('br_active',-1),('br_cancel',0)]:e.uc.mem_write(s[key],struct.pack('>I',v&0xffffffff))
   e.uc.mem_write(s['br_lane_wet'],bytes(24))
  for b in range(32):
   outputs=[]
   for j,(e,s) in enumerate(zip(engines,states)):
    e.count=0;e.block(63 if b%8==0 else 0);e.call(s['br_audio'])
    for lane in range(6) if shared else ():
     e.uc.mem_write(0x401bbd60+4*lane,struct.pack('>I',0 if lane==3 else (512,2048,3072)[b//8%3]))
     e.uc.mem_write(0x401bbd7c+4*lane,struct.pack('>I',(0,4096,8191)[b//8%3]))
     e.call(0x401badda,E.TRACK_BASE+128*lane,lane)
    blocks[j].append(e.count);totals[j]+=e.count;outputs.append(bytes(e.uc.mem_read(E.TRACK_BASE,768)))
   assert outputs[0]==outputs[1],('combined samples',mode,b)
   assert engines[0].uc.mem_read(E.VOICE0,6*E.VSTRIDE)==engines[1].uc.mem_read(E.VOICE0,6*E.VSTRIDE),('voice state',mode,b)
  assert engines[0].uc.mem_read(0x401bbdb4,112)==engines[1].uc.mem_read(0x401bbdb4,112),'shared filter histories'
  assert not any(e.unmapped for e in engines)
  row={'mode':mode,'blocks':32,'instructions':totals,'instructions_mean':[v/32 for v in totals],'instructions_peak':[max(v) for v in blocks],'reduction':100*(1-totals[1]/totals[0]),'limits':'covered voice+repeat+shared filters only; stereo Wizard; Metal silent fixture; ChordKeys stubbed; no hardware-cycle/global CPU result'}
  if BASELINE.endswith('v21') or mode=='armed':assert totals[1]<totals[0]
  results.append(row);print(json.dumps(row),flush=True)
 (ROOT/('output/firmware/private-'+STEM.rsplit('-',1)[-1]+'-combined-audit.json')).write_text(json.dumps(results,indent=2)+'\n')
 print('PASS identical covered voice+repeat audio and voice state',flush=True)
if __name__=='__main__':main()
