#!/usr/bin/env python3
"""Noyau sans sampler : boot/clear/cache, clavier, gammes et vraie boucle audio."""
import argparse,struct
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as mk
import build,gen_performance_core as gen
from test_seq_gen_menu import Rig,STACK,EVENT,OBJ,RAW,VT,SIGNAL
from test_sdvintage import main_os_from_syx
from test_model_tg import engine
from test_model_tg_syntakt import ramp,SL_PND,SL_PDUR,SL_PMSK,SL_PCLK,SL_PFRE,SL_PST,SL_PEN,GLIDE
import mcengine as E

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',help='Clone facultatif pour comparaison');a=ap.parse_args()
 stock=main_os_from_syx(a.cycles);t,blob,s=gen.generate(stock,a.model_tg)
 cats=build.load_catalog()['model-cycles_OS1.13'][1]
 selected=[cats[x] for x in ('latching-mute','trig-preview')]+[t]
 patch,_=build.apply_writes(stock,selected);image=patch+build.build_payload(selected,stock,None)[0]
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});r.s=s;r.u.mem_write(build.BASE,image)
 for va in (0x4019b590,gen.START-16,s['reserved_end'],0x423380a0):r.u.mem_write(va,b'\xa5'*16)
 before=bytes(r.u.mem_read(gen.START,len(blob)))
 r.u.reg_write(mk.UC_M68K_REG_A7,STACK);r.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
 r.u.emu_start(0x40000530,0x4000053a,count=30000000)
 assert r.u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a and r.u.reg_read(mk.UC_M68K_REG_A7)==STACK
 assert r.u.reg_read(mk.UC_M68K_REG_A0)==0xfc044000
 assert bytes(r.u.mem_read(gen.START,len(blob)))==before
 for va in (0x4019b590,gen.START-16,s['reserved_end'],0x423380a0):assert bytes(r.u.mem_read(va,16))==bytes(16)
 r.call(0x4007929c)
 nodes=[];node=r.r32(0x401eb894)
 while node:nodes.append(node);node=r.r32(node+12)
 assert nodes==[0x401eb750+20*i for i in range(1,16)]
 assert bytes(r.u.mem_read(gen.START,len(blob)))==before
 print('ok : vrai boot/clear complet, tampon zéro intact, code conservé, quinze blocs cache natifs disponibles')
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 # Toutes les valeurs de note, cinq gammes, douze tonalités ; routine MIT inchangée.
 tables=((),(0,2,4,5,7,9,11),(0,2,3,5,7,8,10),(0,2,3,5,7,9,10),(0,2,4,7,9))
 for scale,degrees in enumerate(tables):
  for root in range(12):
   r.u.mem_write(s['scale_state'],bytes((scale,root)))
   for note in range(128):
    r.u.reg_write(mk.UC_M68K_REG_D3,note);r.call('snap_note')
    want=note if scale==0 or note==127 else 48+root+12*((note-52)//len(degrees))+degrees[(note-52)%len(degrees)]
    assert r.u.reg_read(mk.UC_M68K_REG_D3)==want&0xffffffff
 r.u.mem_write(s['scale_state'],b'\x00\x00')
 print('ok : Scale Lock autonome, cinq gammes × douze tonalités ×128 notes, mêmes valeurs que le module TG')
 assert r.call(0x4007240c,r.event(13,1,1))==13 and r.r32(s['set_held'])==1
 assert r.call(0x4007240c,r.event(13,0,2))==13 and r.r32(s['set_held'])==0
 for code in (1,2,3,4,5,6,9,10,11,12,15):assert r.call(0x4007240c,r.event(code,1,code+10))==code
 assert not r.r32(s['mm_obj']) and not r.r32(s['rtg_on']) and not r.r32(s['sle_on'])
 assert r.call(0x4007240c,r.event(13,1,50))==13
 r.w32(s['mod_used'],1)
 assert r.call(0x4007240c,r.event(13,0,51))==0
 assert not r.r32(s['set_held'])
 print('ok : modificateur SETTINGS idempotent, release après accord consommée ; aucun menu sampler/retrigger ajouté')
 # SETTINGS + trig : vrai getter/setter de flags, notifications natives.
 for addr,fn in ((0x4000eb90,lambda a:OBJ),(0x400124b8,lambda a:0)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(VT+60,0x9300d200)
 r.stubs[0x9300d200]=lambda a:0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x9300d200,end=0x9300d200)
 r.u.mem_write(RAW,bytes(128));r.u.mem_write(RAW,b'\x00\x01')
 r.u.mem_write(RAW+713,b'\x00\x10')
 assert r.call(0x4007240c,r.event(13,1,100))==13
 press=r.event(16,1,101)
 assert r.call(0x4007240c,press)==0
 assert bytes(r.u.mem_read(RAW,2))==b'\x10\x01'
 assert r.call(0x4007240c,press)==0
 assert bytes(r.u.mem_read(RAW,2))==b'\x10\x01'
 assert r.call(0x4007240c,r.event(16,0,102))==0
 assert r.call(0x4007240c,r.event(16,1,103))==0
 assert bytes(r.u.mem_read(RAW,2))==b'\x00\x01'
 assert r.call(0x4007240c,r.event(16,0,104))==0
 assert r.call(0x4007240c,r.event(13,0,105))==0
 assert not r.r32(s['set_held'])
 print('ok : SETTINGS + trig active/désactive le slide via les vrais flags ; lecture répétée idempotente')
 # Sans slide, les six machines d'origine restent identiques échantillon par échantillon.
 es,ec=engine(stock),engine(image)
 for track in range(6):
  for e in (es,ec):e.set(track,machine=track,note=60,pitch=64,color=64,shape=64,sweep=64,contour=64,punch=0,gate=0,finetune=64,decay=60)
 for block in range(40):assert np.array_equal(es.block(63 if block==1 else 0),ec.block(63 if block==1 else 0))
 assert not es.unmapped and not ec.unmapped
 print('ok : vraie boucle audio six machines, sortie sans slide identique au stock')
 # Glissement des mêmes trois paramètres que la preuve historique Model-TG.
 dur=40;frames=70;clk=5000;track=4;base=dict(machine=4,note=60,pitch=64,color=64,shape=64,sweep=64,contour=64,punch=0,gate=0,finetune=64,decay=60)
 outputs=[]
 for mode in ('slide','ramp','fixed'):
  e=engine(image);e.set(track,**base);sb=s['SLD_BASE'];frm={k:base[name]*256 for k,(name,to) in GLIDE.items()}
  def w32(at,value):e.uc.mem_write(at,struct.pack('>I',value))
  w32(s['blk_clk'],clk);w32(s['sld_init'],1)
  if mode=='slide':
   for off,value in ((SL_PND,2),(SL_PDUR,dur),(SL_PCLK,clk),(SL_PFRE,0),(SL_PMSK,sum(1<<k for k in GLIDE))):w32(sb+track*4+off,value)
   for k,(_,to) in GLIDE.items():
    e.uc.mem_write(sb+track*64+SL_PST+2*k,struct.pack('>h',frm[k]));e.uc.mem_write(sb+track*64+SL_PEN+2*k,struct.pack('>h',to*256))
  rendered=[]
  for block in range(frames):
   if mode=='ramp':
    for k,(name,to) in GLIDE.items():e.trk[track][name]=ramp(frm[k],to*256,dur,block)/256
   rendered.append(e.block(1<<track if block==1 else 0))
   if mode!='fixed':
    for k,(_,to) in GLIDE.items():assert struct.unpack('>h',e.uc.mem_read(E.PARAMS+0xe+track*0x42+2*k,2))[0]==ramp(frm[k],to*256,dur,block)
   w32(s['blk_clk'],clk+block+1)
  assert not e.unmapped;outputs.append(np.stack(rendered))
 assert np.array_equal(outputs[0],outputs[1]) and not np.array_equal(outputs[0],outputs[2])
 print('ok : slide autonome Pitch/Color/Decay audible, rampe identique échantillon par échantillon ; aucun DSP sampler')
 print('Limites : I/O et contrôles matériels non vérifiés ; autres mods à reconnecter au noyau autonome')
if __name__=='__main__':main()
