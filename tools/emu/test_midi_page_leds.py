"""Note120 : vrai bootstrap, callback LED B et boucle PAGE stock compares."""
import argparse,json,pathlib,struct,sys,time
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_UNMAPPED,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,OBJ,STACK
ROOT=HERE.parent.parent

def run(prefix):
 img,mem,ts=boot_case(prefix);bank=next(t for t in ts if t['id']=='midi-out-bank');q=next(t for t in ts if t['id']=='midi-page-leds-test');r=Rig(img,{'writes':[]},{'writes':[],'symbols':{**bank['symbols'],**q['symbols']}});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in mem:u.mem_write(at,raw)
 assert r.call('ml_prepare')==1;clock=r.r32(r.s['ml_clock_state']);active=0x930b0000;r.w32(0x40a7887c,active);r.w32(active+30706,0);assert r.call('ml_bank_ui_sync')==1;pattern=r.r32(r.s['ml_pattern']);r.w32(r.s['mlp_obj'],OBJ);r.w32(r.s['ml_play_pattern'],pattern)
 led=0x930b1000;claims=0x930b2000;mapping=0x930b3000;pages=[r.r32(0x400fbccc+4*i) for i in range(4)];pads=[r.r32(0x400fbc78+4*i) for i in range(6)]
 r.w32(0x404a8bc4,0x400fbccc);r.w32(0x404a8bdc,mapping);u.mem_write(mapping,struct.pack('>16I',*range(1,17)));r.w32(0x404a8ba0,0x400fbc78)
 for at,fn in ((0x400cf9a8,lambda a:0x930b4000),(0x4006b978,lambda a:0),(0x400cfaf4,lambda a:led),(0x4008e942,lambda a:a[0]),(0x4008e964,lambda a:0),(0x4008e998,lambda a:0),(0x4008e8ce,lambda a:0)):
  r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 u.hook_add(UC_HOOK_MEM_UNMAPPED,lambda u,access,addr,size,value,data:print('UNMAPPED',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),size,flush=True) or False)
 cb=r.r32(r.s['mlp_led_vt']+16);assert cb==r.s['pg_led'];allocated=r.new_count;tests=0
 def states():return [r.r32(led+40+4*i) for i in pages]
 def stock(selected,step):
  u.mem_write(led,bytes(256));u.reg_write(mk.UC_M68K_REG_D2,led);u.reg_write(mk.UC_M68K_REG_D5,step//16 if step>=0 else 0xffffffff);u.reg_write(mk.UC_M68K_REG_D6,selected);u.reg_write(mk.UC_M68K_REG_D7,int(step>=0 and (step&3)>1));u.reg_write(mk.UC_M68K_REG_A7,STACK);u.emu_start(0x400222f2,0x40022346,count=10000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x40022346;assert u.reg_read(mk.UC_M68K_REG_A7)==STACK;return states()
 for lane in range(6):
  r.w32(r.s['mlp_track'],lane)
  for length in (5,16,17,31,32,48,64):
   u.mem_write(pattern+264*lane+4,bytes([length]))
   for selected in range((length+15)//16):
    r.w32(r.s['mlp_step'],selected*16)
    for step in [s for s in (0,1,2,3,14,15,16,17,30,31,32,47,48,63) if s<length]:
     r.w32(0x40a7883c,1);r.w32(clock,1);r.w32(clock+8+8*lane,(step+1)%length);expected=stock(selected,step);u.mem_write(led,bytes(256));u.mem_write(claims,bytes(8));assert r.call(cb,OBJ+0x500,0,claims)==1;assert states()==expected,(lane,length,selected,step,states(),expected)
     mask=r.r32(claims)<<32|r.r32(claims+4);assert mask==sum(1<<i for i in list(range(1,17))+pads+pages),hex(mask)
     tests+=1
    for transport in (0,2):
     r.w32(0x40a7883c,transport);expected=stock(selected,-1);u.mem_write(led,bytes(256));assert r.call(cb,OBJ+0x500,0,claims)==1;assert states()==expected
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
 print('PASS',prefix,tests,'playing states match actual stock PAGE loop; stopped/paused, masks, six lane lengths, B exit and off-page polling; no allocation',flush=True)

 # NORMAL A pilote les longueurs B ; TRACK conserve six longueurs differentes.
 audio=0x930e0000;r.w32(0x40a7887c,audio);u.mem_write(audio,bytes(30712));u.mem_write(audio+30667,b'\x01');lengths=[5,7,12,16,31,64]
 for lane,length in enumerate(lengths):u.mem_write(pattern+264*lane+4,bytes([length,2]))
 saved=bytes(u.mem_read(pattern,1584));r.call('pg_poll');assert bytes(u.mem_read(pattern,1584))==saved
 assert r.call('pg_config',pattern,2,4,9)==1;assert bytes(u.mem_read(pattern+2*264+4,1))==b'\x09'
 for length in (1,5,16,17,31,32,48,64):
  u.mem_write(audio+30667,b'\0');u.mem_write(audio+30662,struct.pack('>H',length));snapshot=bytes(u.mem_read(audio,30712));r.call('pg_poll')
  assert [u.mem_read(pattern+264*lane+4,1)[0] for lane in range(6)]==[length]*6
  assert r.call('pg_config',pattern,2,4,63)==1;assert u.mem_read(pattern+2*264+4,1)[0]==length
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
 data=json.loads((ROOT/'docs/flasher-midi-page-leds-test/midi-page-leds-data.js').read_text().split('window.MCMidiPageLeds=',1)[1].strip().rstrip(';'));at=r.s['pg_api']-data['symbols']['pg_api'];size=len(data['hex'])//2;body=bytes(u.mem_read(at,size));slot=r.r32(r.s['mlp_led_vt']+16);r.call(0x4007929c);assert bytes(u.mem_read(at,size))==body and r.r32(r.s['mlp_led_vt']+16)==slot
 print('PASS normal length follows A 1/5/16/17/31/32/48/64, real clock wrap, independent per-track lengths/config, immutable empty bank, A bytes unchanged; no allocation',prefix,flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');a=p.parse_args()
 for i in range(3):
  prefix=ROOT/f'build/midi-page-leds/{i}-after';start=time.monotonic()
  while not prefix.with_suffix('.syx').exists():
   if not a.watch or time.monotonic()-start>1200:raise AssertionError(('missing build',i))
   time.sleep(2)
  run(prefix)
if __name__=='__main__':main()
