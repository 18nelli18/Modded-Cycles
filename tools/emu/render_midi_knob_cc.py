#!/usr/bin/env python3
"""Aperçu CC B : renderer propre et primitives/polices OS natifs exécutés."""
import argparse,pathlib,subprocess,tempfile,struct,json
from unicorn import m68k_const as mk
from unicorn import UC_HOOK_CODE
from render_midi_bank import DrawingRig,png
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--output',required=True);ap.add_argument('--tweak');ap.add_argument('--lock-preview',action='store_true');a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 defs={'TG_set_held':0x9306a000,'mlp_track':0x9306a004,'ml_pattern':0x9306a008,'mlp_obj':0x9306a00c,'TG_blk_clk':0x9306a010,'TG_mod_used':0x9306a014}
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in ('knob_cc','knob_cc_ui','knob_cc_scroll','lfo_cc_names'):
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  (p/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { .text 0x93050000 : { *(.text*) *(.rodata*) *(.data*) } }')
  subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','mlkc_enc','-o',str(p/'k.elf'),*objs],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'k.elf'),str(p/'k.bin')],check=True)
  code=(p/'k.bin').read_bytes();syms=symbols(cross,p/'k.elf')
 base={'writes':[]}
 if a.tweak:
  catalog=json.loads((root/'work/midi-clear-catalog.json').read_text());base=next(t for t in catalog['tweaks'] if t['id']=='model-tg-st')
 r=DrawingRig(main_os_from_syx(a.cycles),base,{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 if a.tweak:
  t=json.loads(pathlib.Path(a.tweak).read_text());syms={k:int(v,16) for k,v in t['symbols'].items()};r.s=syms
  for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  for w in t['writes']:
   at=0x40000400+w['off']
   if 0x40100000<=at<0x401ab750:r.u.mem_write(at,bytes.fromhex(w['new']))
  defs={k:syms[k] for k in defs}
 r.stubs[0x400802ec]=lambda args:0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
 pat,event=0x93070000,0x93071000;r.w32(defs['ml_pattern'],pat);r.w32(defs['mlp_track'],0)
 r.u.mem_write(pat,bytes((1,0,6,4,16,2,0,0))+bytes(1576));r.w32(event+12,2)
 r.w32(defs['TG_set_held'],1);r.delta=75
 assert r.call('mlkc_enc',event)==1 and r.u.mem_read(syms['mlkc_state'],2)==bytes((74,64))
 assert r.r32(defs['TG_mod_used'])==1
 if a.tweak:
  tg=symbols(cross,root.parent/'model-tg/build/_b.elf')
  assert tg['mod_used']==defs['TG_mod_used']
  r.w32(defs['mlp_obj'],0x930a8000)
  r.w32(event+12,13);r.w32(event+16,16)
  r.u.reg_write(mk.UC_M68K_REG_A0,event)
  r.u.reg_write(mk.UC_M68K_REG_D0,13)
  assert r.call(tg['kh_mod'])==0 and r.r32(defs['TG_set_held'])==0
  assert r.r32(defs['mlp_obj'])==0x930a8000
  r.w32(event+12,2)
  print('ok : vrai handler Model-TG consomme release SETTINGS après assignation ; vue B conservée')
 sent=[]
 def send(args):sent.append((args[0],bytes(r.u.mem_read(args[1],3)),args[2]));return 0
 r.stubs[0x400826b0]=send;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
 r.w32(0x40fe4228,1);r.w32(defs['TG_set_held'],0);r.delta=1
 assert r.call('mlkc_enc',event)==1 and sent==[(3,b'\xb6\x4a\x41',4)]
 r.w32(defs['TG_set_held'],1);r.delta=-1
 assert r.call('mlkc_enc',event)==1 and len(sent)==1
 r.delta=1;r.call('mlkc_enc',event);assert len(sent)==1
 if a.tweak:
  r.w32(defs['TG_set_held'],0)
  r.stubs[syms['ml_bank_ui_sync']]=lambda args:1
  r.u.hook_add(UC_HOOK_CODE,r.stub,begin=syms['ml_bank_ui_sync'],end=syms['ml_bank_ui_sync'])
  r.stubs[0x400760ba]=lambda args:0
  r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400760ba,end=0x400760ba)
  r.w32(syms['ml_store_load_ready'],1)
  r.call('mlp_enc',0x930a8000,event)
  assert sent[-1]==(3,b'\xb6\x4a\x42',4),sent
  sent.pop()
 # OFF conserve les contrôles préexistants ; voie muette ne transmet rien.
 r.u.mem_write(pat+1,b'\x01');r.w32(defs['TG_set_held'],0)
 assert r.call('mlkc_enc',event)==1 and len(sent)==1
 r.u.mem_write(pat+1,b'\x00');r.w32(event+12,3)
 assert r.call('mlkc_enc',event)==0 and len(sent)==1
 r.w32(event+12,2);r.w32(defs['TG_set_held'],1)
 if a.lock_preview:
  r.w32(syms['mlp_held'],8);r.w32(syms['mlp_step'],3);r.w32(defs['TG_set_held'],0)
  r.delta=3;r.call('mlkc_enc',event)
 r.call(0x400e7dbc)
 bitmap,fb=0x93006000,0x93090000;r.u.mem_write(fb,bytes(1024));r.call(0x40070172,bitmap,128,64,fb,0)
 try:r.call('mlkc_render',0,bitmap)
 except Exception:
  pc=r.u.reg_read(mk.UC_M68K_REG_PC);print('PC',hex(pc),bytes(r.u.mem_read(pc,12)).hex());raise
 data=bytes(r.u.mem_read(fb,1024));assert any(data)
 pixels=[]
 for y in range(63,-1,-1):
  for x in range(128):
   word=struct.unpack_from('>I',data,(x*2+y//32)*4)[0];pixels.append(0 if word&(1<<(31-y%32)) else 255)
 pathlib.Path(a.output).parent.mkdir(parents=True,exist_ok=True);png(a.output,pixels)
 print('ok : SETTINGS assigne sans émission, mouvement normal transmet CC74 canal7, mute/OFF respectés')
 print('ok : vrai renderer/polices OS, fenêtre nom bornée, image PNG sans export firmware')
if __name__=='__main__':main()
