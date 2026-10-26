"""Recepteur148 : envois repetes, fragmentation, mauvais paquet et reprise."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_wizard_playback
from test_fx_menu_control import fixture
stem='staging/all-features-polivoks-cpu-trim-test-v148';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());r,s,h,l,files,key,turn,data,bind=fixture(stem);s.update(m['legacy']['symbols']);r.s.update(s)
bind(0x400d0a10,lambda a:1);forwarded=[];bind(s['dx7_usb_original'],lambda a:forwarded.append(bytes(r.u.mem_read(a[0],a[1]))) or 88)
bank=Path('C:/Users/austi/OneDrive/Desktop/Muzak/Legowelt magic DX7 cart.syx').read_bytes()
def packet(slot):
 body=bytes([83,77,76,1,slot])+b'Repeated bank'.ljust(16,b' ')+bank[6:4102];return bytes([240,125])+body+bytes([(-sum(body))&127,247])
def send(raw,chunk):
 for i in range(0,len(raw),chunk):
  part=bytes(raw[i:i+chunk]);r.u.mem_write(0x93013000,part);r.call(0x4007f6a8,0x93013000,len(part))
r.call('dx7_service')
for n in range(32):
 slot=n%16;chunk=[1,3,64,128,256,512,4096,4121][n%8];send(packet(slot),chunk);r.call('dx7_service');assert r.r32(s['dx7_imported'])==n+1 and not r.r32(s['dx7_rejected']);assert len(files[f'/Legacy{slot+1:02}.cfg'])==5000;assert not forwarded
 print('PASS repeated native bank save',n+1,'slot',slot+1,'fragment',chunk,flush=True)
# Un paquet recu complet en lecture attend le STOP ; tout nouvel envoi est perdu jusque-la.
r.w32(0x40a7883c,1);send(packet(0),64);r.call('dx7_service');send(packet(1),64);r.w32(0x40a7883c,0);r.call('dx7_service');assert r.r32(s['dx7_imported'])==33
send(packet(1),64);r.call('dx7_service');assert r.r32(s['dx7_imported'])==34
bad=bytearray(packet(2));bad[-2]^=1;send(bad,64);r.call('dx7_service');assert r.r32(s['dx7_rejected'])==1
send(packet(2),64);r.call('dx7_service');assert r.r32(s['dx7_imported'])==35
print('PASS native parser repeated saves/overwrites/recovery; pending packet while playing drops later bank until stop; browser has no acknowledgement',flush=True)
