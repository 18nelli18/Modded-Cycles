#!/usr/bin/env python3
"""Copies LFO allégées : différence binaire/PCM de paramètres, natif exact.

Compte les instructions exécutées, pas des cycles CPU matériels. Tous les
paramètres, phases et registres callee-saved doivent rester identiques.
"""
import argparse,json,pathlib,random,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
import build
from test_tempo_max import Rig,LFO_PHASE
from test_sdvintage import main_os_from_syx

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--base',required=True);p.add_argument('--tweak',required=True);a=p.parse_args()
 stock=main_os_from_syx(a.cycles);base=json.loads(pathlib.Path(a.base).read_text());fast=json.loads(pathlib.Path(a.tweak).read_text());s={k:int(v,16) for k,v in base['symbols'].items()};assert fast['symbols']==base['symbols']
 rigs=[Rig(build.apply_writes(stock,[t])[0]) for t in (base,fast)];counts=[0,0]
 for i,r in enumerate(rigs):
  def count(u,pc,size,data,index=i):counts[index]+=1
  r.uc.hook_add(UC_HOOK_CODE,count)
 rng=random.Random(20261013);src,dst,state1,state2=0x93050000,0x93051000,0x93052000,0x93053000
 # Le helper externe n'expose pas D0/D1 ; A0/A1 restent les mêmes fins.
 data=bytes(rng.randrange(256) for _ in range(476))
 for r in rigs:
  r.uc.mem_write(src,data);r.uc.mem_write(dst,b'\xa5'*476)
  r.uc.reg_write(mk.UC_M68K_REG_A0,src);r.uc.reg_write(mk.UC_M68K_REG_A1,dst)
  r.call(s['lf2_copy_frame'])
  assert bytes(r.uc.mem_read(dst,476))==data
  assert r.uc.reg_read(mk.UC_M68K_REG_A0)==src+476 and r.uc.reg_read(mk.UC_M68K_REG_A1)==dst+476
 assert counts[0]-counts[1]==119,(counts,'copie')
 print('ok : copie476 exacte,119 instructions retirées par appel, pas de NOP dans la boucle',flush=True)
 # Mixer générique : tailles paires/impaires/zéro, zéro à12 destinations,
 # destinations égales, profondeur négative et saturation des deux côtés.
 for size in (0,1,2,7,197,198,237,238):
  for active in (0,1,6,12):
   blob=b''.join(struct.pack('>H',rng.randrange(32513)) for _ in range(238))
   banks=[bytearray(192),bytearray(192)]
   for j in range(12):
    struct.pack_into('>ii',banks[j//6],32*(j%6)+16,11 if j<active else -1,rng.randrange(-32768,32768))
   result=[]
   for r in rigs:
    r.uc.mem_write(src,blob);r.uc.mem_write(dst,b'\xa5'*480)
    r.uc.mem_write(state1,bytes(banks[0]));r.uc.mem_write(state2,bytes(banks[1]))
    r.call(s['lf2_mix'],dst,src,size,state1,state2)
    result.append(bytes(r.uc.mem_read(dst,480)))
   assert result[0]==result[1],(size,active)
 print('ok :32 cas de mixer, tailles0..238 paires/impaires, clipping et destinations communes identiques',flush=True)
 # Dispatch complet : vraie routine OS LFO1 et LFO2, enums, sync natif des
 # cinq champs sauvés, phases. Les deux images reçoivent le même frame brut.
 ctx,frame=0x93060000,0x93070000
 for r in rigs:
  r.uc.mem_write(ctx,bytes(1240));r.w32(s['lf2_context'],ctx);r.uc.mem_write(LFO_PHASE,bytes(192));r.emac.macsr=0x20
  for lane in range(6):
   r.uc.mem_write(ctx+192+lane*16,struct.pack('>8H',20000,9<<8,16000,11<<8,3<<8,5000,0,28000))
 saved=[]
 for tick in range(120):
  blob=bytearray(476)
  for lane in range(6):
   struct.pack_into('>8H',blob,16+lane*66,17000+lane*100,9<<8,16384,11<<8,(tick%7)<<8,8000,0,29000)
   struct.pack_into('>5H',blob,70+lane*66,21000+lane*100,9<<8,((tick+lane)%7)<<8,(11 if tick%3 else 0)<<8,27000)
  outputs=[];before=counts[:]
  for r in rigs:
   r.uc.mem_write(frame,bytes(blob));r.uc.reg_write(mk.UC_M68K_REG_SR,0x2500)
   r.call(s['lf2_dispatch'],frame,14400,63 if tick%16==0 else 0)
   outputs.append((bytes(r.uc.mem_read(frame,476)),bytes(r.uc.mem_read(ctx,1240)),bytes(r.uc.mem_read(LFO_PHASE,192))))
  assert outputs[0]==outputs[1],tick
  saved.append((counts[0]-before[0])-(counts[1]-before[1]))
 assert set(saved)=={476},set(saved)
 print('ok :120 blocs dispatch natif, phases/paramètres strictement identiques ;476 instructions/bloc retirées',flush=True)
 assert not any(r.bad for r in rigs)
 print('Limite : gain en cycles matériels et charge complète Syntakt/ACID à mesurer sur Cycles ; aucun résultat CPU% revendiqué')
if __name__=='__main__':main()
