#!/usr/bin/env python3
"""RNG SCRAMBLE B sans import Sequence Genie : mêmes états ColdFire.

L'appelant fournit un seed non nul. Vérifie 4096 sorties et la diversité CC,
sans périphérique ni double du code assembleur.
"""
import argparse,pathlib,subprocess,tempfile,struct
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);a=p.parse_args();at=0x401f0000
 with tempfile.TemporaryDirectory() as d:
  root=pathlib.Path(d);source=pathlib.Path(__file__).resolve().parents[1]/'machines/midi_lanes/random.s'
  subprocess.run(['m68k-elf-as','-march=cfv4e','-o',str(root/'r.o'),str(source)],check=True)
  subprocess.run(['m68k-elf-ld','-Ttext='+hex(at),'-e','ml_random','-o',str(root/'r.elf'),str(root/'r.o')],check=True)
  subprocess.run(['m68k-elf-objcopy','-O','binary',str(root/'r.elf'),str(root/'r.bin')],check=True);code=(root/'r.bin').read_bytes()
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_write(at,code)
 for seed in [1,0x6d2b79f5,0xffffffff,0x80000000]:
  x=seed;values=set();r.u.reg_write(mk.UC_M68K_REG_D7,x)
  for _ in range(1024):
   x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;x&=0xffffffff
   result=r.call(at);assert result==(x&32767) and r.u.reg_read(mk.UC_M68K_REG_D7)==x
   values.add(result&127)
  assert len(values)>=120
 print('ok : 4096 sorties et états ColdFire exacts, diversité CC ; SCRAMBLE ne requiert plus le RNG du générateur')
if __name__=='__main__':main()
