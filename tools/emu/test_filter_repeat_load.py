"""Note 105 : vraies voix + beat repeat + filtre, cinq/six voies, comparaison main.
I/O et historique fixtures ; pas de simulation de deadline physique.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
from test_model_tg import engine,MIX_GAIN
import mcengine as E
ROOT=HERE.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--kick-swarms',action='store_true');a=p.parse_args();img,rt,ts=boot(a.case);ws=next(t['symbols'] for t in ts if t['id']=='sample-wizard');fs=next(t['symbols'] for t in ts if t['id']=='wizard-continuous-filter');br=next(t for t in ts if t['id']=='control-all-beat-repeat');bs={k:int(v,16) for k,v in br['symbols'].items()};old=json.loads((ROOT/'docs/flasher/filter-precision-data.js').read_text().split('=',1)[1].strip().rstrip(';'));baseline=bytearray(img);at=old['at']-E.BASE;baseline[at:at+old['size']]=bytes.fromhex(old['hex'])
 names=next(t['machine_names'] for t in ts if t.get('machine_names'))
 swarm=next((i for i,n in enumerate(names) if n.upper() in ('SY SWARM','SYSWM')),None)
 if a.kick_swarms:assert swarm is not None,names
 for voices in (5,6):
  for repeat in ('off','armed','repeat'):
   engines=[]
   for image in (bytes(baseline),img):
    e=engine(image,payload=(0x46700000,rt));e.uc.mem_write(int(br['append']['dest'],16),bytes.fromhex(br['append']['parts'][0]['hex']));e.uc.mem_write(0x41000000,bytes(12*131072*2))
    def put(addr,value,e=e):e.uc.mem_write(addr,struct.pack('>I',value&0xffffffff))
    put(bs['br_history'],0x41000000);put(bs['br_blocks'],4096);put(bs['br_keys'],0 if repeat=='off' else 3);put(bs['br_requested'],0 if repeat=='repeat' else -1);put(0x40149310,57600);put(0x40a7883c,1);put(0x40a78888,0x41400000);put(0x40a78840,1)
    for lane in range(6):
     machine=(0 if lane in (0,5) else swarm) if a.kick_swarms else 16
     e.set(lane,machine=machine,note=48+lane*3,color=64,shape=0,sweep=64,contour=0,decay=90)
     e.uc.mem_write(E.PARAMS+14+66*lane+46,struct.pack('>3h',0,64*256,0));put(MIX_GAIN+4*lane,0x20000000 if lane<voices else 0)
    e.instructions=0
    def count(u,pc,size,data,e=e):e.instructions+=1
    # Ne pas compter les boucles de synthese : seuls les modules compares.
    filter_at=int(ws['gflt_run'],16);beat_at=int(br['append']['dest'],16)
    e.uc.hook_add(UC_HOOK_CODE,count,begin=filter_at,end=filter_at+old['size'])
    e.uc.hook_add(UC_HOOK_CODE,count,begin=beat_at,end=beat_at+br['append']['size']);engines.append(e)
   totals=[0,0]
   # 480 BPM/1-64 : la boucle de 375 samples reboucle dans ces 512 samples.
   for block in range(16):
    outputs=[]
    for index,e in enumerate(engines):
     e.block((1<<voices)-1 if block%4==0 else 0);e.instructions=0;e.call(bs['br_audio'])
     for lane in range(6):e.call(int(fs['avfc_run'],16),E.TRACK_BASE+128*lane,lane)
     totals[index]+=e.instructions;outputs.append(bytes(e.uc.mem_read(E.TRACK_BASE,6*128)))
    assert outputs[0]==outputs[1],(voices,repeat,block)
   assert totals[1]<totals[0];print('PASS vraies voix/beat repeat/filtre',voices,'repeat',repeat,'16 blocs identiques, boucle complete ; instructions modules',totals,flush=True)
if __name__=='__main__':main()
