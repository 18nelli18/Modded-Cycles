"""MIDI seul : vrai setter natif, CC/popup et aucune vue de synthese consommee.

Getters peripheriques et primitives LCD instrumentes ; les wrappers et le
setter OS sont executes. Pas de preuve materielle ni de composition complete.
"""
import json,pathlib,struct,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_notes import Rig,SOUND,VT,STACK,STOP
from unicorn import UC_HOOK_CODE,m68k_const as mk
import gen_sdvintage_7th as g7
ROOT=HERE.parent.parent;EVENT=0x920b0000
class UI(Rig):
 def stub(self,at,fn):
  if at==0x40012412:fn=lambda a:self.track
  if at==0x4007faf4:fn=lambda a:int(a[0]==13 and self.assign)
  return super().stub(at,fn)
 def __init__(self,stock,data,pay=0x46800000):
  self.track=0;self.assign=True;self.popups=[];self.lines=[];self.notified=0
  super().__init__(stock,bytes.fromhex(data['hex']),pay)
  self.s={k:int(v,16) for k,v in data['symbols'].items()}
  self.stub(self.s['mm_popup'],lambda a:self.popups.append(self.string(a[0])))
  self.stub(0x40071a04,lambda a:self.lines.append(self.string(a[6])))
  self.stub(0x40070dea,lambda a:0)
  self.word(VT+16,0x92060400);self.stub(0x92060400,lambda a:0)
  for lane in range(6):self.u.mem_write(SOUND+0x1000*lane+38,bytes((data.get('machine',6),0)))
 def string(self,at):return bytes(self.u.mem_read(at,64)).split(b'\0')[0].decode()
 def event(self,knob,delta):self.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,knob+2,delta&0xffffffff,0));return EVENT
def main():
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));data=json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text());r=UI(stock,data)
 assert r.call(r.s['mm_encoder'],r.event(0,75))==1
 params=struct.unpack('>33H',r.u.mem_read(SOUND+20,66));assert params[11]==75*128+64 and params[32]==0x4d49
 assert not r.output and r.popups[-1]=='CC01 ASSIGN 074',r.popups
 r.assign=False;assert r.call(r.s['mm_encoder'],r.event(0,1))==1
 assert r.popups[-1]=='CC01 074 = 065';assert ('DIN',bytes((0xb0,74,65))) in r.output
 assert r.call(r.s['mm_draw'],0,0x920c0000)==1
 assert r.lines[0]=='T1 MIDI OUT' and len(r.lines)==13
 assert not any(any(w in line for w in ('Color','Shape','Sweep','Contour','Decay','Filter','Resonance')) for line in r.lines+r.popups)
 print('PASS setter natif, assignation sans CC, valeur MIDI transmise, ecran et popup MIDI seuls')
 for at,name,expected in ((0x40077532,'mm_encoder_hook','4fefffc048d70c04'),(0x4001b22a,'mm_draw_hook','4e56ffc048d73cfc'),(0x40077720,'mm_ui_key_hook','4fefffa048d77cfc')):
  assert bytes(r.u.mem_read(at,8)).hex()==expected,(hex(at),bytes(r.u.mem_read(at,8)).hex())
  r.u.mem_write(at,b'\x4e\xf9'+struct.pack('>I',r.s[name])+b'\x4e\x71')
 r.stub(0x400802e0,lambda a:(_ for _ in ()).throw(AssertionError('allocation/vue synthese depuis geste CC')))
 original=[0x100+i for i in range(33)];original[9]=6<<8
 for lane in range(6):
  r.track=lane;r.u.mem_write(SOUND+0x1000*lane+20,struct.pack('>33H',*original))
  for knob in range(12):
   r.assign=True;r.output.clear();assert r.call(0x40077532,0,r.event(knob,knob+1))==1
   assert not r.output and r.popups[-1]==f'CC{knob+1:02} ASSIGN {knob:03}'
   r.assign=False;assert r.call(0x40077532,0,r.event(knob,1))==1
   assert ('DIN',bytes((0xb0,knob,65))) in r.output
  words=struct.unpack('>33H',r.u.mem_read(SOUND+0x1000*lane+20,66))
  assert words[:11]==tuple(original[:11]) and words[23:32]==tuple(original[23:32])
  r.lines.clear();r.call(0x4001b22a,0,0x920c0000);assert r.lines[0]==f'T{lane+1} MIDI OUT' and len(r.lines)==13
 # La release SETTINGS est consommee apres assignation, sans ouvrir CONFIG.
 r.assign=True;r.call(0x40077532,0,r.event(0,1));r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,13,0,0))
 assert r.call(0x40077720,0,EVENT)==1
 print('PASS vrais dispatchs : six pistes x12potards, aucun handler/parametre synthese, ecran MIDI, release SETTINGS consommee')
 print('LIMITES : locks, sauvegarde, composition complete et verification physique encore requis')
if __name__=='__main__':main()
