"""Note 112 : fonction oscillateur stock complete, index exact et ABI."""
import json,pathlib,random,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
import emac

def main(pair=False):
 root=HERE.parents[1];stock=main_os_from_syx('firmware/model-cycles_OS1.13.syx');all_data=json.loads((root/'build/audio-load/data.json').read_text());data=all_data['native'];lo,hi=0x400a8204,0x400a835e;off=data['at']-lo

 if pair:data=all_data['native_pair'];lo,hi=0x400a80e6,0x400a8204;off=data['at']-lo
 old=stock[lo-0x40000400:hi-0x40000400];new=bytearray(old);changed=(bytearray(old[off+2:])+bytearray.fromhex('4e71')) if pair else (bytearray.fromhex(data['index_hex'])+bytearray(old[off+12:])+bytearray.fromhex('4e71'));
 if pair:
  for at,hexdata in [(0x400a817c,'4844'),(0x400a8184,'0284000000ff'),(0x400a818c,'28744c00'),(0x400a819c,'28344c04')]:
   i=at-data['at']-2;changed[i:i+len(hexdata)//2]=bytes.fromhex(hexdata)
 bi=data['branch']-data['at']-2;struct.pack_into('>h',changed,bi+2,struct.unpack_from('>h',changed,bi+2)[0]+2);new[off:]=changed
 rigs=[]
 for i,raw in enumerate((old,bytes(new))):
  r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_write(lo,raw);path=root/f'build/audio-load/native-{i}.bin';path.write_bytes(raw);r.emac=emac.EMAC(r.u);r.emac.install(emac.disasm(str(path),lo,lo,hi));r.count=0
  def count(u,pc,size,data,r=r):r.count+=1
  r.u.hook_add(UC_HOOK_CODE,count,begin=lo,end=hi);rigs.append(r)
 rng=random.Random(113);base,in1,in2,out1,out2,table=0x93010000,0x93020000,0x93021000,0x93022000,0x93023000,0x93024000;counts=[0,0]
 for case in range(512):
  state=bytearray(rng.randbytes(208))
  for at,address in [(148,in1),(152,in2),(168,table),(192,out1),(196,out2)]:struct.pack_into('>I',state,at,address)
  a=rng.randbytes(132);b=rng.randbytes(132);t=rng.randbytes(257*4);outputs=[];saved=[rng.getrandbits(32) for _ in range(11)];regs=[getattr(mk,'UC_M68K_REG_D'+str(n)) for n in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(n)) for n in range(2,7)]
  for i,r in enumerate(rigs):
   r.u.mem_write(base,bytes(state));r.u.mem_write(in1,a);r.u.mem_write(in2,b);r.u.mem_write(table,t);r.u.mem_write(out1,bytes(128));r.u.mem_write(out2,bytes(128));r.emac.macsr=0xa0 if case%2 else 0xb0;r.emac.acc[:]=[0,0,123,456];r.count=0;
   for reg,value in zip(regs,saved):r.u.reg_write(reg,value)
   r.call(lo,0,base);counts[i]+=r.count
   assert [r.u.reg_read(reg) for reg in regs]==saved
   outputs.append((bytes(r.u.mem_read(base,208)),bytes(r.u.mem_read(out1,128)),bytes(r.u.mem_read(out2,128)),tuple(r.emac.acc),r.emac.macsr))
  assert outputs[0]==outputs[1],case
 assert counts[0]-counts[1]==512*32,counts
 print('PASS pair' if pair else 'PASS index', '512 fonctions oscillateur stock : samples/etats/accumulateurs/MACSR/ABI exacts ; 32 instructions gagnees par appel',counts,flush=True)
def incoming():
 root=HERE.parents[1];stock=main_os_from_syx('firmware/model-cycles_OS1.13.syx');path=root/'build/audio-load/native-incoming.bin';path.write_bytes(stock)
 ranges=((0x400a816e,0x400a8204,0x400a80e6),(0x400a82e2,0x400a835e,0x400a8204))
 ins=emac.disasm(str(path),0x40000400,0x40000400,0x40100000)
 import re
 for pc,(_,mn,ops) in ins.items():
  if not (mn.startswith('b') or mn.startswith('j') or mn.startswith('db')):continue
  for match in re.finditer(r'0x([0-9a-f]+)',ops):
   target=int(match.group(1),16)
   for lo,hi,entry in ranges:
    assert not (lo<=target<hi and not entry<=pc<hi),('branche entrante',hex(pc),mn,ops)
 for i in range(0,len(stock)-3,2):
  value=int.from_bytes(stock[i:i+4],'big')
  assert not any(lo<=value<hi for lo,hi,_ in ranges),('pointeur entrant',hex(0x40000400+i),hex(value))
 print('PASS regions decalees : aucune branche externe ni pointeur absolu entrant',flush=True)
if __name__=='__main__':incoming();main();main(True)
