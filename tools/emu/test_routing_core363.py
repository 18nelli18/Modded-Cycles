"""Quatre bus reels : PCM/gains/etat/EMAC/ABI et changements de routes exacts."""
from pathlib import Path
import argparse,json,random,struct,sys,subprocess
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
import emac
from routing_core363 import apply
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());native=bytearray((a.capture/'native.bin').read_bytes());runtime=bytearray((a.capture/'runtime.bin').read_bytes());d=apply(m,native,runtime,a.output.parent/'module');sy=m['per_track_fx']['symbols'];r=Rig(bytes(native),{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,bytes(runtime));u.mem_map(0x80000000,0x20000);u.mem_write(0x80000000,(a.capture/'sram.bin').read_bytes())
real_run=subprocess.run
def run(cmd,*args,**kwargs):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=['H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe',*cmd[1:]]
 return real_run(cmd,*args,**kwargs)
subprocess.run=run;mac=emac.EMAC(u)
spans=[(0x40056000,8192),(m['per_track_fx']['code'],m['per_track_fx']['code_bytes']),(m['complete_irq_accounting']['code'],m['complete_irq_accounting']['code_bytes'])]
for key in ['sparse_static_mixer','native_two_mix300']:
 if m.get(key):spans.append((m[key]['code'],m[key]['code_bytes']))
for i,(at,n) in enumerate(spans):
 raw=a.output.parent/f'code{i}.bin';raw.write_bytes(u.mem_read(at,n));mac.install(emac.disasm(str(raw),at,at,at+n))
sync=[0]
def synchronize(args):sync[0]+=1;return 0
u.hook_add(UC_HOOK_CODE,r.stub,begin=sy['mf_sync_audio'],end=sy['mf_sync_audio']);r.stubs[sy['mf_sync_audio']]=synchronize
rng=random.Random(363);out=0x41000000;inp=0x41001000;dp=0x41002000;rows=[]
regs=[getattr(C,'UC_M68K_REG_'+name) for name in ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']]
for case in range(128):
 mode,ready=[(0,1),(1,0),(1,1),(1,1)][case%4];routes=bytes(12) if case%8<4 else bytes(rng.randrange(5) for _ in range(12));sources=struct.pack('>224I',*[rng.getrandbits(32) for _ in range(224)]);seed=[rng.getrandbits(32) for _ in regs];acc=[0]+[rng.getrandbits(48) for _ in range(3)]
 masks=[0,1,3,63,127][case%5];gain=[];delta=[]
 for count in [6,6,7,7]:
  gain.append([rng.randrange(-0x70000000,0) if masks&(1<<t) else 0 for t in range(count)]);delta.append([rng.randrange(-100000,100000) if masks&(1<<t) and case%3==0 else 0 for t in range(count)])
 before=bytes(u.mem_read(0x46700000,0x300000));results=[];cost=[]
 for optimized in [False,True]:
  u.mem_write(0x46700000,before);u.mem_write(sy['mf_live'],routes+bytes(36));r.w32(sy['mf_mode'],mode);r.w32(sy['mf_audio_ready'],ready);r.w32(sy['enabled'],0x12345678);r.w32(0x40a78888,0x41004000);u.mem_write(0x404e9b53,bytes([case%64]));u.mem_write(inp,sources);u.mem_write(out,b'X'*1024);sync[0]=0
  for patch in d['patches']:
   raw=bytes.fromhex(patch['new' if optimized else 'old']);u.mem_write(patch['at'],raw);u.ctl_remove_cache(patch['at'],patch['at']+len(raw))
  for t in range(6):u.mem_write(0x41004000+28+100*t+38,bytes([17 if t==case%6 else t]))
  for j,address in enumerate([0x40a78bd0,0x40a78bb8,0x40a78b9c,0x40a78b80]):u.mem_write(address,struct.pack('>%di'%len(gain[j]),*gain[j]));u.mem_write(dp+32*j,struct.pack('>%di'%len(delta[j]),*delta[j]))
  for reg,value in zip(regs,seed):u.reg_write(reg,value)
  mac.macsr=0xa0
  for j,value in enumerate(acc):mac.acc[j]=value
  n=[0];hook=u.hook_add(UC_HOOK_CODE,lambda *unused:n.__setitem__(0,n[0]+1))
  for j,address in enumerate([0x40a78bd0,0x40a78bb8,0x40a78b9c,0x40a78b80]):
   if j==2 and case%8==7:u.mem_write(sy['mf_live'],bytes(12))
   entry=d['symbols']['ac_sum6' if j<2 else 'ac_sum7'] if optimized else sy['mf_sum6' if j<2 else 'mf_sum7'];r.call(entry,out+4*(j%2)+(512 if j>=2 else 0),inp,address,dp+32*j)
  u.hook_del(hook);assert [u.reg_read(reg) for reg in regs]==seed
  state=bytearray(u.mem_read(0x46700000,0x300000))
  for patch in d['patches']:
   raw=bytes.fromhex(patch['old']);state[patch['at']-0x46700000:patch['at']-0x46700000+len(raw)]=raw
  results.append((bytes(u.mem_read(out,1024)),bytes(u.mem_read(0x40a78b80,104)),bytes(state),mac.macsr,list(mac.acc),sync[0]));cost.append(n[0])
 assert results[0]==results[1],(case,[i for i,(x,y) in enumerate(zip(*results)) if x!=y]);assert sync[0]==1
 rows.append(dict(case=case,mode=mode,ready=ready,routed=any(routes),mask=masks,old=cost[0],new=cost[1],saved=cost[0]-cost[1]))
a.output.write_text(json.dumps(dict(module=d,cases=rows,PCM_gain_state_EMAC_ABI_exact=True,sync_once=True,routing_changes_immediate=True),indent=2)+'\n');print('PASS128 four-bus cases, exact PCM/gains/state/EMAC/ABI; sync once; route changes immediate');print('instruction range',min(x['saved'] for x in rows),max(x['saved'] for x in rows))
