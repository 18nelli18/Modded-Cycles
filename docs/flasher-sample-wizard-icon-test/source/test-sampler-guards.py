"""Les gardes sampler préservent les branches et appels des six machines stock."""
import subprocess,struct,pathlib
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
text=subprocess.check_output(['m68k-elf-nm','work/supermodel-sampler-prototype/guard.elf'],text=True);syms={row.split()[2]:int(row.split()[0],16) for row in text.splitlines() if len(row.split())==3 and row.split()[1]!='U'}
raw=pathlib.Path('work/supermodel-sampler-prototype/guard.bin').read_bytes();stock=load_stock('firmware/model-cycles_OS1.13.syx')
for machine in range(6):
 for active in [0,1]:
  target=0x400a7db0 if active else 0x400a7de0
  results=[]
  for entry in [0x400a7da8,syms['sampler_pre']]:
   r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw)
   for reg,val in [(mk.UC_M68K_REG_A6,0x93090000),(mk.UC_M68K_REG_A2,0x93091000),(mk.UC_M68K_REG_A3,0x93092000),(mk.UC_M68K_REG_D1,1234),(mk.UC_M68K_REG_D2,2),(mk.UC_M68K_REG_A7,STACK)]:u.reg_write(reg,val)
   u.mem_write(0x93091012,bytes([machine]));r.w32(0x93092000,active)
   u.emu_start(entry,target,count=1000);assert u.reg_read(mk.UC_M68K_REG_PC)==target
   results.append((r.r32(0x9309003c),u.reg_read(mk.UC_M68K_REG_D1),u.reg_read(mk.UC_M68K_REG_A7)))
  assert results[0]==results[1],(machine,active,results)
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw);calls=[]
 for at,n in [(0x93097000,'update'),(0x93097010,'render')]:
  r.stubs[at]=lambda args,n=n:calls.append((n,args)) or 0;u.mem_write(at,b'\x4e\x75');u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.w32(0x93095000+4*machine,0x93097000);r.w32(0x40118610+4*machine,0x93097010)
 for reg,val in [(mk.UC_M68K_REG_D4,machine),(mk.UC_M68K_REG_D6,0x93095000),(mk.UC_M68K_REG_D1,1234),(mk.UC_M68K_REG_D3,0x93096000),(mk.UC_M68K_REG_A2,0x93091000),(mk.UC_M68K_REG_A6,0x93090000),(mk.UC_M68K_REG_A7,STACK)]:u.reg_write(reg,val)
 u.emu_start(syms['sampler_dispatch'],0x400a7e24,count=1000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x400a7e24 and u.reg_read(mk.UC_M68K_REG_A7)==STACK
 assert [x[0] for x in calls]==['update','render'];assert calls[0][1][:3]==(1234,0x93090000,0x93091000);assert calls[1][1][:2]==(0x93096000,0x93090000)
 print('PASS stock pre/dispatch',machine,flush=True)
print('Prototype uniquement : hooks clavier/stockage et pruning encore nécessaires.')
for lane in range(6):
 for machine in range(6):
  r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw);r.w32(0x40a700c4,lane);r.w32(0x40a78888,0x930a0000);u.mem_write(0x930a0000+66+100*lane,bytes([machine]));event=0x930b0000
  for key in [4,6,9,13,14,16,31]:
   r.w32(event+12,key);r.w32(event+16,1);u.reg_write(mk.UC_M68K_REG_D1,0x12345678);u.reg_write(mk.UC_M68K_REG_A1,0x930c0000)
   assert r.call(syms['key_hook'],event)==key
   assert u.reg_read(mk.UC_M68K_REG_D1)==0x12345678 and u.reg_read(mk.UC_M68K_REG_A1)==0x930c0000
   assert r.r32(syms['set_held'])==0 and r.r32(syms['mod_used'])==0
print('PASS 252 événements clavier stock : code/registres conservés, aucun modificateur sampler.')
# Une touche commencée sur Wizard doit finir proprement sur une piste stock.
r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw);r.w32(0x40a700c4,0);r.w32(0x40a78888,0x930a0000);event=0x930b0000
u.mem_write(0x930a0042,b'\x06');r.w32(event+12,13);r.w32(event+16,1);r.call(syms['key_hook'],event);assert r.r32(syms['set_held'])==1
u.mem_write(0x930a0042,b'\x00');r.w32(event+16,0);r.call(syms['key_hook'],event);assert r.r32(syms['set_held'])==0
r.w32(syms['kh_eaten'],1);r.w32(event+12,5);r.call(syms['key_hook'],event);assert r.r32(syms['kh_eaten'])==0
print('PASS releases SETTINGS/MACHINES consommées après changement Wizard → piste stock ; aucun modificateur bloqué.')
