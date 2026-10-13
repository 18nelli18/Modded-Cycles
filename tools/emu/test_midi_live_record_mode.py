#!/usr/bin/env python3
"""B : getters live/quant et branche PLAY native avec RECORD maintenu."""
import argparse,pathlib,subprocess,tempfile
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,OBJ,RAW,SIGNAL
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);obj=p/'live.o';elf=p/'live.elf'
  subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes/live_record_mode.s')],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93050000','--defsym=mlp_obj=0x93060000','-e','mllr_mode','-o',str(elf),str(obj)],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(elf),str(p/'live.bin')],check=True)
  r.u.mem_write(0x93050000,(p/'live.bin').read_bytes());r.s=symbols(cross,elf)
 r.stubs[SIGNAL]=lambda args:0
 ui=0x930a0000
 for addr,fn in ((0x400cf9a8,lambda args:ui),(0x4000eb90,lambda args:OBJ)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(r.s['mlp_obj'],OBJ)
 for playing in (0,1,2):
  r.w32(0x40a7883c,playing);r.w32(0x40a78874,0)
  for live in (0,1):
   r.u.mem_write(ui+359,bytes([live]))
   for quant in (0,1):
    r.w32(RAW+180,quant)
    assert r.call('mllr_mode')==(1 if quant else 2) * int(playing==1 and live==1)
 # Même routine de bascule que PLAY dans le handler natif, contexte factice.
 r.w32(0x40a7883c,1);r.u.mem_write(ui+359,b'\x01');r.w32(RAW+180,0)
 before=bytes(r.u.mem_read(RAW,722))
 for expected in (1,2,1,2):
  r.call(0x400133ca,OBJ)
  assert r.call('mllr_mode')==expected
  after=bytes(r.u.mem_read(RAW,722));assert after[:180]==before[:180] and after[184:]==before[184:]
 # Branche PLAY du handler OS : D5 représente RECORD maintenu.
 for addr,fn in ((0x400cfd0e,lambda args:OBJ),(0x40069b84,lambda args:0),(0x4006b988,lambda args:0),(0x4006a938,lambda args:1)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.u.mem_write(ui+357,b'\x01\x01\x00');r.w32(RAW+180,1)
 def play_fragment(stop):
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  r.u.reg_write(mk.UC_M68K_REG_A7,0x93008000)
  r.u.reg_write(mk.UC_M68K_REG_D3,ui)
  r.u.reg_write(mk.UC_M68K_REG_D5,1)
  r.u.reg_write(mk.UC_M68K_REG_D6,0)
  try:r.u.emu_start(0x4002449c,stop,count=20000)
  except Exception:
   print("PC",hex(r.u.reg_read(mk.UC_M68K_REG_PC)));raise
  assert r.u.reg_read(mk.UC_M68K_REG_PC)==stop
  assert r.u.reg_read(mk.UC_M68K_REG_A7)==0x93008000
 play_fragment(0x4002457c)
 assert r.u.mem_read(ui+359,1)==b'\x01' and r.call('mllr_mode')==1
 for expected in (2,1,2,1):
  play_fragment(0x4002464a);assert r.call('mllr_mode')==expected
 r.w32(r.s['mlp_obj'],0);assert r.call('mllr_mode')==0
 r.w32(r.s['mlp_obj'],OBJ);r.u.reg_write(mk.UC_M68K_REG_SR,0x2500);assert r.call('mllr_mode')==0
 print('ok : getters natifs live-rec et quantification, Stop/Pause/B absent/IRQ refusés, bascule stock répétée')
 print('ok : branche PLAY native active live-rec puis bascule quantification à chaque nouvelle pression avec RECORD maintenu')
if __name__=='__main__':main()
