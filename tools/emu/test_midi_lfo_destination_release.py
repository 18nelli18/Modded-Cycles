"""Edition Dest silencieuse : vrai encodeur DATA, producteur et worker MIDI."""
import json,struct
from boot_candidate import ROOT,boot
import test_step_rec_legacy as S
from unicorn import m68k_const as C
for version in [6,9]:
 for prefix in ['all-features','no-filter']:
  stem=f'{prefix}-midi-playability-no-diagnostic-v{version}'
  sy=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())['playability_symbols']
  profile=json.loads((ROOT/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());old=next(t for t in profile['composedTweaks'] if t['id']=='midi-out-machine')['symbols'];sy={**{k:int(v,16) for k,v in old.items()},**sy}
  im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));r=S.Rig(im,mem);r.uc.reg_write(C.UC_M68K_REG_SR,0x2000)
  sent=[];r.hooks[0x40001fba]=lambda a:0;r.hooks[0x400826b0]=lambda a:sent.append(bytes(r.uc.mem_read(a[1],a[0]))) or 0;r.hooks[0x40076bee]=lambda a:0;r.hooks[0x4007faf4]=lambda a:0
  r.w32(sy['mm_assign_lane'],6)
  params=r.call(sy['mm_params'],0);r.uc.mem_write(params+18,struct.pack('>H',17<<8));r.call(sy['mm_setup'],params)
  def ui(page,row=2,edit=1):
   for key,value in [('mm_page_lane',0),('mm_page',page),('mm_row',row),('mm_edit',edit)]:r.w32(sy[key],value)
  def put(lane,knob,cc=74):return r.call(sy['mm_cc_put'],lane,knob,0,cc,64,3)
  def flush():r.call(sy['mm_cc_worker'],sy['mm_wakeup'])
  ui(1)
  result=put(0,12);assert result==(1 if version==6 else 0)
  flush();assert len(sent)==(1 if version==6 else 0)
  if version==6:
   print('REPRODUCED',stem,'LFO CC sent during Dest edit',flush=True);continue
  for page in [1,2]:
   ui(0);assert put(0,11+page);ui(page);flush();assert not sent
   # Le chemin note doit aussi jeter un ancien CC de ce LFO.
   ui(0);assert put(0,11+page);ui(page)
   packet=0x920e0000;r.uc.mem_write(packet,b'\x01'+bytes(15));r.call(sy['mm_cc_worker'],packet);assert not sent
   for cc in range(128):assert put(0,11+page,cc)==0
   # Vrai encodeur DATA : Destination change sans message MIDI.
   for _ in range(5):
    old=r.call(sy['mm_lfo_read'],params,page-1,3)
    delta=-1 if old==128 else 1
    r.uc.mem_write(S.EVT,struct.pack('>6I',0x400fbebc,0,0,1,delta&0xffffffff,0));assert r.call(sy['mi_lfo_encoder'],S.EVT)==1
    assert r.call(sy['mm_lfo_read'],params,page-1,3)!=old
    assert put(0,11+page,74)==0
   # Les producteurs non concernes restent disponibles.
   for lane,knob in [(0,0),(0,14-page),(1,11+page)]:
    assert put(lane,knob);flush();assert sent;sent.clear()
   # Sortie par DATA ou navigation : reprise immediate sur la cible choisie.
   for row,edit in [(2,0),(3,1)]:
    ui(page,row,edit);assert put(0,11+page,95);flush();assert sent[-1]==bytes([0xb0,95,64]);sent.clear()
  print('PASS',stem,'Dest DATA edit, all128 CC silent, queued/next-note stale packets discarded; other LFO/manual CC/track independent; leaving resumes output',flush=True)
