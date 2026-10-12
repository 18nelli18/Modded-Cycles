#!/usr/bin/env python3
"""Page LFO MIDI : construction native et isolation des réglages audio."""
import argparse,pathlib,subprocess,tempfile,json
import build
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
   (p/'link.ld').write_text('mlp_obj = 0x930d1000; mlp_track = 0x930d1004; SECTIONS { .text 0x930e0000 : { *(.text*) } .data : { *(.data*) *(.rodata*) } }')
   subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','mlccp_open','-o',str(p/'e.elf'),*objects],check=True)
   subprocess.run([cross+'objcopy','-O','binary',str(p/'e.elf'),str(p/'e.bin')],check=True)
   r.u.mem_write(0x930e0000,(p/'e.bin').read_bytes());r.s.update(symbols(cross,p/'e.elf'))
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
 # Le pad change uniquement la voie MIDI sélectionnée.
 r.w32(EVENT+20,6);event(r,0,1);r.call('mlccp_pad',obj+16,EVENT)
 assert r.r32(r.s['mlp_track'])==5 and r.r32(r.s['mlccp_track'])==5
 assert bytes(r.u.mem_read(CTX,1240))==audio
 assert bytes(r.u.mem_read(FRAME,476))==frame
 assert r.r32(r.s['mlp_obj'])==0x930d2000
 print('ok : page native MIDI, titres LFO1/2, sélection B et réglages audio isolés')
if __name__=='__main__':main()
