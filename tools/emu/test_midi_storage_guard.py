#!/usr/bin/env python3
"""Garde I/O compilée, chemin cache natif, backend disque simulé."""
import argparse,pathlib,subprocess,tempfile
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--extended',action='store_true');a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp)
  subprocess.run([cross+'as','-march=cfv4e']+(['--defsym','ML_STORAGE2=1'] if a.extended else [])+['-o',str(p/'g.o'),str(root/'tools/machines/midi_lanes/storage_guard.s')],check=True)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'c.o'),str(root/'tools/machines/midi_lanes/storage_checked.s')],check=True)
  (p/'link.ld').write_text('SECTIONS { .text 0x93050000 : { *(.text*) *(.data*) } } ml_store_read = 0x93060000; ml_store_write = 0x93060004;')
  subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','ml_store_disk_read','-o',str(p/'g.elf'),str(p/'g.o'),str(p/'c.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'g.elf'),str(p/'g.bin')],check=True)
  code=(p/'g.bin').read_bytes();syms=symbols(cross,p/'g.elf')
 if a.extended:
  import struct
  for read_status,write_status in ((0,0),(-1,0),(0,-1)):
   r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
   seen=[]
   for entry,name in ((0x4008b24a,'ml_store_disk_read'),(0x4008b3f6,'ml_store_disk_write')):
    r.u.mem_write(entry,b'\x4e\xf9'+struct.pack('>I',syms[name])+b'\x4e\x71')
   def backend(u,addr,size,data):
    sp=u.reg_read(mk.UC_M68K_REG_A7)
    seen.append((addr,tuple(r.r32(sp+x) for x in (24,28,32))))
    for i,reg in enumerate((mk.UC_M68K_REG_D2,mk.UC_M68K_REG_D3,mk.UC_M68K_REG_D4,mk.UC_M68K_REG_D5,mk.UC_M68K_REG_A2)):
     u.reg_write(reg,r.r32(sp+i*4))
    u.reg_write(mk.UC_M68K_REG_D0,(read_status if addr==0x4008b252 else write_status)&0xffffffff)
    u.reg_write(mk.UC_M68K_REG_PC,r.r32(sp+20));u.reg_write(mk.UC_M68K_REG_A7,sp+24)
   for addr in (0x4008b252,0x4008b3fe):r.u.hook_add(UC_HOOK_CODE,backend,begin=addr,end=addr)
   assert r.call('ml_store_io_begin')==1
   assert r.call(0x4008b24a,123,512,0x93070000)&0xffffffff==read_status&0xffffffff
   assert r.call(0x4008b3f6,456,512,0x93071000)&0xffffffff==(-1 if read_status else write_status)&0xffffffff
   assert seen[0]==(0x4008b252,(123,512,0x93070000))
   assert len(seen)==(1 if read_status else 2)
   assert r.call('ml_store_io_end')==int(not(read_status or write_status))
   count=len(seen)
   if read_status or write_status:
    assert r.call(0x4008b3f6,789,512,0x93071000)&0xffffffff==0xffffffff
    assert len(seen)==count
   # La finalisation native retourne 0 même après erreur physique : notre garde
   # doit la détecter et interdire le write suivant malgré ce faux succès.
   r.w32(r.s['ml_store_io_poison'],0);seen.clear()
   obj=0x930d0000;r.u.mem_write(obj,bytes(32))
   for addr in (0x4007e764,0x4007ba6a,0x4007d9c0,0x4007e042,0x4007d89a,0x4007e6ae,0x4007e68c):
    r.stubs[addr]=(lambda args: obj) if addr==0x4007e764 else (lambda args: 0)
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
   assert r.call('ml_store_io_begin')==1
   assert r.call(0x4007e13a,0x1234)==0
   assert len(seen)==(1 if read_status else 2)
   assert r.call('ml_store_io_end')==int(not(read_status or write_status))
  print('ok : entrées disque natives, prologues/arguments, poison persistant et écritures interdites après erreur')
  return
 for status,inside in ((0,True),(-1,True),(-1,False)):
  r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
  base=0x401eb750;r.u.mem_write(base,bytes(0x160));r.w32(0x400792f2,base+140);r.w32(0x400792bc,base+176)
  r.call(0x4007929c);r.w32(0x400798ca,r.s['ml_store_disk_read'])
  calls=[]
  def disk(args):calls.append(args[:3]);return status
  r.stubs[0x4008b24a]=disk;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4008b24a,end=0x4008b24a)
  assert r.call('ml_store_io_end')==0
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2500);assert r.call('ml_store_io_begin')==0
  r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  if inside:
   assert r.call('ml_store_io_begin')==1
   assert r.call('ml_store_io_begin')==0 # pas de transaction imbriquée
  buf=r.call(0x40079726,123)
  assert calls==[((123<<5)+0x1c4050,16384,buf)]
  assert r.r32(r.s['ml_store_io_poison'])==int(status!=0)
  if inside:assert r.call('ml_store_io_end')==int(status==0)
  assert r.call('ml_store_io_begin')==int(status==0)
  # Une lecture suivante réussie ne peut pas effacer l'erreur antérieure.
  status=0;r.call('ml_store_disk_read',0,512,0x93070000)
  if r.r32(r.s['ml_store_io_poison']):assert r.call('ml_store_io_begin')==0
 # API haut niveau simulée pouvant masquer une erreur de lecture physique.
 for api in ('lookup','read','write'):
  for high,low in ((0,0),(1,0),(1,-1),(0,-1)):
   r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
   addr={'lookup':0x4007ad86,'read':0x93060000,'write':0x93060004}[api];seen=[]
   def upper(args):
    seen.append(args[:3])
    if low:r.w32(r.s['ml_store_io_poison'],1)
    return high
   r.stubs[addr]=upper;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
   result=r.call('ml_store_'+api+'_checked',2,0x93070000,1616)
   expected=(-1 if low else high) if api=='lookup' else (0 if low else high)
   assert result&0xffffffff==expected&0xffffffff,(api,high,low,result)
   assert seen==[(2,0x93070000,1616)]
   assert r.r32(r.s['ml_store_io_busy'])==0
 print('ok : cache natif protégé, erreur dans/hors transaction persistante, ABI disque, IPL et nesting')
 print('Prototype seulement : hook boot, absence fichier et Save ne sont pas raccordés.')
if __name__=='__main__':main()
