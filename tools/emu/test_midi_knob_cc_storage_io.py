#!/usr/bin/env python3
"""CC vers adaptateurs disque existants : vraie ABI, chunks et relecture entière."""
import argparse,pathlib,tempfile,subprocess
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in ('knob_cc_storage_verify','storage_io'):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_CC_STORAGE=1','-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93050000','-e','mlkcs_verified','-o',str(p/'a.elf'),*objs],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'a.elf'),str(p/'a.bin')],check=True)
  code=(p/'a.bin').read_bytes();syms=symbols(cross,p/'a.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 path,record,scratch=0x93060000,0x93064000,0x93068000;r.u.mem_write(path,b'/ModdedCycles/09-12345678/CCL-00-B\0')
 state={};calls=[]
 def opened(args):
  assert args[0]==path;state['mode']=r.string(args[1]);state['cursor']=0;calls.append('open-'+state['mode']);return 0
 def prealloc(args):
  assert args[1]==0 and args[2]==state['size'];state['file']=bytearray(args[2]);calls.append('prealloc');return 0
 def write(args):
  buf,count,handle=args[:3];assert 0<count<=512 and handle and buf==record+state['cursor'];calls.append('write')
  if state.get('fail_write'):return 0
  n=min(count,state.get('partial',count));i=state['cursor'];state['file'][i:i+n]=r.u.mem_read(buf,n);state['cursor']+=n;return n
 def read(args):
  buf,count,handle=args[:3];assert buf==scratch and count==state['size'] and handle;calls.append('read')
  data=bytearray(state['file'])
  if state.get('corrupt') is not None:data[state['corrupt']]^=1
  r.u.mem_write(buf,bytes(data));return count-1 if state.get('short') else count
 def flush(args):calls.append('flush');return -1 if state.get('fail_flush') else 0
 def close(args):calls.append('close');return -1 if state.get('fail_close') else 0
 for addr,fn in ((0x4007bc5e,opened),(0x4007bb76,prealloc),(0x4007bb0a,write),(0x4007baaa,read),(0x4007e2f6,flush),(0x4007bc1c,close)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 for size in (176,9248):
  data=bytes(i%251 for i in range(size));r.u.mem_write(record,data)
  for failure in ({},{'partial':127},{'fail_write':1},{'fail_flush':1},{'fail_close':1},{'short':1},{'corrupt':size-1}):
   state.clear();state.update(size=size,**failure);calls.clear()
   expected=int(not any(k in failure for k in ('fail_write','fail_flush','fail_close','short','corrupt')))
   assert r.call('mlkcs_verified',path,record,scratch,size)==expected,(size,failure,calls)
   assert bytes(r.u.mem_read(record,size))==data
   if expected:assert bytes(r.u.mem_read(scratch,size))==data and calls[-3:]==['open-r','read','close']
  for ipl in range(1,8):
   calls.clear();r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8));assert r.call('mlkcs_verified',path,record,scratch,size)==0 and not calls
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  for dest,n in ((record,size),(record+4,size),(scratch,size-1)):
   calls.clear();assert r.call('mlkcs_verified',path,record,dest,n)==0 and not calls
 print('ok : CC176/9248 via writer natif existant, ABI tampon/taille/handle, chunks<=512 et écritures partielles')
 print('ok : flush/close/relecture intégrale, corruption/short/erreur refusés ; IRQ et alias sans accès disque')
 print('Limite : API fichier simulée, pas de hook Save ni test de persistance matérielle')
if __name__=='__main__':main()
