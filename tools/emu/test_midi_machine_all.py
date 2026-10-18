"""Boot du vrai preset signe,18machines, CC/UI/sauvegarde et relais conserves."""
import json,pathlib,sys,struct,tempfile
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_midi_machine_ui import UI,SOUND,EVENT
from test_midi_machine_notes import PROJECT,OBJECT,VT
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_sdvintage_7th import ROW_COUNT
CASE='build/midi-machine/all/preset'
def main():
 img,mem,ts=boot_case(CASE);engine=next(t for t in ts if t.get('machine_selection')==1023)
 assert not any(t['id']=='midi-out-bank' for t in ts)
 assert any(t.get('symbols',{}).get('br_load_address') for t in ts)
 pay=int(engine['append']['dest'],16);blob=next(raw for at,raw in mem if at==pay)
 r=UI(img,dict(hex=blob.hex(),symbols=engine['symbols'],machine=17),pay)
 for at,raw in mem:r.u.mem_write(at,raw)
 r.call(0x4005a274);assert r.word(ROW_COUNT)==18
 assert r.call(0x4005a4e8,126)==11 and r.call(0x4005a4e8,130)==18
 print('PASS boot complet signe :18machines, bornes131, MIDI present, diagnostic present, aucune banque B')
 # Les detours partages doivent deleguer a ChordKeys, au stockage Wizard et aux LFO audio.
 for index in range(4):assert r.word(r.s['mm_live_api']+4*index)!=0
 assert r.word(r.s['mm_sequence_api'])!=0 and r.word(r.s['mm_sequence_api']+4)==1
 assert r.word(r.s['mm_storage_api']+8)!=0
 assert r.word(r.s['mm_lfo_api'])!=0x40091ab2
 print('PASS chaines explicites ChordKeys live/sequence, stockage Wizard et second LFO audio conservees')
 for lane in range(6):
  r.track=lane;params=SOUND+0x1000*lane+20
  r.assign=True;r.output.clear();assert r.call(0x40077532,0,r.event(0,75))==1;assert not r.output
  r.assign=False;r.call(0x40077532,0,r.event(0,1));assert ('DIN',bytes((0xb0,74,65))) in r.output
  r.lines.clear();r.call(0x4001b22a,0,0x920c0000);assert r.lines[0]==f'T{lane+1} MIDI OUT'
  r.call(r.s['mm_setup'],params);r.call(r.s['mm_lfo_edit'],params,0,3,-54)
  r.call(r.s['mm_route_edit'],params,0,-11);r.call(r.s['mm_route_edit'],params,1,4)
  before=bytes(r.u.mem_read(params,66));record=0x920a0000
  assert r.call(0x4005afa0,record,SOUND+0x1000*lane)==1
  r.u.mem_write(SOUND+0x1000*lane,bytes(100));assert r.call(0x4005aecc,SOUND+0x1000*lane,record)==1
  assert bytes(r.u.mem_read(params,66))==before
  r.output.clear();r.call(r.s['mm_live_on'],lane,60,99);r.call(r.s['mm_live_off'],lane,60)
  assert ('DIN',bytes((0x95,60,99))) in r.output and ('USB',bytes((0x85,60,0))) in r.output
 print('PASS six pistes du preset : CC sans synthese, ecran MIDI seul,33mots exacts apres hooks save/load complets, notes live routees')
 r.output.clear();r.call(r.s['mm_live_on'],0,63,99)
 r.u.mem_write(SOUND+38,b'\0\0');packet=0x920b8000;r.u.mem_write(packet,b'\6'+bytes(15))
 assert r.call(r.s['mm_cc_worker'],packet)==0
 assert ('DIN',bytes((0x85,63,0))) in r.output and ('USB',bytes((0x85,63,0))) in r.output
 print('PASS STOP ferme aussi les notes live capturees apres changement de machine, sur leur canal/port initial')
 from test_midi_machine_sequence import Sequence
 sq=Sequence(img,dict(hex=blob.hex(),symbols=engine['symbols'],machine=17),pay,prepared=True)
 for at,raw in mem:sq.uc.mem_write(at,raw)
 sq.e.call(0x4005a274)
 for lane in range(6):
  sq.queue.clear();sq.sent.clear();assert sq.sequence(lane,74,17+lane)==1<<lane
  notes=[bytes(sq.uc.mem_read(pointer,16)) for pointer in sq.queue if pointer!=sq.s['mm_wakeup']]
  assert len(notes)==1 and notes[0][0]==1 and notes[0][8:11]==bytes((lane,60,97)),(lane,notes)
  sq.drain();assert bytes((0xb0|lane,74,17+lane)) in sq.sent
 print('PASS vrai chemin sequence du preset avec ChordKeys : exactement une note MIDI et CC locks, aucune attaque double')
 import emac
 mac=emac.EMAC(r.u);mac.macsr=0x20
 with tempfile.TemporaryDirectory() as folder:
  file=pathlib.Path(folder)/'patched.bin';file.write_bytes(img);mac.install(emac.disasm(str(file),0x40000400,0x4008f100,0x40091d50))
 secondary=next(t for t in ts if t['id']=='lfo-secondary');context=0x920e0000
 r.word(int(secondary['symbols']['lf2_context'],16),context);r.u.mem_write(context,bytes(1240))
 frame=0x920c0000;initial=bytearray(476)
 for lane in range(6):
  p=[0]*33;p[4]=127<<8;p[9]=lane<<8
  if lane==1:
   params=SOUND+0x1000*lane+20;r.call(r.s['mm_lfo_edit'],params,0,7,12000);r.call(r.s['mm_lfo_edit'],params,0,0,8000)
   p=struct.unpack('>33H',r.u.mem_read(params,66))
  struct.pack_into('>33H',initial,14+66*lane,*p)
 for tick in range(6):
  r.u.mem_write(frame,bytes(initial));r.u.reg_write(mk.UC_M68K_REG_SR,0x2700);before=len(r.output)
  r.call(r.s['mm_lfo_dispatch'],frame,14400,0)
  assert len(r.output)==before
  assert bytes(r.u.mem_read(frame+14+66,66))==initial[14+66:14+132]
 print('PASS LFO MIDI avec vrai second LFO audio actif : tranche MIDI restauree, aucun writer IRQ')
 print('LIMITES : projet et ports physiques, rendu temps reel et utilisation manuelle a verifier sur appareil')
if __name__=='__main__':main()
