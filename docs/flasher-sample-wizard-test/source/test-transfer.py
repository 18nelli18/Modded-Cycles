"""Transfert Sample Wizard : CYC natif et traduction SMP ; pas de vrai USB."""
import json,pathlib,struct
from unicorn import m68k_const as m
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/supermodel-sampler-prototype');t=json.load(open(p/'installer.json'));s={k:int(v,16) for k,v in t['symbols'].items()};stock=load_stock('firmware/model-cycles_OS1.13.syx');r=Rig(stock,t,{'writes':[],'symbols':{}});u=r.u;msg=0x93100000
pairs=dict(zip([0x10,0x11,0x12,0x20,0x21,0x22,0x23,0x30,0x31,0x32,0x36,0x40,0x41,0x42,0x46],[0x14,0x15,0x16,0x24,0x25,0x26,0x27,0x33,0x34,0x35,0x37,0x43,0x44,0x45,0x47]))
for mode in [0,1]:
 r.w32(s['id_mode'],mode)
 for kind in range(256):
  if mode and kind==9:continue
  u.mem_write(msg+8,bytes([kind]));expected=pairs.get(kind,kind) if mode else kind
  assert r.call(0x400949d8,msg)==kind
  assert r.call(s['rpc_type'],msg)==expected
  assert bytes(u.mem_read(msg+8,1))==bytes([expected])
  u.mem_write(msg+8,bytes([kind]));u.reg_write(m.UC_M68K_REG_A2,msg);u.reg_write(m.UC_M68K_REG_A7,STACK)
  u.emu_start(s['rpc_ot'],0x40094ca2,count=1000)
  expect=next((a|128 for a,b in pairs.items() if (b|128)==kind),kind) if mode else kind
  assert u.reg_read(m.UC_M68K_REG_D0)==expect
  assert u.reg_read(m.UC_M68K_REG_A7)==STACK+32
r.w32(s['id_mode'],1)
for query,pending in [('sample_file.interleaved_stereo_support',2),('unknown',1)]:
 data=bytes(5)+query.encode()+b'\0';u.mem_write(0x93101000,data);r.w32(msg+12,0x93101000);r.w32(msg+16,0x93101000+len(data));u.mem_write(msg+8,b'\x09')
 assert r.call(s['rpc_type'],msg)==2 and r.r32(s['qry_pend'])==pending
 u.mem_write(msg+8,b'\x82');u.reg_write(m.UC_M68K_REG_A2,msg);u.reg_write(m.UC_M68K_REG_A7,STACK);u.emu_start(s['rpc_ot'],0x40094ca2,count=1000)
 assert u.reg_read(m.UC_M68K_REG_D0)==0x89 and r.r32(s['qry_pend'])==0
 assert r.r32(STACK+80)==s['qry_yes' if pending==2 else 'qry_none']
print('PASS CYC : 256 requêtes/réponses inchangées ; SMP : 255 traductions bornées + requêtes stéréo/inconnue ; ABI pile conservée.')
from unicorn import UC_HOOK_CODE
rows=[];r.stubs[s['lm_add_row']]=lambda args:rows.append(args[:2]) or 0
u.hook_add(UC_HOOK_CODE,r.stub,begin=s['lm_add_row'],end=s['lm_add_row'])
u.reg_write(m.UC_M68K_REG_A2,0x93102000);u.reg_write(m.UC_M68K_REG_A7,STACK);u.emu_start(s['cfg_hook'],0x40032af4,count=1000)
assert rows==[(0x93102000,s['id_row'])],rows
print('PASS Device Config : seule la ligne Transfer ajoutée ; aucune page System/profilage TG.')
