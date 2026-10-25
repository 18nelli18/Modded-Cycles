"""QntM : setter natif, limites pattern, IRQ/ABI et navigation du sous-menu."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v143';stem='staging/all-features-polivoks-cpu-trim-test-'+v
m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());q=m['mute_quant']['symbols'];base=m['symbols'];r,s,h,log,files,key,turn,data,bind=fixture(stem);r.s.update(q)
r.u.reg_write(C.UC_M68K_REG_SR,0x2700)
r.u.mem_map(0x80000000,0x20000)
state=0x931a0000;pattern=0x931b0000
r.w32(0x40a7887c,pattern);r.w32(pattern+30706,7)
def length(n):r.u.mem_write(pattern+30662,struct.pack('>H',n))
def playing(n):r.w32(0x40a78874,n);r.w32(0x40a7883c,0)
def masks(a,b):r.w32(state+20,a);r.w32(state+24,b);r.call('mq_set',state)
def step(n):r.w32(0x40a788ac,n);r.call('mq_tick')
def actual():return r.r32(0x800017ac),r.r32(0x800017b0)
playing(1);length(16)
for index,count in enumerate((16,8,4,2,1)):
 r.w32(q['mq_enabled'],0);masks(0,0);r.w32(q['mq_division'],index);step(0);r.w32(q['mq_enabled'],1);step(0)
 masks(5,2);assert actual()==(0,0)
 for n in range(16//count):step(n);assert actual()==(0,0)
 step(16//count);assert actual()==(5,2)
 print('PASS native queued mute+solo at pattern fraction',count,flush=True)
# Un second geste peut annuler la demande ; STOP et Off appliquent immediatement.
r.w32(q['mq_enabled'],0);masks(0,0);step(0);r.w32(q['mq_enabled'],1);r.w32(q['mq_division'],4);step(0)
masks(1,0);masks(0,0);step(16);assert actual()==(0,0)
masks(3,4);playing(0);step(17);assert actual()==(3,4)
playing(1);r.w32(q['mq_enabled'],0);masks(6,1);assert actual()==(6,1)
# La nouvelle identite de pattern est une frontiere meme au meme numero de pas.
r.w32(q['mq_enabled'],1);step(2);masks(1,2);r.w32(pattern+30706,8);step(2);assert actual()==(1,2)
regs={getattr(C,'UC_M68K_REG_'+kind+str(i)):0x12345000+i for kind,ids in [('D',range(8)),('A',range(7))] for i in ids}
for reg,value in regs.items():r.u.reg_write(reg,value)
r.call('mq_irq')
assert all(r.u.reg_read(reg)==(r.r32(0x800017ac) if reg==C.UC_M68K_REG_D1 else value) for reg,value in regs.items())
print('PASS native setter Off/stop/cancel/pattern change and IRQ saved registers',flush=True)
# Utiliser les handlers reels de la chaine UI.
def event(code,flags):
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,100,code,flags,0));return r.call(q['mq_key'],EVENT)
r.w32(base['menu'],1);r.w32(base['row'],8);event(32,1);event(32,16);assert r.r32(q['mq_page'])==1
before=r.r32(q['mq_enabled']);event(32,1);event(32,16);assert r.r32(q['mq_enabled'])==1-before
r.delta=1;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,101,1,1,0));r.call(q['mq_encoder'],EVENT);assert r.r32(q['mq_row'])==1
event(32,1);event(32,16);assert r.r32(q['mq_edit'])==1
event(12,1);event(12,16);assert not r.r32(q['mq_edit']) and r.r32(q['mq_page'])
event(12,1);event(12,16);assert not r.r32(q['mq_page']) and r.r32(base['row'])==8
for offset in (248,332,416,500):assert f'clrb %a0@({offset})' not in (R/'output/firmware'/('governor-recovery-'+v)/'mq_sub.S').read_text()
print('PASS QntM open/toggle/division edit/BACK and two-row storage bounds',flush=True)
