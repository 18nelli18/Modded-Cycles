"""Variantes MD navigateur : bootstrap natif, code/tables, masques et ABI dispatch.
Les fichiers ROM et SYX restent uniquement des entrees locales. Note203.
"""
from pathlib import Path
import argparse,sys,json,struct
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R.parent/'boot-check-deps'),str(R/'tools/emu'),str(R/'tools')]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--variants',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
from test_seq_gen_menu import Rig,STACK
from unicorn import UC_HOOK_CODE,m68k_const as C
bc.ROOT=a.work/'browser-native-cache';m=json.loads((a.work/'probe/BUILD.json').read_text());s=m['symbols'];base_module=(a.work/'probe/md.bin').read_bytes();rows=[]
for path in sorted(a.variants.glob('mask-*.syx')):
 mask=int(path.stem.split('-')[1],16);image,mem=bc.boot(path);base,runtime=mem[0]
 expected=bytearray(base_module);struct.pack_into('>I',expected,s['md_mask']-m['code'],mask)
 assert runtime[m['code']-base:m['code']-base+len(expected)]==expected
 assert not any(runtime[m['bss']-base:m['bss']-base+m['bss_bytes']])
 r=Rig(image,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}})
 for at,data in mem:r.u.mem_map(at,len(data));r.u.mem_write(at,data)
 dispatches=0
 for machine in range(30):
  enabled=machine<6 or machine<28 and bool(mask&(1<<(machine-6)))
  assert bool(r.call('md_enabled',machine))==enabled
  out=0x931a0000;r.u.mem_write(out,b'\x5a'*128);r.u.reg_write(C.UC_M68K_REG_A7,STACK);r.u.reg_write(C.UC_M68K_REG_D0,27);r.u.reg_write(C.UC_M68K_REG_D1,0x12345678);r.u.reg_write(C.UC_M68K_REG_D3,out);r.u.reg_write(C.UC_M68K_REG_D4,machine)
  stops=[]
  def stop(u,pc,*args):stops.append(pc);u.emu_stop()
  hooks=[r.u.hook_add(UC_HOOK_CODE,stop,begin=pc,end=pc) for pc in (0x46788700,0x400a7e24)]
  r.u.emu_start(s['md_dispatch'],0,count=1000)
  for h in hooks:r.u.hook_del(h)
  assert stops==[0x46788700 if enabled else 0x400a7e24],(mask,machine,stops)
  assert r.u.reg_read(C.UC_M68K_REG_A7)==STACK and r.u.reg_read(C.UC_M68K_REG_D1)==0x12345678
  assert bytes(r.u.mem_read(out,128))==(b'\x5a'*128 if enabled else bytes(128));dispatches+=1
 rows.append(dict(file=path.name,mask=mask,native_boot=True,module_and_all_sine_entries_exact=True,BSS_zero=True,dispatches=dispatches,disabled_voices_silent=True));print('PASS native browser variant',hex(mask),'code/tables/BSS and30dispatches',flush=True)
a.output.write_text(json.dumps(dict(cases=rows,hardware_tested=False),indent=2)+'\n')
