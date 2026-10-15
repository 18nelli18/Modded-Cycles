"""Démarrage réel du candidat quinze machines, sans Model-TG sélectionné.

Exécute décompression/initialisation et cache LRU ; MOVEC est intercepté car
Unicorn ne simule pas le cache physique. Ne prétend pas simuler l'audio matériel.
"""
import json,struct,pathlib,hashlib,sys
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
import build,syntakt,gen_syntakt_engines as gs
P=pathlib.Path('work/sample-wizard-main');cat=json.load(open(P/(sys.argv[1] if len(sys.argv)>1 else 'combined.json')));w=next(t for t in cat if t['id']=='sample-wizard');e=next(t for t in cat if t['id']=='wizard-engines-all-wave');stock=load_stock('firmware/model-cycles_OS1.13.syx');st=syntakt.dsp_image('firmware/Syntakt_OS1.42.syx');packed=P/'private-packed-fixture.json'
if len(cat)>2 and packed.exists():
 fixtures=json.load(open(packed))
 for t in cat:
  if t.get('append',{}).get('compress'):t['append']['compressed_hex']=fixtures[t['id']]
image,_=build.apply_writes(stock,cat);payload,_=build.build_payload(cat,stock,'firmware/Syntakt_OS1.42.syx');full=bytes(image)+payload
r=Rig(full,{'writes':[]},{'writes':[],'symbols':w['symbols']});u=r.u;u.mem_map(0x46700000,0x100000);u.mem_map(0x80000000,0x200000)
for lo,hi,to in gs.CY_SRAM_INIT:u.mem_write(to,full[lo-build.BASE:hi-build.BASE])
ranges=[(build.BASE,full)]+[(int(t['append']['dest'],16),build.payload_runtime(t,stock,st)) for t in cat if t.get('append')]
cache=[]
def skip(uc,pc,size,user):cache.append(pc);uc.reg_write(m.UC_M68K_REG_PC,pc+4)
for pc in {at+i for at,b in ranges for i in range(0,len(b)-3,2) if b[i:i+2]==b'\x4e\x7b'}:u.hook_add(UC_HOOK_CODE,skip,begin=pc,end=pc)
for at in [0x4019b590,0x401a7750,0x40210000,0x41000000,0x423380a0]:u.mem_write(at,b'\xa5'*16)
u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(m.UC_M68K_REG_A7,STACK);u.emu_start(0x40000530,0x4000053a,count=45000000)
assert u.reg_read(m.UC_M68K_REG_PC)==0x4000053a,hex(u.reg_read(m.UC_M68K_REG_PC))
assert u.reg_read(m.UC_M68K_REG_A7)==STACK-4
for at in [0x4019b590,0x401a7750,0x40210000,0x41000000,0x423380a0]:assert bytes(u.mem_read(at,16))==bytes(16),hex(at)
raw=build.payload_runtime(w,stock,st);got=bytes(u.mem_read(int(w['append']['dest'],16),len(raw)));diff=[i for i,(a,b) in enumerate(zip(raw,got)) if a!=b];print('diff Wizard',len(diff),[hex(int(w['append']['dest'],16)+i) for i in diff[:16]],flush=True);assert got==raw
# Seuls les constructeurs moteurs écrivent leurs variables ; les plages de
# code d'origine doivent être copiées exactement après décompression.
rt=build.payload_runtime(e,stock,st);dest=int(e['append']['dest'],16)
for part in e['append']['parts']:
 at=int(part['dest'],16)
 if 'hex' in part and part['hex'] and at!=0x46733800:
  expected=bytes.fromhex(part['hex']);got=bytes(u.mem_read(at,len(expected)))
  assert got==expected,hex(at)
r.call(0x4007929c);nodes=[];p=r.r32(0x401eb894);prev=0
while p:
 assert p not in nodes and r.r32(p+16)==prev
 nodes.append(p);prev=p;p=r.r32(p+12)
assert nodes==[0x401eb750+20*i for i in range(w['cache_blocks'],16)]
assert bytes(u.mem_read(int(w['append']['dest'],16),len(raw)))==raw
assert r.r32(r.s['av_wave_machine'])==14
ck=next((t for t in cat if t['id']=='chord-keys-supermodel'),None)
if ck:
 ckraw=build.payload_runtime(ck,stock,st)
 assert bytes(u.mem_read(int(ck['append']['dest'],16),len(ckraw)))==ckraw,'ChordKeys non chargé'
 assert r.r32(r.s['av_perf_on'])==1 and r.r32(r.s['av_ui_mods'])==1

(P/'boot-proof.json').write_text(json.dumps(dict(sha256=hashlib.sha256(full).hexdigest(),free_cache_blocks=len(nodes),cache_instructions=len(cache),model_tg_required=False)))
print('PASS démarrage natif quinze machines : décompression, BSS et code Wizard préservés, moteurs copiés, cache LRU borné, neuf blocs disque libres avec ChordKeys ; cache physique non simulé.')
