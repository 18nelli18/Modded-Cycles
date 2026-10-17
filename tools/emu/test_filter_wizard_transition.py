"""Note112 : regression du double filtre apres passage par Wizard.

Vraies boucles voix, pre/post et noyaux du SYX. Fixtures metadata retenue et
transition de frames audio ; aucune validation de menu ou cache physique.
"""
import argparse,pathlib,struct,sys,tempfile,os,shutil
import numpy as np
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_model_tg import engine,MIX_GAIN
import mcengine as E

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',required=True);p.add_argument('--case',required=True);p.add_argument('--blocks',type=int,default=8);p.add_argument('--all',action='store_true');p.add_argument('--native-digiemu');a=p.parse_args()
 if a.native_digiemu:
  sys.path.insert(0,str(pathlib.Path(a.native_digiemu).resolve()))
  from emu.unicorn_compat import evaluate
  from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,m68k_const as mk
  def cpu():
   u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY);return u
  assert evaluate(factory=cpu)['compatible'],'runtime EMAC natif requis'
  import emac
  emac.EMAC.install=lambda self,ops:0;E._emac_instrs=lambda *args:{};E._emac_payload=lambda *args:{}
 else:
  alias=tempfile.TemporaryDirectory();os.symlink(shutil.which('m68k-linux-gnu-objdump'),pathlib.Path(alias.name)/'m68k-elf-objdump');os.environ['PATH']=alias.name+os.pathsep+os.environ['PATH']
 images=[boot(a.baseline),boot(a.case)];machines=range(7,17) if a.all else (7,11,16);old_changed=False
 def make(image,lane,machine,warm):
  img,rt,ts=image;e=engine(img,payload=(0x46700000,rt));ws={k:int(v,16) for k,v in next(t['symbols'] for t in ts if t['id']=='sample-wizard').items()};fs={k:int(v,16) for k,v in next(t['symbols'] for t in ts if t['id']=='wizard-continuous-filter').items()}
  for track in range(6):
   e.set(track,machine=machine if track==lane else 127,note=48+track*3,color=64,shape=64,sweep=64,contour=64,decay=90)
   e.uc.mem_write(E.PARAMS+14+66*track+46,struct.pack('>3h',0,(126 if track==lane else 127)*256,0));e.uc.mem_write(MIX_GAIN+4*track,struct.pack('>I',0x20000000))
  if warm:e.uc.mem_write(ws['voice_ptr']+4*lane,struct.pack('>I',E.VOICE0+E.VSTRIDE*lane))
  e.filter_count=0
  def observe(u,pc,size,data):e.filter_count+=1
  e.uc.hook_add(UC_HOOK_CODE,observe,begin=ws['gflt_run'],end=ws['gflt_run'])
  return e,ws,fs
 def render(fixture,lane,blocks):
  e,ws,fs=fixture;voice=post=0;audio=[]
  for block in range(blocks):
   e.filter_count=0;e.block((1<<lane) if block%4==0 else 0);voice+=e.filter_count;e.filter_count=0
   for track in range(6):e.call(fs['avfc_run'],E.TRACK_BASE+128*track,track)
   post+=e.filter_count;audio.append(bytes(e.uc.mem_read(E.TRACK_BASE+128*lane,128)))
  assert not e.unmapped,e.unmapped
  return voice,post,b''.join(audio)
 for lane in range(6):
  for machine in machines:
   print('CHECK piste',lane+1,'machine',machine,flush=True)
   rows=[[render(make(image,lane,machine,warm),lane,a.blocks) for warm in (False,True)] for image in images]
   cold,retained=rows[0];fixed_cold,fixed_retained=rows[1]
   assert cold[0]==0 and retained[0]>0,('baseline must reproduce extra voice filtering',lane,machine,rows[0][:2])
   assert fixed_cold[0]==fixed_retained[0]==0,('obsolete voice call survives',lane,machine)
   assert fixed_cold[1]==fixed_retained[1]==6*a.blocks
   assert fixed_cold[2]==fixed_retained[2]==cold[2],('cold/warm corrected audio differs',lane,machine)
   old_changed|=cold[2]!=retained[2]
  # La voie stock reste identique meme avec metadata Wizard retenue.
  stock=[[render(make(image,lane,0,warm),lane,a.blocks) for warm in (False,True)] for image in images]
  assert all(row[0]==0 and row[2]==stock[0][0][2] for pair in stock for row in pair)
  # Vraie transition des frames audio : Wizard publie le pointeur, puis SY.
  for index,image in enumerate(images):
   fixture=make(image,lane,6,False);e,ws,fs=fixture
   render(fixture,lane,3)
   pointer=int.from_bytes(e.uc.mem_read(ws['voice_ptr']+4*lane,4),'big')
   assert pointer==E.VOICE0+E.VSTRIDE*lane,('Wizard did not publish voice pointer',lane,hex(pointer))
   e.set(lane,machine=7);after=render(fixture,lane,a.blocks)
   assert (after[0]>0 if index==0 else after[0]==0),('Wizard transition route',index,lane,after[0])
  print('PASS piste',lane+1,': voix ajoutees froid/retenu identiques apres correction, ancien double passage reproduit ; Kick et transition audio Wizard verifies',flush=True)
 assert old_changed,'fixture must reproduce an audible-data difference'
 print('PASS',len(machines),'machines ajoutees x six pistes ; un seul proprietaire filtre post-voix ; aucune preuve hardware inventee')
if __name__=='__main__':main()
