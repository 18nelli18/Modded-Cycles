"""Routage natif partagé : six pistes × quinze machines, note et navigateur.

Exécute les wrappers installés ; intercepte seulement les corps de chargement
pour contrôler le destinataire et l'ABI, sans lecture de samples matériels.
"""
import json,pathlib,struct
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
import build,syntakt
P=pathlib.Path('work/sample-wizard-main');w,e=json.load(open(P/'combined.json'));stock=load_stock('firmware/model-cycles_OS1.13.syx');s={k:int(v,16) for k,v in w['symbols'].items()};g=json.load(open(P/'wave.json'))['gsyms']
r=Rig(stock,w,{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x46700000,0x100000)
image,_=build.apply_writes(stock,[w,e]);u.mem_write(build.BASE,bytes(image));u.mem_write(0x46700000,build.payload_runtime(e,stock,syntakt.dsp_image('firmware/Syntakt_OS1.42.syx')))
kit=0x93120000;r.w32(0x40a78888,kit);targets=[]
def catch(uc,pc,size,user):
 targets.append(pc);sp=uc.reg_read(m.UC_M68K_REG_A7);assert sp==STACK
 assert tuple(struct.unpack('>6I',uc.mem_read(sp+4,24)))==args
 uc.reg_write(m.UC_M68K_REG_PC,STOP)
for at in [s['pad_load_hook'],s['preset_fail_hook'],g['wt_note'],g['wt_yes']]:u.hook_add(UC_HOOK_CODE,catch,begin=at,end=at)
for lane in range(6):
 for machine in range(15):
  u.mem_write(kit+100*lane+66,bytes([machine]))
  for entry,wavefn,stockfn in [('av_pad_hook','wt_note','pad_load_hook'),('av_yes_hook','wt_yes','preset_fail_hook')]:
   args=(lane,0x93140000,lane,0xabcdef,0x1234,0x5678);u.mem_write(STACK,struct.pack('>7I',STOP,*args));u.reg_write(m.UC_M68K_REG_A7,STACK)
   sentinels={reg:0x12345000+i for i,reg in enumerate([m.UC_M68K_REG_D1,m.UC_M68K_REG_D2,m.UC_M68K_REG_D3,m.UC_M68K_REG_D4,m.UC_M68K_REG_A1,m.UC_M68K_REG_A2,m.UC_M68K_REG_A3])}
   for reg,value in sentinels.items():u.reg_write(reg,value)
   u.emu_start(s[entry],STOP,count=1000)
   assert targets[-1]==(g[wavefn] if machine==14 else s[stockfn]),(lane,machine,entry)
   assert all(u.reg_read(reg)==value for reg,value in sentinels.items())
assert len(targets)==180
# Une identité et un buffer message communs, trois drapeaux WAVE indépendants.
assert g['smp_mode']==s['id_mode'] and g['wt_msg']==s['msg_buf']
for symbol,target in [('av_wave_tick','wt_tick'),('av_wave_note','wt_note'),('av_wave_yes','wt_yes')]:assert r.r32(s[symbol])==g[target]
assert r.r32(s['av_wave_machine'])==14
assert int(w['symbols']['reserved_end'],16)<0x401c3750
print('PASS 180 routages installés : 6 pistes × 15 machines × note/YES ; pile, arguments et registres conservés ; identité/message uniques ; réserve Wizard bornée.')
