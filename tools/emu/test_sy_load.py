"""Note 107 : six vraies voix DSP Syntakt, son exact Toy/Bits et Swarm lite.
Mesure d instructions du programme DSP ; ne simule pas le budget audio Cycles.
"""
import pathlib,sys,struct,json,collections
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import stengine as S,syntakt
ROOT=HERE.parents[1]
def main():
 image=syntakt.dsp_image(str(ROOT/'firmware/Syntakt_OS1.42.syx'));data=json.loads((ROOT/'build/swarm-lite/swarm-lite-data.js').read_text().split('=',1)[1].strip().rstrip(';'));patched=bytearray(image)
 for e in data['exact']+data['edits']:
  off=e['source']-S.BASE;patched[off:off+e['size']]=bytes.fromhex(e['hex'])
 for name,controls in [('SY TOY',(24,60,110,64)),('SY BITS',(52,102,0,21)),('SY SWARM',(20,15,70,64))]:
  es=[]
  for img in (image,patched):
   e=S.Engine(img);e.solo(0);e.count=0;e.osc=collections.Counter()
   for lane in range(6):
    e.machine(lane,name);e.note(lane,48+lane*3);e.set(lane,tune=64,p1=controls[0],p2=controls[1],p3=controls[2],p4=controls[3],punch=2 if name=='SY SWARM' else 0,gate=0,decay=90,over=0)
   def count(u,pc,size,data,e=e):e.count+=1
   def osc(u,pc,size,data,e=e):e.osc[struct.unpack('>I',bytes(u.mem_read(u.reg_read(mk.UC_M68K_REG_A7)+4,4)))[0]]+=1
   e.uc.hook_add(UC_HOOK_CODE,count);e.uc.hook_add(UC_HOOK_CODE,osc,begin=0x40006434,end=0x40006434);es.append(e)
  counts=[0,0];different=False;audible=False
  for block in range(8):
   outputs=[]
   for i,e in enumerate(es):e.count=0;outputs.append(e.block(63 if block in (1,5) else 0));counts[i]+=e.count
   equal=(outputs[0]==outputs[1]).all();different|=not equal
   if name!='SY SWARM':assert equal,(name,block)
   audible|=bool(any(outputs[1].flatten()))
  assert audible,(name,'silence')
  saving=100*(1-counts[1]/counts[0]);print('PASS six',name,'DSP instructions',counts,'saving',round(saving,2),'%','audio changed',different,flush=True)
  if name=='SY SWARM':
   assert different and saving>15
   assert set(es[0].osc)==set(range(7)),es[0].osc;assert set(es[1].osc)=={0,3,6},es[1].osc
   print('PASS Swarm : sept appels vers trois par piste/bloc',dict(es[0].osc),dict(es[1].osc),flush=True)
if __name__=='__main__':main()
