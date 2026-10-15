"""Décodage stéréo sampler sans FX master TG ; frontières du mélange natif."""
import pathlib,struct,subprocess
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/supermodel-sampler-prototype')
s={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output(['m68k-elf-nm',str(p/'guard.elf')],text=True).splitlines() if len(r.split())==3 and r.split()[1]!='U'}
raw=(p/'guard.bin').read_bytes();stock=load_stock('firmware/model-cycles_OS1.13.syx')
for lane in range(-1,6):
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x80000000,0x20000);u.mem_write(0x401ab750,raw)
 left=[];right=[]
 for i in range(6):
  mid=[10000+i*100+j for j in range(32)];side=[-300+i*10+j for j in range(32)]
  u.mem_write(0x80001858+128*i,struct.pack('>32i',*mid));u.mem_write(s['sx_side']+128*i,struct.pack('>32i',*side))
  left.append([a+b for a,b in zip(mid,side)] if i==lane else mid)
  right.append([a-b for a,b in zip(mid,side)] if i==lane else mid)
  r.w32(s['sx_on']+4*i,int(i==lane))
 def forbid(uc,addr,size,user):raise AssertionError('FX master TG appelé')
 u.hook_add(UC_HOOK_CODE,forbid,begin=s['rtg_fxpass'],end=s['rtg_fxpass'])
 for bus,expected in [(0x8000b990,left),(0x8000b994,right),(0x93010000,right)]:
  u.mem_write(STACK,struct.pack('>5I',0x9300f000,bus,6,0x93011000,0x93012000))
  u.reg_write(m.UC_M68K_REG_A7,STACK)
  for reg in [m.UC_M68K_REG_D2,m.UC_M68K_REG_D3,m.UC_M68K_REG_D4,m.UC_M68K_REG_A2]:u.reg_write(reg,0x12345678)
  u.emu_start(s['sx_mix'],0x40056618,count=10000)
  assert u.reg_read(m.UC_M68K_REG_PC)==0x40056618
  # Le prologue natif a réservé 40 octets et sauvé les registres.
  assert u.reg_read(m.UC_M68K_REG_A7)==STACK-40
  assert bytes(u.mem_read(STACK+4,16))==struct.pack('>4I',bus,6,0x93011000,0x93012000)
  for reg in [m.UC_M68K_REG_D2,m.UC_M68K_REG_D3,m.UC_M68K_REG_D4,m.UC_M68K_REG_A2]:assert u.reg_read(reg)==0x12345678
  for i in range(6):assert struct.unpack('>32i',u.mem_read(0x80001858+128*i,128))==tuple(expected[i]),(lane,bus,i)
 assert all(r.r32(s['sx_on']+4*i)==0 for i in range(6))
print('PASS stéréo six pistes + aucun sampler : PCM gauche/droite, mono intact, ABI native et aucun FX master TG.')

for stereo in [False,True]:
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw);calls=[]
 r.w32(s['sx_on']+20,int(stereo))
 r.stubs[0x40056d9c]=lambda args:calls.append(args[0]) or 0
 u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40056d9c,end=0x40056d9c)
 u.hook_add(UC_HOOK_CODE,forbid,begin=s['rtg_audio'],end=s['rtg_audio'])
 r.call(s['sx_gain'],0x93018000)
 assert calls==([s['sx_side'],0x93018000] if stereo else [0x93018000]),calls
print('PASS gain : appel natif conservé ; gain side seulement si stéréo, aucun retrigger global TG.')
