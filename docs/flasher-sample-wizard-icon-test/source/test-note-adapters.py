"""Capture sampler isolée : ABI du constructeur et notes live, sans slides TG."""
import subprocess,struct,pathlib
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
s={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output(['m68k-elf-nm','work/supermodel-sampler-prototype/guard.elf'],text=True).splitlines() if len(r.split())==3 and r.split()[1]!='U'}
raw=pathlib.Path('work/supermodel-sampler-prototype/guard.bin').read_bytes();stock=load_stock('firmware/model-cycles_OS1.13.syx')
regs=[m.UC_M68K_REG_D0,m.UC_M68K_REG_D1,m.UC_M68K_REG_D2,m.UC_M68K_REG_D3,m.UC_M68K_REG_A0,m.UC_M68K_REG_A2]
for lane in range(6):
 for step in [0,15,63]:
  for note in [0,60,127,255]:
   for fired in [0,1]:
    r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw);pattern=0x93100000;args=(lane,pattern,0x93110000,step,0x55,0x93120000);seen=[]
    r.stubs[0x400548ce]=lambda a:seen.append(a[:6]) or fired;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400548ce,end=0x400548ce)
    u.mem_write(pattern+722*lane+580+step,bytes([note]));u.mem_write(pattern+722*lane+712,b'\x40');u.mem_write(s['live_note'],bytes([52])*8)
    for i,reg in enumerate(regs):u.reg_write(reg,0x12340000+i)
    u.mem_write(STACK,struct.pack('>7I',STOP,*args));u.reg_write(m.UC_M68K_REG_A7,STACK);u.emu_start(s['sm_seq_capture'],STOP,count=1000)
    assert seen==[args] and u.reg_read(m.UC_M68K_REG_D0)==fired
    assert u.reg_read(m.UC_M68K_REG_A7)==STACK+28
    for i,reg in enumerate(regs[1:],1):assert u.reg_read(reg)==0x12340000+i
    expected=bytearray([52]*8)
    if fired:expected[lane]=64 if note==255 else note
    assert bytes(u.mem_read(s['live_note'],8))==bytes(expected)
print('PASS 144 captures séquence : six arguments/résultat/pile/registres, six pistes, notes extrêmes/héritage, aucun changement si trig absent.')
for lane in range(6):
 for note in [0,60,127]:
  for limit in [0,127]:
   r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw);u.mem_write(s['live_note'],bytes([52])*8)
   for reg,val in [(m.UC_M68K_REG_D0,limit),(m.UC_M68K_REG_D2,lane),(m.UC_M68K_REG_D3,note),(m.UC_M68K_REG_D1,0x12345678),(m.UC_M68K_REG_A0,0x93100000),(m.UC_M68K_REG_A7,STACK)]:u.reg_write(reg,val)
   target=0x40081742 if limit>=note else 0x4008190e;u.emu_start(s['sm_live_note_capture'],target,count=1000)
   assert u.reg_read(m.UC_M68K_REG_PC)==target and u.reg_read(m.UC_M68K_REG_A7)==STACK
   assert u.reg_read(m.UC_M68K_REG_D1)==0x12345678 and u.reg_read(m.UC_M68K_REG_A0)==0x93100000
   expected=bytearray([52]*8)
   if limit>=note:expected[lane]=note
   assert bytes(u.mem_read(s['live_note'],8))==bytes(expected)
print('PASS 36 captures live : branche native, registres/pile, six pistes indépendantes ; aucune installation Scale Lock TG.')
