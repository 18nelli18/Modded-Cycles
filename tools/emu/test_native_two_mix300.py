"""Deux passes natives : alias, rampes, EMAC et registres, sans estimation de cycles."""
from pathlib import Path
setup_text=Path(__file__).with_name('test_stock_machine_parity.py').read_text().split('peaks=[0]*6')[0]
exec(compile(setup_text,__file__,'exec'))
from unicorn import UC_HOOK_CODE
import os,subprocess,random
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(t,*a):return subprocess.check_output([cross+t+'.exe',*map(str,a)],text=True)
run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/native-two-mix300.S','-o',W/'two.o');(W/'two.ld').write_text('SECTIONS { .text 0x47000000 : { *(.text*) } }\ntm_native = 0x400a9884;\n');run('ld','-T',W/'two.ld','-o',W/'two.elf',W/'two.o');run('objcopy','-O','binary',W/'two.elf',W/'two.bin');sy={v[2]:int(v[0],16) for line in run('nm',W/'two.elf').splitlines() if len(v:=line.split())==3};blob=(W/'two.bin').read_bytes();e.uc.mem_map(0x47000000,0x10000);e.uc.mem_write(0x47000000,blob);e.emac.install(emac.disasm(str(W/'two.bin'),0x47000000,0x47000000,0x47000000+len(blob)))
# Les memes instructions natives, dans le meme moteur EMAC que le candidat.
f=W/'native-two.bin';f.write_bytes(e.uc.mem_read(0x400a9884,0xc8));e.emac.install(emac.disasm(str(f),0x400a9884,0x400a9884,0x400a994c))
rng=random.Random(300);base=E.PARAMS+0x10000;regs=[getattr(C,'UC_M68K_REG_D'+str(i)) for i in range(8)]+[getattr(C,'UC_M68K_REG_A'+str(i)) for i in range(7)];rows=[]
for kind in ('separate','inplace0','inplace1','input_alias','same_gain','overlap_gain','output_gain','output_descriptor','descriptor_gain'):
 for case in range(64):
  raw=bytearray(rng.getrandbits(8) for _ in range(4096));a,b,out,desc,state=base,base+256,base+512,base+768,base+1024
  i,j=(0,16) if kind!='same_gain' else (0,0)
  if kind=='inplace0':out=a+(case%4)*4
  if kind=='inplace1':out=b+(case%4)*4
  if kind=='input_alias':b=a+(case%8)*4
  if kind=='overlap_gain':j=4
  if kind=='output_gain':out=state+8+(case%4)*4
  if kind=='output_descriptor':desc=out+(case%16)*4
  if kind=='descriptor_gain':desc=state+24-(case%2)*4
  struct.pack_into('>2I',raw,desc-base,i,j)
  # Valeurs extremes de gain et rampes, y compris l overflow32bits natif.
  if kind not in ('descriptor_gain',):
   for index in {i,j}:
    for off in (8,24):struct.pack_into('>I',raw,state-base+4*index+off,rng.getrandbits(32))
  if kind in ('output_descriptor','descriptor_gain'):
   raw[a-base:a-base+132]=bytes(132);raw[b-base:b-base+132]=bytes(132)
   if kind=='descriptor_gain':
    for index in {i,j}:struct.pack_into('>I',raw,state-base+4*index+8,int.from_bytes(raw[state-base+4*index+24:state-base+4*index+28],'big'))
  status=(0x20,0xa0,0x30,0xb0,0,0x40,0x60,0xe0)[case%8];acc=[rng.getrandbits(48) for _ in range(4)];acc[0]=0 if kind in ('output_descriptor','descriptor_gain') else acc[0];seed=[rng.getrandbits(32) for _ in regs];results=[];counts=[]
  for fn in (0x400a9884,sy['tm_render']):
   e.uc.mem_write(base,bytes(raw));e.emac.macsr=status
   for k,v in enumerate(acc):e.emac.put_physical(k,v)
   for reg,v in zip(regs,seed):e.uc.reg_write(reg,v)
   n=[0];h=e.uc.hook_add(UC_HOOK_CODE,lambda *x:n.__setitem__(0,n[0]+1));e.uc.reg_write(C.UC_M68K_REG_SR,0x2715)
   e.call(fn,a,b,out,desc,state);e.uc.hook_del(h)
   results.append((bytes(e.uc.mem_read(base,len(raw))),[e.uc.reg_read(reg) for reg in regs],e.uc.reg_read(C.UC_M68K_REG_SR),e.emac.macsr,[e.emac.physical(k) for k in range(4)]));counts.append(n[0])
  assert results[0]==results[1],(kind,case,[k for k,(x,y) in enumerate(zip(*results)) if x!=y])
  if kind=='separate':assert counts[1]<counts[0],counts
  rows.append(dict(kind=kind,case=case,before=counts[0],after=counts[1]))
 print('PASS',kind,64,'cases; instructions',counts,flush=True)
args.output.write_text(json.dumps(dict(cases=len(rows),code_bytes=len(blob),rows=rows,emac_and_ABI_exact=True,hardware_cycles=False,hardware_tested=False),indent=2)+'\n')
