"""Note123 : vrai bootstrap puis hook de chargement ChordKeys et cache disque."""
import argparse,pathlib,sys
from unicorn import m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,STACK
import build

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();img,memories,ts=boot_case(a.case)
 ck=next(t for t in ts if t['id']=='chord-keys-supermodel');dest=0x401c383c
 if ck.get('append'):raw=bytes.fromhex(next(p['hex'] for p in ck['append']['parts'] if p['dest']=='0x401c383c'))
 else:
  owner=next(t for t in ts if t.get('chord_source') or t['id']=='midi-out-bank');source=owner.get('chord_source','0x4672e900');raw=bytes.fromhex(next(p['hex'] for p in owner['append']['parts'] if p['dest']==source))
 assert img[dest-build.BASE:dest-build.BASE+len(raw)]==raw,'ChordKeys pas charge par le bootstrap reel'
 r=Rig(img,{'writes':[]},{'writes':[],'symbols':ck['symbols']});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,data in memories:u.mem_write(at,data)
 src=0x930b0000;dst=0x930b1000;u.mem_write(src,bytes(128));u.mem_write(dst,bytes(128));u.mem_write(src+28,b'\x5a')
 u.reg_write(mk.UC_M68K_REG_A2,dst);u.reg_write(mk.UC_M68K_REG_A3,src);u.reg_write(mk.UC_M68K_REG_A7,STACK);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
 u.emu_start(int(ck['symbols']['ck_storage_load_hook'],16),0x4005b4b0,count=100000)
 assert u.reg_read(mk.UC_M68K_REG_PC)==0x4005b4b0
 assert bytes(u.mem_read(dst+28,1))==b'\x5a' and u.reg_read(mk.UC_M68K_REG_D0)==1 and u.reg_read(mk.UC_M68K_REG_A7)==STACK
 r.call(0x4007929c);assert bytes(u.mem_read(dest,len(raw)))==raw,'cache disque ecrase ChordKeys'
 print('PASS vrai bootstrap, ChordKeys exact, chargement projet/ABI et cache disque:',a.case)
if __name__=='__main__':main()
