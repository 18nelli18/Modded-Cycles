"""Vraie tache MIDI : CC bornes/coalesces, aucun writer IRQ, notes natives.

La mailbox/pilotes sont instrumentes ; le dispatch OS et le routeur tournent.
Ne mesure ni debit DIN physique ni ordonnanceur temps reel.
"""
import json,struct,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_ui import UI,ROOT,STACK,STOP
from unicorn import m68k_const as mk
import gen_sdvintage_7th as g7
class Worker(UI):
 def send(self,port,args):
  assert not self.u.reg_read(mk.UC_M68K_REG_SR)&0x700,'Writer MIDI depuis IRQ'
  return super().send(port,args)
 def run_worker(self):
  self.u.reg_write(mk.UC_M68K_REG_A7,STACK);self.u.mem_write(STACK,struct.pack('>I',STOP));self.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  self.u.emu_start(0x4008a0ba,STOP,count=3000000);assert self.u.reg_read(mk.UC_M68K_REG_PC)==STOP

def main():
 r=Worker(g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text()))
 at=0x4008a0f0;assert bytes(r.u.mem_read(at,8)).hex()=='720126407113b280'
 r.u.mem_write(at,b'\x4e\xf9'+struct.pack('>I',r.s['mm_worker_hook'])+b'\x4e\x71')
 put=lambda lane,knob,ch,cc,value,port:r.call(r.s['mm_cc_put'],lane,knob,ch,cc,value,port)
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
 for lane in range(6):
  for knob in range(12):
   for value in (1,9,31,127):assert put(lane,knob,lane,knob,value,4)==1
 assert len(r.queue)==1 and not r.output,'Token multiplie ou sortie IRQ'
 assert r.u.reg_read(mk.UC_M68K_REG_SR)==0x2700
 token=r.queue.pop(0);r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 assert r.call(r.s['mm_cc_worker'],token)==1
 assert len(r.output)==16 and len(r.queue)==1,'Budget huit CC DIN+USB depasse'
 r.run_worker()
 for port in ('DIN','USB'):
  actual=[packet for dest,packet in r.output if dest==port]
  expected=[bytes((0xb0|lane,knob,127)) for lane in range(6) for knob in range(12)]
  assert actual==expected,(port,len(actual))
 print('PASS288changements IRQ =>72CC coalesces, un token,8CC par passage, DIN+USB hors IRQ')
 r.output.clear();assert put(5,11,15,127,0,2)==1;r.run_worker();assert r.output
 assert not r.queue;assert put(0,0,0,0,1,4)==1;r.run_worker()
 for args in ((6,0,0,0,0,4),(0,14,0,0,0,4),(0,0,16,0,0,4),(0,0,0,128,0,4),(0,0,0,0,128,4),(0,0,0,0,0,1)):
  assert put(*args)==0
 assert not r.queue
 print('PASS rearmement apres vidage, routes explicites et bornes ; aucune attente/allocation dans producteur')
 # Note puis expiration dans le vrai worker apres passage par le nouveau hook.
 r.output.clear();r.channel=2;r.u.mem_write(0x40fdd580,bytes(range(6)))
 message=0x920b1000;raw=bytearray(16);raw[0]=1;raw[8]=2;raw[9]=60;raw[10]=100;struct.pack_into('>I',raw,12,10)
 r.u.mem_write(message,bytes(raw));r.queue.append(message);r.run_worker()
 assert any(packet==bytes((0x92,60,100)) for _,packet in r.output),r.output
 print('PASS message note natif non consomme par le hook CC ; branchement et registres du worker conserves')
 r.output.clear();r.queue.append(message)
 for knob in range(12):assert put(2,knob,2,knob,80+knob,4)==1
 r.run_worker()
 for port in ('DIN','USB'):
  messages=[packet for dest,packet in r.output if dest==port]
  assert messages[:12]==[bytes((0xb2,k,80+k)) for k in range(12)]
  assert bytes((0x92,60,100)) in messages[12:]
 print('PASS12CC avant attaque meme si message note deja en tete de mailbox ; autres notes gerees par OS')
 # Routage du son applique aux notes natives, puis port capture a l'expiration.
 r.u.mem_write(0x40082726,b'\x4e\xf9'+struct.pack('>I',r.s['mm_note_route'])+b'\x4e\x71')
 r.u.ctl_remove_cache(0x40082726,0x4008273c)
 params=0x92080000+0x2000+20
 r.call(r.s['mm_setup'],params);r.call(r.s['mm_route_edit'],params,0,-11)
 r.call(r.s['mm_route_edit'],params,1,2)
 raw[9]=65;r.u.mem_write(message,bytes(raw));r.output.clear();r.queue.append(message);r.run_worker()
 assert r.output==[('USB',bytes((0x95,65,100)))],r.output
 r.call(r.s['mm_route_edit'],params,0,1);r.call(r.s['mm_route_edit'],params,1,1)
 # La fixture conserve un evenement futur dans la liste native d'expiration.
 raw[9]=66;struct.pack_into('>I',raw,12,1000);r.u.mem_write(message,bytes(raw));r.queue.append(message);r.run_worker()
 expiry=message+64;event=bytearray(16);event[0]=3;struct.pack_into('>I',event,12,100)
 r.u.mem_write(expiry,bytes(event));r.queue.append(expiry);r.run_worker()
 assert ('USB',bytes((0x95,65,0))) in r.output,r.output
 assert not any(port=='DIN' and packet==bytes((0x95,65,0)) for port,packet in r.output)
 print('PASS note sequence sur canal/port propres ; expiration sur port capture apres changement de reglages')
 # Parcours CC : ne rien transmettre, meme si un token precede le geste.
 r.output.clear();r.queue.clear();r.word(r.s['mm_assign_lane'],6)
 assert put(2,0,2,3,64,4)==1
 r.word(r.s['mm_assign_lane'],2)
 assert put(2,0,2,4,64,4)==0 and put(2,12,2,3,64,4)==0
 r.run_worker();assert not r.output,r.output
 assert put(1,0,1,74,75,4)==1;r.run_worker();assert ('DIN',bytes((0xb1,74,75))) in r.output
 r.word(r.s['mm_assign_lane'],6);r.output.clear();assert put(2,0,2,3,65,4)==1;r.run_worker()
 assert ('DIN',bytes((0xb2,3,65))) in r.output
 print('PASS assignation : CC sequence/LFO et ancien token bloques pour la piste ; autres pistes et reprise apres release conservees')
if __name__=='__main__':main()
