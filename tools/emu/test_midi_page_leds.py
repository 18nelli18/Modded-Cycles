"""Note120 : vrai bootstrap, callback LED B et boucle PAGE stock compares."""
import argparse,json,os,pathlib,struct,sys,time
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_UNMAPPED,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,OBJ,STACK
ROOT=HERE.parent.parent
CASES=os.environ.get("MIDI_PAGES_OUT","build/midi-page-leds")

def run(prefix):
 img,mem,ts=boot_case(prefix);bank=next(t for t in ts if t['id']=='midi-out-bank');q=next(t for t in ts if t['id'] in ('midi-page-leds-test','midi-page-leds'));r=Rig(img,{'writes':[]},{'writes':[],'symbols':{**bank['symbols'],**q['symbols']}});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in mem:u.mem_write(at,raw)
 assert r.call('ml_prepare')==1;clock=r.r32(r.s['ml_clock_state']);active=0x930b0000;r.w32(0x40a7887c,active);r.w32(active+30706,0);assert r.call('ml_bank_ui_sync')==1;pattern=r.r32(r.s['ml_pattern']);r.w32(r.s['mlp_obj'],OBJ);r.w32(r.s['ml_play_pattern'],pattern)
 record=[1];led=0x930b1000;claims=0x930b2000;mapping=0x930b3000;pages=[r.r32(0x400fbccc+4*i) for i in range(4)];pads=[r.r32(0x400fbc78+4*i) for i in range(6)]
 r.w32(0x404a8bc4,0x400fbccc);r.w32(0x404a8bdc,mapping);u.mem_write(mapping,struct.pack('>16I',*range(1,17)));r.w32(0x404a8ba0,0x400fbc78)
 for at,fn in ((0x400cf9a8,lambda a:0x930b4000),(0x4006b978,lambda a:record[0]),(0x400cfaf4,lambda a:led),(0x4008e942,lambda a:a[0]),(0x4008e964,lambda a:0),(0x4008e998,lambda a:0),(0x4008e8ce,lambda a:0)):
  r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 u.hook_add(UC_HOOK_MEM_UNMAPPED,lambda u,access,addr,size,value,data:print('UNMAPPED',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),size,flush=True) or False)
 cb=r.r32(r.s['mlp_led_vt']+16);assert cb==r.s['pg_led'];allocated=r.new_count;tests=0
 def states():return [r.r32(led+40+4*i) for i in pages]
 def stock_record(selected,step):
  u.mem_write(led,bytes(256));u.reg_write(mk.UC_M68K_REG_D2,led);u.reg_write(mk.UC_M68K_REG_D5,step//16 if step>=0 else 0xffffffff);u.reg_write(mk.UC_M68K_REG_D6,selected);u.reg_write(mk.UC_M68K_REG_D7,int(step>=0 and (step&3)>1));u.reg_write(mk.UC_M68K_REG_A7,STACK);u.emu_start(0x400222f2,0x40022346,count=10000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x40022346;assert u.reg_read(mk.UC_M68K_REG_A7)==STACK;return states()
 def stock(selected,step,length):
  if record[0]:return stock_record(selected,step)
  u.mem_write(led,bytes(256));frame=0x930b5000;r.w32(frame-20,(length+15)//16)
  for reg,value in ((mk.UC_M68K_REG_D3,led),(mk.UC_M68K_REG_D5,step//16 if step>=0 else 0xffffffff),(mk.UC_M68K_REG_D6,0),(mk.UC_M68K_REG_D7,(step&3) if step>=0 else 0),(mk.UC_M68K_REG_A5,0x40005fe6),(mk.UC_M68K_REG_A6,frame),(mk.UC_M68K_REG_A7,STACK)):u.reg_write(reg,value)
  u.emu_start(0x4001cdf2,0x4001ce28,count=10000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4001ce28;assert u.reg_read(mk.UC_M68K_REG_A7)==STACK
  return [value or 1 for value in states()]
 for rec in (0,1):
  record[0]=rec
  for lane in range(6):
   r.w32(r.s['mlp_track'],lane)
   for length in (5,16,17,31,32,48,64):
    u.mem_write(pattern+264*lane+4,bytes([length]))
    for selected in range((length+15)//16):
     r.w32(r.s['mlp_step'],selected*16)
     for step in [s for s in (0,1,2,3,14,15,16,17,30,31,32,47,48,63) if s<length]:
      r.w32(0x40a7883c,1);r.w32(clock,1);r.w32(clock+8+8*lane,(step+1)%length);expected=stock(selected,step,length);u.mem_write(led,bytes(256));u.mem_write(claims,bytes(8));assert r.call(cb,OBJ+0x500,0,claims)==1;assert states()==expected,(rec,lane,length,selected,step,states(),expected)
      mask=r.r32(claims)<<32|r.r32(claims+4);assert mask==sum(1<<i for i in list(range(1,17))+pads+pages),hex(mask)
      tests+=1
     for transport in (0,2):
      r.w32(0x40a7883c,transport);expected=stock(selected,-1,length);u.mem_write(led,bytes(256));assert r.call(cb,OBJ+0x500,0,claims)==1;assert states()==expected
 # Le retour vers A et les objets etrangers ne revendiquent pas les pages B.
 r.w32(r.s['mlp_obj'],0);u.mem_write(led,bytes(256));u.mem_write(claims,bytes(8));r.call(cb,OBJ+0x500,0,claims);assert states()==[0]*4 and r.r32(claims)==r.r32(claims+4)==0;r.w32(r.s['mlp_obj'],OBJ)
 assert r.new_count==allocated
 # Page lue hors page editee : le poll doit suivre le clignotement sans curseur visible.
 redraw=[];poll=[]
 for at,fn in ((0x400760ba,lambda a:redraw.append(a[0]) or 0),(r.s['mlp_led_poll'],lambda a:poll.append(1) or 0)):
  r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.w32(r.s['mlp_track'],0);r.w32(r.s['mlp_step'],0);u.mem_write(pattern+4,b'\x40');r.w32(0x40a7883c,1);r.w32(clock,1);r.w32(clock+8,17);r.call('pg_poll');redraw.clear()
 for _ in range(20):r.call('pg_poll')
 assert not redraw
 r.w32(clock+8,19);r.call('pg_poll');assert redraw==[OBJ];redraw.clear();r.w32(clock+8,33);r.call('pg_poll');assert redraw==[OBJ]
 assert len(poll)==23
 redraw.clear();record[0]=0;r.call('pg_poll');assert redraw==[OBJ];redraw.clear();record[0]=1;r.call('pg_poll');assert redraw==[OBJ]
 print('PASS',prefix,tests,'playing states match actual stock PAGE loop; stopped/paused, masks, six lane lengths, B exit and off-page polling; no allocation',flush=True)

 # NORMAL A pilote les longueurs B ; TRACK conserve six longueurs differentes.
 audio=0x930e0000;r.w32(0x40a7887c,audio);u.mem_write(audio,bytes(30712));u.mem_write(audio+30667,b'\x01');lengths=[5,7,12,16,31,64]
 for lane,length in enumerate(lengths):u.mem_write(pattern+264*lane+4,bytes([length,2]))
 saved=bytes(u.mem_read(pattern,1584));r.call('pg_poll');assert bytes(u.mem_read(pattern,1584))==saved
 assert r.call('pg_config',pattern,2,4,9)==1;assert bytes(u.mem_read(pattern+2*264+4,1))==b'\x09'
 for length in (1,5,16,17,31,32,48,64):
  u.mem_write(audio+30667,b'\0');u.mem_write(audio+30662,struct.pack('>H',length));snapshot=bytes(u.mem_read(audio,30712));r.call('pg_poll')
  assert [u.mem_read(pattern+264*lane+4,1)[0] for lane in range(6)]==[length]*6
  r.w32(r.s['mlp_obj'],0);assert r.call('pg_config',pattern,2,4,63)==1;assert u.mem_read(pattern+2*264+4,1)[0]==length;r.w32(r.s['mlp_obj'],OBJ)
  r.w32(clock,0)
  for tick in range(2*length+2):
   r.call('pg_clock',r.r32(r.s['ml_runtime']),pattern,clock,100000000+tick*5400000,1)
   assert [r.r32(clock+8+8*lane) for lane in range(6)]==[(tick+1)%length]*6,(length,tick)
  assert bytes(u.mem_read(audio,30712))==snapshot
 u.mem_write(audio+30667,b'\x01')
 for lane,length in enumerate(lengths):u.mem_write(pattern+264*lane+4,bytes([length,2]))
 r.w32(clock,0)
 for tick in range(80):
  r.call('pg_clock',r.r32(r.s['ml_runtime']),pattern,clock,100000000+tick*5400000,1)
  assert [r.r32(clock+8+8*lane) for lane in range(6)]==[(tick+1)%length for length in lengths]
 assert [u.mem_read(pattern+264*lane+4,1)[0] for lane in range(6)]==lengths
 empty=r.r32(r.s['ml_bank_empty']);before=bytes(u.mem_read(empty,1584));u.mem_write(audio+30667,b'\0');u.mem_write(audio+30662,b'\x00\x20');r.call('pg_clock',r.r32(r.s['ml_runtime']),empty,clock,200000000,0);assert bytes(u.mem_read(empty,1584))==before
 assert r.new_count==allocated
 # Len commun depuis B : vrais setters Len/page A et vraies touches/encodeur B.
 model=0x930c1000;header_vt=0x930c2000;getter=0x930c3000;notify=0x930c4000;settings_ui=0x930c5000;settings_raw=0x930c6000;settings_vt=0x930c7000
 header=audio+30642;r.w32(model+44,header_vt);r.w32(model+60,header);r.w32(header_vt+40,getter);r.w32(header_vt+16,notify)
 r.w32(settings_ui,settings_vt);r.w32(settings_ui+16,settings_raw);r.w32(settings_vt+40,getter);r.w32(settings_vt+16,notify)
 u.mem_write(getter,bytes.fromhex('206f0004202800104e75'));r.w32(0x40fe4228,0x93005000);r.w32(0x40fe4218,0);notifications=[]
 def bind(address,fn):
  fresh=address not in r.stubs;r.stubs[address]=fn
  if fresh:u.hook_add(UC_HOOK_CODE,r.stub,begin=address,end=address)
 bind(0x4000f208,lambda a:model);bind(0x4000eb90,lambda a:settings_ui);bind(notify,lambda a:notifications.append(a[0]) or 0)
 u.mem_write(audio+30667,b'\0');u.mem_write(audio+30662,b'\x00\x10');r.w32(r.s['mlp_obj'],OBJ);r.w32(r.s['mlp_track'],0)
 notes=[bytes(u.mem_read(pattern+264*lane+8,256)) for lane in range(6)]
 for value in (1,2,5,16,17,31,32,48,64):
  before=bytearray(u.mem_read(audio,30712));r.w32(settings_raw+8,3);count=len(notifications)
  assert r.call('pg_config',pattern,0,4,value)==1
  expected=max(2,value);before[30662:30664]=struct.pack('>H',expected)
  assert bytes(u.mem_read(audio,30712))==bytes(before)
  assert [u.mem_read(pattern+264*lane+4,1)[0] for lane in range(6)]==[expected]*6
  assert r.r32(settings_raw+8)==(3 if expected>48 else 0)
  assert model+44 in notifications[count:]
 # Les entrees invalides ne changent pas la longueur commune.
 for value in (0,65,0xffffffff):
  before=bytes(u.mem_read(audio,30712));assert r.call('pg_config',pattern,6,4,value)==0;assert bytes(u.mem_read(audio,30712))==before
 # Ouverture stock FUNC+PAGE, cycles PAGE de16 et limites DATA.
 for name in ('mlp_setup','mlp_func','mlp_func_inherited','mlp_held','mlp_edit','ml_genie_settings','TG_set_held'):
  if name in r.s:r.w32(r.s[name],0)
 def key(code,flags=1):return r.call('mlp_menu_key',OBJ,r.event(code,flags))
 def turn(delta):
  r.delta=delta;return r.call('mlp_enc',OBJ,r.event(1))
 u.mem_write(audio+30662,b'\x00\x10');r.call('pg_poll');key(1);key(15);key(15,0);key(1,0)
 assert r.r32(r.s['mlp_setup'])==2 and r.r32(r.s['mlp_row'])==3 and r.r32(r.s['mlp_edit'])==1
 for expected in (32,48,64,16,32):
  key(15);key(15,0);assert struct.unpack('>H',u.mem_read(audio+30662,2))[0]==expected
  assert [u.mem_read(pattern+264*lane+4,1)[0] for lane in range(6)]==[expected]*6
 turn(1);assert struct.unpack('>H',u.mem_read(audio+30662,2))[0]==33
 turn(-1);assert struct.unpack('>H',u.mem_read(audio+30662,2))[0]==32
 # Longueur partielle : PAGE atteint le prochain multiple de16.
 assert r.call('pg_config',pattern,0,4,17)==1;key(15);key(15,0);assert struct.unpack('>H',u.mem_read(audio+30662,2))[0]==32
 for _ in range(65):turn(-1)
 assert struct.unpack('>H',u.mem_read(audio+30662,2))[0]==2
 for _ in range(65):turn(1)
 assert struct.unpack('>H',u.mem_read(audio+30662,2))[0]==64
 assert [bytes(u.mem_read(pattern+264*lane+8,256)) for lane in range(6)]==notes
 # Mode TRACK : PAGE et DATA ne modifient que la voie MIDI selectionnee.
 u.mem_write(audio+30667,b'\x01');r.w32(r.s['mlp_track'],2)
 for lane,length in enumerate(lengths):u.mem_write(pattern+264*lane+4,bytes([length]))
 before=bytes(u.mem_read(audio,30712));key(15);key(15,0);assert [u.mem_read(pattern+264*lane+4,1)[0] for lane in range(6)]==[5,7,16,16,31,64]
 turn(1);assert u.mem_read(pattern+2*264+4,1)[0]==17;assert bytes(u.mem_read(audio,30712))==before
 print('PASS native shared A/B length setter and notifications, A page validation, FUNC+PAGE menu, PAGE16/32/48/64 wrap, DATA2..64, unchanged notes and independent per-track edits',prefix,flush=True)
 # Ouverture : page A heritee uniquement en mode normal et apres succes natif.
 native=[];opened=[1]
 settings=0x930b6100;vtable=0x930b6200;page_object=0x930b6300;getter=0x930b6400
 r.w32(settings,vtable);r.w32(vtable+40,getter);u.mem_write(getter,b'\x20\x3c'+struct.pack('>I',page_object)+b'\x4e\x75')
 def opening(a):
  native.append(1)
  if opened[0]:r.w32(r.s['mlp_obj'],OBJ)
  return opened[0]
 for address,fn in ((r.s['mlp_open'],opening),(0x400cf866,lambda a:0x930b6000),(0x4000eb90,lambda a:settings)):
  fresh=address not in r.stubs;r.stubs[address]=fn
  if fresh:u.hook_add(UC_HOOK_CODE,r.stub,begin=address,end=address)
 for mode in (0,1):
  for length in (5,17,32,48,64):
   u.mem_write(audio+30667,bytes([mode]));u.mem_write(audio+30662,struct.pack('>H',length))
   for page in range((length+15)//16):
    r.w32(r.s['mlp_obj'],0);r.w32(r.s['mlp_step'],7);r.w32(page_object+8,page);count=len(native);assert r.call('pg_open')==1;assert len(native)==count+1
    assert r.r32(r.s['mlp_step'])==(page*16 if mode==0 else 7),(mode,length,page)
 u.mem_write(audio+30667,b'\0');u.mem_write(audio+30662,b'\x00\x40');r.w32(r.s['mlp_obj'],0);r.w32(r.s['mlp_step'],19);r.w32(page_object+8,3);opened[0]=0;assert r.call('pg_open')==0;assert r.r32(r.s['mlp_step'])==19
 opened[0]=1;r.w32(r.s['mlp_obj'],OBJ);assert r.call('pg_open')==1;assert r.r32(r.s['mlp_step'])==19
 print('PASS normal-mode A-to-B page inheritance, per-track independence, native open forwarding, failed/already-open guards',prefix,flush=True)
 data=json.loads((ROOT/'docs/flasher-midi-page-leds-test/midi-page-leds-data.js').read_text().split('window.MCMidiPageLeds=',1)[1].strip().rstrip(';'));at=r.s['pg_api']-data['symbols']['pg_api'];size=len(data['hex'])//2;body=bytes(u.mem_read(at,size));slot=r.r32(r.s['mlp_led_vt']+16);r.call(0x4007929c);assert bytes(u.mem_read(at,size))==body and r.r32(r.s['mlp_led_vt']+16)==slot
 print('PASS normal length follows A 1/5/16/17/31/32/48/64, real clock wrap, independent per-track lengths/config, immutable empty bank, A bytes unchanged; no allocation',prefix,flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');a=p.parse_args()
 for i in range(3):
  prefix=ROOT/f'{CASES}/{i}-after';start=time.monotonic()
  while not prefix.with_suffix('.syx').exists():
   if not a.watch or time.monotonic()-start>1200:raise AssertionError(('missing build',i))
   time.sleep(2)
  run(prefix)
if __name__=='__main__':main()
