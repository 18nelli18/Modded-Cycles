#!/usr/bin/env python3
"""Bootstrap natif du candidat Banque sans TG/Genie/LFO2 audio.

MOVEC cache observé mais non simulé ; aucune preuve de MIDI physique.
"""
import argparse,json,pathlib,struct,importlib.util
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
import build

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--candidate',required=True);p.add_argument('--syntakt');p.add_argument('--build-module');a=p.parse_args()
 stock=load_stock(a.cycles);data=json.loads(pathlib.Path(a.candidate).read_text());bank=data['bank'];cat=([data['engine']] if data.get('engine') else [])+[data['core']]+data.get('supports',[])+[bank]
 image,_=build.apply_writes(stock,cat);source=int(bank['append']['at'],16);packed=bytes.fromhex(bank['append']['compressed_hex'])
 if data.get('engine') or data['core'].get('append'):
  spec=importlib.util.spec_from_file_location('candidate_build',a.build_module);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  extra,_=module.build_payload([t for t in cat if t is not bank],stock,a.syntakt)
 else:extra=b''
 image=bytes(image)+extra+bytes(source-build.BASE-len(image)-len(extra))+packed
 raw=bytes.fromhex(bank['append']['parts'][0]['hex']);dest=int(bank['append']['dest'],16)
 r=Rig(image,{'writes':[]},{'writes':[],'symbols':bank['symbols']});u=r.u
 if data.get('engine') or data['core'].get('append'):
  u.mem_map(0x43000000,0x800000);u.mem_map(0x80000000,0x200000)
  import gen_syntakt_engines as gs
  for src,end,to in gs.CY_SRAM_INIT:u.mem_write(to,image[src-build.BASE:end-build.BASE])
 if not data.get('engine'):u.mem_write(dest,b'\xa5'*len(raw))
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
 def fault(u,access,addr,size,value,data):
  print('FAULT',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),size,flush=True);return False
 u.hook_add(UC_HOOK_MEM_INVALID,fault)
 sites=set()
 for at,body in [(build.BASE,image),(dest,raw)]:sites.update(at+i for i in range(0,len(body)-3,2) if body[i:i+2]==b'\x4e\x7b')
 def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
 for site in sites:u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
 u.emu_start(0x400004b2 if data.get('engine') else 0x40000530,0x4000053a,count=30000000)
 assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,'bootstrap incomplet'
 assert bytes(u.mem_read(dest,len(raw)))==raw,'payload modifié par clear'
 assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-(4 if data['core'].get('append') and not data.get('engine') else 0),'pile modifiée'
 print('ok : décompression réelle et clear natif ; noyau + Banque conservés, pile intacte',flush=True)
 r.call(0x4007929c);nodes=[];node=r.r32(0x401eb894);previous=0
 while node:
  assert node not in nodes and r.r32(node+16)==previous
  nodes.append(node);previous=node;node=r.r32(node+12)
 assert nodes==[0x401eb750+20*i for i in range(bank['cache_blocks'],16)]
 assert bytes(u.mem_read(dest,len(raw)))==raw,'cache écrase le payload'
 print('ok : cache natif conserve',16-bank['cache_blocks'],'blocs disque et',bank['cache_blocks'],'blocs privés',flush=True)
 for at,name in [(0x4007240c,'ml_key'),(0x400597c8,'mlcc_audio'),(0x400594aa,'ml_audio_hook')]:
  operand=at+2 if at==0x4007240c else at
  assert r.r32(operand)==r.s[name],(hex(at),name)
 print('ok : hooks clavier, LFO et transport survivent au bootstrap ; stockage absent',flush=True)
 # Fixtures UI restaurées après le clear natif : objets extérieurs simulés.
 from test_seq_gen_menu import RAW,EVENT,OBJ,VT,GET,SIGNAL
 r.w32(0x40fe4178,1);r.w32(OBJ,VT);r.w32(VT+40,GET);r.w32(VT+16,SIGNAL)
 u.mem_write(GET,b'\x20\x3c'+struct.pack('>I',RAW)+b'\x4e\x75')
 r.w32(0x93005030,0x93005100);r.w32(0x93005128,0x93005200)
 u.mem_write(0x93005200,b'\x20\x3c'+struct.pack('>I',0x93005300)+b'\x4e\x75');r.w32(0x93005304,0)
 u.mem_write(RAW,bytes(722));u.mem_write(RAW+713,struct.pack('>H',16));saved=bytes(u.mem_read(RAW,722))
 r.w32(r.s['TG_set_held'],1);r.event(2,3,1)
 assert r.call(0x4007240c,EVENT)==0
 obj=r.r32(r.s['mlp_obj']);ctx=r.r32(r.s['ml_context']);assert obj and ctx
 r.event(2,2,2);assert r.call(0x4007240c,EVENT)==0
 assert bytes(u.mem_read(RAW,722))==saved
 print('ok : accord FUNC+SETTINGS+TRACK via hook natif ouvre B, relâchement consommé, A intact',flush=True)
 state=0x930a0000
 for addr,fn in [(0x400cf9a8,lambda a:state),(0x4000f208,lambda a:0x930a1000),(0x4000cfcc,lambda a:0x930a2000),(0x40016da6,lambda a:8)]:
  r.stubs[addr]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(r.s['TG_set_held'],0)
 live=r.s['ml_live_runtime']
 pattern=r.r32(r.s['ml_pattern'])
 for lane in range(6):u.mem_write(pattern+264*lane+6,b'\x08')
 for lane in range(6):
  r.w32(r.s['mlp_track'],lane)
  for note in range(16):
   r.event(16+note,1,3+note*2);r.call('mlp_menu_key',obj,EVENT)
   packet=r.call('ml_take',live);expected=((0x96+lane)<<24)|((60+note)<<16)|(100<<8)|4
   assert packet==expected,(lane,note,hex(packet),hex(expected))
   r.event(16+note,0,4+note*2);r.call('mlp_menu_key',obj,EVENT)
   assert r.call('ml_take',live)==((0x86+lane)<<24)|((60+note)<<16)|4
 assert bytes(u.mem_read(RAW,722))==saved
 print('ok : 96 notes et 96 releases sur canaux 7–12, A intact ; writer physique simulé',flush=True)
 if 'SG_config' in r.s:
  cfg=r.s['SG_config'];adv=r.s['SG_advanced'];opts=r.s['SG_options']
  for off,val in [(4,100),(8,48),(12,72),(24,123456)]:r.w32(cfg+off,val)
  for off,val in [(0,80),(4,110),(24,0),(28,100),(32,0),(36,4),(40,0)]:r.w32(adv+off,val)
  for off in [0,4,8]:r.w32(opts+off,0)
  r.w32(0x40a7883c,0);r.call('ml_repeat_prepare_ui')
  for lane in range(6):
   r.w32(r.s['mlp_track'],lane);before=bytes(u.mem_read(pattern,1584))
   r.call('ml_genie_generate');assert r.r32(r.s['SG_error'])==0
   got=bytes(u.mem_read(pattern,1584));lo=264*lane
   assert before[:lo]==got[:lo] and before[lo+264:]==got[lo+264:]
   assert all(got[lo+8+4*i+3]&1 and got[lo+8+4*i+1]>0 for i in range(16))
   assert bytes(u.mem_read(RAW,722))==saved
   r.call('ml_genie_undo');assert bytes(u.mem_read(pattern,1584))==before
  print('ok : Genie génère six voies B isolées, vélocités audibles, Undo exact, A intact',flush=True)
 r.call('mlp_dtor1',obj)
 from test_midi_lane_scheduler import prove
 prove(r)
if __name__=='__main__':main()
