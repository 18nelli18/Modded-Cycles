"""Regression105 : routage MIDI, sauvegarde sans popup et niveaux LEGACY."""
from pathlib import Path
import sys,json,struct,os
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_wizard_playback,emac
from test_fx_menu_control import fixture
from test_vinyl_dust import IN,OUT,rig
stem='staging/all-features-polivoks-cpu-trim-test-v105retro';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());r,s,h,log,files,key,turn,data,bind=fixture(stem);d=m['legacy'];s.update(d['symbols']);r.s.update(s)
bind(0x400d0a10,lambda a:1);bind(0x40012412,lambda a:0);bind(0x4001e318,lambda a:0x12340015)
def forbidden(a):raise AssertionError('native popup from bank path')
bind(s['dx7_notice'],forbidden);usb=[];din=[]
bind(s['dx7_usb_original'],lambda a:usb.append(bytes(r.u.mem_read(a[0],a[1]))) or 88)
bind(s['dx7_din_original'],lambda a:din.append(a[0]&255) or 77)
cart=Path(os.environ.get('MC_TEST_DX7_BANK',str(R/'firmware/dx7-user-cart.syx'))).read_bytes();body=bytes([83,77,76,1,3])+b'Test bank'.ljust(16,b' ')+cart[6:4102];packet=bytes([240,125])+body+bytes([(-sum(body))&127,247])
r.call('dx7_service')
for chunk in [1,5,6,64,4096,4121]:
 usb.clear()
 for i in range(0,len(packet),chunk):
  part=packet[i:i+chunk];r.u.mem_write(IN,part);r.call(0x4007f6a8,IN,len(part))
 assert not usb,chunk
 r.call('dx7_service');assert len(files['/Legacy04.cfg'])==5000
for message in [bytes([0x90,60,100,0x80,60,0]),cart,bytes([240,125,83,77,75,1,2,247]),bytes([248,250,252])]:
 usb.clear()
 for b in message:r.u.mem_write(IN,bytes([b]));r.call(0x4007f6a8,IN,1)
 assert b''.join(usb)==message
 din.clear()
 for b in message:r.call(0x4007f694,b)
 assert bytes(din)==message
din.clear()
for b in packet:r.call(0x4007f694,b)
assert not din;r.call('dx7_service')
key(1);assert key(5)==(0,0);key(5,0);key(1,0);assert r.r32(s['browser']);key(12);key(12,0)
print('PASS105 USB/DIN: owned bank frames suppressed; other MIDI unchanged; fragmented/whole bank saved without native popup; real MACHINES key',flush=True)
