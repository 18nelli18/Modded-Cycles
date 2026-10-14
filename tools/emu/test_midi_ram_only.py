#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rollback RAM : vraies entrées Save/Load, aucune E/S B, données conservées."""
import argparse,json,pathlib,struct
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig,OBJ,RAW
from test_sdvintage import main_os_from_syx
import build

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--base',required=True);p.add_argument('--tweak',required=True);a=p.parse_args()
 base=json.loads(pathlib.Path(a.base).read_text());t=json.loads(pathlib.Path(a.tweak).read_text());s={k:int(v,16) for k,v in t['symbols'].items()}
 before=bytes.fromhex(base['append']['parts'][0]['hex']);after=bytes.fromhex(t['append']['parts'][0]['hex']);dest=int(t['append']['dest'],16)
 permitted={i for name in ('ml_store_service','ml_store_bootstrap','ml_store_save_notice') for i in range(s[name]-dest,s[name]-dest+2)}
 assert len(before)==len(after) and {i for i,(x,y) in enumerate(zip(before,after)) if x!=y}<=permitted
 assert all(after[s[n]-dest:s[n]-dest+2]==b'\x4e\x75' for n in ('ml_store_service','ml_store_bootstrap','ml_store_save_notice'))
 removed={0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6};assert not removed&{build.BASE+w['off'] for w in t['writes']}
 load=next(w for w in t['writes'] if build.BASE+w['off']==0x4006a660);assert load['new']=='4ef9'+struct.pack('>I',s['ml_repeat_project_hook']).hex()+'4e71'
 stock=main_os_from_syx(a.cycles);r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});r.s=s
 for w in t['writes']:r.u.mem_write(build.BASE+w['off'],bytes.fromhex(w['new']))
 r.u.mem_write(dest,after)
 for va in removed:assert bytes(r.u.mem_read(va,8))==stock[va-build.BASE:va-build.BASE+8]
 def fail(args):raise AssertionError('API disque B atteinte')
 for va in (0x4007ad86,0x4007ac46,0x4007bc5e,0x4007baaa,0x4007bb0a,0x4007bc1c,0x4007bb76,0x4007e2f6):r.stubs[va]=fail;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=va,end=va)
 table,bank,cache,callback,serialized=0x93070000,0x93071000,0x93074000,0x93075000,0x41400000
 pattern=bytearray(4992);pattern[8:12]=bytes((72,100,4,1));r.u.mem_write(bank,bytes(pattern));r.u.mem_write(table,bytes(384));r.w32(table+20,bank)
 for name,val in (('ml_bank_table',table),('ml_pattern',bank),('ml_play_pattern',bank),('ml_runtime',0),('ml_store_load_ready',1),('ml_store_load_serial',9),('ml_store_load_pending_id',0xdeadbeef),('ml_store_load_active',1)):r.w32(s[name],val)
 maps=bytes((74,77,71,99))+bytes((255,64))*70;r.u.mem_write(s['mlkc_state'],maps)
 locks=r.call('mlkc_locks_for',bank,1);assert locks and r.call('mlkc_lock_set',locks,0,0,0,74,111)==1
 lock_before=bytes(r.u.mem_read(locks,9216));r.w32(RAW+8,0x12345678);r.u.mem_write(callback,bytes(16))
 for va,fn in ((0x400cfdaa,lambda args:cache),(0x4006a216,lambda args:serialized),(0x4005d18a,lambda args:1),(0x4006a4d6,lambda args:1),(0x4006a3ac,lambda args:serialized),(0x4005d3dc,lambda args:1),(0x400d0aae,lambda args:0),(0x400cf044,lambda args:0)):
  r.stubs[va]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=va,end=va)
 def intact():
  assert r.r32(s['ml_bank_table'])==table and r.r32(s['ml_store_load_ready'])==1
  assert bytes(r.u.mem_read(bank,4992))==bytes(pattern) and bytes(r.u.mem_read(s['mlkc_state'],144))==maps
  assert bytes(r.u.mem_read(locks,9216))==lock_before
 for _ in range(12):r.call('ml_store_service');r.call('ml_store_bootstrap');r.call('ml_store_save_notice');intact()
 assert r.call(0x4000f762,OBJ,3,callback)&255==1;intact()
 assert r.call(0x4006a5a0,cache,3,OBJ,callback)&255==1;intact()
 for _ in range(12):r.call('ml_store_service');intact()
 print('ok : code musical identique ; Save/disque natifs non hookés ; Load annule seulement repeat RAM')
 print('ok : Save/Load natifs + notification obsolète ne remplacent pas notes, assignations ou locks ; aucune API fichier B')
 print('Limite : convertisseur/cache A simulés ; rollback et transport physiques à vérifier sur matériel')
if __name__=='__main__':main()
