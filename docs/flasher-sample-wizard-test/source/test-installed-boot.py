"""Installation réelle Sample Wizard : boot/BSS, réserve cache et routage.

MOVEC cache physique non simulé ; arrêt à la reprise native du boot.
"""
import pathlib,json,struct
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK
from chord_keys_pr87 import load_stock
import build
p=pathlib.Path('work/supermodel-sampler-prototype');t=json.load(open(p/'installer.json'));stock=load_stock('firmware/model-cycles_OS1.13.syx');s={k:int(v,16) for k,v in t['symbols'].items()}
r=Rig(stock,t,{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x80000000,0x20000)
raw=build.payload_runtime(t,stock,None);code=raw[0x1610:];cache=[]
def skip_cache(uc,pc,size,user):cache.append(pc);uc.reg_write(m.UC_M68K_REG_PC,pc+4)
for i in range(0,len(code)-3,2):
 if code[i:i+2]==b'\x4e\x7b':u.hook_add(UC_HOOK_CODE,skip_cache,begin=0x401ab750+i,end=0x401ab750+i)
for at in [0x4019b590,0x401a7750,0x401ab740,0x40210000,0x41000000,0x423380a0]:u.mem_write(at,b'\xa5'*16)
u.reg_write(m.UC_M68K_REG_A7,STACK);u.emu_start(0x40000530,0x4000053a,count=30000000)
assert u.reg_read(m.UC_M68K_REG_PC)==0x4000053a and u.reg_read(m.UC_M68K_REG_A7)==STACK-4
assert cache
for at in [0x4019b590,0x401a7750,0x401ab740,0x40210000,0x41000000,0x423380a0]:assert bytes(u.mem_read(at,16))==bytes(16),hex(at)
assert bytes(u.mem_read(0x401ab750,len(code)))==code
assert bytes(u.mem_read(0x401a7750,16384))==bytes(16384)
before=bytes(u.mem_read(0x401ab750,len(code)));r.call(0x4007929c);nodes=[];node=r.r32(0x401eb894);prev=0
while node:
 assert node not in nodes and r.r32(node+16)==prev
 nodes.append(node);prev=node;node=r.r32(node+12)
assert nodes==[0x401eb750+20*i for i in range(t['cache_blocks'],16)]
assert bytes(u.mem_read(0x401ab750,len(code)))==before
for at,name in [(0x400ff9cc,'tick_hook'),(0x400ff9b8,'led_hook'),(0x400a7daa,'sampler_pre'),(0x400a7e04,'sampler_dispatch'),(0x4007240e,'key_hook'),(0x4005982c,'sx_gain'),(0x40056612,'sx_mix')]:assert r.r32(at)==s[name],(hex(at),name)
print('PASS vrai raccord boot + cache LRU : BSS/tampon FS zéro, code préservé, dix blocs disque libres, routage installé correct ; cache physique non simulé.')
