#!/usr/bin/env python3
"""Décompression ColdFire réelle du nouveau flux, banque entière et moteur partagé."""
import argparse,json,pathlib,struct,subprocess,tempfile
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import aplib_cost,build,syntakt

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt',required=True);ap.add_argument('--tweak',required=True);ap.add_argument('--depth',type=int,default=128);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];stock=main_os_from_syx(a.cycles);r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}})
 cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'d.o'),str(root/'tools/machines/midi_lanes/lfo_cc_depack.s')],check=True);subprocess.run([cross+'objcopy','-O','binary',str(p/'d.o'),str(p/'d.bin')],check=True);r.u.mem_write(0x93050000,(p/'d.bin').read_bytes())
 t=json.loads(pathlib.Path(a.tweak).read_text());bank=bytes.fromhex(t['append']['parts'][0]['hex'])
 cat=json.loads((root/'work/midi-clear-catalog.json').read_text());engine=next(t for t in cat['tweaks'] if t['id']=='syntakt-tg-sd-cp-toy-bits-swarm-macro-acid');raw=build.payload_runtime(engine,stock,syntakt.dsp_image(a.syntakt))
 for name,data in (('bank',bank),('engines',raw)):
  packed=aplib_cost.pack(data,a.depth,True);src,dest=0x93080000,0x93100000;r.u.mem_write(src,packed);r.u.mem_write(dest,b'\xa5'*(len(data)+16));r.u.mem_write(STACK,struct.pack('>I',STOP));r.u.reg_write(mk.UC_M68K_REG_A7,STACK);r.u.reg_write(mk.UC_M68K_REG_A0,src);r.u.reg_write(mk.UC_M68K_REG_A1,dest)
  r.u.emu_start(0x93050000,STOP,count=30000000);assert r.u.reg_read(mk.UC_M68K_REG_PC)==STOP
  assert bytes(r.u.mem_read(dest,len(data)))==data
  assert bytes(r.u.mem_read(dest+len(data),16))==b'\xa5'*16
  print('ok : décodeur ColdFire existant',name,len(packed),'->',len(data),'octets exacts et garde intacte',flush=True)
if __name__=='__main__':main()
