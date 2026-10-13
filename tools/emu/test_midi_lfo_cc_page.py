#!/usr/bin/env python3
"""Page LFO MIDI : construction native et isolation des réglages audio."""
import argparse,pathlib,subprocess,tempfile,json
import build
from unicorn import UC_HOOK_CODE
from test_lfo_secondary_page import make,event,CTX,FRAME
from test_seq_gen_menu import EVENT
from test_sdvintage import main_os_from_syx
from gen_midi_lfo_cc_page import sources
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 r=make(main_os_from_syx(a.cycles));cfg=0x930d0000
 if a.tweak:
  t=json.loads(pathlib.Path(a.tweak).read_text());cat=build.load_catalog()['model-cycles_OS1.13'][1]
  chosen=sorted([cat[x] for x in t['requires']],key=lambda x:x['order'])
  image,_=build.apply_writes(main_os_from_syx(a.cycles),chosen+[t]);r.u.mem_write(build.BASE,image)
  for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  r.s.update({k:int(v,16) for k,v in t['symbols'].items()})
 else:
  with tempfile.TemporaryDirectory() as temp:
   p=pathlib.Path(temp);objects=[]
   for name,source in sources().items():
    src=p/(name+'.s');src.write_text(source);obj=p/(name+'.o');objects.append(str(obj))
    subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(src)],check=True)
   for name in ('settings','names'):
    obj=p/(name+'.o');objects.append(str(obj))
    subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/('lfo_cc_'+name+'.s'))],check=True)
   (p/'link.ld').write_text('mlp_obj = 0x930d1000; mlp_track = 0x930d1004; TG_blk_clk = 0x930d1010; mlp_keyboard = 0x930d1020; mlp_keyboard_cancel = 0x930d1024; mlp_pad = 0x930d1028; SECTIONS { .text 0x930e0000 : { *(.text*) } .data : { *(.data*) *(.rodata*) } }')
   subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','mlccp_open','-o',str(p/'e.elf'),*objects],check=True)
   subprocess.run([cross+'objcopy','-O','binary',str(p/'e.elf'),str(p/'e.bin')],check=True)
   r.u.mem_write(0x930e0000,(p/'e.bin').read_bytes());r.s.update(symbols(cross,p/'e.elf'))
 if not a.tweak:
  def pad(args):
   lane=r.r32(args[1]+20)-1
   if 0<=lane<6:r.w32(r.s['mlp_track'],lane)
   return 1
  r.stubs[r.s['mlp_pad']]=pad;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=r.s['mlp_pad'],end=r.s['mlp_pad'])
 r.stubs[r.s['mlp_keyboard_cancel']]=lambda args:0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=r.s['mlp_keyboard_cancel'],end=r.s['mlp_keyboard_cancel'])
 audio=bytes(r.u.mem_read(CTX,1240));frame=bytes(r.u.mem_read(FRAME,476))
 assert r.call('mlcc_cfg_init',cfg)==1
 r.w32(r.s['mlcc_settings'],cfg);r.w32(r.s['mlp_obj'],0x930d2000);r.w32(r.s['mlp_track'],1)
 def present(args):
  page=r.r32(args[1]);assert r.r32(page+28)==r.r32(page+32)
  return 0
 r.stubs[0x4007700e]=present
 r.call('mlccp_open');obj=r.r32(r.s['mlccp_obj']);assert obj
 assert r.r32(r.s['mlccp_track'])==1
 if a.tweak:
  # Le vrai callback B doit ouvrir cette page, sans céder au handler audio.
  assert r.call('ml_prepare')==1
  r.w32(0x40a7887c,0x930c0000);r.u.mem_write(0x930c0000+30706,bytes((0,)))
  r.w32(r.s['mlccp_obj'],0);event(r,8,0)
  assert r.call('mlp_menu_key',0x930d2000,EVENT)==1
  assert r.r32(r.s['mlccp_obj'])
  obj=r.r32(r.s['mlccp_obj'])
 for lfo in (0,1):
  assert r.r32(r.s['mlccp_index'])==lfo
  assert r.call('mlcc_cfg_edit',cfg,1,lfo,3,74)==1
  r.texts.clear();r.call('mlccp_render',obj,0x93006000)
  texts=[s for x,y,s in r.texts]
  assert 'M LFO '+str(lfo+1) in texts,texts
  event(r,8,0);r.call('mlccp_menu_key',obj,EVENT)
 # Parcours complet des destinations via l'encodeur réel de la page.
 r.w32(r.s['mlccp_row'],4);r.w32(r.s['mlccp_edit'],1)
 for lfo in (0,1):
  r.w32(r.s['mlccp_index'],lfo)
  assert r.call('mlcc_cfg_edit',cfg,1,lfo,3,0)==1
  for cc in range(1,129):
   r.delta=1;event(r,1);assert r.call('mlccp_enc',obj,EVENT)==1
   assert r.call('mlcc_cfg_get',cfg,1,lfo,3)==cc
  r.delta=1;event(r,1);r.call('mlccp_enc',obj,EVENT)
  assert r.call('mlcc_cfg_get',cfg,1,lfo,3)==128
 # Fenêtre bornée, pauses aux extrémités et retour complet des noms.
 name=r.call('mlcc_name',74);clock=r.s['TG_blk_clk']
 def window(t):
  r.w32(clock,t);ptr=r.call('mlccp_window',name)
  return bytes(r.u.mem_read(ptr,7)).split(b'\0')[0].decode()
 assert window(0)=='CC74 C'
 assert window(1499)=='CC74 C'
 assert window(1500)=='C74 Cu'
 assert window(1875)=='74 Cut'
 assert window(2250)=='4 Cuto'
 assert window(2625)==' Cutof'
 assert window(3000)=='Cutoff'
 assert window(4499)=='Cutoff'
 assert window(4500)==' Cutof'
 assert len(window(4875))==6
 short=r.call('mlcc_name',128)
 assert r.call('mlccp_window',short)==short
 # Clavier réel sous le menu, même REC actif : Note On/Off, sans édition.
 if a.tweak:
  state=0x930a0000
  for addr,fn in ((0x400cf9a8,lambda a:state),(0x4000f208,lambda a:0x930a1000),
                  (0x4000cfcc,lambda a:0x930a2000),(0x40016da6,lambda a:8)):
   r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
  r.u.mem_write(state+357,b'\x01\x01')
  r.w32(r.s['mlp_setup'],0);r.w32(r.s['mlp_func'],0);r.w32(r.s['TG_set_held'],0)
  lane=r.r32(r.s['mlp_track']);pattern=r.r32(r.s['ml_pattern'])
  before=bytes(r.u.mem_read(pattern,1584));live=r.s['ml_live_runtime']
  r.u.mem_write(r.s['TG_snap_note'],b'\x4e\x75') # Gamme OFF ; TG testé dans le boot complet.
  event(r,16,1);assert r.call('mlccp_menu_key',obj,EVENT)==1
  packet=r.call('ml_take',live)
  assert packet==((0x96+lane)<<24)|(52<<16)|(100<<8)|4,(hex(packet),lane,hex(pattern),hex(r.r32(r.s['ml_pattern'])))
  event(r,16,0);assert r.call('mlccp_menu_key',obj,EVENT)==1
  assert r.call('ml_take',live)==((0x86+lane)<<24)|(52<<16)|4
  assert bytes(r.u.mem_read(pattern,1584))==before
 if a.tweak:
  for lane in range(6):
   r.w32(r.s['mlp_pads'],0);r.w32(EVENT+20,lane+1);event(r,0,1)
   assert r.call('mlccp_pad',obj+16,EVENT)==1
   assert r.r32(r.s['mlp_track'])==lane and r.r32(r.s['mlccp_track'])==lane
   assert r.call('ml_take',live)==((0x96+lane)<<24)|(72<<16)|(100<<8)|4
   event(r,0,0);assert r.call('mlccp_pad',obj+16,EVENT)==1
   assert r.call('ml_take',live)==((0x86+lane)<<24)|(72<<16)|4
  for code in range(2,14):
   event(r,code);assert r.call('mlccp_enc',obj,EVENT)==1
  assert bytes(r.u.mem_read(pattern,1584))==before
 # Les appuis ET relâchements trigs vont au clavier B, jamais à la grille A.
 routed=[]
 r.stubs[r.s['mlp_keyboard']]=lambda args:routed.append(tuple(args[:2])) or 1
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=r.s['mlp_keyboard'],end=r.s['mlp_keyboard'])
 for flags in (1,0):
  event(r,19,flags);assert r.call('mlccp_menu_key',obj,EVENT)==1
 assert routed==[(19,1),(19,0)],routed
 # Le pad reste routé au clavier/pad MIDI privé, puis synchronise la sélection.
 r.w32(EVENT+20,6);event(r,0,1);r.call('mlccp_pad',obj+16,EVENT)
 assert r.r32(r.s['mlp_track'])==5 and r.r32(r.s['mlccp_track'])==5
 assert bytes(r.u.mem_read(CTX,1240))==audio
 assert bytes(r.u.mem_read(FRAME,476))==frame
 assert r.r32(r.s['mlp_obj'])==0x930d2000
 print('ok : page native MIDI, titres LFO1/2, sélection B et réglages audio isolés')
if __name__=='__main__':main()
