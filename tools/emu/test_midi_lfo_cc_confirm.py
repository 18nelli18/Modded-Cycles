#!/usr/bin/env python3
"""Brouillon destination LFO : code ColdFire, confirmation/annulation/contexte."""
import argparse,pathlib,subprocess,tempfile,json
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in ('settings','confirm'):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/('lfo_cc_'+name+'.s'))],check=True)
  (p/'vars.s').write_text('.data\n.globl mlccp_row,mlccp_edit,mlccp_track,mlccp_index,mlcc_settings\nmlccp_row: .long 4\nmlccp_edit: .long 0\nmlccp_track: .long 0\nmlccp_index: .long 0\nmlcc_settings: .long 0\n')
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'vars.o'),str(p/'vars.s')],check=True);objs.append(str(p/'vars.o'))
  subprocess.run([cross+'ld','-Ttext=0x93050000','-Tdata=0x93054000','-o',str(p/'x.elf'),*objs],check=True,stderr=subprocess.DEVNULL)
  syms={x[2]:int(x[0],16) for line in subprocess.check_output([cross+'nm','--defined-only',str(p/'x.elf')],text=True).splitlines() if len(x:=line.split())==3}
  r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms
  for section,at in (('.text',0x93050000),('.data',0x93054000)):
   subprocess.run([cross+'objcopy','-O','binary','--only-section='+section,str(p/'x.elf'),str(p/'section.bin')],check=True);r.u.mem_write(at,(p/'section.bin').read_bytes())
 cfg=0x93060000;r.w32(syms['mlcc_settings'],cfg);assert r.call('mlcc_cfg_init',cfg)==1
 for lane in range(6):
  for lfo in range(2):
   r.w32(syms['mlccp_track'],lane);r.w32(syms['mlccp_index'],lfo)
   assert r.call('mlcc_cfg_edit',cfg,lane,lfo,3,74)==1
   before=bytes(r.u.mem_read(cfg,192));r.call('mlccp_confirm_data');assert r.r32(syms['mlccp_edit'])==1
   for cc in range(129):
    assert r.call('mlccp_confirm_write',cfg,lane,lfo,3,cc)==1
    assert bytes(r.u.mem_read(cfg,192))==before
    assert r.call('mlcc_cfg_get',cfg,lane,lfo,3)==74
   r.call('mlccp_confirm_data');assert r.call('mlcc_cfg_get',cfg,lane,lfo,3)==128
   assert r.r32(syms['mlccp_draft'])==0xffffffff and not r.r32(syms['mlccp_edit'])
   r.call('mlccp_confirm_data');r.call('mlccp_confirm_write',cfg,lane,lfo,3,71);r.call('mlccp_confirm_cancel');assert r.call('mlcc_cfg_get',cfg,lane,lfo,3)==128
   # Les autres champs ne passent pas dans le brouillon destination.
   r.call('mlccp_confirm_data');assert r.call('mlccp_confirm_write',cfg,lane,lfo,7,8192)==1;assert r.call('mlcc_cfg_get',cfg,lane,lfo,7)==8192;r.call('mlccp_confirm_cancel')
 # Tout changement propriétaire annule la sélection provisoire.
 for name,new in (('mlccp_track',0),('mlccp_index',0),('mlcc_settings',cfg+256)):
  r.w32(syms['mlccp_track'],5);r.w32(syms['mlccp_index'],1);r.w32(syms['mlcc_settings'],cfg)
  r.call('mlccp_confirm_data');r.call('mlccp_confirm_write',cfg,5,1,3,12);r.w32(syms[name],new);r.call('mlccp_confirm_validate');assert r.r32(syms['mlccp_draft'])==0xffffffff
 print('ok : 12 LFO, 129 destinations parcourues sans mutation cfg, DATA confirme, BACK annule, autres champs et changements contexte')
 if a.tweak:integration(a.cycles,a.tweak)

def integration(cycles,tweak):
 import build
 t=json.loads(pathlib.Path(tweak).read_text());s={k:int(v,16) for k,v in t['symbols'].items()}
 r=Rig(main_os_from_syx(cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=s
 for w in t['writes']:r.u.mem_write(build.BASE+w['off'],bytes.fromhex(w['new']))
 for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
 pat,event,obj,vtable,context=0x93070000,0x93076000,0x93077000,0x93078000,0x93079000
 cfg=pat+4704;r.w32(s['mlcc_settings'],cfg);r.w32(s['ml_pattern'],pat);r.w32(s['mlcc_context'],context)
 assert r.call('mlcc_cfg_init',cfg)==1
 r.w32(obj,vtable);r.w32(vtable+40,0x9307f000)
 closed=[];keyboard=[];sent=[]
 for at,fn in ((0x40076082,lambda args:0),(0x4006f73a,lambda args:1),(0x9307f000,lambda args:closed.append(1) or 0),(s['mlp_keyboard'],lambda args:keyboard.append(tuple(args[:2])) or 1),(0x400826b0,lambda args:sent.append(tuple(args[:3])) or 0)):
  if at not in r.stubs:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 def key(k,flags):r.w32(event+12,k);r.w32(event+16,flags);return r.call('mlccp_menu_key',obj,event)
 # Sans DATA, la molette navigue seulement entre les lignes.
 r.w32(s['mlccp_row'],4);r.call('mlccp_confirm_cancel');before=bytes(r.u.mem_read(cfg,192));r.w32(event+12,1)
 r.call('mlccp_enc',obj,event)
 assert bytes(r.u.mem_read(cfg,192))==before
 for lane in range(6):
  for lfo in range(2):
   r.w32(s['mlccp_track'],lane);r.w32(s['mlccp_index'],lfo);r.w32(s['mlccp_row'],4);r.call('mlccp_confirm_cancel')
   r.call('mlcc_cfg_edit',cfg,lane,lfo,3,74);before=bytes(r.u.mem_read(cfg,192))
   key(32,16);r.w32(event+12,1)
   for _ in range(5):r.call('mlccp_enc',obj,event)
   assert r.r32(s['mlccp_draft'])==79 and bytes(r.u.mem_read(cfg,192))==before
   # Snapshot réel de l'audio : destination confirmée74, pas le brouillon79.
   r.call('mlcc_refresh');snapshot=r.r32(context+3016);assert int.from_bytes(r.u.mem_read(snapshot+lane*32+lfo*16+6,2),'big')==74
   key(32,16);assert r.call('mlcc_cfg_get',cfg,lane,lfo,3)==79
   key(32,16);r.w32(event+12,1);r.call('mlccp_enc',obj,event);key(12,1)
   assert not closed and r.call('mlcc_cfg_get',cfg,lane,lfo,3)==79
   key(16,1);key(16,0);assert keyboard[-2:]==[(16,1),(16,0)]
 # BACK suivant ferme seulement la fenêtre, LFO change annule le brouillon.
 key(12,1);assert len(closed)==1
 key(32,16);key(8,0);assert r.r32(s['mlccp_draft'])==0xffffffff and not r.r32(s['mlccp_edit'])
 assert not sent
 print('ok : vrais handlers DATA/encoder/BACK des12LFO, snapshot audio confirmé pendant défilement, clavier press/release, aucun envoi MIDI UI')

if __name__=='__main__':main()
