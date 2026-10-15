"""Codec son natif, LFO2 conservé, ladder réel et contournement sampler."""
import json,struct,random
import build,test_lfo_plus as C
from chord_keys_pr87 import load_stock
from unicorn import m68k_const as m
P='work/wizard-filter-integration/';data=json.load(open(P+'recipe.json'));f=data['recipe'];w=json.load(open('work/sample-wizard-main/installer.json'));lf=next(t for t in json.load(open('work/sample-wizard-options/case-pair-lfo-secondary.json'))['tweaks'] if t['id']=='lfo-secondary')
for ch in data['changes']:
 i=ch['off']*2;p=w['append']['parts'][0];assert p['hex'][i:i+len(ch['old'])]==ch['old'];p['hex']=p['hex'][:i]+ch['new']+p['hex'][i+len(ch['old']):]
stock=load_stock('firmware/model-cycles_OS1.13.syx');image,_=build.apply_writes(stock,[w,lf,f]);r=C.Rig(image,[(int(w['append']['dest'],16),build.payload_runtime(w,stock,None))]);s={k:int(v,16) for k,v in w['symbols'].items()};sy={k:int(v,16) for k,v in f['symbols'].items()}
rng=random.Random(41);values=[0x4c00,0x0800,0x0300,0x1800,0x5100]
for machine in range(7):
 for fn in [C.SND_SAVE1,C.SND_SAVE2]:
  snd=bytearray(C.sound_bytes(rng,values));snd[38]=machine;struct.pack_into('>HH',snd,68,0x3300,0x2100);snd[72:76]=b'\x12\x34\x56\x78'
  r.uc.mem_write(C.SOUND,bytes(snd));r.uc.mem_write(C.REC,b'\xa5'*100);assert r.call(fn,C.REC,C.SOUND,check='shared sound save')&255==1
  rec=r.rd(C.REC,100);assert rec[78:82]==bytes.fromhex('4c002100');tag=r.r32(C.REC+88);assert tag>>30==2
  r.uc.mem_write(C.SOUND2,b'\x55'*100);r.call(C.SND_LOAD,C.SOUND2,C.REC,check='shared sound load');assert r.rd(C.SOUND2+68,4)==bytes.fromhex('33002100');assert fn==C.SND_SAVE1 or [r.r16(C.SOUND2+76+2*i) for i in range(5)]==values,(machine,hex(fn))
  assert r.rd(C.SOUND2+72,4)==b'\x12\x34\x56\x78'
print('PASS 14 native sound saves / filter reloads (7 current-format LFO2 reloads): filter, LFO2 first five settings, Wizard mode/Slice packed state, ABI preserved')
frame=C.FAKE+0x20000;buf=C.FAKE+0x30000;voice=C.FAKE+0x40000
signal=[0x10000000 if i%2==0 else -0x10000000 for i in range(32)];raw=struct.pack('>32i',*signal)
for track in range(6):
 r.w32(s['voice_ptr']+4*track,voice);r.w32(voice+56,0)
 for machine,cut,reso,bypass in [(0,32512,0,True),(5,0x1800,0,False),(7,0x1800,0,False),(6,0x1800,0,True)]:
  r.w16(frame+48,cut);r.w16(frame+50,reso);r.call(s['gflt_coef'],regs={C.D[1]:machine,C.D[2]:track,C.A[2]:frame},check='coefficient ABI')
  r.uc.mem_write(buf,raw);r.call(s['gflt_run'],buf,track,check='ladder ABI');out=struct.unpack('>32i',r.rd(buf,128))
  assert (r.rd(buf,128)==raw) if bypass else sum(abs(x) for x in out)<sum(abs(x) for x in signal),(track,machine,cut)
print('PASS real ladder on 6 tracks: stock/extra voices filtered, open-cutoff bypass bit exact, Wizard bypass bit exact; no LFO2 parameter slots touched')
r.stub(0x4001e814,lambda a:123);assert r.call(sy['avf_objects'],1,2,3,4)==123
for descriptor in [11,12]:assert r.r32(0x40a71754+100*descriptor+32)==0x400456c8 and r.r32(0x40a71754+100*descriptor+44)==0
assert not C.FAIL and not r.bad,(C.FAIL,r.bad)
print('PASS native parameter UI formatters for Filter/Res; all native ABI checks passed')
# Pool du pattern : format natif, paramètres 23..31 et anciennes valeurs inchangés.
ram=C.FAKE+0x50000;file=C.FAKE+0x60000
locks=[(0,0,24,0x2300),(1,4,25,0x1800),(5,63,24,0x7600),(2,9,13,0x4400),(3,7,23,0x1000),(4,2,31,0x0200),(5,5,32,0x1200)]
def init():r.uc.mem_write(ram,(b'\xff\xff'*(34*64)+bytes(33))*6)
def lock(t,step,k,v):r.w16(ram+4385*t+68*step+2*k,v);r.w8(ram+4385*t+4352+k,1)
def verify():
 for t,step,k,v in locks:assert r.r16(ram+4385*t+68*step+2*k)==v,(t,step,k)
init()
for l in locks:lock(*l)
r.uc.mem_write(file,bytes(10400));r.call(0x4005b95c,file,ram,0,check='pool save');init();r.call(0x4005b766,ram,file,check='pool load');verify()
lock(0,8,24,0x3400);r.call(0x4005ba90,file,ram,0,24,0,check='pool update');init();r.call(0x4005b766,ram,file,check='pool reload');verify();assert r.r16(ram+8*68+48)==0x3400
assert not C.FAIL and not r.bad,(C.FAIL,r.bad)
print('PASS native pattern pool save/load/update: cutoff/res locks, ordinary locks and extended indices retained')
# Adaptateurs installés : registres du pré-traitement et six blocs post-volume.
seen=[]
def pre_stub(args):
 seen.append((r.uc.reg_read(C.D[1]),r.uc.reg_read(C.D[2]),r.uc.reg_read(C.A[6])))
 return 0
r.stub(s['sampler_pre'],pre_stub)
for track in range(6):
 r.w8(frame+18,0);r.w16(frame+48,32512);r.w16(frame+50,0)
 r.call(sy['avf_pre'],regs={C.D[1]:0x12345678,C.D[2]:track,C.A[2]:frame,C.A[6]:voice},check='pre wrapper ABI')
 assert seen[-1]==(0x12345678,track,voice) and r.r32(s['voice_ptr']+4*track)==voice
r.stub(0x40056f58,lambda a:seen.append(tuple(a[:2])) or 0)
for track in range(6):
 r.w16(frame+48,0x1800 if track==0 else 32512);r.w16(frame+50,0);r.call(s['gflt_coef'],regs={C.D[1]:0,C.D[2]:track,C.A[2]:frame},check='coefficient setup')
 r.uc.mem_write(buf+128*track,raw)
r.call(sy['avf_post'],buf,frame,check='post wrapper ABI');assert seen[-1]==(buf,frame);assert r.rd(buf,128)!=raw
for track in range(1,6):assert r.rd(buf+128*track,128)==raw
assert not C.FAIL and not r.bad,(C.FAIL,r.bad)
print('PASS installed pre/post adapters: 6 voice pointers, original native registers/arguments retained; selected track filtered, other five bit-identical')
