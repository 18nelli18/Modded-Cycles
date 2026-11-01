"""Vrais noyaux : gains stables, rampes et alias delta/out, etat EMAC exact."""
from pathlib import Path
setup_text=Path(__file__).with_name('test_stock_machine_parity.py').read_text().split('peaks=[0]*6')[0]
exec(compile(setup_text,__file__,'exec'))
from unicorn import UC_HOOK_CODE
import os,subprocess,random
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/sparse-static-mix.S','-o',W/'mix.o');(W/'mix.ld').write_text('SECTIONS { .text '+hex(meta.get('sparse_static_mixer',{}).get('code',0x47000000))+' : { *(.text*) } }\nsm_resume = '+hex(meta['static_gain_mixer']['symbols']['sg_static6']+8)+';\n');run('ld','-T',W/'mix.ld','-o',W/'mix.elf',W/'mix.o');run('objcopy','-O','binary',W/'mix.elf',W/'mix.bin');sy={x[2]:int(x[0],16) for line in run('nm',W/'mix.elf').splitlines() if len(x:=line.split())==3};blob=(W/'mix.bin').read_bytes();assert len(blob)<6656;address=sy['sm_dispatch']
if meta.get('sparse_static_mixer'):assert bytes(e.uc.mem_read(address,len(blob)))==blob
else:e.uc.mem_map(0x47000000,0x10000);e.uc.mem_write(address,blob)
e.emac.install(emac.disasm(str(W/'mix.bin'),address,address,address+len(blob)))
at=meta['static_gain_mixer']['symbols']['sg_static6'];old_prefix=bytes.fromhex(meta['sparse_static_mixer']['original_prefix']) if meta.get('sparse_static_mixer') else bytes(e.uc.mem_read(at,8));new_prefix=b'\x4e\xf9'+struct.pack('>I',sy['sm_dispatch'])+b'\x4e\x71';e.uc.mem_write(at,b'\x4e\xf9'+struct.pack('>I',sy['sm_dispatch'])+b'\x4e\x71');e.uc.ctl_remove_cache(at,at+32)
sy['sg_sum6']=meta['static_gain_mixer']['symbols']['sg_sum6']
rng=random.Random(290);output=E.PARAMS+0x10000;input=output+0x1000;g=input+0x1000;delta=g+0x1000;rows=[]
regs=[getattr(C,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(C,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]
for n,native in [(6,meta['per_track_fx']['symbols']['mf_old_sum6'])]:
 # Reference du noyau stock, pas le crochet candidat du trampoline.
 e.uc.mem_write(native,bytes(stock.uc.mem_read(0x40056716 if n==6 else 0x40056698,8)));e.uc.ctl_remove_cache(native,native+32)
 assert bytes(e.uc.mem_read(native,4)).hex()==('4fefffe0' if n==6 else '4fefffd8')
 for kind in ('static','ramp','alias','input_alias','negative'):
  for case in range(64):
   output=input+((case%7)*4-4) if kind=='input_alias' else E.PARAMS+0x10000
   audio=struct.pack('>'+str(n*32)+'i',*[rng.randrange(-2**31,2**31) for _ in range(n*32)]);gains=struct.pack('>'+str(n)+'i',*[((-rng.randrange(1,2**31) if kind=='negative' else rng.randrange(-2**31,2**31)) if case>>t&1 else 0) for t in range(n)]);deltas=bytes(n*4) if kind!='ramp' else struct.pack('>'+str(n)+'i',*[rng.randrange(-10000,10000) for _ in range(n)]);d=output+(case%4)*4 if kind=='alias' else delta;initial=bytes([0xa5])*256;mode=(0x20,0xa0,0x30,0xb0)[case%4];acc=[rng.getrandbits(48) for _ in range(4)];seed=[rng.getrandbits(32) for _ in regs];result=[];cost=[]
   for variant,fn in enumerate((native,sy['sg_sum'+str(n)],sy['sg_sum'+str(n)])):
    e.uc.mem_write(at,old_prefix if variant==1 else new_prefix);e.uc.ctl_remove_cache(at,at+32)
    e.uc.mem_write(input,audio);e.uc.mem_write(g,gains);e.uc.mem_write(output,initial);e.uc.mem_write(d,deltas);e.emac.macsr=mode
    for i,value in enumerate(acc):e.emac.put_physical(i,value)
    for reg,value in zip(regs,seed):e.uc.reg_write(reg,value)
    count=[0];h=e.uc.hook_add(UC_HOOK_CODE,lambda *unused:count.__setitem__(0,count[0]+1));e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(fn,output,input,g,d);e.uc.hook_del(h);assert e.uc.reg_read(C.UC_M68K_REG_PC)==E.STOP
    assert [e.uc.reg_read(reg) for reg in regs]==seed
    result.append((bytes(e.uc.mem_read(output,256)),bytes(e.uc.mem_read(input,n*128)),bytes(e.uc.mem_read(g,n*4)),bytes(e.uc.mem_read(d,n*4)),e.emac.macsr,[e.emac.physical(i) for i in range(4)]));cost.append(count[0])
   assert result[0]==result[1]==result[2],(n,kind,case,[i for i,(x,y) in enumerate(zip(*result)) if x!=y])
   if kind=='static' and 2<=case.bit_count()<=3:assert cost[2]<cost[1],(case,cost)
   rows.append(dict(channels=n,kind=kind,stock=cost[0],before=cost[1],after=cost[2],mask=case))
  print('PASS',n,kind,'64 cases, PCM/gains/input/EMAC/ABI exact; instructions',cost,flush=True)
args.output.write_text(json.dumps(dict(cases=len(rows),code_bytes=len(blob),rows=rows,hardware_cycles=False,hardware_tested=False),indent=2)+'\n')
