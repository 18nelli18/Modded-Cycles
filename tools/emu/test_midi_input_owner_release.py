"""Reception auto : le note-off garde la piste de son attaque apres selection.
Reproduit v9 puis verifie v13, deux variantes et 24 changements chacune.
"""
import sys,json,struct,subprocess
_original_run=subprocess.run
def cross_run(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[str(__import__('pathlib').Path('../retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe').resolve()),*cmd[1:]]
 return _original_run(cmd,*args,**kw)
subprocess.run=cross_run
from boot_candidate import ROOT,boot
import sys
sys.path.insert(0,str(ROOT/'output/firmware'))
import test_step_rec_legacy as S
from lofi_ui import UI
profile=json.loads((ROOT/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text())
old={k:int(v,16) for t in profile['composedTweaks'] if t['id']=='midi-out-machine' for k,v in t['symbols'].items()}


for version in [9,13]:
 for prefix_name in ['all-features','no-filter']:
  stem=f'{prefix_name}-midi-playability-no-diagnostic-v{version}';m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());sy=m['playability_symbols'];im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));r=S.Rig(im,mem)
  r.hooks[0x4007faf4]=lambda a:0;r.hooks[0x40076bee]=lambda a:0;r.hooks[old['mm_popup']]=lambda a:0;r.hooks[0x400826b0]=lambda a:0
  for lane,machine in [(0,4),(1,17),(2,17),(3,4),(4,17),(5,17)]:
   p=r.call(old['mm_params'],lane);r.uc.mem_write(p+18,struct.pack('>H',machine<<8))
   if machine==17:r.call(sy['mm_setup'],p)
  cfg=r.call(0x4000d0dc,r.call(0x4000f208,r.proj));events=[]
  r.hooks[0x4005894a]=lambda a:events.append(bytes(r.uc.mem_read(a[0],56))) or 0
  for lane in [0,3]:
   raw=r.call(r.u32(r.u32(r.track(lane))+40),r.track(lane));r.uc.mem_write(raw+512,b'\x00');r.uc.mem_write(raw+514,b'\x09');r.call(0x4000cd2a,cfg,lane,1)
   for selected_after in [1,2,4,5]:
    for note in [36,60,84]:
     events.clear();r.w32(0x40a70100,15);r.w32(0x40a700c4,lane);r.hooks[0x40012412]=lambda a,lane=lane:lane
     r.call(sy['mi_receive_on'],15,note,100,0x40);before=len(events);assert before>=1
     r.w32(0x40a700c4,selected_after);r.hooks[0x40012412]=lambda a,selected_after=selected_after:selected_after
     r.call(sy['mi_receive_off'],15,note,0x40)
     if version==9:assert len(events)==before
     else:
      assert len(events)==before+1,(lane,selected_after,note,len(events),before)
      last=struct.unpack('>11I',events[-1][:44]);assert last[3]==2 and last[0]==lane,(lane,last)
      # Un second relachement ne renvoie rien a l'ancienne piste.
      r.call(sy['mi_receive_off'],15,note,0x40);assert len(events)==before+1
     r.call(sy['mi_reset'],lane)
  print('PASS' if version==13 else 'REPRODUCED',stem,'24 Tone arp key releases after auto-track changes; correct owner, no duplicate off',flush=True)
