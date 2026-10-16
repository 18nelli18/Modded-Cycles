"""Navigateur et notes réels avec Wizard et ChordKeys ; fichiers et chargeur simulés."""
import json,pathlib,types,struct
import build
from chord_keys_pr87 import load_stock
import test_sample_preview as T
P=pathlib.Path('work/preview-chord-test');stock=load_stock('firmware/model-cycles_OS1.13.syx')
cat=json.load(open(P/'case-preview-chord.json'))['tweaks']
w=next(t for t in cat if t['id']=='sample-wizard');ck=next(t for t in cat if t['id']=='chord-keys-supermodel');pv=next(t for t in cat if t['id']=='wizard-sample-preview')
sy={k:int(v,16) for k,v in w['symbols'].items()}
for name in ['SP_LOCK','TRACK_LOCK','TRACK_HASH','TRACK_SLOT','KIT_OK','PL_DIRTY']:setattr(T,name,sy[name.lower()])
def image(ts):
 data,_=build.apply_writes(stock,ts);payload,_=build.build_payload(ts,stock,None);return bytes(data)+payload
v=types.SimpleNamespace(tgs=sy,pvs={k:int(v,16) for k,v in pv['symbols'].items()},end=0x401c5dd0,payload=None)
v.base=image([t for t in cat if t['id']!=pv['id']]);v.img=image(cat)
Original=T.Rig
class Rig(Original):
 def __init__(self,v,img,track=2):
  super().__init__(v,img,track)
  raw=build.payload_runtime(ck,stock,None);self.uc.mem_write(int(ck['append']['dest'],16),raw)
T.Rig=Rig
T.browser_tests(v)
T.note_tests(v)
assert not T.FAIL,T.FAIL
print('PASS navigateur réel, préécoute, notes et garde ABI avec ChordKeys présent ; chargeur/fichiers simulés')
