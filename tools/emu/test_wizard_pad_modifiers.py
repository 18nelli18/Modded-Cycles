"""Test130 : Pad Setup dans la vraie chaine clavier ; SETTINGS ne reste pas colle a MACRO."""
import pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_macro_fine import load,SCRATCH,PITCH
def main():
 r,ts=load(sys.argv[1] if len(sys.argv)>1 else 'build/wizard-control/usb-after');sy={k:int(v,16) for t in ts for k,v in t.get('symbols',{}).items()}
 delegate=SCRATCH+0x7000;r.uc.mem_write(sy['mm_ui_api']+16,struct.pack('>I',delegate));r.hooks[delegate]=('native-final-dispatch',0)
 r.settings=False;r.lookup(12,2,False);event=SCRATCH+0x5000
 def key(code,flags):r.uc.mem_write(event,struct.pack('>6I',0,0,0,code,flags,0));return r.call(0x40077720,0,event)
 held=r.u32(sy['mf_api']+16)
 if held:r.uc.mem_write(held,bytes(4))
 key(13,1);key(2,1)
 if 'long' in sys.argv:key(2,33)
 key(2,0);key(13,0)
 if held:assert r.u32(held)==0
 assert r.call(sy['wf_menu_edit'])==0
 key(32,16);assert r.call(sy['wf_menu_edit'])==1
 key(12,1);r.lookup(12,2,False)
 assert r.edit_func(PITCH,0x4000,256)==0x4100,'SETTINGS fantome apres Pad Setup'
 key(13,1);assert r.edit_func(PITCH,0x4000,256)==0x4002
 key(13,0);assert r.edit_func(PITCH,0x4000,256)==0x4100
 print('PASS vraie chaine SETTINGS+TRACK -> DATA -> BACK : flag partage et MACRO relaches ; fine tune tenu/release intact')
if __name__=='__main__':main()
