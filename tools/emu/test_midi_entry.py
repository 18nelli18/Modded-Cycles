"""Note114 : vrai bootstrap, gate de premiere ouverture, MIDI/curseur et transport."""
import argparse,json,pathlib,sys,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build

def boot_case(prefix):
 path=pathlib.Path(prefix);ts=json.loads(path.with_suffix('.json').read_text())['tweaks'];img=main_os_from_syx(str(path.with_suffix('.syx')));r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
 for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,size)
 sites=set()
 for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in ts for p in t.get('append',{}).get('parts',[]) if 'hex'in p]:sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
 for site in sites:u.hook_add(UC_HOOK_CODE,lambda u,pc,size,data:u.reg_write(mk.UC_M68K_REG_PC,pc+4),begin=site,end=site)
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK);u.emu_start(0x40000530,0x4000053a,count=200_000_000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a
 memories=[(int(t['append']['dest'],16),bytes(u.mem_read(int(t['append']['dest'],16),t['append']['size']))) for t in ts if t.get('append')]
 return bytes(u.mem_read(build.BASE,0x40200000-build.BASE)),memories,ts

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();img,memories,ts=boot_case(a.case);bank=next(t for t in ts if t['id']=='midi-out-bank')
 for reference in (True,False):
  r=Rig(img,{'writes':[]},{'writes':[],'symbols':bank['symbols']});u=r.u;u.mem_map(0x43000000,0x800000);u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000)
  for dest,raw in memories:u.mem_write(dest,raw)
  for t in ts:
   for part in t.get('append',{}).get('parts',[]):
    if 'hex'in part:u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  at=r.s['ml_native_tick'];assert bytes(u.mem_read(at+0x30,4)).hex()=='67000050';assert bytes(u.mem_read(at+0x3a,4)).hex()=='66000046'
  if reference:u.mem_write(at+0x32,b'\0\x5c');u.mem_write(at+0x3c,b'\0\x52')
  assert r.r32(r.s['ml_context'])==0
  r.w32(r.s['ml_start_due'],100);r.w32(r.s['ml_start_context'],0);r.w32(r.s['ml_start_serial'],1);r.w32(0x40a7883c,1)
  assert r.call('ml_prepare')==1;ctx=r.r32(r.s['ml_context']);runtime=r.r32(r.s['ml_runtime']);clock=r.r32(r.s['ml_clock_state']);pattern=r.r32(r.s['ml_pattern'])
  active=0x930b0000;r.w32(0x40a7887c,active);r.w32(active+30706,0)
  assert r.call('ml_bank_ui_sync')==1;r.call('ml_repeat_prepare_ui')
  for lane in range(6):
   for step in range(16):
    assert r.call('ml_edit',pattern,lane,step,0,60+step)==1;assert r.call('ml_edit',pattern,lane,step,3,1)==1
  original=bytes(u.mem_read(pattern,1584));allocations=r.new_count
  def forbidden(u,pc,size,data):raise AssertionError('allocation/sortie physique depuis audio '+hex(pc))
  for site in (0x400802e0,0x400826b0):u.hook_add(UC_HOOK_CODE,forbidden,begin=site,end=site)
  def drain():
   out=[]
   while (packet:=r.call('ml_take',runtime)):out.append(packet)
   return out
  def tick(now,mode=1):
   r.w32(0x8000184c,now&0xffffffff);r.w32(0x40a7883c,mode);u.reg_write(mk.UC_M68K_REG_SR,0x2500);r.call('ml_native_tick');assert u.reg_read(mk.UC_M68K_REG_SR)&0x700==0x500
  notes=[];cursors=[]
  for step in range(17):
   tick(1000000+step*5400000);packets=drain();notes.extend(p for p in packets if p>>28==9);cursors.append(r.call('mlp_cursor')&0xffffffff)
  if reference:assert notes==[] and cursors==[0xffffffff]*17
  else:
   assert len(notes)==102;assert [(p>>16)&127 for p in notes]==[60+i%16 for i in range(17) for lane in range(6)];assert cursors==list(range(16))+[0]
   tick(1000000+16*5400000+1,0);assert len(drain())==6 and r.r32(clock)==0
   tick(1000000+16*5400000+2,0);assert drain()==[]
   due=200000000;r.w32(r.s['ml_start_due'],due);r.w32(r.s['ml_start_context'],ctx);r.w32(r.s['ml_start_serial'],2);r.w32(r.s['ml_start_resume'],0)
   tick(due-1);assert drain()==[];tick(due+100);packets=drain();assert len(packets)==6 and all((p>>16)&127==60 for p in packets)
   tick(due+5400000);drain();tick(due+5400001,2);assert len(drain())==6 and r.r32(clock)==2
   resumed=300000000;r.w32(r.s['ml_start_due'],resumed);r.w32(r.s['ml_start_serial'],3);r.w32(r.s['ml_start_resume'],1)
   tick(resumed-1);assert not drain();tick(resumed);assert not drain();tick(resumed+5399999);assert [((p>>16)&127) for p in drain() if p>>28==9]==[62]*6
  assert bytes(u.mem_read(pattern,1584))==original and r.new_count==allocations
  print('PASS', 'reference bloque premiere entree' if reference else 'candidat : six voies,16 pas+reboucle,Stop/Start/Pause/Continue,curseur et ABI,aucune allocation IRQ',flush=True)
 print('LIMITES : ports physiques, LEDs et entree par boutons a verifier sur appareil')
if __name__=='__main__':main()
