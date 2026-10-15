"""Tables sampler statiques : six icônes stock inchangées, septième bornée."""
import pathlib,subprocess,struct,random
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/supermodel-sampler-prototype');s={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output(['m68k-elf-nm',str(p/'guard.elf')],text=True).splitlines() if len(r.split())==3 and r.split()[1]!='U'}
raw=(p/'guard.bin').read_bytes();stock=load_stock('firmware/model-cycles_OS1.13.syx');rng=random.Random(909)
r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_write(0x401ab750,raw)
old=[]
for i,root in enumerate([0x40fe32cc,0x40fe384c]):
 data=rng.randbytes(168);old.append(data);addr=0x93100000+i*0x1000;u.mem_write(addr,data)
 for k,val in enumerate([addr,addr+168,addr+168]):r.w32(root+4*k,val)
def forbid(uc,addr,size,user):raise AssertionError('allocation dessin inattendue')
u.hook_add(UC_HOOK_CODE,forbid,begin=0x40080064,end=0x40080064)
for repeat in range(2):
 u.mem_write(STACK,struct.pack('>2I',0x9300f000,0x93110000));u.reg_write(m.UC_M68K_REG_A7,STACK)
 u.reg_write(m.UC_M68K_REG_D2,0x12345678);u.reg_write(m.UC_M68K_REG_A2,0x23456789)
 u.emu_start(s['sampler_lazy_init_trampoline'],0x400a24ca,count=10000)
 assert u.reg_read(m.UC_M68K_REG_PC)==0x400a24ca
 assert u.reg_read(m.UC_M68K_REG_A7)==STACK
 assert u.reg_read(m.UC_M68K_REG_D2)==0x12345678 and u.reg_read(m.UC_M68K_REG_A2)==0x23456789
 for i,(root,table,pixels,palette,width,height) in enumerate([(0x40fe32cc,'sm_icons_a','sampler_icon_a_pixels',0x4016ac78,48,33),(0x40fe384c,'sm_icons_b','sampler_icon_b_pixels',0x4017c20c,34,34)]):
  dest=s[table];assert [r.r32(root+4*k) for k in range(3)]==[dest,dest+196,dest+196]
  assert bytes(u.mem_read(dest,168))==old[i]
  assert struct.unpack('>7I',u.mem_read(dest+168,28))==(0x401117c8,width,height,2,s[pixels],palette,0)
 assert r.r32(s['mp_obj'])==0x93110000
print('PASS menu machine : six icônes stock intactes, deux tables sampler bornées, réouverture idempotente, ABI et aucune allocation.')
for old_fn,new_fn,values in [(0x4004df5c,'table_lookup_a_fixed',range(1,7)),(0x4004df76,'table_lookup_b_fixed',range(6))]:
 for value in values:
  before=r.call(old_fn,value);after=r.call(s[new_fn],value);assert before==after,(new_fn,value,hex(before),hex(after))
assert r.call(s['table_lookup_a_fixed'],7)==r.call(0x4004df5c,1)
assert r.call(s['table_lookup_b_fixed'],6)==r.call(0x4004df76,0)
print('PASS descripteurs : 12 index stock identiques au vrai OS ; septième slot borné sur un descripteur initialisé.')
# Le trampoline de commit rejoue uniquement le prologue natif.
u.mem_write(STACK,struct.pack('>I',0x9300f000));u.reg_write(m.UC_M68K_REG_A7,STACK);u.reg_write(m.UC_M68K_REG_A6,0x93112000)
u.emu_start(s['log_trampoline'],0x4001407a,count=100)
assert u.reg_read(m.UC_M68K_REG_PC)==0x4001407a
assert 'sampler_track_table' not in s and 'update_sampler_table' not in s
print('PASS aucun code/table diagnostic de suivi des pistes lié au sampler.')
