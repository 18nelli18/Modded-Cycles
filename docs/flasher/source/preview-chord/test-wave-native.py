"""Navigateur et notes réels avec Wizard et ChordKeys ; fichiers et chargeur simulés."""
import json,pathlib,types,struct
import build
from chord_keys_pr87 import load_stock
import test_sample_preview as T
P=pathlib.Path('work/preview-chord-test');stock=load_stock('firmware/model-cycles_OS1.13.syx')
cat=json.load(open(P/'case-preview-chord-wave.json'))['tweaks']
engine=next(t for t in cat if t['id']=='wizard-machines-128');engine['append']['compressed_hex']=json.load(open('work/sample-wizard-options/private-packed.json'))['128']
w=next(t for t in cat if t['id']=='sample-wizard');ck=next(t for t in cat if t['id']=='chord-keys-supermodel');pv=next(t for t in cat if t['id']=='wizard-sample-preview')
sy={k:int(v,16) for k,v in w['symbols'].items()}
for name in ['SP_LOCK','TRACK_LOCK','TRACK_HASH','TRACK_SLOT','KIT_OK','PL_DIRTY']:setattr(T,name,sy[name.lower()])
def image(ts):
 data,_=build.apply_writes(stock,ts);payload,_=build.build_payload(ts,stock,None);return bytes(data)+payload
engine=next(t for t in cat if t['id']=='wizard-machines-128');payload=(int(engine['append']['dest'],16),build.payload_runtime(engine,stock,None))
v=types.SimpleNamespace(tgs=sy,pvs={k:int(v,16) for k,v in pv['symbols'].items()},end=0x401c5dd0,payload=payload)
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

# WAVE conserve son navigateur et son chemin pad, sans désigner un sample Wizard.
from unicorn import UC_HOOK_CODE
meta=json.load(open('work/sample-wizard-options/variants.json'))['128']['wave'];ws=meta['gsyms']
r=Rig(v,v.img);r.uc.mem_write(T.KIT+28+100*2+38,bytes([meta['index']]));r.w32(T.ARMED,0);r.browse(0)
want=struct.pack('>IIII',0x100,T.H1,2_000_000,0)
assert r.mem(ws['wt_h']+16*2,12)==want[:12],r.mem(ws['wt_h']+32,16).hex()
assert r.r32(T.ARMED)==0
# Le chargement de table est simulé ; le routage pad et le code wt_note restent réels.
seen=[]
r.uc.hook_add(UC_HOOK_CODE,lambda uc,a,size,ud:seen.append(a),begin=ws['wt_note'],end=ws['wt_note'])
r.stub(ws['wt_load'],lambda args:1)
r.press(2)
assert seen and not r.loads
assert r.clean(),r.low
print('PASS WAVE : curseur mémorisé par wt_parse et pad routé dans wt_note ; aucune charge Wizard')
