"""Banc RPC : delegation UI, modificateurs bornes, snapshots et restauration."""
from pathlib import Path
import argparse,json,struct,sys,random
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
m=json.loads((a.build/'BUILD.json').read_text());d=m['remote_panel'];s=d['symbols'];al=d['aliases'];r=Rig((a.capture/'native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,(a.capture/'runtime.bin').read_bytes());u.mem_map(0xfc070000,4096)
app=0x41000000;node=app+0x1000;view=app+0x2000;msg=app+0x3000;data=msg+0x100;params=app+0x4000;queue=[];keys=[];encoders=[];writes=[];panics=[]
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
bind(0x400d0974,lambda args:app);bind(al['rp_old_request'],lambda args:0);bind(al['rp_old_send'],lambda args:0);bind(al['rp_old_held'],lambda args:0)
bind(0x400072c0,lambda args:queue.append(bytes(u.mem_read(args[1],16))) or 1)
bind(0x40077720,lambda args:keys.append((args[0],struct.unpack('>6I',u.mem_read(args[1],24)))) or 1)
bind(0x40059692,lambda args:panics.append(('transport',args[0])) or 0)
if al.get('rp_deep_stop',0x40059692)!=0x40059692:bind(al['rp_deep_stop'],lambda args:panics.append(('transport',args[0])) or 0)
bind(0x40058c04,lambda args:panics.append(('set',args[0])) or 0)
if al.get('rp_clear_counters'):bind(al['rp_clear_counters'],lambda args:0)
bind(al['rp_ui_encoder'],lambda args:encoders.append((args[0],struct.unpack('>6I',u.mem_read(args[1],24)),r.r32(s['scope']))) or 1)
bind(al['rp_params'],lambda args:params+128*args[0]);bind(0x400cf866,lambda args:app+0x5000);bind(0x4000eb9c,lambda args:app+0x6000);bind(0x40009c1a,lambda args:app+0x7000+128*args[1])
if d.get('stock_machine_test'):
 u.mem_map(0x80000000,0x20000);bind(0x40009c5a,lambda args:70+args[1])
 bind(0x400cf9a8,lambda args:app+0x5000);bind(0x4006ba76,lambda args:0xa5a50000);bind(0x4006b978,lambda args:0x5a5a0000);bind(0x4006bdfe,lambda args:0xffff0000)
def setter(args):
 pair=struct.unpack('>2I',u.mem_read(args[1],8));values=struct.unpack('>'+str((pair[1]-pair[0])//4)+'I',u.mem_read(pair[0],pair[1]-pair[0]));writes.append((args[0],values))
 for i in range(0,len(values),2):u.mem_write(params+128*((args[0]-app-0x7000)//128)+2*values[i],struct.pack('>H',values[i+1]>>16))
 return 1
bind(0x4001416c,setter)
sentinel=app+84;r.w32(sentinel,node);r.w32(node,sentinel);r.w32(node+8,view);r.w32(view,0x400ff000);r.w32(al['rp_menu'],0)
for t in range(6):
 for slot,value in [(9,t),(20,20+t),(21,40+t),(24,127-t),(25,t),(26,70+t)]:u.mem_write(params+128*t+2*slot,struct.pack('>H',value<<8))
def request(body):
 u.mem_write(data,bytes.fromhex('1234000002')+body);r.w32(msg+8,0x02000000);r.w32(msg+12,data);r.w32(msg+16,data+5+len(body));r.call('rp_request',msg)
def run(body):
 request(body);assert len(queue)==1;queue.pop();r.call('rp_run',0);assert not r.r32(s['queued']) and not r.r32(s['scope']);assert r.r32(s['status'])==2
for token,key,count in [(b'SMPL318!',10,1),(b'SMST318!',11,1),(b'SMS2318!',11,2)]:
 keys.clear();run(token);assert len(keys)==count*2 and all(x[0]==app+64 and x[1][3]==key for x in keys);assert [x[1][4] for x in keys]==[1,16]*count
 if d.get('native_key_event_vtable'):
  for ctx,event in keys:
   assert event[0]==d['native_key_event_vtable'];ti=r.r32(event[0]-4);name=r.r32(ti+4);assert r.string(name)=='8KeyEvent'
expected=[('transport',0),('set',1)] if d.get('panic_api')=='soft-setter' else [('transport',1)] if d.get('double_stop_native_panic') else []
assert panics==expected,(panics,expected)
if d.get('deep_stop_test'):
 run(b'SMDS318!');assert panics==expected+[('transport',1)]
 run(b'SMNP318!');assert panics==expected+[('transport',1)]
if al.get('rp_clear_counters'):
 keys.clear();run(b'SMN2318!');assert [event[4] for ctx,event in keys]==[1,16,5,20]
 keys.clear();run(b'SMPB318!');assert [event[3:5] for ctx,event in keys]==[(5,3),(5,18)]
 keys.clear();run(b'SMBK318!');assert [event[3:5] for ctx,event in keys]==[(12,1),(12,16)]
 run(b'SMCP318!')
if d.get('sequence_genie_open'):
 keys.clear();run(b'SMGE348!');assert [(x[1][3],x[1][4]) for x in keys]==[(13,1),(15,1),(15,16),(13,16)],keys
 assert not r.r32(s['scope'])
for token,knob,delta in [(b'SMFC318!',6,1),(b'SMFC318!',6,-32),(b'SMFR318!',7,4)]:
 encoders.clear();run(token+bytes([delta&255]));assert len(encoders)==1;ctx,e,scope=encoders[0];assert ctx==app+64 and e[0]==0x400fbebc and e[3]==knob and e[4]==delta&0xffffffff and scope==1
for sr,active in [(0x2000,False),(0x2000,True),(0x2700,True)]:
 u.reg_write(C.UC_M68K_REG_SR,sr);r.w32(s['scope'],int(active))
 for key in [1,2,5,6,13,32]:assert r.call('rp_held',key)==int(active and sr==0x2000 and key in [2,5]),(hex(sr),key)
u.reg_write(C.UC_M68K_REG_SR,0x2000);r.w32(s['scope'],0)
run(b'SMRQ318!');request(b'SMR2318!');r.w32(msg+8,0x82000000);r.w32(msg+16,data+15);u.mem_write(data,bytes.fromhex('0000123482')+bytes(10));r.call('rp_send',msg);assert bytes(u.mem_read(data+5,10))==bytes([82,86,125,2,22,42,2,1,2,2])
if d.get('volume_readback'):
 request(b'SMVL318!');r.w32(msg+8,0x82000000);r.w32(msg+16,data+15);u.mem_write(data,bytes.fromhex('0000123482')+bytes(10));r.call('rp_send',msg);assert bytes(u.mem_read(data+5,10))==b'RL'+bytes(range(70,76))+bytes(2)
run(b'SMW1318!'+bytes([111,0,30,40]));assert writes[-1]==(app+0x7000+128,(24,111<<24,25,0,20,30<<24,21,40<<24))
# Aucun geste dans une fenetre d upgrade ou de confirmation.
for vt in [0x40111104,0x40111544,0x40111054]:
 r.w32(view,vt);n=len(keys);request(b'SMPL318!');queue.pop();r.call('rp_run',0);assert r.r32(s['status'])==3 and len(keys)==n
r.w32(view,0x400ff000);r.w32(al['rp_menu'],1);n=len(encoders);request(b'SMFC318!\x01');queue.pop();r.call('rp_run',0);assert r.r32(s['status'])==3 and len(encoders)==n;r.w32(al['rp_menu'],0)
if d.get('stock_machine_test'):
 machines=[]
 bind(0x4001477e,lambda args:machines.append(tuple(args[:4])) or 1)
 run(b'SMM3370!\x03');assert machines==[(app+0x7000+3*128,3,0,0)]
 for address in (0x40a7883c,0x40a78874,al['rp_menu']):
  r.w32(address,1);request(b'SMM3370!\x04');assert len(queue)==1;queue.pop();r.call('rp_run',0)
  assert r.r32(s['status'])==3 and len(machines)==1;r.w32(address,0)
 for body in (b'SMM6370!\x03',b'SMM3370!\x09',b'SMM3370!\xff',b'SMM3370!',b'SMM3370!\x03\0'):
  request(body);assert not queue
 commits=[];bind(al['rp_fx_commit'],lambda args:commits.append(1) or 0)
 encoders.clear();run(b'SMFX370!\x00\x04');assert len(encoders)==4 and all(e[1][3:5]==(14,1) and e[2]==3 for e in encoders)
 run(b'SMFK370!');assert commits==[1]
 for sr in (0x2000,0x2700):
  u.reg_write(C.UC_M68K_REG_SR,sr);r.w32(s['scope'],3)
  for key in (1,2,5,13):assert r.call('rp_held',key)==int(sr==0x2000 and key==2)
 u.reg_write(C.UC_M68K_REG_SR,0x2000);r.w32(s['scope'],0)
 for body in (b'SMFX370!\x02\x01',b'SMFX370!\0\x11',b'SMFX370!\0\xef'):
  request(body);assert not queue
 notes=[];bind(0x40019e7a,lambda args:notes.append(tuple(args[:5])) or 0);bind(0x40019c84,lambda args:notes.append(tuple(args[:3])) or 0)
 run(b'SMNT370!\x06\x64');assert notes==[(0,t,60,100,0xffffffff) for t in range(6)]
 notes.clear();run(b'SMNT370!\x06\x00');assert notes==[(0,t,60) for t in range(6)]
 # Les getters booleens natifs ne definissent que D0.b : ignorer D0[31:8].
 for at in (0x4006ba76,0x4006b978):
  bind(at,lambda args:0xa5a50001);notes.clear();request(b'SMNT370!\x06\x64');queue.pop();r.call('rp_run',0)
  assert not notes and r.r32(s['status'])==3
  bind(at,lambda args:0xa5a50000)

 notes.clear();r.w32(0x40a78874,1);request(b'SMNT370!\x06\x64');queue.pop();r.call('rp_run',0);assert not notes and r.r32(s['status'])==3;r.w32(0x40a78874,0)
 for body in (b'SMNT370!\x07\x64',b'SMNT370!\x06\x80'):
  request(body);assert not queue
 run(b'SMPW370!\x05\x12\x6e\0');assert writes[-1]==(app+0x7000+5*128,(18,110<<24))
 request(b'SMPR370!\x05\x12');r.w32(msg+8,0x82000000);r.w32(msg+16,data+15);u.mem_write(data,bytes.fromhex('0000123482')+bytes(10));r.call('rp_send',msg);assert bytes(u.mem_read(data+5,10))==b'RP\x05\x12\x6e\0'+bytes(4)
 for body in (b'SMPR370!\x06\x12',b'SMPW370!\x05\x09\x6e\0',b'SMPW370!\x05\x12\x80\0'):
  request(body);assert not queue
 keys.clear();run(b'SMKY370!\x09');assert [event[3:5] for ctx,event in keys]==[(9,1),(9,16)]
 request(b'SMUI370!');r.w32(msg+8,0x82000000);r.w32(msg+16,data+15);u.mem_write(data,bytes.fromhex('0000123482')+bytes(10));r.call('rp_send',msg);assert bytes(u.mem_read(data+5,10))==b'RU\0\x03'+bytes(6)

 # Telemetrie bornee : notes stockees, position native et horloge.
 raw=app+0x9000;r.w32(0x40a7887c,raw);u.mem_write(raw,bytes(30710));u.mem_write(raw+30709,b'\x04')
 for t,count in enumerate((4,2,16,5,6,3)):
  for i in range(count):u.mem_write(raw+722*t+2*i,b'\0\1')
 u.mem_write(0x40a7886c,bytes([0,4,8,12,3,11]));r.w32(0x8000184c,123456);r.w32(0x40149310,14400)
 def packet(body):
  request(body);r.w32(msg+8,0x82000000);r.w32(msg+16,data+15);u.mem_write(data,bytes.fromhex('0000123482')+bytes(10));r.call('rp_send',msg);return bytes(u.mem_read(data+5,10))
 assert packet(b'SMTS370!')==b'TS'+bytes([4,4,2,16,5,6,3,0])
 assert packet(b'SMTC370!')==b'TC'+bytes([0,4,8,12,3,11,0,0])
 assert packet(b'SMTT370!')==b'TT'+struct.pack('>IH',123456,14400)+bytes(2)
 if 'rp_pattern_snapshot' in al:
  assert packet(b'SMPL374!')==b'PL'+bytes(8)
 r.w32(0x40a7887c,1);assert packet(b'SMTS370!')[2]==255
 paired=[];bind(0x40077720,lambda a:paired.append((r.r32(s['scope']),struct.unpack('>6I',u.mem_read(a[1],24)))) or 1)
 for modifier,key in ((2,21),(3,16),(3,31)):
  paired.clear();run(b'SMCK370!'+bytes([modifier,key]));assert [(sc,e[3],e[4]) for sc,e in paired]==[(256+modifier,modifier,1),(256+modifier,key,1),(256+modifier,key,16),(0,modifier,16)]
 for body in (b'SMCK370!\x02\x16',b'SMCK370!\x01\x10',b'SMCK370!\x03\x20'):
  request(body);assert not queue
 for sr in (0x2000,0x2700):
  u.reg_write(C.UC_M68K_REG_SR,sr);r.w32(s['scope'],259)
  for key in (1,2,3,13):assert r.call('rp_held',key)==int(sr==0x2000 and key==3)
 u.reg_write(C.UC_M68K_REG_SR,0x2000);r.w32(s['scope'],0)
 print('PASS native sequence readback and paired TRACK/PATTERN chords; no modifier in IRQ')
 for engine in (6,7,8,10,12,14,24):
  run(b'SMM5370!'+bytes([engine]));assert machines[-1]==(app+0x7000+5*128,engine,0,0)
 print('PASS remote machine setter: stopped-only, bounded profiled-engine whitelist, strict packet bounds')
rng=random.Random(318)
for size in range(21):request(bytes(rng.randrange(256) for _ in range(size)));assert not queue
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(transport_delegates_panel_events=True,CTRL_ALL_modifiers_scoped_to_encoder=True,modifiers_hidden_from_IRQ=True,readback=True,restore_only_four_parameters=True,upgrade_dialogs_blocked=True,malformed_requests_ignored=True,native_UI_delegates_observed_not_executed=True,hardware_tested=False),indent=2)+'\n')
print('PASS panel RPC: transport events, native encoder delegation, scoped modifiers/IRQ guard, readback, four-parameter restoration, modal/malformed guards')
