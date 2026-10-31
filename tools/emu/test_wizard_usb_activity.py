"""Preuve native des reglages ACID, navigation et sauvegarde globale."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));s=m['activity_masks']['symbols'];al=m['direct_jump']['aliases']
bc.ROOT=a.output.parent/'ui-cache';fx.metadata=m;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text(encoding='utf-8'))",'m=metadata');exec(src,fx.__dict__)
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');bind(al['gc_input_quiet'],lambda a:1);bind(0x400423e4,lambda a:0);return r,files,bind

r,files,bind=fixture();feature=m['activity_masks']
assert bytes(r.u.mem_read(feature['code'],feature['code_bytes']))==(a.build/'module.bin').read_bytes().ljust(feature['code_bytes'],b'\0')
for hook in feature['hooks']:assert bytes(r.u.mem_read(hook['at'],6))==b'\x4e\xf9'+struct.pack('>I',hook['target']),hex(hook['at'])
r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);bind(0x40000542,lambda a:0);r.call(s['am_boot_finish']);assert bytes(r.u.mem_read(0x401adbf6,6))==b'\x4e\xf9'+struct.pack('>I',s['am_wizard_usb'])
voice=0x931a0000
# Voix active, aucun signal route vers le mix principal ni les sends.
for at in (0x401bcc80,0x401b9b14,0x401ba5e0,0x401ba59c,0x40a78e18):r.w32(at,0)
r.u.mem_write(0x401adcc0,b'\1'*6);r.u.mem_write(0x401adb10,bytes(24));r.u.mem_write(voice,bytes(0x300));r.w32(voice+0x298,1)
for at in (0x40a78c08,0x40a78be8,0x40a78bd0,0x40a78bb8,0x40a78b9c,0x40a78b80):r.u.mem_write(at,bytes(24))
results=[]
for packet,expected in ((0x38,1),(0xc0,0)):
 r.u.mem_write(0x40002ceb,bytes([packet]));r.u.reg_write(C.UC_M68K_REG_A0,voice);r.u.reg_write(C.UC_M68K_REG_D1,0);r.u.reg_write(C.UC_M68K_REG_D2,0x12345678)
 got=r.call(0x401adb4c);assert got==expected,(packet,got);assert r.u.reg_read(C.UC_M68K_REG_D2)==0x12345678;results.append([packet,got])
print('PASS native boot, installed masks/PUNCH hooks and Wizard USB output independent of main-send gains',flush=True)
a.output.write_text(json.dumps(dict(native_boot=True,wizard_main_send_independence=results,hardware_tested=False),indent=2)+'\n')
