#!/usr/bin/env python3
"""Note65 : LFO CC placé avec réglages par pattern, moteur natif et worker.

Recette candidate fournie ; appels physiques MIDI simulés, EMAC exact.
"""
import argparse,json,pathlib,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_tempo_max import Rig,OBJ,LFO_PHASE
from test_sdvintage import main_os_from_syx
import build

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak',required=True);ap.add_argument('--pattern-settings',action='store_true',help='Réglages CC stockés dans MBK2/3/4');a=ap.parse_args()
 stock=main_os_from_syx(a.cycles);t=json.loads(pathlib.Path(a.tweak).read_text());cat=build.load_catalog()['model-cycles_OS1.13'][1]
 chosen=sorted([cat[x] for x in t['requires']],key=lambda x:x['order'])
 image,_=build.apply_writes(stock,chosen+[t]);r=Rig(image);u=r.uc;r.emac.macsr=0x20
 s={k:int(v,16) for k,v in t['symbols'].items()}
 for part in t['append']['parts']:u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
 def call(name,*args):return r.call(s[name],*args)[0]
 ctx=0x93060000;pat=0x93070000
 u.mem_write(ctx,bytes(3020));u.mem_write(pat,bytes(4992 if a.pattern_settings else 1584));r.w32(s['mlcc_context'],ctx);r.w32(s['ml_play_pattern'],pat)
 cfg=pat+4704 if a.pattern_settings else ctx
 r.w32(s['mlcc_settings'],cfg)
 if a.pattern_settings:r.w32(s['ml_pattern'],pat)
 u.reg_write(mk.UC_M68K_REG_SR,0x2000);assert call('mlcc_cfg_init',cfg)==1
 for lane in range(6):
  u.mem_write(pat+264*lane,bytes((1,0,6+lane,4)))
  for lfo in range(2):
   for field,value in enumerate((20000+lane,9,16384,74 if lfo==0 else 1,3,16384,0,28000)):
    assert call('mlcc_cfg_edit',cfg,lane,lfo,field,value)==1
 call('mlcc_refresh');active=r.r32(ctx+3016);assert active==ctx+192
 old=bytes(u.mem_read(active,1144));call('mlcc_refresh');assert r.r32(ctx+3016)==ctx+1336 and bytes(u.mem_read(active,1144))==old
 # Moteur A sans destination, mais phases natives normales conservées.
 frame=bytearray(476)
 for lane in range(6):struct.pack_into('>8H',frame,lane*66+16,16384,9<<8,16384,127<<8,0,0,0,16384)
 u.mem_write(OBJ,bytes(frame));seen=[]
 def send(u,addr,size,data):
  sp=u.reg_read(mk.UC_M68K_REG_A7);n,ptr,port=struct.unpack('>3I',u.mem_read(sp+4,12))
  assert u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
  seen.append((bytes(u.mem_read(ptr,n)),port));r._ret(0)
 u.hook_add(UC_HOOK_CODE,send,begin=0x400826b0,end=0x400826b0);r.w32(0x40fe4228,1)
 for tick in range(150):
  u.reg_write(mk.UC_M68K_REG_SR,0x2500);call('mlcc_audio',OBJ,14400,0)
  assert bytes(u.mem_read(OBJ,476))==bytes(frame)
  u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  call('mlcc_worker');call('mlcc_worker')
 assert len(seen)==25,len(seen)
 slots=set()
 for packet,port in seen:
  assert len(packet)==3 and 0xb6<=packet[0]<=0xbb and packet[1] in (1,74) and packet[2]<=127 and port==4
  slots.add((packet[0],packet[1]))
 assert len(slots)==12,slots
 print('ok : octets placés, douze LFO -> CC propres aux six voies ;250 messages/s, aucun writer IRQ')
 # Muter toutes les voies purge les paquets en attente sans envoi tardif.
 for lane in range(6):u.mem_write(pat+264*lane+1,bytes((1,)))
 before=len(seen);call('mlcc_worker');assert len(seen)==before
 assert all(r.r32(ctx+2864+slot*12+8)==0 for slot in range(12))
 print('ok : snapshots alternés, frame audio intact, mute purge les CC en attente')
 assert not r.bad
if __name__=='__main__':main()
