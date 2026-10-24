"""Le paquet du navigateur doit passer le vrai importeur LEGACY121.

MC_TEST_PRIVATE_ROOT : dossier des builds prives. Seules les API fichiers et
la destination MIDI native sont simulees ; parser/validation/publication reels.
"""
from pathlib import Path
import sys,os,json
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_fx_menu_control as fx
fx.ROOT=Path(os.environ.get('MC_TEST_PRIVATE_ROOT',R))
stem='staging/all-features-polivoks-cpu-trim-test-v121'
m=json.loads((fx.ROOT/'output/firmware'/(stem+'.json')).read_text())
r,s,held,log,files,key,turn,data,bind=fx.fixture(stem)
s.update(m['legacy']['symbols']);r.s.update(s)
forwarded=[];bind(s['dx7_usb_original'],lambda a:forwarded.append(a[1]) or 0)
def forbidden(args):raise AssertionError('native blocking popup called')
bind(s['dx7_notice'],forbidden)
packet=(R/'output/import-check/rom3a-packet.bin').read_bytes();assert len(packet)==4121
IN=0x93013000;OUT=0x93016000
r.call('dx7_service')
for i in range(0,len(packet),64):
 chunk=packet[i:i+64];r.u.mem_write(IN,chunk);r.call(0x4007f6a8,IN,len(chunk))
assert not forwarded
r.call('dx7_service')
assert r.r32(s['dx7_imported'])==1 and r.r32(s['dx7_rejected'])==0
assert len(files['/Legacy01.cfg'])==5000 and files['/Legacy01.nam']==b'ROM3A'.ljust(16,b' ')
saved=files['/Legacy01.cfg']
for i in range(32):
 voice=saved[4+156*i:4+156*(i+1)];r.u.mem_write(OUT,voice);assert r.call('dx7_valid',OUT)==1
assert saved[4+156*19+4*21+6]==99
assert r.call('dx7_library_load',1)==1 and files['/Dx7Bank.cfg']==saved
print('PASS exact121 USB -> native bank validation -> saved32voices -> native reload, corrected TIMPANI value99, no native popup',flush=True)
