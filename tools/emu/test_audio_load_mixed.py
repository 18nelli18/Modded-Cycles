"""Note 112 : six voix du rapport, repeat et filtre, candidats/actuel exacts.
Peripheriques simules, comparaison d instructions et non de cycles materiels.
"""
import argparse,pathlib,struct,sys,shutil,tempfile,os
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_model_tg import engine,MIX_GAIN
import mcengine as E

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--baseline',required=True);p.add_argument('--blocks',type=int,default=48);p.add_argument('--mode',choices=('off','armed','repeat'));a=p.parse_args()
 alias=tempfile.TemporaryDirectory();os.symlink(shutil.which('m68k-linux-gnu-objdump'),pathlib.Path(alias.name)/'m68k-elf-objdump');os.environ['PATH']=alias.name+os.pathsep+os.environ['PATH']
 cases=[boot(a.baseline),boot(a.case)]
 for repeat in ((a.mode,) if a.mode else ('off','armed','repeat')):
  engines=[]
  for img,rt,ts in cases:
   e=engine(img,payload=(0x46700000,rt));br=next(t for t in ts if t['id']=='control-all-beat-repeat');bs={k:int(v,16) for k,v in br['symbols'].items()};f=next(t for t in ts if t['id']=='wizard-continuous-filter');fs={k:int(v,16) for k,v in f['symbols'].items()};ws=next(t['symbols'] for t in ts if t['id']=='sample-wizard')
   for part in br['append']['parts']:
    if 'hex' in part:e.uc.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
   e.uc.mem_write(0x41000000,bytes(12*131072*2));put=lambda at,v:e.uc.mem_write(at,struct.pack('>I',v&0xffffffff))
   for key,v in [('br_history',0x41000000),('br_blocks',4096),('br_keys',0 if repeat=='off' else 3),('br_requested',0 if repeat=='repeat' else -1)]:put(bs[key],v)
   for at,v in [(0x40149310,57600),(0x40a7883c,1),(0x40a78888,0x41400000),(0x40a78840,1)]:put(at,v)
   for lane,machine in enumerate((0,1,2,3,4,7)):
    e.set(lane,machine=machine,note=48+3*lane,color=64,shape=64,sweep=64,contour=64,decay=90)
    e.uc.mem_write(E.PARAMS+14+66*lane+46,struct.pack('>3h',0,64*256,0));put(MIX_GAIN+4*lane,0x20000000)
   e.count=0;e.filter_calls=0
   def filter_entry(u,pc,size,data,e=e):e.filter_calls+=1
   e.uc.hook_add(UC_HOOK_CODE,filter_entry,begin=int(ws['gflt_run'],16),end=int(ws['gflt_run'],16))
   def count(u,pc,size,data,e=e):e.count+=1
   e.uc.hook_add(UC_HOOK_CODE,count,begin=int(ws['gflt_run'],16),end=int(ws['gflt_run'],16)+678)
   e.uc.hook_add(UC_HOOK_CODE,count,begin=int(br['append']['dest'],16),end=int(br['append']['dest'],16)+br['append']['size'])
   engines.append((e,bs,fs))
  totals=[0,0];voice_filters=[0,0];post_filters=[0,0];audible=False
  for block in range(a.blocks):
   outputs=[]
   for index,(e,bs,fs) in enumerate(engines):
    e.filter_calls=0;e.block(63 if block%4==0 else 0);voice_filters[index]+=e.filter_calls;e.filter_calls=0;e.count=0;e.call(bs['br_audio'])
    for lane in range(6):e.call(fs['avfc_run'],E.TRACK_BASE+128*lane,lane)
    post_filters[index]+=e.filter_calls;totals[index]+=e.count;outputs.append(bytes(e.uc.mem_read(E.TRACK_BASE,768)))
   assert outputs[0]==outputs[1],(repeat,block);audible|=any(outputs[0])
  assert audible;print('PASS Kick/Snare/Metal/Perc/Tone/SDVtg',repeat,a.blocks,'blocs exacts ; instructions filtre+repeat',totals,'appels filtre voix/post',voice_filters,post_filters,flush=True)
if __name__=='__main__':main()
