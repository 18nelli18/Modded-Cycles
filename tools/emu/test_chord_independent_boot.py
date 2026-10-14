#!/usr/bin/env python3
"""Boot Chord seul : décompression puis clear RAM réel, sans TG/Banque.

Cache MOVEC non simulé. Arrêt avant reprise native 0x4000053a ; aucun
matériel ni audio n'est simulé par cette preuve ciblée du bootstrap.
"""
import argparse,json,pathlib,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--tweak',required=True);p.add_argument('--tg');p.add_argument('--engine');p.add_argument('--syntakt');a=p.parse_args()
 stock=main_os_from_syx(a.cycles);t=json.loads(pathlib.Path(a.tweak).read_text())
 tg=json.loads(pathlib.Path(a.tg).read_text()) if a.tg else None
 engine=json.loads(pathlib.Path(a.engine).read_text()) if a.engine else None
 assert t['requires']==([tg['id']] if tg else [])+([engine['id']] if engine else [])
 selected=([tg] if tg else [])+([engine] if engine else [])+[t]
 image,_=build.apply_writes(stock,selected)
 # Même sérialisation du builder ; réserve fixe uniquement dans le prototype.
 st=None
 if engine and engine.get('append',{}).get('syntakt'):
  import syntakt
  st=syntakt.dsp_image(a.syntakt)
 extra=bytearray()
 for recipe in selected:
  ap=recipe.get('append')
  if not ap:continue
  at=int(ap['at'],16);end=build.BASE+len(stock)+len(extra)
  if end<at:
   assert recipe is t and ap.get('zero_pad_from')==hex(build.BASE+len(stock)) and at<build.END_LIMIT
   extra+=bytes(at-end)
  assert build.BASE+len(stock)+len(extra)==at
  extra+=build.payload_image(recipe,build.payload_runtime(recipe,stock,st))
 r=Rig(bytes(image)+extra,{'writes':[]},{'writes':[],'symbols':t['symbols']});u=r.u
 u.mem_map(0x43000000,0x800000);u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000)
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
 events=[]
 def cache(u,pc,size,data):
  if bytes(u.mem_read(pc,2))==b'\x4e\x7b':events.append(pc);u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 u.hook_add(UC_HOOK_CODE,cache)
 # Le clear doit atteindre la fin BSS ; son exception ne couvre que Chord.
 sentinels=[0x40210000,0x41000000,0x423380a0]
 source=int(t['append']['at'],16);source_end=source+len(bytes.fromhex(t['append']['compressed_hex']))
 assert all(not (at<source_end and source<at+16) for at in sentinels)
 for at in sentinels:u.mem_write(at,b'\xa5'*16)
 raw=bytes.fromhex(t['append']['parts'][0]['hex']);dest=int(t['append']['dest'],16)
 try:
  u.emu_start(0x40000530,int(t['symbols']['chord_clear'],16),count=12000000)
  assert u.reg_read(mk.UC_M68K_REG_PC)==int(t['symbols']['chord_clear'],16),'limite instructions avant clear'
  actual=bytes(u.mem_read(dest,len(raw)))
  assert actual==raw,('décompression',next((i for i,(x,y) in enumerate(zip(actual,raw)) if x!=y),None))
  u.emu_start(int(t['symbols']['chord_clear'],16),0x4000053a,count=30000000)
 except Exception:
  pc=u.reg_read(mk.UC_M68K_REG_PC)
  print('boot échec PC',hex(pc),'octets',bytes(u.mem_read(pc,16)).hex(),flush=True);raise
 assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a
 assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-(4 if tg or engine else 0)
 assert bytes(u.mem_read(dest,len(raw)))==raw
 for at in sentinels:assert bytes(u.mem_read(at,16))==bytes(16),hex(at)
 assert len(events)>=2
 if tg:
  begin=int(tg['symbols']['blob_start'],16);end=int(tg['symbols']['reserved_end'],16)
  assert bytes(u.mem_read(begin,end-begin))==(bytes(image)+extra)[begin-build.BASE:end-build.BASE]
 before=bytes(u.mem_read(dest,len(raw)))
 r.call(0x4007929c);nodes=[];node=r.r32(0x401eb894);previous=0
 while node:
  assert node not in nodes and r.r32(node+16)==previous
  nodes.append(node);previous=node;node=r.r32(node+12)
 assert nodes==[0x401eb750+20*i for i in range(t['cache_blocks'],16)]
 assert bytes(u.mem_read(dest,len(raw)))==before
 print('ok : cache LRU natif',len(nodes),'blocs disque ; réserve Chord exclue et intacte')
 print('ok : boot Chord '+('avec TG' if tg else 'sans TG')+', '+(engine['id'] if engine else 'sans moteurs')+', sans Banque ; RAW Chord/TG conservés, clear BSS et pile natifs ; cache non simulé')
if __name__=='__main__':main()
