"""Reglages MIDI : codec son OS reel puis extension uniquement machine MIDI.

Les fichiers restent100octets ; aucun sidecar/banque B. Comparaison stricte
des six machines audio au codec stock, et12CC complets apres sauvegarde.
"""
import json,struct,sys,pathlib
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,SOUND
import gen_sdvintage_7th as g7
RECORD=0x920a0000
HOOKS=((0x4005afa0,'mm_save2_hook'),(0x4005b054,'mm_save1_hook'),(0x4005aecc,'mm_load_hook'))

def main():
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));data=json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text())
 r=UI(stock,data);reference=UI(stock,data)
 for site,name in HOOKS:
  assert bytes(r.u.mem_read(site,8)).hex()=='4feffff448d71c00'
  r.u.mem_write(site,b'\x4e\xf9'+struct.pack('>I',r.s[name])+b'\x4e\x71')
 for machine in range(6):
  source=bytearray(100)
  for slot in range(33):struct.pack_into('>H',source,20+2*slot,(slot*173+machine*19)%0x7f00)
  source[38]=machine;source[39]=0;struct.pack_into('>H',source,28,13<<8);struct.pack_into('>I',source,88,17)
  for save,_ in HOOKS[:2]:
   outputs=[]
   for rig in (r,reference):
    rig.u.mem_write(SOUND,bytes(source));rig.call(save,RECORD,SOUND);record=bytes(rig.u.mem_read(RECORD,100))
    rig.u.mem_write(SOUND,bytes(100));rig.call(0x4005aecc,SOUND,RECORD)
    outputs.append((record,bytes(rig.u.mem_read(SOUND,100))))
   assert outputs[0]==outputs[1],(machine,hex(save))
 print('PASS six sons audio x2formats : fichiers et chargements strictement identiques au stock')
 for lane in range(6):
  r.track=lane;address=SOUND+0x1000*lane;r.u.mem_write(address,bytes(100));r.u.mem_write(address+38,b'\6\0')
  for knob in range(12):
   r.assign=True;r.call(r.s['mm_encoder'],r.event(knob,128-knob))
   r.assign=False;r.call(r.s['mm_encoder'],r.event(knob,knob-6))
  expected=bytes(r.u.mem_read(address+42,24))
  for save,_ in HOOKS[:1]:
   r.call(save,RECORD,address);r.u.mem_write(address,bytes(100));r.call(0x4005aecc,address,RECORD)
   assert bytes(r.u.mem_read(address+42,24))==expected,(lane,hex(save),expected.hex(),bytes(r.u.mem_read(address+42,24)).hex())
   assert bytes(r.u.mem_read(address+84,2))==b'MI'
 print('PASS six sons MIDI x12CC : assignations, valeurs et tag preserves par save/load OS format2')
 # Chargement legacy sans tag : aucune ancienne valeur audio ne devient un CC.
 reference.u.mem_write(SOUND,bytes(100));reference.u.mem_write(SOUND+38,b'\6\0');reference.call(0x4005afa0,RECORD,SOUND)
 r.u.mem_write(RECORD,bytes(reference.u.mem_read(RECORD,100)));r.call(0x4005aecc,SOUND,RECORD)
 assert struct.unpack('>12H',r.u.mem_read(SOUND+42,24))==(64,)*12
 assert r.call(r.s['mm_cc_read'],SOUND+20,0)==64
 print('PASS ancien son MIDI sans tag charge avec12CC OFF ; aucune valeur audio convertie en emission')
 before=bytes(r.u.mem_read(SOUND,100));r.u.mem_write(RECORD,bytes(100))
 assert r.call(0x4005aecc,SOUND,RECORD)==0
 assert bytes(r.u.mem_read(SOUND,100))==before
 print('PASS fichier invalide refuse sans toucher aux reglages MIDI deja en memoire')
 print('LIMITES : composition avec hooks filtre/all-features et sauvegarde projet physique encore requises')
if __name__=='__main__':main()
