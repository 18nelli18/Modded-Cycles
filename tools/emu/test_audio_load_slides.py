"""Note 112 : vrai boot et tick slides candidat contre trampoline original."""
import argparse,json,pathlib,random,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();prefix=pathlib.Path(a.case);cat=json.loads(prefix.with_suffix('.json').read_text())['tweaks'];bank=next(t for t in cat if t['id']=='midi-out-bank');owner=next(t for t in cat if t.get('symbols',{}).get('ao_tick'));img=main_os_from_syx(str(prefix.with_suffix('.syx')))
 r=Rig(img,{'writes':[]},{'writes':[],'symbols':{**bank['symbols'],**owner['symbols']}});u=r.u
 for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,size)
 def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 sites=set()
 for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in cat for p in t.get('append',{}).get('parts',[]) if 'hex' in p]:sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
 for at in sites:u.hook_add(UC_HOOK_CODE,cache,begin=at,end=at)
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK);u.emu_start(0x40000530,0x4000053a,count=200_000_000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a;r.call(0x4007929c)
 for part in owner['append']['parts']:
  if 'hex' in part:assert bytes(u.mem_read(int(part['dest'],16),len(part['hex'])//2))==bytes.fromhex(part['hex'])
 print('PASS vrai boot/cache extension slides exacte',flush=True)
 rng=random.Random(112);pattern,clock=0x93080000,0x93090000;states=r.s['mlkc_slide_states'];queue=r.s['mlkc_queue'];counts=[0,0];count=[0]
 def count_code(u,pc,size,data):count[0]+=1
 u.hook_add(UC_HOOK_CODE,count_code)
 for case in range(512):
  u.mem_write(pattern,bytes(1584));initial=bytearray(384)
  for lane in range(6):
   u.mem_write(pattern+264*lane,bytes((1,int(case%17==0),6+lane,4,16,2,0,0))+bytes(256))
   active=0 if case<128 else rng.randrange(4096)
   struct.pack_into('>4I',initial,64*lane,pattern if case%7 else pattern+2000,50,1000,((6+lane)<<24)|(4<<16)|active)
   for knob in range(12):initial[64*lane+16+4*knob:64*lane+20+4*knob]=bytes((knob+40,rng.randrange(128),rng.randrange(128),rng.randrange(128)))
  rate=2 if case<128 else rng.choice((0,1,2,3,0xffffffff));cursor=rng.randrange(72) if case<128 or case%13 else 72;outputs=[]
  for index,name in enumerate(('ao_tick_original','mlkc_slide_tick')):
   r.w32(r.s['ml_clock_state'],clock);r.w32(clock,1 if case<128 or case%11 else 0);r.w32(r.s['ml_play_pattern'],pattern);r.w32(r.s['mlkcq_owner'],pattern if case<128 or case%9 else 0)
   r.w32(r.s['mlkc_slide_rate'],rate);r.w32(r.s['mlkc_slide_cursor'],cursor);r.w32(r.s['TG_blk_clk'],100+case*4)
   u.mem_write(states,bytes(initial));u.mem_write(queue,bytes(868));u.reg_write(mk.UC_M68K_REG_SR,0x2500);count[0]=0;r.call(name)
   if case<128:counts[index]+=count[0]
   outputs.append((bytes(u.mem_read(states,384)),bytes(u.mem_read(queue,868)),r.r32(r.s['mlkc_slide_rate']),r.r32(r.s['mlkc_slide_cursor'])))
   assert u.reg_read(mk.UC_M68K_REG_SR)&0x700==0x500
  assert outputs[0]==outputs[1],case
 print('PASS 512 cas slides : queue/etats/cadence/curseur identiques, arret/mute/owner/wrap',flush=True)
 assert counts[1]<counts[0];print('MESURE balayage vide instructions',counts,'reduction',round(100*(1-counts[1]/counts[0]),1),'%; pas cycles materiels',flush=True)
if __name__=='__main__':main()
