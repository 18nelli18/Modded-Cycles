"""Note116 : reproduire l'ecrasement du PC40187548 par un vrai note-off ChordKeys."""
import argparse,pathlib,sys
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig

def run(case,broken):
 img,memories,ts=boot_case(case);ck=next(t for t in ts if t['id']=='chord-keys-supermodel');q=next(t for t in ts if t['id']=='quick-save-exit');r=Rig(img,{'writes':[]},{'writes':[],'symbols':{**ck['symbols'],**q['symbols']}});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in memories:u.mem_write(at,raw)
 entry=r.s['qs_exit'];before=bytes(u.mem_read(entry,92));assert r.r32(0x40100c44)==entry
 r.stubs[0x400826b0]=lambda args:0;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
 # Ancienne image : les instructions se font passer pour count/root ChordKeys.
 live=r.s['live'];expanded=r.s['expanded'];assert live==0x40187528
 # Permettre la reconstruction du placement fautif depuis un build corrige.
 if broken and entry!=live:
  u.mem_write(live,before);r.w32(0x40100c44,live);entry=live
 if broken:assert live==entry and bytes(u.mem_read(0x40187548,2))==b'\x2f\x0b'
 for track in ([4] if broken else range(6)):
  if not broken:u.mem_write(live+8*track,bytes([1,60,0,0,60,0,0,0]));note=60
  else:note=u.mem_read(live+8*track+1,1)[0]
  r.w32(expanded+16*track+4*(note//32),1<<(note%32));assert r.call('ck_midi_live_off',track,note)==1
 after=bytes(u.mem_read(entry,92))
 if broken:assert before!=after and u.mem_read(0x40187548,1)==b'\0';print('PASS reproduction : vrai note-off ChordKeys ecrase instruction40187548',flush=True)
 else:assert before==after and not(live<=entry<live+192);print('PASS correction : six note-offs reels, etat ChordKeys modifiable, code save intact dans payload',flush=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--after',required=True);a=p.parse_args();run(a.before,True);run(a.after,False)
if __name__=='__main__':main()
