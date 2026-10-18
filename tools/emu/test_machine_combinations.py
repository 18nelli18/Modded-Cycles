#!/usr/bin/env python3
"""Menus compacts, bootstrap reel et audio des choix independants de machines."""
import argparse,json,pathlib,sys,tempfile,os,shutil,struct
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_model_tg import engine
import mcengine as E,test_sdvintage_7th as T

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',default='build/machine-combinations/exact-build');p.add_argument('--baseline',default='build/performance-release/repeat-only');p.add_argument('--blocks',type=int,default=3);p.add_argument('--normal',action='store_true');a=p.parse_args()
 alias=tempfile.TemporaryDirectory();os.symlink(shutil.which('m68k-linux-gnu-objdump'),pathlib.Path(alias.name)/'m68k-elf-objdump');os.environ['PATH']=alias.name+os.pathsep+os.environ['PATH']
 images=[boot(a.baseline,True),boot(a.case,True)]
 names=[next(t['machine_names'] for t in ts if t.get('machine_names')) for img,rt,ts,sram in images]
 print('PASS vrai bootstrap et cache disque',names[1],flush=True)
 img,rt,ts,sram=images[1];nm=len(names[1]);pay=0x46700000
 if not a.normal:
  owner=next(t for t in ts if t.get('machine_selection') is not None);part=next(p for p in owner['append']['parts'] if p['dest']=='0x4672e900');raw=bytes.fromhex(part['hex']);at=0x401c383c-E.BASE;assert img[at:at+len(raw)]==raw,'ChordKeys copie/cache disque'
  print('PASS copie ChordKeys intacte apres bootstrap et cache disque',flush=True)
 class UI(T.UI):
  def __init__(self,img,payload=b''):
   super().__init__(img,payload);self.uc.mem_write(E.BASE,img);self.uc.mem_map(pay,0x100000);self.uc.mem_write(pay,payload)
 u=UI(img,rt);u.call(0x4005a274);assert u.u32(T.ROW_COUNT)==nm,(u.u32(T.ROW_COUNT),nm)
 first=6 if a.normal else 7
 for index in range(first,nm):assert u.call(0x4005a692,12,index)==77+5*(index-first), (index,u.call(0x4005a692,12,index))
 assert not u.bad
 print('PASS constructeur OS, descripteurs compacts, aucun ajout non choisi',flush=True)
 for index,name in enumerate(names[1]):
  original=names[0].index(name);engines=[engine(im,payload=(pay,runtime)) for im,runtime,_,_ in images]
  for e,image,which in zip(engines,images,[original,index]):
   e.uc.mem_write(0x80000000,image[3])
   for track in range(6):e.set(track,machine=which,note=48+track*3,color=64,shape=0,sweep=64,contour=0,decay=90)
  for block in range(a.blocks):
   try:x,y=[e.block(63 if block==0 else 0) for e in engines]
   except Exception:
    from unicorn import m68k_const as mk
    print('FAIL PC',[(hex(e.uc.reg_read(mk.UC_M68K_REG_PC)),e.uc.mem_read(e.uc.reg_read(mk.UC_M68K_REG_PC),8).hex()) for e in engines],flush=True);raise
   assert np.array_equal(x,y),(name,block,int(np.max(np.abs(x-y))))
  assert not any(e.unmapped for e in engines)
  print('PASS audio identique, six pistes : '+name,flush=True)
 print('PASS boot, UI OS et audio ; aucune mesure de charge materielle revendiquee',flush=True)
if __name__=='__main__':main()
