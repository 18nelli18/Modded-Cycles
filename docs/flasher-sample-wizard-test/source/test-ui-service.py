"""Service UI commun : IPL, cadence, réentrance, clavier natif conservé.

Les services fichier sont remplacés aux frontières ; cette preuve ne valide
pas le système de fichiers ni le contenu des fichiers utilisateur.
"""
import pathlib,subprocess
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/supermodel-sampler-prototype')
s={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output(['m68k-elf-nm',str(p/'guard.elf')],text=True).splitlines() if len(r.split())==3 and r.split()[1]!='U'}
raw=(p/'guard.bin').read_bytes();stock=load_stock('firmware/model-cycles_OS1.13.syx')
services=['atk_watch','gran_watch','slice_watch','name_probe','load_pending','pl_step','nm_step','nm_tick','rs_watch']
for entry in ['tick_hook','led_hook']:
 for ipl in range(8):
  r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x80000000,0x20000);u.mem_write(0x401ab750,raw);calls=[]
  for name in services:
   r.stubs[s[name]]=lambda args,name=name:calls.append(name) or 0
   u.hook_add(UC_HOOK_CODE,r.stub,begin=s[name],end=s[name])
  r.stubs[0x4001a0d2]=lambda args:calls.append(('native',args[:2])) or 73
  u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4001a0d2,end=0x4001a0d2)
  u.reg_write(m.UC_M68K_REG_SR,0x2000|(ipl<<8));r.w32(0x8000184c,5)
  result=r.call(s[entry],11,22)
  expected=([('native',(11,22))] if entry=='tick_hook' else [])+(services if ipl==0 else [])
  assert calls==expected,(entry,ipl,calls)
  if entry=='tick_hook':assert result==73
  assert r.r32(s['ld_busy'])==0
  if ipl:assert r.r32(s['lh_clock'])==0
  else:
   # L'autre entrée au même bloc ne répète pas le travail fichier.
   calls.clear();other='led_hook' if entry=='tick_hook' else 'tick_hook'
   r.call(s[other],11,22)
   assert calls==([('native',(11,22))] if other=='tick_hook' else [])
   # Nouvelle cadence : un service déjà occupé ne réentre pas.
   calls.clear();r.w32(0x8000184c,6);r.w32(s['ld_busy'],1)
   r.call(s['led_hook']);assert calls==[] and r.r32(s['ld_busy'])==1
print('PASS 16 entrées UI/IPL : aucun service en interruption, clavier natif conservé, dédoublonnage et réentrance.')
