"""Recepteur148 : envois repetes, fragmentation, mauvais paquet et reprise."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_wizard_playback
from test_fx_menu_control import fixture
stem='staging/all-features-polivoks-cpu-trim-test-v150';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());r,s,h,l,files,key,turn,data,bind=fixture(stem);s.update(m['legacy']['symbols']);r.s.update(s)
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
r.call('dx7_service')
for n in range(32):
 slot=n%16;before=dict(files)
 for i,f in enumerate(frames(slot,n)):
  service(f)
  if i<33:assert files==before,'write before COMMIT'
 assert imported()==n+1 and rejected()==0
 assert len(files[f'/Legacy{slot+1:02}.cfg'])==5000 and files[f'/Legacy{slot+1:02}.nam']==b'Repeated bank'.ljust(16,b' ')
 assert not forwarded
 print('PASS native SML2 save',n+1,'slot',slot+1,flush=True)
# Ancien protocole intact, memes fichiers ; puis erreurs et reprise.
expected=dict(files);service(packet(0));assert imported()==33 and files==expected
fs=frames(0,80)
for case,seq in [('missing',[fs[0],*fs[2:]]),('order',[fs[0],fs[2]]),('crc',[fs[0],fs[1][:-2]+bytes([fs[1][-2]^1,247])]),('transaction',[fs[0],frames(0,81)[1]])]:
 old=rejected();snap=dict(files)
 for f in seq:service(f)
 assert rejected()>old and imported()==33 and files==snap,case
 print('PASS rejected without save',case,flush=True)
# Un duplicata identique n'ajoute pas deux fois le payload.
for f in [fs[0],fs[1],fs[1],*fs[2:]]:service(f)
assert imported()==34 and files==expected
# BEGIN neuf abandonne une ancienne transmission partielle.
for f in [fs[0],fs[1],*frames(1,82)]:service(f)
assert imported()==35 and files==expected
service(packet(2));assert imported()==36 and files==expected
print('PASS native old importer, checked chunks, duplicate, cancel/retry and persistent file identity',flush=True)

# Duree5s, y compris bouclage du compteur materiel.
draw=[]
for at in (0x40070efc,0x40070c4e):bind(at,lambda a:0)
bind(0x40071a04,lambda a:draw.append(r.string(a[6])) or 0)
for stamp in (1000000,0xffff0000):
 r.w32(0xfc07000c,stamp);r.call('dx7_message',s['dx7_code_end']-4)
 for ticks,want in [(0,1),(270336001,1),(675840000,1),(675840001,0)]:
  r.w32(0xfc07000c,(stamp+ticks)&0xffffffff);draw.clear();r.call('dx7_status_draw',0);assert len(draw)==want,(stamp,ticks,draw)
print('PASS five-second status, timer wrap and expiry',flush=True)
# Echec fichier explicite ; le nouvel envoi reussit apres restauration.
prev=rejected();bind(0x4007bb0a,lambda a:0)
for f in frames(3,90):service(f)
assert imported()==36 and rejected()==prev+1
print('PASS file-write failure detected without false success',flush=True)
# MIDI ordinaire : aucun changement du flux transmis.
forwarded.clear();raw=bytes([0x90,60,100,0xf8,0x80,60,0]);send(raw,3);assert b''.join(forwarded)==raw
print('PASS ordinary MIDI and real-time bytes forwarded exactly',flush=True)
