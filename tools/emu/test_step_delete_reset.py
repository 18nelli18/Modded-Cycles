#!/usr/bin/env python3
"""Release grille A : locks natifs, SCRAMBLE/slide et recréation fraîche.

La sélection projet/voix et les observateurs sont contrôlés. Exécute le vrai
gestionnaire de grille, le pool de locks et les setters OS, pas des doubles.
--cycles OS1.13 --catalog sélection.json --tweak step-delete-reset.json
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'chord_keys_compat'));sys.path.insert(0,str(HERE.parent))
import build
from chord_plock_checks import PlockRig,UI
from probe_chord_storage import B1,PROJECT
from test_sdvintage import main_os_from_syx

def image(stock,tweaks):
 data,_=build.apply_writes(stock,tweaks);out=bytearray(data)
 for t in tweaks:
  ap=t.get('append',{})
  for part in ap.get('parts',[]):
   if 'hex' not in part:continue
   at=int(part['dest'],16)
   if not 0x40000000<=at<0x42400000:continue
   code=bytes.fromhex(part['hex']);off=at-build.BASE
   if len(out)<off+len(code):out.extend(bytes(off+len(code)-len(out)))
   out[off:off+len(code)]=code
 return bytes(out)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True);p.add_argument('--tweak',required=True);a=p.parse_args()
 stock=main_os_from_syx(a.cycles);cat=json.loads(pathlib.Path(a.catalog).read_text())['tweaks'];fix=json.loads(pathlib.Path(a.tweak).read_text());chord=next(t for t in cat if t['id']=='chord-keys-supermodel')
 reference=image(stock,cat);patched=image(stock,cat+[fix])
 all_results=[]
 for enabled,blob in ((False,reference),(True,patched)):
  r=PlockRig(reference,blob,chord['symbols']);view,event=0x92060000,0x92062000
  r.uc.mem_write(UI,bytes(512));r.uc.mem_write(UI+357,b'\x01\x01')
  for address,fn in ((0x4000ee90,lambda args:PROJECT),(0x400124b8,lambda args:0),
                     (0x4000f208,lambda args:PROJECT),(0x4000cfcc,lambda args:r.track(r.selected)),
                     (0x400760ba,lambda args:0),(0x40069b84,lambda args:0),(0x40075f3c,lambda args:0),
                     (0x400124b8,lambda args:r.page)):
   r.stub(address,fn)
  r.page=0
  r.word(0x40fe4218,UI)
  calls=[]
  def observe(u,pc,size,data):
   sp=u.reg_read(mk.UC_M68K_REG_A7);calls.append(struct.unpack('>3I',u.mem_read(sp+4,12)))
  r.uc.hook_add(UC_HOOK_CODE,observe,begin=0x40017c4e,end=0x40017c4e)
  def key(code,flags,time):
   r.call(0x4007238c,event,code,flags,time,127)
   return r.call(0x40022382,view,event)
  outcomes=[]
  for lane in range(6):
   r.selected=lane;track=r.track(lane)
   # Le getter virtuel natif est moins fragile qu'un offset de pattern copié.
   getter=r.word(r.word(track)+40);raw=r.call(getter,track)
   assert raw
   for step in (0,7,15,16,31,32,47,48,63):
    for slot in range(33):r.set(lane,step,slot,2000+slot)
    r.call(0x40017b48,track,step,1)
    for mask in (64,4,0x8000):r.call(0x400179ce,track,step,mask,1)
    before_other=[r.bytes(r.call(r.word(r.word(r.track(t))+40),r.track(t)),722) for t in range(6) if t!=lane]
    before_raw=r.bytes(raw,722)
    neighbor=(step+1)%64;r.set(lane,neighbor,11,12345)
    # UIStates page : vraie action pending1 + release du bon TRIG.
    r.call(0x4006b91a,UI,step,1)
    r.uc.mem_write(UI+356,b'\x00')
    r.page=step//16
    key(16+step%16,0,1000+step)
    assert calls and calls[-1]==(track,step,0),(lane,step,calls[-1:] if calls else [])
    flags=struct.unpack('>H',r.bytes(raw+2*step,2))[0];outcomes.append(flags)
    assert all(r.get(lane,step,slot)==-1 for slot in range(33)),(lane,step,'locks')
    if enabled:assert flags==0,(lane,step,hex(flags))
    else:assert flags&64,(lane,step,'régression SCRAMBLE absente')
    allowed={2*step,2*step+1}|{offset+step for offset in (128,192,256,320,384,448,516,580,644)}
    assert all(x==y or i in allowed for i,(x,y) in enumerate(zip(before_raw,r.bytes(raw,722))))
    assert r.get(lane,neighbor,11)==12345
    assert [r.bytes(r.call(r.word(r.word(r.track(t))+40),r.track(t)),722) for t in range(6) if t!=lane]==before_other
    # Recréer avec l'API stock, puis contrôler absence de locks/flags hérités.
    r.call(0x40017b48,track,step,1)
    if enabled:
     # L'OS peut reprendre ses flags de base de piste (7/9/10).
     # Aucun marqueur SCRAMBLE, slide ou retrig du pas supprimé ne revient.
     assert struct.unpack('>H',r.bytes(raw+2*step,2))[0]&(1|64|4|0x8000)==1
     assert all(r.get(lane,step,slot)==-1 for slot in range(33))
  all_results.append(outcomes)
  # Hors REC, le même release ne doit pas rejoindre le clear de grille.
  r.uc.mem_write(UI+357,b'\x00\x00');r.page=0
  before=r.bytes(B1,30642);n=len(calls)
  key(16,0,3000)
  assert len(calls)==n and r.bytes(B1,30642)==before
  print(('ok corrigé' if enabled else 'ok régression')+' : six pistes, quatre pages, release UI et33 slots natifs ; son/autres pistes conservés',flush=True)
 assert any(all_results[0]) and not any(all_results[1])
 print('ok : SCRAMBLE/slide retirés, recréation native fraîche ; essai matériel requis')
if __name__=='__main__':main()
