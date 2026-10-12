#!/usr/bin/env python3
"""Checkpoint automatique compilé : cadence, changements, refus IRQ/Load/E/S.

Backend simulé. Le test session vérifie séparément l'isolation WRK/SEQ.
"""
import argparse,pathlib,subprocess,tempfile,zlib
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 names=('ml_store_load_ready','ml_store_load_active','ml_store_io_busy','ml_store_io_poison','TG_blk_clk','ml_store_owner_id','ml_store_load_serial','ml_bank_table','ml_store_namespace','ml_store_project_ctx')
 funcs=('ml_audio_lfo_capture','ml_record_crc','ml_store_resolve_slot','ml_store_session_save')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);obj=p/'a.o';elf=p/'a.elf'
  subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_WORKING=1','-o',str(obj),str(root/'tools/machines/midi_lanes/storage_autosave.s')],check=True)
  script='SECTIONS { .text 0x93050000 : { *(.text*) *(.data*) } }\n'
  script+='\n'.join('%s = 0x%x;'%(n,0x93078000+i*4) for i,n in enumerate(names))
  script+='\n'+'\n'.join('%s = 0x%x;'%(n,0x93079000+i*16) for i,n in enumerate(funcs))
  (p/'link.ld').write_text(script)
  subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','ml_store_autosave','-o',str(elf),str(obj)],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(elf),str(p/'a.bin')],check=True)
  code=(p/'a.bin').read_bytes();syms=symbols(cross,elf)
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 state={'write_ok':1,'slot_ok':1};writes=[];alloc=[];captures=[]
 bank,table,heap=0x930a0000,0x930a2000,0x930a3000
 r.w32(table,bank);r.w32(syms['ml_bank_table'],table);r.w32(syms['ml_store_load_ready'],1)
 r.w32(syms['ml_store_owner_id'],0x12345678);r.w32(syms['ml_store_load_serial'],1);r.w32(syms['ml_store_project_ctx'],0x930a4000)
 def save(args):
  assert args[:4]==(0x930a4000,0x12345678,3,0),args
  assert r.r32(syms['ml_store_namespace'])==2
  writes.append(bytes(r.u.mem_read(args[4],4992)));return state['write_ok']
 def resolve(args):
  assert args[:2]==(0x12345678,96),args
  return 3 if state['slot_ok'] else 0xffffffff
 stubs={syms['ml_audio_lfo_capture']:lambda args:captures.append(1) or 0,
        syms['ml_record_crc']:lambda args:zlib.crc32(bytes(r.u.mem_read(args[0],args[1]))),
        syms['ml_store_resolve_slot']:resolve,syms['ml_store_session_save']:save,
        0x400802e0:lambda args:alloc.append(args[0]) or heap}
 for at,fn in stubs.items():
  existing=at in r.stubs;r.stubs[at]=fn
  if not existing:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 tick=0
 def cycle(count=1):
  nonlocal tick
  for _ in range(count):tick+=150;r.w32(syms['TG_blk_clk'],tick);r.call('ml_store_autosave')
 r.call('ml_store_autosave');assert not alloc
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2500);cycle();assert not alloc
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);cycle();assert alloc==[1536] and not writes
 cycle(96);assert len(writes)==1
 cycle(192);assert len(writes)==1
 r.u.mem_write(bank+20,b'\x66');cycle(96);assert len(writes)==1
 cycle(96);assert len(writes)==2 and writes[-1][20]==0x66
 cycle(96);assert len(writes)==2
 for flag in ('ml_store_load_ready','ml_store_load_active','ml_store_io_busy','ml_store_io_poison'):
  old=r.r32(syms[flag]);r.w32(syms[flag],0 if flag=='ml_store_load_ready' else 1)
  before=len(captures);cycle(96);assert len(captures)==before;r.w32(syms[flag],old)
 r.u.mem_write(bank+20,b'\x67');state['write_ok']=0;cycle(192);assert len(writes)==3
 state['write_ok']=1;cycle(96);assert len(writes)==4
 cycle(96);assert len(writes)==4
 r.u.mem_write(bank+20,b'\x68');state['slot_ok']=0;cycle(192);assert len(writes)==4
 state['slot_ok']=1;cycle(96);assert len(writes)==5
 print('ok : allocation unique1536, scan cadencé, checkpoint après stabilité, état identique non réécrit')
 print('ok : IRQ/Load/busy/poison exclus ; échec écriture réessayé, association invalide sans I/O')
 print('Limite : cadence et charge UI réelles, coupure alimentation et disque matériel à tester')
if __name__=='__main__':main()
