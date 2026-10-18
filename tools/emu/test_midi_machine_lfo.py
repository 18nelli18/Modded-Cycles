"""Deux LFO MIDI sur vrai moteur OS, sans banque B ni writer depuis IRQ."""
import json,struct,pathlib,sys,tempfile
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_worker import Worker,ROOT
from test_midi_machine_notes import SOUND
from unicorn import UC_HOOK_CODE,m68k_const as mk
import emac,gen_sdvintage_7th as g7
FRAME=0x920c0000
def prepare(stock,data):
 r=Worker(stock,data)
 r.u.mem_write(0x4008a0f0,b"\x4e\xf9"+struct.pack(">I",r.s["mm_worker_hook"])+b"\x4e\x71")
 r.mac=emac.EMAC(r.u);r.mac.macsr=0x20
 with tempfile.TemporaryDirectory() as folder:
  file=pathlib.Path(folder)/'stock.bin';file.write_bytes(stock);r.mac.install(emac.disasm(str(file),0x40000400,0x4008f100,0x40091d50))
 r.u.hook_add(UC_HOOK_CODE,lambda u,pc,size,data: (_ for _ in ()).throw(AssertionError((hex(pc),bytes(u.mem_read(u.reg_read(mk.UC_M68K_REG_A7),48)).hex()))),begin=0x40092272,end=0x40092272)
 return r
def main():
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));data=json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text());r=prepare(stock,data);baseline=prepare(stock,data)
 initial=bytearray(476)
 for lane in range(6):
  p=[0]*33;p[1]=24000;p[2]=9<<8;p[3]=16384;p[4]=11<<8;p[8]=28000;p[9]=lane<<8;p[11]=16384
  struct.pack_into('>33H',initial,14+66*lane,*p)
 for tick in range(12):
  for rig,function in ((baseline,0x40091ab2),(r,r.s['mm_lfo_dispatch'])):
   rig.u.mem_write(FRAME,bytes(initial));rig.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
   rig.call(function,FRAME,14400,0)
  assert bytes(r.u.mem_read(FRAME,476))==bytes(baseline.u.mem_read(FRAME,476))
  assert bytes(r.u.mem_read(0x40fde838,192))==bytes(baseline.u.mem_read(0x40fde838,192))
 assert not r.queue and not r.output
 print('PASS six pistes audio seules : resultat et phases LFO natifs identiques, aucune file MIDI')
 # Deux pistes MIDI ; les autres pistes gardent leur modulation native exacte.
 for lane in (0,5):
  params=SOUND+lane*0x1000+20;r.call(r.s['mm_setup'],params)
  for lfo in range(2):
   r.call(r.s['mm_lfo_edit'],params,lfo,0,8000)
   r.call(r.s['mm_lfo_edit'],params,lfo,3,-54-lfo)
   r.call(r.s['mm_lfo_edit'],params,lfo,7,12000)
  initial[14+66*lane:14+66*(lane+1)]=r.u.mem_read(params,66)
 for tick in range(96):
  r.u.mem_write(FRAME,bytes(initial));r.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
  before=len(r.output);r.call(r.s['mm_lfo_dispatch'],FRAME,14400,0)
  assert len(r.output)==before,'Sortie MIDI IRQ'
  for lane in (0,5):assert bytes(r.u.mem_read(FRAME+14+66*lane,66))==initial[14+66*lane:14+66*(lane+1)]
  if r.queue:r.run_worker()
 packets=[packet for port,packet in r.output if port=='DIN']
 assert packets and {p[1] for p in packets}=={73,74},packets
 assert len(packets)<=32,len(packets)
 assert len({p[2] for p in packets})>2,packets
 print('PASS deux LFO par son MIDI, CC73/74 variables, tranche son intacte, sortie worker bornee a un CC/3blocs')
 print('LIMITES : cout temps reel et destinations physiques a confirmer sur appareil')
if __name__=='__main__':main()
