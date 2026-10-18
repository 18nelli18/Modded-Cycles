"""Regresse PC401c4b44 : vrai bootstrap Select All, hook stockage et cache disque."""
import argparse,pathlib,struct,sys
from unicorn import m68k_const as mk,UcError
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,STACK,STOP
import build

def run(case,fixed):
 img,memories,ts=boot_case(case);bank=next(t for t in ts if t['id']=='midi-out-bank');ck=next(t for t in ts if t['id']=='chord-keys-supermodel');p=next(p for p in bank['append']['parts'] if p['dest']=='0x4672e900');raw=bytes.fromhex(p['hex']);dest=0x401c383c
 assert (img[dest-build.BASE:dest-build.BASE+len(raw)]==raw)==fixed
 r=Rig(img,{'writes':[]},{'writes':[],'symbols':ck['symbols']});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,data in memories:u.mem_write(at,data)
 src=0x930b0000;dst=0x930b1000;u.mem_write(src,bytes(128));u.mem_write(dst,bytes(128));u.mem_write(src+28,b'\x5a')
 u.reg_write(mk.UC_M68K_REG_A2,dst);u.reg_write(mk.UC_M68K_REG_A3,src);u.reg_write(mk.UC_M68K_REG_A7,STACK);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
 pc=int(ck['symbols']['ck_storage_load_hook'],16);assert pc==0x401c4b44
 try:u.emu_start(pc,0x4005b4b0,count=100000)
 except UcError:
  if fixed:raise
 reached=u.reg_read(mk.UC_M68K_REG_PC)==0x4005b4b0
 assert reached==fixed,(case,hex(u.reg_read(mk.UC_M68K_REG_PC)))
 if not fixed:print('PASS ancien Select All reproduit : ChordKeys absent, hook401c4b44 invalide au chargement projet',flush=True);return
 assert bytes(u.mem_read(dst+28,1))==b'\x5a' and u.reg_read(mk.UC_M68K_REG_D0)==1 and u.reg_read(mk.UC_M68K_REG_A7)==STACK
 r.call(0x4007929c)
 assert bytes(u.mem_read(dest,len(raw)))==raw,'cache disque ecrase ChordKeys'
 print('PASS corrige : vrai bootstrap, hook401c4b44 execute, octet28/retour/pile corrects, code conserve apres cache disque',flush=True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',default='build/machine-combinations-test-1/all-midi');p.add_argument('--after',default='build/machine-combinations-test-2/all-midi');a=p.parse_args();run(a.before,False);run(a.after,True)
if __name__=='__main__':main()
