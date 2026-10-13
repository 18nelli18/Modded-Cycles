#!/usr/bin/env python3
"""Codec CC annexe réel : identité, CRC, OFF, locks et refus sans mutation."""
import argparse,pathlib,tempfile,subprocess,struct,zlib
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in ('knob_cc_storage_codec','storage_codec'):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93050000','-e','mlkcs_encode','-o',str(p/'a.elf'),*objs],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'a.elf'),str(p/'a.bin')],check=True)
  code=(p/'a.bin').read_bytes();syms=symbols(cross,p/'a.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 src,dst,record=0x93060000,0x93064000,0x93068000
 owner=0x12345678
 for pattern,size in ((96,144),(0,9216),(95,9216)):
  payload=bytearray(bytes((255,64))*72 if size==144 else b'\xff'*9216)
  payload[:6]=bytes((0,0,74,127,127,1));r.u.mem_write(src,bytes(payload));r.u.mem_write(dst,b'\xa5'*size)
  assert r.call('mlkcs_encode',record,size+32,src,size,owner,9,pattern,0xffffffff)==1
  raw=bytes(r.u.mem_read(record,size+32));header=struct.unpack('>8I',raw[:32])
  assert header[:6]==(0x4d434331,size,owner,9,pattern,0xffffffff)
  assert header[6]==zlib.crc32(payload) and header[7]==zlib.crc32(raw[:28])
  assert r.call('mlkcs_decode',dst,record,size+32,owner,9,pattern)==1
  assert bytes(r.u.mem_read(dst,size))==payload
  before=b'\xa5'*size
  for off in (0,4,8,12,16,20,24,28,32,size+31):
   broken=bytearray(raw);broken[off]^=1;r.u.mem_write(record,bytes(broken));r.u.mem_write(dst,before)
   assert r.call('mlkcs_decode',dst,record,size+32,owner,9,pattern)==0,(pattern,off)
   assert bytes(r.u.mem_read(dst,size))==before
  r.u.mem_write(record,raw)
  for ident,slot,pat in ((owner+1,9,pattern),(owner,8,pattern),(owner,9,95 if pattern!=95 else 0)):
   assert r.call('mlkcs_decode',dst,record,size+32,ident,slot,pat)==0
  for pair in ((128,0),(254,0),(0,128),(255,128)):
   bad=bytearray(payload);bad[:2]=bytes(pair);r.u.mem_write(src,bytes(bad));r.u.mem_write(record,b'\xa5'*(size+32))
   assert r.call('mlkcs_encode',record,size+32,src,size,owner,9,pattern,1)==0,pair
   assert bytes(r.u.mem_read(record,size+32))==b'\xa5'*(size+32)
  r.u.mem_write(src,bytes(payload))
  assert r.call('mlkcs_encode',src,size+32,src,size,owner,9,pattern,1)==0
  assert r.call('mlkcs_encode',record,size+31,src,size,owner,9,pattern,1)==0
 print('ok : MCC1 maps144/locks9216, CC0/valeur0/OFF, CRC hôte identiques, propriétaires/bornes/corruption refusés sans mutation')
 print('Limite : codec seulement ; aucun raccordement Save Project ni E/S dans ce test')
if __name__=='__main__':main()
