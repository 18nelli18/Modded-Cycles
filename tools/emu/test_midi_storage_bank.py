#!/usr/bin/env python3
"""Banques MBK2 placées : initialisation, locks/LFO par pattern, copie et retrait."""
import argparse,json,pathlib,struct
import build
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak',required=True);a=ap.parse_args()
 stock=main_os_from_syx(a.cycles);t=json.loads(pathlib.Path(a.tweak).read_text());cat=build.load_catalog()['model-cycles_OS1.13'][1]
 chosen=sorted([cat[x] for x in t['requires']],key=lambda x:x['order']);image,_=build.apply_writes(stock,chosen+[t])
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_write(build.BASE,image)
 for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
 r.s={k:int(v,16) for k,v in t['symbols'].items()}
 assert r.call('ml_prepare')==1
 ctx=r.r32(r.s['ml_context']);table=r.r32(r.s['ml_bank_table']);bank=r.r32(r.s['ml_pattern']);empty=r.r32(r.s['ml_bank_empty'])
 assert table==ctx+1956 and bank==ctx+2340 and empty==ctx+7236
 assert r.r32(table)==bank and r.r32(r.s['ml_runtime'])==ctx+1584
 for ptr in (bank,empty):
  for lane in range(6):
   assert bytes(r.u.mem_read(ptr+lane*264,8))==bytes((1,0,6+lane,4,16,2,0,0))
   assert bytes(r.u.mem_read(ptr+1584+lane*520,8))==bytes((0,8,0,0,5,1,0,0))
   assert bytes(r.u.mem_read(ptr+1584+lane*520+8,512))==bytes((0,0,0,0,0,1,0,0))*64
  assert bytes(r.u.mem_read(ptr+4704,192))==struct.pack('>8H',16384,9,16384,128,0,0,0,16384)*12
 assert r.call('ml_repeat_pattern_prepare',bank)==bank+1584
 assert r.call('ml_repeat_pattern_lookup',bank)==bank+1584
 # Un autre pattern possède tous ses réglages, sans alias ni écrasement.
 r.w32(0x40a7887c,0x930c0000);r.w32(0x930c0000+30706,95)
 assert r.call('ml_bank_ui_sync')==1
 other=r.r32(r.s['ml_pattern']);assert other not in (bank,empty)
 assert r.r32(table+95*4)==other
 r.u.mem_write(other+1584+8,bytes((1,4,12,0,2,3,63,165)))
 assert bytes(r.u.mem_read(bank+1584+8,8))==bytes((0,0,0,0,0,1,0,0))
 assert r.call('mlcc_prepare')==0 or r.r32(r.s['mlcc_context'])
 r.call('mlcc_refresh');assert r.r32(r.s['mlcc_settings'])==other+4704
 assert r.call('mlcc_cfg_edit',other+4704,5,1,3,74)==1
 assert r.call('mlcc_cfg_get',bank+4704,5,1,3)==128
 r.w32(0x930c0000+30706,0);r.call('ml_bank_ui_sync');r.call('mlcc_refresh')
 assert r.r32(r.s['mlcc_settings'])==bank+4704
 assert r.call('mlcc_cfg_get',other+4704,5,1,3)==74
 # Retrait : ne jamais free un sous-bloc du contexte embarqué.
 retired=0x930e0000;r.u.mem_write(retired,bytes(384));r.w32(retired,bank);r.w32(retired+4,empty)
 freed=[]
 r.stubs[0x400802ec]=lambda args:freed.append(args[0]) or 0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
 assert r.call('ml_store_retire',retired)==1 and freed==[retired]
 # Le changement de projet coupe l'ancien playback avant l'I/O UI.
 runtime=r.r32(r.s['ml_runtime'])
 assert r.call('ml_step',runtime,0,0x903c6404,4)==1
 r.call('ml_store_suspend')
 assert r.r32(r.s['ml_store_load_ready'])==0
 assert r.r32(r.s['ml_pattern'])==empty and r.r32(r.s['ml_play_pattern'])==empty
 assert r.call('ml_bank_ui_sync')==0
 assert r.call('mlp_keyboard',16,1)==1
 packet=r.call('ml_take',runtime)
 assert packet==0x803c0004,hex(packet)
 print('ok : suspension Load, notes en attente annulées y compris canal1, B ancien retiré, édition/clavier bloqués')
 print('ok : MBK2 placé, initialisation notes/locks/LFO, patterns indépendants, configurations CC sélectionnées, sous-blocs protégés')
if __name__=='__main__':main()
