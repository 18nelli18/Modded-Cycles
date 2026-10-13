#!/usr/bin/env python3
"""Genie B : chance effacée, Undo et annulation d'une édition concurrente."""
import argparse,pathlib,tempfile,subprocess,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as temp:
  p=pathlib.Path(temp);subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_GENIE_CHANCE=1','-o',str(p/'c.o'),str(root/'tools/machines/midi_lanes/genie_chance.s')],check=True)
  (p/'l.ld').write_text('SECTIONS { .text 0x93050000 : { *(.text) *(.data) } } ml_repeat_edit_settings = 0x93060000; mlp_track = 0x93060004; ml_gq_track = 0x93060008; ml_gq_pattern = 0x9306000c; ml_repeat_pattern_lookup = 0x93060020;')
  subprocess.run([cross+'ld','-T',str(p/'l.ld'),'-e','ml_gc_capture','-o',str(p/'c.elf'),str(p/'c.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'c.elf'),str(p/'c.bin')],check=True)
  code=(p/'c.bin').read_bytes();syms=symbols(cross,p/'c.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_write(0x93050000,code);r.s=syms
 settings,pattern=0x93070000,0x93072000
 r.w32(syms['ml_repeat_edit_settings'],settings);r.w32(syms['ml_gq_pattern'],pattern)
 r.stubs[syms['ml_repeat_pattern_lookup']]=lambda args:settings if args[0]==pattern else 0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=syms['ml_repeat_pattern_lookup'],end=syms['ml_repeat_pattern_lookup'])
 for track in range(6):
  initial=bytes((i*17+track)%256 for i in range(3120));r.u.mem_write(settings,initial)
  r.w32(syms['mlp_track'],track);r.w32(syms['ml_gq_track'],track)
  assert r.call('ml_gc_capture')==1 and r.call('ml_gc_validate')==1
  r.call('ml_gc_save_undo');r.u.reg_write(mk.UC_M68K_REG_SR,0x2700);r.call('ml_gc_apply');r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  expected=bytearray(initial)
  for step in range(64):expected[track*520+15+step*8]=0
  assert bytes(r.u.mem_read(settings,3120))==expected
  assert r.call('ml_gc_capture')==1;r.call('ml_gc_restore_candidate')
  assert r.call('ml_gc_validate')==1;r.call('ml_gc_apply')
  assert bytes(r.u.mem_read(settings,3120))==initial
  assert r.call('ml_gc_capture')==1
  at=settings+track*520+15;r.u.mem_write(at,bytes(((initial[track*520+15]+1)%256,)))
  assert r.call('ml_gc_validate')==0
  r.w32(syms['ml_gq_pattern'],pattern+4);assert r.call('ml_gc_validate')==0;r.w32(syms['ml_gq_pattern'],pattern)
 r.w32(syms['mlp_track'],6);assert r.call('ml_gc_capture')==0
 r.w32(syms['ml_repeat_edit_settings'],0);assert r.call('ml_gc_capture')==0
 print('ok : six voies ×64 conditions effacées ; défauts de voie, autres locks et voies inchangés')
 print('ok : Undo restaure les conditions ; changement de chance/pattern refuse la publication ; bornes/null refusés')


if __name__=='__main__':main()
