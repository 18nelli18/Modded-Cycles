"""Preuve ColdFire du noyau : permutations, routage, refus atomiques et codecs OS."""
from pathlib import Path
import argparse,json,os,random,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import m68k_const as C
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
obj=a.output/'swap.o';elf=a.output/'swap.elf';binary=a.output/'swap.bin';ld=a.output/'swap.ld'
ld.write_text('SECTIONS { .text 0x4679d000 : { *(.text*) *(.rodata*) } }\n')
def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/track-swap377.c','-o',obj)
run('ld','-T',ld,'-o',elf,obj);run('objcopy','-O','binary','-j','.text',elf,binary)
sy={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
r=Rig((a.capture/'native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in sy.items()}});u=r.u
u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,(a.capture/'runtime.bin').read_bytes());assert not any(u.mem_read(0x4679d000,len(binary.read_bytes())));u.mem_write(0x4679d000,binary.read_bytes())
plan,blocks,masks=0x42000000,0x42000100,0x42000200
raw,sounds,fx=0x42010000,0x42020000,0x42021000
def wr(at,*values):u.mem_write(at,struct.pack('>'+str(len(values))+'I',*values))
def rd(at,n):return bytes(u.mem_read(at,n))
def setup():
 wr(plan,blocks,4,masks,1)
 for i,row in enumerate([(raw,722,722,6),(raw+4332,4385,4385,6),(sounds,100,100,6),(fx,5,5,6)]):wr(blocks+16*i,*row)
 wr(masks,fx,5,6);r.w32(0x40a7883c,0);r.w32(0x40a78874,0)
rng=random.Random(377);original=bytes(rng.randrange(256) for _ in range(30710));snd=bytes(rng.randrange(256) for _ in range(600));routing=bytes([0x82,1,2,3,4,0x84,6,7,8,9,0x81,11,12,13,14,0x90,16,17,18,19,0x88,21,22,23,24,0x80,26,27,28,29])
checks=0
for left in range(6):
 for right in range(left+1,6):
  setup();u.mem_write(raw,original);u.mem_write(sounds,snd);u.mem_write(fx,routing)
  before=(rd(raw,30710),rd(sounds,600),rd(fx,30));assert r.call('ts_exchange',plan,left,right)==1
  for t in range(6):
   source=right if t==left else left if t==right else t
   assert rd(raw+t*722,722)==original[source*722:(source+1)*722]
   assert rd(raw+4332+t*4385,4385)==original[4332+source*4385:4332+(source+1)*4385]
   assert rd(sounds+t*100,100)==snd[source*100:(source+1)*100]
   expected=bytearray(routing[source*5:(source+1)*5]);m=expected[0];d=((m>>left)^(m>>right))&1;expected[0]=m^(d<<left)^(d<<right)
   assert rd(fx+t*5,5)==expected
  assert rd(raw+30642,68)==original[30642:];assert r.call('ts_exchange',plan,left,right)==1
  assert (rd(raw,30710),rd(sounds,600),rd(fx,30))==before;checks+=1
print('PASS all15 track pairs: sequence722, locks4385, sound100, routing rows/columns; swap twice restores every byte')
for kind in range(8):
 setup();before=(rd(raw,30710),rd(sounds,600),rd(fx,30));left,right=1,4
 if kind==0:r.w32(0x40a7883c,1)
 if kind==1:r.w32(0x40a78874,1)
 if kind==2:left=6
 if kind==3:right=left
 if kind==4:wr(blocks+16,raw,4385,4385,6)
 if kind==5:wr(blocks+16,0,4385,4385,6)
 if kind==6:wr(blocks+16,raw+4332,4385,4386,6)
 if kind==7:wr(plan,blocks,65,masks,1)
 assert r.call('ts_exchange',plan,left,right)==0
 assert before==(rd(raw,30710),rd(sounds,600),rd(fx,30))
print('PASS transport, invalid pair, alias, null, bounds: rejected before changing any contents')
for left in range(6):
 for right in range(6):
  for mask in range(256):
   expected=mask^((((mask>>left)^(mask>>right))&1)*((1<<left)|(1<<right))) if left!=right else mask
   assert r.call('ts_bits',mask,left,right)==expected
print('PASS all256 masks and36 pairs: unrelated flags preserved')
setup();r.call(0x400615e8,raw,0)
markers=[]
for track in range(6):
 u.mem_write(raw+4332+4385*track+4352+11,b'\3')
 for step in (0,15,63):
  at=raw+722*track+2*step;u.mem_write(at,struct.pack('>H',1))
  at=raw+4332+4385*track+68*step+22;value=(track+1)*256+step
  u.mem_write(at,struct.pack('>H',value));markers.append((track,step,value))
assert r.call('ts_exchange',plan,1,4)==1
serial,loaded=0x42028000,0x42030000
assert r.call(0x4005ba0a,serial,raw,0)&255
assert r.call(0x4005b894,loaded,serial,0)&255
for track,step,value in markers:
 destination=4 if track==1 else 1 if track==4 else track
 assert rd(loaded+722*destination+2*step,2)==b'\0\1'
 assert rd(loaded+4332+4385*destination+68*step+22,2)==struct.pack('>H',value)
print('PASS native OS pattern encoder/decoder retains swapped trigs and lock values across all6 tracks')
(a.output/'proof.json').write_text(json.dumps(dict(pairs=checks,refusal_cases=8,mask_cases=9216,code_bytes=binary.stat().st_size,hardware_tested=False,UI_integrated=False),indent=2))
