"""Recepteur148 : envois repetes, fragmentation, mauvais paquet et reprise."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_wizard_playback
from test_fx_menu_control import fixture
v=sys.argv[1] if len(sys.argv)>1 else 'v151';stem='staging/all-features-polivoks-cpu-trim-test-'+v;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());r,s,h,l,files,key,turn,data,bind=fixture(stem);s.update(m['legacy']['symbols']);r.s.update(s)
bind(0x400d0a10,lambda a:1);forwarded=[];bind(s['dx7_usb_original'],lambda a:forwarded.append(bytes(r.u.mem_read(a[0],a[1]))) or 88)
bank=Path('C:/Users/austi/OneDrive/Desktop/Muzak/Legowelt magic DX7 cart.syx').read_bytes()
def packet(slot):
 body=bytes([83,77,76,1,slot])+b'Repeated bank'.ljust(16,b' ')+bank[6:4102];return bytes([240,125])+body+bytes([(-sum(body))&127,247])
def send(raw,chunk):
 for i in range(0,len(raw),chunk):
  part=bytes(raw[i:i+chunk]);r.u.mem_write(0x93013000,part);r.call(0x4007f6a8,0x93013000,len(part))

def frames(slot,tx=0):
 full=packet(slot)
 def frame(cmd,data):
  b=bytes([83,77,76,2,tx,cmd])+bytes(data);return bytes([240,125])+b+bytes([(-sum(b))&127,247])
 payload=full[23:4119]
 return [frame(0,bytes([slot])+full[7:23])]+[frame(1,bytes([i])+payload[i*128:(i+1)*128]) for i in range(32)]+[frame(2,[(-sum(payload))&127])]
def service(raw):send(raw,3);r.call('dx7_service')
def imported():return r.r32(s['dx7_imported'])
def rejected():return r.r32(s['dx7_rejected'])

r.call('dx7_service');f=frames(0,1)
wave=m['wave_starter'];factory=bytes(r.u.mem_read(wave['data'],wave['bytes']))
if v=='v151':
 import hashlib
 assert hashlib.sha256(factory).hexdigest()==wave['pcm_sha256']
 assert not any(r.u.mem_read(m['bank_queue']['code'],m['bank_queue']['end']-m['bank_queue']['code']))
# Les34messages sont recues sans aucun passage UI entre eux.
send(b''.join(f),4486);assert imported()==0 and '/Legacy01.cfg' not in files
r.call('dx7_service')
if v=='v150':
 assert imported()==0
 service(f[-1]);assert rejected()==1
 print('PASS reproduced v150 packet loss and INCOMPLETE BANK with delayed UI',flush=True)
else:
 assert imported()==1 and rejected()==0
 print('PASS v151 full bank burst retained until UI, then saved once',flush=True)
 for n in range(32):
  before=imported();send(b''.join(frames(n%16,(n+2)&127)),[1,3,64,128,512,4486][n%6]);assert imported()==before;r.call('dx7_service');assert imported()==before+1 and rejected()==0
  assert len(files[f'/Legacy{n%16+1:02}.cfg'])==5000
 print('PASS 32 burst bank saves, 16slots, queue wrap, fragmented/coalesced USB',flush=True)
 before=imported();snap=dict(files);r.w32(0x40a7883c,1);send(b''.join(frames(0,55)),4486);r.call('dx7_service');assert files==snap and imported()==before;r.w32(0x40a7883c,0);r.call('dx7_service');assert imported()==before+1
 print('PASS queued while playing: no filesystem until STOP, complete bank retained',flush=True)
 before=imported();rej=rejected();snap=dict(files)
 send(b''.join(frames(1,60)+frames(2,61)),4486);r.call('dx7_service');assert imported()==before and rejected()==rej+1 and files==snap
 send(b''.join(frames(2,62)),4486);r.call('dx7_service');assert imported()==before+1
 print('PASS queue overflow cancels without saving, explicit error and clean retry',flush=True)
 # Etat DIN/USB separe : deux banques simultanees, tous messages avant UI.
 before=imported()
 for raw in frames(4,70):
  for byte in raw:r.call(0x4007f694,byte)
 send(b''.join(frames(5,71)),4486);r.call('dx7_service');assert imported()==before+2
 assert bytes(r.u.mem_read(wave['data'],wave['bytes']))==factory
 print('PASS independent DIN/USB full-bank queues and factory WAVE preserved byte-for-byte',flush=True)
