"""Boot du vrai preset signe,18machines, CC/UI/sauvegarde et relais conserves."""
import json,pathlib,sys,struct,tempfile,os
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_midi_machine_ui import UI,SOUND,EVENT
from test_midi_machine_worker import Worker
from test_midi_machine_notes import PROJECT,OBJECT,VT
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_sdvintage_7th import ROW_COUNT
CASE=os.environ.get('MIDI_MACHINE_CASE','build/midi-machine/all/preset')
def main():
 img,mem,ts=boot_case(CASE);engine=next(t for t in ts if t.get('machine_selection')==1023)
 assert not any(t['id']=='midi-out-bank' for t in ts)
 assert any(t.get('symbols',{}).get('br_load_address') for t in ts)==('main-' not in CASE)
 pay=int(engine['append']['dest'],16);blob=next(raw for at,raw in mem if at==pay)
 r=Worker(img,dict(hex=blob.hex(),symbols=engine['symbols'],machine=17),pay)
 for at,raw in mem:r.u.mem_write(at,raw)
 r.call(0x4005a274);assert r.word(ROW_COUNT)==18
 assert r.call(0x4005a4e8,126)==11 and r.call(0x4005a4e8,130)==18
 print('PASS boot complet signe :18machines, bornes131, MIDI present, diagnostic conforme au profil, aucune banque B')
 # Les detours partages doivent deleguer a ChordKeys, au stockage Wizard et aux LFO audio.
 for index in range(4):assert r.word(r.s['mm_live_api']+4*index)!=0
 assert r.word(r.s['mm_sequence_api'])!=0 and r.word(r.s['mm_sequence_api']+4)==1
 assert r.word(r.s['mm_storage_api']+8)!=0
 assert r.word(r.s['mm_lfo_api'])!=0x40091ab2
 print('PASS chaines explicites ChordKeys live/sequence, stockage Wizard et second LFO audio conservees')
 for lane in range(6):
  r.track=lane;params=SOUND+0x1000*lane+20
  r.assign=False;r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,13,1,0));r.call(r.s['mm_ui_key'],EVENT);r.output.clear();assert r.call(0x40006158,0,r.event(0,75))==1;assert not r.output
  r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,13,0,0));assert r.call(r.s['mm_ui_key'],EVENT)==1;r.call(0x40006158,0,r.event(0,1));assert ('DIN',bytes((0xb0,74,65))) in r.output
  r.lines.clear();assert r.call(r.s['mm_draw'],0,0x920c0000)==0 and not r.lines
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
 # Chaque machine audio du catalogue doit recevoir ses propres defauts apres MIDI.
 params=SOUND+0x5000+20
 for machine in range(17):
  r.u.mem_write(params+18,bytes((17,0)));r.call(r.s['mm_setup'],params);r.call(r.s['mm_audio_poll'])
  pitch=bytes(r.u.mem_read(params+20,2));r.u.mem_write(params+18,bytes((machine,0)));r.call(r.s['mm_audio_poll'])
  words=struct.unpack('>33H',r.u.mem_read(params,66));assert words[9]==machine<<8 and words[32]==0
  assert bytes(r.u.mem_read(params+20,2))==pitch
  for field in range(1,32):
   if field not in (9,10):assert words[field]==r.call(r.s['mm_native_default'],field,machine),(machine,field)
 print('PASS transitions MIDI vers les17machines audio du preset : defauts natifs propres, machine/Pitch conserves et marqueur efface')
 from test_midi_machine_sequence import Sequence
 sq=Sequence(img,dict(hex=blob.hex(),symbols=engine['symbols'],machine=17),pay,prepared=True)
 for at,raw in mem:sq.uc.mem_write(at,raw)
 sq.e.call(0x4005a274)
 for lane in range(6):
  sq.queue.clear();sq.sent.clear();assert sq.sequence(lane,74,17+lane)==1<<lane
  notes=[bytes(sq.uc.mem_read(pointer,16)) for pointer in sq.queue if pointer!=sq.s['mm_wakeup']]
  assert len(notes)==1 and notes[0][0]==1 and notes[0][8:11]==bytes((lane,60,97)),(lane,notes)
  # Acheminer le vrai message produit vers la vraie tache MIDI, pas seulement le compter.
  r.u.mem_write(SOUND+0x1000*lane+38,bytes((17,0)));params=SOUND+0x1000*lane+20
  r.call(r.s['mm_route_edit'],params,0,-127);r.call(r.s['mm_route_edit'],params,0,lane);r.call(r.s['mm_route_edit'],params,1,127)
  packet=r.call(0x4008a5d0);r.u.mem_write(packet,notes[0]);r.output.clear();r.queue.append(packet);r.run_worker()
  for port in ('DIN','USB'):assert (port,bytes((0x90|lane,60,97))) in r.output,(lane,port,r.output)
  sq.drain();assert bytes((0xb0|lane,74,17+lane)) in sq.sent
 print('PASS sequence complete avec MOut audio desactive : file audio -> une note -> vrai worker -> DIN et USB sur six canaux, CC locks conserves')
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
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 # Quitter une machine ferme ses notes live ET sequencees, pas celles d'une autre piste.
 for lane in (0,1):
  params=SOUND+0x1000*lane+20;r.u.mem_write(params+18,bytes((17,0)));r.call(r.s['mm_setup'],params)
  r.call(r.s['mm_route_edit'],params,0,-127);r.call(r.s['mm_route_edit'],params,0,2+lane)
  r.call(r.s['mm_route_edit'],params,1,-127);r.call(r.s['mm_route_edit'],params,1,2+lane)
 r.call(r.s['mm_audio_poll'])
 for lane in (0,1):
  r.call(r.s['mm_live_on'],lane,70+lane,99)
  packet=r.call(0x4008a5d0);raw=bytearray(16);raw[0]=1;raw[8]=lane;raw[9]=72+lane;raw[10]=99;struct.pack_into('>I',raw,12,1000)
  r.u.mem_write(packet,bytes(raw));r.queue.append(packet);r.run_worker()
 r.output.clear();r.u.mem_write(SOUND+38,b'\0\0');r.call(r.s['mm_audio_poll'])
 assert ('USB',bytes((0x82,70,0))) in r.output and ('USB',bytes((0x82,72,0))) in r.output,r.output
 assert not any(packet[1] in (71,73) for _,packet in r.output if len(packet)==3),r.output
 assert not any(port=='DIN' and packet[1] in (70,72) for port,packet in r.output if len(packet)==3),r.output
 r.output.clear();r.call(r.s['mm_audio_poll']);assert not r.output
 print('PASS sortie machine : note-offs live et sequences sur canal/port captures, autre piste intacte, pas de repetition')
 print('LIMITES : projet et ports physiques, rendu temps reel et utilisation manuelle a verifier sur appareil')
if __name__=='__main__':main()
