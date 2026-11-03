"""Frontiere postmix : sorties/etat et delegates, avec stereo, routes et queues."""
from pathlib import Path
import argparse,json,random,struct,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from routing_post364 import apply
from unicorn import UC_HOOK_CODE,m68k_const as C
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());native=bytearray((a.capture/'native.bin').read_bytes());runtime=bytearray((a.capture/'runtime.bin').read_bytes());d=apply(m,native,runtime,a.output.parent/'module');s=m['per_track_fx']['symbols'];r=Rig(bytes(native),{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,bytes(runtime));u.mem_map(0x80000000,0x20000);MIX=0x41000000;SIDE=0x41002000;ON=0x41003000;rng=random.Random(364);calls=[];active=[False]
def native_post(args):calls.append(('native',args[0]));return 0
def mask(args):calls.append(('mask',args[0]));return args[0]|2
def slots(args):
 left,right,route,send,enabled,out=args[:6];calls.append(('slots',bytes(u.mem_read(left,768)),bytes(u.mem_read(right,768)),bytes(u.mem_read(route,12)),bytes(u.mem_read(send,96)),enabled))
 if not active[0]:return 0
 values=[(i-32)*12000000 for i in range(64)];u.mem_write(out,struct.pack('>64i',*values));return 1
for at,fn in [(s['mf_old_post'],native_post),(s['lt_source_mask'],mask),(s['lt_run_slots'],slots)]:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at);r.stubs[at]=fn
rows=[];regs=[getattr(C,'UC_M68K_REG_'+x) for x in ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']]
for case in range(96):
 mode=case%4!=0;ready=case%4!=1;routes=bytes(12) if case%3==0 else bytes([rng.randrange(5) for _ in range(6)]+[rng.randrange(4) for _ in range(6)]);requested=int(any(routes));tail=(1<<(case%8)) if case%5==0 else 0;active[0]=bool(requested or tail);signal=struct.pack('>64i',*[rng.randrange(-2000000000,2000000001) for _ in range(64)]);mid=struct.pack('>192i',*[rng.randrange(-2000000000,2000000001) for _ in range(192)]);side=mid[::-1];on=struct.pack('>6I',*[int((case>>i)&1) for i in range(6)]);initial=bytes(u.mem_read(0x46700000,0x300000));seed=[rng.getrandbits(32) for _ in regs];results=[];counts=[];logs=[]
 for optimized in [False,True]:
  u.mem_write(0x46700000,initial);u.mem_write(s['mf_live'],routes+bytes(36))
  for key,value in [('mf_mode',mode),('mf_audio_ready',ready),('mf_requested',requested),('lt_active',tail),('enabled',case%64),('mf_side',SIDE if case%7 else 0),('mf_side_on',ON if case%7 else 0)]:r.w32(s[key],value)
  u.mem_write(MIX-4,b'ABCD'+signal+b'EFGH');u.mem_write(0x80001858,mid);u.mem_write(SIDE,side);u.mem_write(ON,on);calls.clear()
  for patch in d['patches']:
   raw=bytes.fromhex(patch['new' if optimized else 'old']);u.mem_write(patch['at'],raw);u.ctl_remove_cache(patch['at'],patch['at']+len(raw))
  for reg,value in zip(regs,seed):u.reg_write(reg,value)
  n=[0];hook=u.hook_add(UC_HOOK_CODE,lambda *unused:n.__setitem__(0,n[0]+1));r.call(s['mf_post'],MIX);u.hook_del(hook);assert [u.reg_read(reg) for reg in regs]==seed
  state=bytearray(u.mem_read(0x46700000,0x300000))
  for patch in d['patches']:
   raw=bytes.fromhex(patch['old']);state[patch['at']-0x46700000:patch['at']-0x46700000+len(raw)]=raw
  results.append((bytes(u.mem_read(MIX-4,264)),bytes(state)));counts.append(n[0]);logs.append(calls.copy())
 assert results[0]==results[1],case
 if mode and ready and not active[0]:assert [x[0] for x in logs[0]]==['native','slots'] and [x[0] for x in logs[1]]==['native'] and counts[1]<counts[0]
 else:assert logs[0]==logs[1],case
 assert results[0][0][:4]==b'ABCD' and results[0][0][-4:]==b'EFGH';rows.append(dict(case=case,active=active[0],mode=mode,ready=ready,instructions=counts,saved=counts[0]-counts[1]))
a.output.write_text(json.dumps(dict(module=d,cases=rows,PCM_state_ABI_exact=True,tail_delegation_retained=True,stereo_inputs_and_routes_exact=True,native_post_always_called=True),indent=2)+'\n');print('PASS96 post boundaries: exact PCM/state/ABI, stereo reconstruction, clipping, routes, tails and mandatory native post');print('instruction range',min(x['saved'] for x in rows),max(x['saved'] for x in rows))
