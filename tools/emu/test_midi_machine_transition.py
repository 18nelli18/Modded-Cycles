"""Transition MIDI -> audio : defauts natifs, vraie notification, notes/pattern preserves."""
import json,pathlib,struct,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,SOUND
import gen_sdvintage_7th as g7

def main():
 r=UI(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text()));r.call(0x4005a274)
 for lane in range(6):
  r.track=lane;p=SOUND+0x1000*lane+20;r.u.mem_write(p+20,struct.pack('>H',0x4002));r.call(r.s['mm_setup'],p)
  assert r.u.mem_read(p+8,2)==b'\x80\0','fixture MIDI : destination LFO audio invalide absente'
 r.call(r.s['mm_audio_poll'])
 for lane in range(6):
  r.u.mem_write(SOUND+0x1000*lane+38,bytes((lane,0)))
 r.call(r.s['mm_audio_poll'])
 for lane in range(6):
  p=SOUND+0x1000*lane+20;words=struct.unpack('>33H',r.u.mem_read(p,66))
  assert words[9]==lane<<8 and words[10]==0x4002 and words[32]==0
  for field in range(1,32):
   if field in (9,10):continue
   assert words[field]==r.call(r.s['mm_native_default'],field,lane),(lane,field,words[field])
  assert words[17]==64<<8 and words[18]>0
 # Le detour encodeur doit reparer apres delegation native, sans attendre le dessin.
 r.track=0;p=SOUND+20;r.u.mem_write(p+18,b'\x06\0');r.call(r.s['mm_setup'],p);r.call(r.s['mm_audio_poll'])
 delegate=0x92060420;r.word(r.s['mm_ui_api']+8,delegate)
 def choose(a):
  r.u.mem_write(p+18,b'\0\0');return 17
 r.stub(delegate,choose);r.assign=False
 event=r.event(-1,1)
 assert r.call(r.s['mm_encoder_hook'],0,event)==17
 assert bytes(r.u.mem_read(p+64,2))==b'\0\0'
 assert struct.unpack('>H',r.u.mem_read(p+34,2))[0]==64<<8
 before=bytes(r.u.mem_read(SOUND,0x6000));r.call(r.s['mm_audio_poll']);assert bytes(r.u.mem_read(SOUND,0x6000))==before
 import os,tempfile,shutil,numpy as np,mcengine as E
 with tempfile.TemporaryDirectory() as folder:
  os.symlink(shutil.which('m68k-linux-gnu-objdump'),pathlib.Path(folder)/'m68k-elf-objdump');os.environ['PATH']=folder+os.pathsep+os.environ['PATH']
  e=E.Engine(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')))
  for lane in range(6):
   e.uc.mem_write(E.PARAMS+14+66*lane,bytes(r.u.mem_read(SOUND+0x1000*lane+20,66)));e.uc.mem_write(E.PMOD+4*lane,struct.pack('>I',60<<16))
  audible=[False]*6
  for block in range(16):
   e.call(E.VOICE_LOOP,E.TRACK_BASE,E.PARAMS,63 if block==0 else 0,0)
   for lane in range(6):audible[lane]|=any(e.uc.mem_read(E.TRACK_BASE+128*lane,128))
  assert all(audible),audible
 print('PASS six moteurs audio reels rendent des echantillons non nuls apres la transition')
 print('PASS six sorties MIDI -> audio : reglages MIDI remplaces par defauts natifs du moteur, machine/Pitch conserves, pas de reset repete')
if __name__=='__main__':main()
