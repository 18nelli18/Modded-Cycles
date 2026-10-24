"""Modele d'acces ACC/ACCext pendant sauvegarde/restauration NXP5.3.1.2.

Etend le modele DSP existant seulement pour les nouveaux bancs du Wizard.
La representation physique48bits reste invariante au changement F/I.
"""
import emac
from unicorn import m68k_const as C
BaseEMAC=emac.EMAC
MASK48=(1<<48)-1
def signed48(v):
 v&=MASK48;return v-(1<<48) if v&(1<<47) else v
class ExtendedEMAC(BaseEMAC):
 def physical(self,i):return ((self.acc[i]>>23) if self.frac else self.acc[i])&MASK48
 def put_physical(self,i,raw):self.acc[i]=signed48(raw)*(1<<23) if self.frac else signed48(raw)
 def _slow(self,uc,addr):
  sz,mn,ops=self.ops[addr];args=[a.strip() for a in ops.split(',')]
  if mn=='movel' and len(args)==2:
   src,dst=args
   if dst=='%macsr':
    raw=[self.physical(i) for i in range(4)];value=int(src[1:]) if src.startswith('#') else self.r(src)
    self.macsr=value&0xfff
    for i,x in enumerate(raw):self.put_physical(i,x)
   elif src in ('%accext01','%accext23'):
    first=0 if src.endswith('01') else 2;v=0
    for i in (first,first+1):
     x=self.physical(i);ext=(((x>>40)&255)<<8|(x&255)) if self.frac else (x>>32)&65535;v=(v<<16)|ext
    self.w(dst,v)
   elif dst in ('%accext01','%accext23'):
    first=0 if dst.endswith('01') else 2;value=int(src[1:]) if src.startswith('#') else self.r(src)
    for j,i in enumerate((first,first+1)):
     ext=(value>>(16 if j==0 else 0))&65535;raw=self.physical(i)
     raw=((ext>>8)<<40)|(raw&0xffffffff00)|(ext&255) if self.frac else (ext<<32)|(raw&0xffffffff)
     self.put_physical(i,raw)
   else:return super()._slow(uc,addr)
   uc.reg_write(C.UC_M68K_REG_PC,addr+sz);return
  return super()._slow(uc,addr)
