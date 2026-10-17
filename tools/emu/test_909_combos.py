"""Note 108 : vrais accords via le getter final apres boot/cache 909.
Objets UI et peripheriques simules ; aucune preuve materielle.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP,OBJ,VT,GET,RAW,SIGNAL,EVENT
from test_sdvintage import main_os_from_syx
import build
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();prefix=pathlib.Path(a.case)
 cat=json.loads(prefix.with_suffix('.json').read_text())['tweaks'];sg=next(t for t in cat if t.get('symbols',{}).get('sg_q_hook'));bank=next((t for t in cat if t['id']=='midi-out-bank'),None)
 img=main_os_from_syx(str(prefix.with_suffix('.syx')));r=Rig(img,{'writes':[]},{'writes':[],'symbols':sg['symbols']});u=r.u;bs={k:int(v,16) for k,v in bank['symbols'].items()} if bank else {}
 for at,n in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,n)
 def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 sites=set()
 for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in cat if t.get('append') for p in t['append']['parts'] if 'hex' in p]:sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
 for at in sites:u.hook_add(UC_HOOK_CODE,cache,begin=at,end=at)
 u.reg_write(mk.UC_M68K_REG_A7,STACK);u.mem_write(STACK,struct.pack('>I',STOP));u.emu_start(0x40000530,0x4000053a,count=200_000_000);assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a;r.call(0x4007929c)
 if bank:
  for part in bank['append']['parts']:
   if 'hex' in part:
    at=int(part['dest'],16);raw=bytes.fromhex(part['hex']);assert bytes(u.mem_read(at,len(raw)))==raw,'code altere par boot/cache'

 ws=next(t['symbols'] for t in cat if t['id']=='sample-wizard');r.s.update({k:int(v,16) for k,v in ws.items()});r.s.update(bs)
 u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 r.w32(0x40fe4178,0x93005000);r.w32(OBJ,VT);r.w32(VT+40,GET);r.w32(VT+16,SIGNAL)
 u.mem_write(GET,b'\x20\x3c'+struct.pack('>I',RAW)+b'\x4e\x75')
 r.w32(0x93005030,0x93005100);r.w32(0x93005128,0x93005200)
 u.mem_write(0x93005200,b'\x20\x3c'+struct.pack('>I',0x93005300)+b'\x4e\x75');r.w32(0x93005304,0)
 u.mem_write(RAW,bytes(722));u.mem_write(RAW+713,struct.pack('>H',16))
 tick=0
 def key(code,flags):
  nonlocal tick
  tick+=1
  try:return r.call(0x4007240c,r.event(code,flags,tick))
  except Exception:
   print('FAULT key',code,'pc',hex(u.reg_read(mk.UC_M68K_REG_PC)),flush=True);raise
 assert r.r32(r.s['av_perf_on'])==1 and r.r32(r.s['av_ui_mods'])==1
 assert key(13,1)==13 and r.r32(r.s['set_held'])==1
 assert key(13,0)==13 and r.r32(r.s['set_held'])==0
 print('PASS vrai getter SETTINGS maintenu/relache apres boot/cache',flush=True)
 assert key(13,1)==13
 assert key(15,1)==0 and r.r32(r.s['sg_obj'])
 key(15,0);key(13,0)
 r.call('sg_dtor1',r.r32(r.s['sg_obj']))
 print('PASS accord SETTINGS + PAGE ouvre Genie A',flush=True)
 sc=next(t for t in cat if t['id'].startswith('scramble'))
 # Isoler seulement le corps musical SCRAMBLE, hors sujet du routeur.
 run=int(sc['symbols']['sc_run'],16);calls=[]
 r.stubs[run]=lambda a:calls.append(a) or 0;u.hook_add(UC_HOOK_CODE,r.stub,begin=run,end=run)
 if 'sc_steps_toggle' in sc['symbols']:
  at=int(sc['symbols']['sc_steps_toggle'],16);r.stubs[at]=lambda a:0;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 assert key(13,1)==13
 assert key(2,1)==0 and calls
 assert r.r32(int(sc['symbols']['sc_taken'],16))==1
 key(2,0);key(13,0)
 print('PASS accord SETTINGS + TRACK atteint SCRAMBLE',flush=True)
 assert key(13,1)==13
 assert key(2,3)==0 and r.r32(r.s['mlp_obj'])
 key(2,2);key(13,0)
 print('PASS accord FUNC + SETTINGS + TRACK ouvre B',flush=True)
 r.call('mlp_dtor1',r.r32(r.s['mlp_obj']))
 # Meme fixture slide que le noyau performance ; getter/setter natifs.
 for addr,fn in ((0x4000eb90,lambda a:OBJ),(0x400124b8,lambda a:0),(r.s['show_popup'],lambda a:0)):
  r.stubs[addr]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(VT+60,0x9300d200);r.stubs[0x9300d200]=lambda a:0
 u.hook_add(UC_HOOK_CODE,r.stub,begin=0x9300d200,end=0x9300d200)
 u.mem_write(RAW,bytes(128));u.mem_write(RAW,b'\x00\x01');u.mem_write(RAW+713,b'\x00\x10')
 assert key(13,1)==13
 assert key(16,1)==0 and bytes(u.mem_read(RAW,2))==b'\x10\x01'
 key(16,0)
 assert key(16,1)==0 and bytes(u.mem_read(RAW,2))==b'\x00\x01'
 key(16,0);key(13,0)
 print('PASS SETTINGS + trig active/desactive slide via flags natifs',flush=True)
 # La vue mute appelle ce garde natif lors de FUNC ; TRACK maintenu verrouille.
 held={2};at=0x4007faf4;r.stubs[at]=lambda a:int(a[0] in held)
 u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 assert key(1,1)==1
 assert r.call(0x401486fc)==1 and bytes(u.mem_read(0x401487ed,1))==b'\x01'
 held.clear();r.w32(0x40a78e28,2048);r.w32(0x401487e0,0)
 assert r.call(0x401486fc)==1
 r.w32(0x401487e0,2048)
 assert r.call(0x401486fc)==0 and bytes(u.mem_read(0x401487ed,1))==b'\x00'
 print('PASS getter FUNC et garde mute verrouille TRACK, maintien et sortie courte',flush=True)
if __name__=='__main__':main()
