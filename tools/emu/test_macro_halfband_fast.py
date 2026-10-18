"""Note124 : filtre MACRO exact, vrais rendus47modeles et comptage instructions."""
import argparse,copy,json,pathlib,random,struct,sys
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import emac,mcengine as E
from test_macro import Fw,load,BASE_KW,BASE
from test_sdvintage import main_os_from_syx
ROOT=HERE.parent.parent;OUT=ROOT/'build/macro-optimization';OFFSET=0xea;SIZE=162

def kernel(old,new):
 start=0x4300060c;end=start+SIZE;results=[];rand=random.Random(124)
 samples=[[0]*86,[32767]*86,[-32768]*86,[32767 if i&1 else -32768 for i in range(86)]]+[[rand.randrange(-32768,32768) for _ in range(86)] for _ in range(96)]
 for label,raw in [('before',old),('after',new)]:
  path=OUT/(label+'-kernel.bin');path.write_bytes(raw);ops=emac.disasm(str(path),start,start,end);u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
  for at,size in [(0x43000000,0x10000),(0x100000,0x40000)]:u.mem_map(at,size)
  u.mem_write(start,raw);mac=emac.EMAC(u);mac.install(ops);count=[0];u.hook_add(UC_HOOK_CODE,lambda *a:count.__setitem__(0,count[0]+1));outs=[]
  for words in samples:
   u.mem_write(0x100000,struct.pack('>86h',*words));u.reg_write(mk.UC_M68K_REG_A0,0x100000);u.reg_write(mk.UC_M68K_REG_A1,0x110000);u.reg_write(mk.UC_M68K_REG_A6,0x100080);u.reg_write(mk.UC_M68K_REG_A7,0x120000)
   mac.macsr=0xa0;mac.acc=[123456789<<31,87654321<<31,100<<31,-123<<31];u.emu_start(start,end,count=10000)
   assert u.reg_read(mk.UC_M68K_REG_PC)==end and mac.macsr==0xa0
   assert mac.acc[1:]==[87654321<<31,100<<31,-123<<31]
   assert u.reg_read(mk.UC_M68K_REG_A0)==0x100080 and u.reg_read(mk.UC_M68K_REG_A1)==0x110080
   outs.append(bytes(u.mem_read(0x110000,128)))
  results.append(outs);print('PASS kernel',label,len(samples),'vectors',count[0]//len(samples),'instructions/block',flush=True)
 assert results[0]==results[1];print('PASS 3200 exact output samples including extremes; MACSR and unused accumulators preserved',flush=True)

def voices(new,models):
 stock=main_os_from_syx(str(ROOT/'firmware/model-cycles_OS1.13.syx'));original=load('25-macro.json');changed=copy.deepcopy(original);p=changed['append']['parts'][0];raw=bytearray.fromhex(p['hex']);at=int(original['symbols']['macro_render'],16)-int(p['dest'],16)+OFFSET;raw[at:at+SIZE]=new;p['hex']=raw.hex()
 fws=[Fw(stock,[original]),Fw(stock,[changed])];rows=[]
 for model in models:
  answers=[];costs=[]
  for fw in fws:
   e=fw.engine(solo=0);e.set(0,machine=fw.index,**dict(BASE_KW,shape=model,decay=127));counter=[0];e.uc.hook_add(UC_HOOK_CODE,lambda *a:counter.__setitem__(0,counter[0]+1));blocks=[];per=[];states=[]
   for i in range(16):
    if i==8:e.set(0,color=110,sweep=17,contour=80)
    c=counter[0];blocks.append(e.block(1 if i in (0,8) else 0).tobytes());per.append(counter[0]-c);states.append((e.emac.macsr,tuple(e.emac.acc)))
   answers.append((blocks,states));costs.append(sum(per[3:])/13)
  assert answers[0]==answers[1],('voice or EMAC state differs',model)
  assert costs[1]<=costs[0],('cost regression',model,costs)
  rows.append(dict(model=model,before=round(costs[0]),after=round(costs[1]),saved=round(costs[0]-costs[1])))
  print('PASS model',model,'exact native audio/state;',round(costs[0]),'->',round(costs[1]),'instructions/block',flush=True)
 (OUT/'voice-costs.json').write_text(json.dumps(rows,indent=2)+'\n')

def main():
 p=argparse.ArgumentParser();p.add_argument('--kernel-only',action='store_true');p.add_argument('--models');a=p.parse_args();OUT.mkdir(exist_ok=True)
 t=load('25-macro.json');part=t['append']['parts'][0];at=int(t['symbols']['macro_render'],16)-int(part['dest'],16)+OFFSET;old=bytes.fromhex(part['hex'])[at:at+SIZE];new=(OUT/'halfband.bin').read_bytes();assert len(new)==len(old)==SIZE
 kernel(old,new)
 if not a.kernel_only:voices(new,[int(x) for x in a.models.split(',')] if a.models else range(47))
if __name__=='__main__':main()
