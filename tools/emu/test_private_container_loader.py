"""Decompresseur natif, vrai conteneur prive, source compressee non ecrasee.
Le banc historique impose END_LIMIT par prudence ; ces images privees depassent
cette borne. Prouver ici chaque octet produit et chaque ecriture dans le stage.
Adresses et arguments du bootstrap identiques a test_sdvintage_exact.py.
"""
import json,pathlib,struct,sys
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_MEM_WRITE,m68k_const as C
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT
from mtlib import aplib,container
from mtlib.syx import unwrap

def check(stem):
 p=container.parse(unwrap((ROOT/'output/firmware'/(stem+'.syx')).read_bytes())[0]);sec={s['id']:p['blob'][s['off']:s['off']+s['size']] for s in p['sections']};want=aplib.depack(sec[3])[0];bs=aplib.depack(sec[2])[0]
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(C.UC_CPU_M68K_ANY);u.mem_map(0x80000000,0x20000);u.mem_map(0x40000000,0x400000);u.mem_write(0x800003fc,bs);u.mem_write(0x40200000,sec[3]);u.mem_write(0x8001e000,struct.pack('>3I',0x8001f000,0x40200000,0x40000400));u.reg_write(C.UC_M68K_REG_A7,0x8001e000)
 overlap=[];gaps=[]
 def write(uc,access,addr,size,value,data):
  cursor=uc.reg_read(C.UC_M68K_REG_A0)
  if addr<0x40200000+len(sec[3]) and addr+size>cursor:overlap.append((hex(addr),hex(cursor)))
  gaps.append(cursor-addr-size)
 u.hook_add(UC_HOOK_MEM_WRITE,write,begin=0x40200000,end=0x403fffff)
 u.emu_start(0x800006bc,0x8001f000,count=400000000)
 assert u.reg_read(C.UC_M68K_REG_PC)==0x8001f000 and u.reg_read(C.UC_M68K_REG_D0)==len(want)
 assert bytes(u.mem_read(0x40000400,len(want)))==want and not overlap,overlap[:2]
 # Ne rien produire apres l'OS ; hors stage, cette zone n'avait aucune donnee.
 tail=0x40000400+len(want)
 if tail>=0x40200000:
  offset=tail-0x40200000;assert bytes(u.mem_read(tail,64))==sec[3][offset:offset+64]
 else:assert not any(u.mem_read(tail,64))
 result={'stem':stem,'native_decompressed_bytes':len(want),'stage_writes':len(gaps),'minimum_unread_gap':min(gaps) if gaps else None,'exact':True,'unread_overwritten':False};print('PASS native bootstrap',result,flush=True);return result
if __name__=='__main__':
 result=[check(s) for s in sys.argv[1:]];(ROOT/'output/firmware/machinedrum-audit/loader-results.json').write_text(json.dumps(result,indent=2)+'\n')
