"""Adaptateur local du petit assembleur PPPCCC ; octets natifs lus au build."""
import struct
BASE=0x40000400
BRA,BSR,HI,LS,CC,CS,NE,EQ,PL,MI,GE,LT,GT,LE=0,1,2,3,4,5,6,7,10,11,12,13,14,15
IMAGE=b''
class A:
 def __init__(s,org):s.org,s.b,s.lab,s.fix=org,bytearray(),{},[]
 def w(s,*words):
  for v in words:s.b+=struct.pack('>H',v)
 def l32(s,v):s.b+=struct.pack('>I',v)
 def label(s,n):s.lab[n]=s.org+len(s.b)
 def bcc(s,op,n):s.w(0x6000|(op<<8));s.fix.append((len(s.b),n));s.w(0)
 def orig(s,at,n):s.b+=IMAGE[at-BASE:at-BASE+n]
 def done(s):
  for p,n in s.fix:s.b[p:p+2]=struct.pack('>h',s.lab[n]-(s.org+p))
  return bytes(s.b)
def check_cf(code,base):
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 i=0
 while i<len(code):
  ins=next(cs.disasm(code[i:i+12],base+i,1),None)
  if ins is None:i+=2;continue
  assert ins.size<=6,(hex(base+i),ins.mnemonic,ins.op_str)
  i+=ins.size
