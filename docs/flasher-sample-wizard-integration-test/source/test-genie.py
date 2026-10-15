"""Menu réellement placé : 21 lignes, entrée Générer, intro bornée à 750 ticks."""
import json,struct
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig,OBJ
from chord_keys_pr87 import load_stock
import build
c=json.load(open('work/sample-wizard-main/controls.json'));sg=next(t for t in c if t['id'].startswith('scale-gen'));tg=c[0]
image,_=build.apply_writes(load_stock('firmware/model-cycles_OS1.13.syx'),sorted(c,key=lambda t:t['order']))
r=Rig(load_stock('firmware/model-cycles_OS1.13.syx'),tg,{'writes':[],'symbols':sg['symbols']});r.u.mem_write(build.BASE,bytes(image))
for row,old in enumerate([20]+list(range(19))+[21]):
 # ABI du petit helper : d0 est le paramètre/retour, pas la pile.
 from unicorn.m68k_const import UC_M68K_REG_D0
 r.u.reg_write(UC_M68K_REG_D0,row);assert r.call('sg_map_row')==old
 r.u.reg_write(UC_M68K_REG_D0,old);assert r.call('sg_unmap_row')==row
r.call('sg_open');assert r.r32(r.s['sg_row'])==0
at=r.s['sg_tick'];w=next(w for w in sg['writes'] if w['off']+0x40000400==at);b=bytes.fromhex(w['new']);assert b[-6:-4]==b'\x4e\xf9';led=int.from_bytes(b[-4:],'big');r.stubs[led]=lambda a:0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=led,end=led)
clock=int(tg['symbols']['blk_clk'],16);r.w32(r.s['sg_intro_time'],1000);r.w32(r.s['sg_intro'],1)
r.w32(clock,1749);r.call('sg_tick');assert r.r32(r.s['sg_intro'])==1
r.w32(clock,1750);r.call('sg_tick');assert r.r32(r.s['sg_intro'])==0
print('PASS menu installé : Générer premier et sélectionné, 21 conversions inversibles, intro active à 749/fermée à 750 ticks.')
