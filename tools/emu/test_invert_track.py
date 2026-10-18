"""Note122 : vrais PadEvent/PadsView/relais notes, stock contre inversion.
Le RTTI du navigateur et les sorties notes sont instrumentes ; audio non emule.
"""
import argparse,pathlib,sys
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from probe_chord_pads import Rig,official_image,BASE,VIEW,CONTROLLER
from test_midi_entry import boot_case

def verify(image):
 for altered in (False,True):
  blob=bytearray(image);blob[118644]=0x66 if altered else 0x67
  for browser in (False,True):
   for track in range(6):
    for held in (False,True):
     for retrig in (False,True):
      r=Rig(bytes(blob));r.pressed=({2} if held else set())|({4} if retrig else set())
      if browser:
       node=0x93200000;view=0x93200100;r.w32(CONTROLLER+20,node);r.w32(node,CONTROLLER+20);r.w32(node+8,view);r.w32(node+12,0)
       r.uc.hook_add(UC_HOOK_CODE,r._stub(lambda a:view),begin=0x400f4cec,end=0x400f4cec)
      r.event(track+1,True,81+track)
      plays=browser or held if altered else browser and not held or not browser and not held
      assert any(kind=='on' for kind,args in r.calls)==plays,(altered,browser,held,retrig,r.calls)
      assert any(kind=='select' for kind,args in r.calls)==(not browser or held),r.calls
      if plays:
       args=next(args for kind,args in r.calls if kind=='on');assert args==(track,60+track,81+track,64,0,0xffffffff,7 if retrig else 0xffffffff),args
      r.pressed.clear();r.event(track+1,False)
      assert [kind for kind,args in r.calls]==(['off'] if plays else []),r.calls
      r.event(track+1,False);assert not r.calls
 print('PASS stock/modified: six pads, TRACK, RETRIG, browser preview, velocity, remembered note-off and double release')

def main():
 p=argparse.ArgumentParser();p.add_argument('--case');a=p.parse_args()
 if a.case:
  image,mem,ts=boot_case(a.case)
  assert image[118644]==0x66
  # Les relais modifies par les autres modules ont leur preuve propre ; observer leurs entrees ici.
  image=bytearray(image);stock=official_image('firmware/model-cycles_OS1.13.syx')
  for lo,hi in ((0x4001d05e,0x4001d180),(0x4001d25e,0x4001d264)):
   image[lo-BASE:hi-BASE]=stock[lo-BASE:hi-BASE]
  verify(bytes(image));print('PASS test firmware bootstrap and guarded patch')
 else:
  image=official_image('firmware/model-cycles_OS1.13.syx');assert image[118644]==0x67;verify(image)
if __name__=='__main__':main()
