#!/usr/bin/env python3
"""Locks CC ColdFire : valeurs0..127, douze potards, copie/clear isolés."""
import argparse,pathlib,subprocess,tempfile
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'k.o'),str(root/'tools/machines/midi_lanes/knob_cc_locks.s')],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93050000','-e','mlkc_lock_set','-o',str(p/'k.elf'),str(p/'k.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'k.elf'),str(p/'k.bin')],check=True)
  code=(p/'k.bin').read_bytes();syms=symbols(cross,p/'k.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 src,dst=0x93060000,0x93064000
 assert r.call('mlkc_lock_init',src)==1 and r.call('mlkc_lock_init',dst)==1
 for lane in range(6):
  for step in (0,15,16,63):
   for knob in range(12):
    value=(lane+step+knob)%128
    assert r.call('mlkc_lock_set',src,lane,step,knob,74,value)==1
    assert r.call('mlkc_lock_get',src,lane,step,knob)==(74<<8)|value
 assert r.call('mlkc_lock_set',src,0,1,0,0,0)==1
 assert r.call('mlkc_lock_get',src,0,1,0)==0
 assert r.call('mlkc_lock_copy',dst,5,63,src,0,16)==1
 for knob in range(12):assert r.call('mlkc_lock_get',dst,5,63,knob)==(74<<8)|((16+knob)%128)
 assert r.call('mlkc_lock_clear',dst,5,63)==1
 assert bytes(r.u.mem_read(dst,9216))==b'\xff'*9216
 before=bytes(r.u.mem_read(src,9216))
 for lane,step,knob,cc,val in ((6,0,0,1,1),(0,64,0,1,1),(0,0,12,1,1),(0,0,0,128,1),(0,0,0,1,128)):
  assert r.call('mlkc_lock_set',src,lane,step,knob,cc,val)==0
 assert bytes(r.u.mem_read(src,9216))==before
 print('ok : six voies/64pas/12CC indépendants, CC0/valeur0 valides, copie24octets et clear complet, bornes sans mutation')
 print('Limite : stockage de locks seul ; édition, lecture MIDI et sauvegarde pas encore raccordées')
if __name__=='__main__':main()
