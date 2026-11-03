"""Echo12k : temps stock, stereo/ping, ranges, changement POTS et queues bornees."""
from pathlib import Path
import argparse,json,struct,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
from eco_fx351 import apply
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());native=(a.capture/'native.bin').read_bytes();runtime=bytearray((a.capture/'runtime.bin').read_bytes());d=apply(m,bytearray(native),runtime,a.output.parent/'module',pressure=True,delay=True);s=d['symbols'];fs=m['fx_menu']['symbols'];ps=m['per_track_fx']['symbols']
r=Rig(native,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,bytes(runtime));IN=0x93180000;OUT=IN+512;P=IN+1024;AUX=IN+2048;resets=[0];inits=[0]
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
def init(args):u.mem_write(args[0],bytes(256));inits[0]+=1;return 0
bind(ps['pots_native'],init);bind(ps['pots_reset'],lambda args:resets.__setitem__(0,resets[0]+1) or 0);bind(0x46835ff0,lambda args:0)
def block(values,time,fb,mode):
 u.mem_write(IN,struct.pack('>64i',*values));u.mem_write(P,struct.pack('>2h',time,fb));u.mem_write(OUT-4,b'ABCD');u.mem_write(OUT+256,b'EFGH');r.w32(fs['cr_mode'],mode)
 r.call(fs['fx_delay'],OUT,IN,P,AUX,AUX)
 assert bytes(u.mem_read(IN,256))==struct.pack('>64i',*values)
 assert bytes(u.mem_read(OUT-4,4))==b'ABCD' and bytes(u.mem_read(OUT+256,4))==b'EFGH'
 assert bytes(u.mem_read(ps['fx_line']-4,4))==b'1234' and bytes(u.mem_read(ps['fx_line']+262144,4))==b'5678'
 return struct.unpack('>64i',u.mem_read(OUT,256))
u.mem_write(ps['fx_line']-4,b'1234');u.mem_write(ps['fx_line']+262144,b'5678');rows=[]
for case,(mode,time,tempo) in enumerate([(0,0,14400),(5,0,14400),(0,4096,28800),(5,16384,14400)]):
 r.w32(ps['mf_fx_panic_count'],case+1);r.w32(0x40149310,tempo)
 target=(((time+256)*48000)>>10)*900//tempo;target=max(32,min(261120,target));rounded=(target+2)//4*4
 first=[None,None];limit=(rounded*2+512)//32+1
 for b in range(limit):
  values=[1000000000 if b==0 and i%2==0 else 0 for i in range(64)];out=block(values,time,20000,mode)
  for c in range(2):
   if first[c] is None:
    for j in range(32):
     if out[2*j+c]:first[c]=b*32+j;break
  assert all(-2147483648<=v<=2147483647 for v in out)
 assert first[0] is not None and abs(first[0]-rounded)<=4,(mode,time,rounded,first)
 if mode==0:assert first[1] is None,first
 else:assert first[1] is not None and abs(first[1]-rounded*2)<=8,(rounded,first)
 rows.append(dict(mode=mode,tempo=tempo,time=time,stock_samples=target,eco_samples=rounded,first_output=first))
# Fin de queue, meme au feedback maximal ; dernier echantillon de fondu nul.
for _ in range(3500):out=block([0]*64,0,32512,5)
assert not any(out)
# Invalider POTS avant de reutiliser sa ligne, afin que son retour reparte vide.
r.w32(ps['pots_slot_active'],1);r.w32(ps['mf_fx_panic_count'],9);r.w32(0x40149310,14400);block([2147483647]*64,0,32512,5)
assert r.r32(ps['pots_slot_active'])==0 and r.r32(ps['pots_slot_gain'])==256 and resets[0]==inits[0]
# Retour POTS : le vrai navigateur doit deleguer, pas rester sur le moteur Eco.
delegated=[0];bind(s['sf_old_delay'],lambda args:delegated.__setitem__(0,delegated[0]+1) or 0)
block([0]*64,0,0,12);assert delegated[0]==1
block([1000000000]*64,0,32512,0);block([0]*64,0,0,12)
assert not any(block([0]*64,0,0,0))
a.output.write_text(json.dumps(dict(rows=rows,stereo_and_ping=True,guarded_buffers=True,POTS_line_reset_before_reuse=True,tail_ends=True,native_initializations=inits[0],hardware_cycles=False),indent=2)+'\n')
print('PASS Eco Delay: stock Time mapping, stereo/ping timing, bounded tail, POTS transition and buffer guards',flush=True)
