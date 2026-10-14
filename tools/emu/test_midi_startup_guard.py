#!/usr/bin/env python3
"""Callback startup sans singletons : aucun getter UI ni allocation précoce.

Frontières OS observées ; ne prouve pas la cause de l'écran blanc matériel.
"""
import argparse,json,pathlib,itertools
from unicorn import UC_HOOK_CODE,m68k_const as mk
import build
from chord_keys_pr87 import load_stock
from test_seq_gen_menu import Rig,STACK

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--candidate',required=True);a=p.parse_args();data=json.loads(pathlib.Path(a.candidate).read_text());b=data['bank'];stock=load_stock(a.cycles)
 recipes=[data['core']]+data['supports']+[b];img,_=build.apply_writes(stock,recipes)
 r=Rig(img,{'writes':[]},{'writes':[],'symbols':b['symbols']});origin=int(b['append']['dest'],16);r.u.mem_write(origin,bytes.fromhex(b['append']['parts'][0]['hex']))
 led=int(data['core']['symbols']['led_hook'],16);seen=[]
 def observe(u,pc,size,data):seen.append(pc)
 for pc in (r.s['ml_ui_drain'],0x400d0974,0x400802e0):r.u.hook_add(UC_HOOK_CODE,observe,begin=pc,end=pc)
 for ui,router in ((0,0),(0,1),(1,0)):
  r.w32(0x40fe4178,ui);r.w32(0x40fe4228,router);r.w32(r.s['ml_context'],0);seen.clear();r.call('ml_safe_ui');r.call(led)
  assert not seen,(ui,router,seen)
  assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
 r.w32(0x40fe4178,1);r.w32(0x40fe4228,1);r.w32(r.s['ml_context'],0);seen.clear();r.call('ml_safe_ui');assert not seen
 print('PASS : avant ouverture B ou singletons manquants, aucune allocation/service/getter UI ; pile native intacte')
 # Route prête : même service existant après ouverture, observé à son entrée.
 r.w32(r.s['ml_context'],0x93010000);r.u.mem_write(r.s['ml_ui_drain'],bytes.fromhex('4e75'));seen.clear();r.call('ml_safe_ui');assert seen==[r.s['ml_ui_drain']]
 print('PASS : service B conservé après ouverture ; garde diagnostic, résultat matériel inconnu')
if __name__=='__main__':main()
