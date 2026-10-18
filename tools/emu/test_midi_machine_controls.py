"""Codec CC ColdFire : bornes, champs natifs preserves, assignation distincte.

Ne prouve pas encore dispatch UI, locks/save natifs ni affichage. Aucun
fichier de firmware produit ; toutes les fonctions teste es sont compilees.
"""
import json,pathlib,struct,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_machine_notes import Rig
import gen_sdvintage_7th as g7
def main():
 root=HERE.parent.parent;data=json.loads((root/'build/midi-machine/controls.json').read_text())
 r=Rig(g7.cycles_main(str(root/'firmware/model-cycles_OS1.13.syx')),bytes.fromhex(data['hex']),0x46800000)
 sy={k:int(v,16) for k,v in data['symbols'].items()};call=lambda name,*args:r.call(sy['mm_cc_'+name],*args)
 for cc in range(-1,128):
  for value in (0,1,63,64,126,127):
   packed=call('pack',cc,value);assert packed==(cc+1)*128+value
   assert call('number',packed)==cc&0xffffffff;assert call('value',packed)==value
 for cc,value in ((-2,64),(128,64),(-1,128),(0,0xffffffff)):assert call('pack',cc,value)==0xffffffff
 print('PASS CC OFF/0..127 et valeurs0..127, representation sans collision, entrees invalides')
 ptr=0x920a0000;original=[0x100+i for i in range(33)];original[9]=6<<8
 for track in range(6):
  at=ptr+128*track;r.u.mem_write(at,struct.pack('>33H',*original))
  before=bytes(r.u.mem_read(at,66))
  for knob in range(12):assert call('read',at,knob)==64
  assert bytes(r.u.mem_read(at,66))==before,'lecture qui modifie le son'
  for knob in range(12):
   assert call('edit',at,knob,knob+1,1)==(knob+1)*128+64
   assert call('edit',at,knob,5,0)==(knob+1)*128+69
  words=struct.unpack('>33H',r.u.mem_read(at,66))
  assert words[:11]==tuple(original[:11]) and words[23:32]==tuple(original[23:32])
  assert words[32]==0x4d49
 assert not r.output,'codec qui transmet pendant une assignation'
 print('PASS six pistes x12CC ; assigner preserve la valeur ; modifier preserve le CC ; aucun envoi MIDI')
 saved=bytes(r.u.mem_read(ptr,66));assert call('edit',ptr,12,1,1)==0xffffffff
 assert bytes(r.u.mem_read(ptr,66))==saved;assert call('edit',0,0,1,1)==0xffffffff
 assert call('edit',ptr,0,0x7fffffff,1)==128*128+69
 assert call('edit',ptr,0,0x80000000,1)==128+69
 assert call('edit',ptr,0,-127,1)==69;assert call('edit',ptr,0,12,0)==69
 print('PASS bornes/saturation et OFF ; notes, machine et LFO natifs preserves')
 print('LIMITES : raccordement au dispatch, setters, locks, sauvegarde et ecran encore requis')
if __name__=='__main__':main()
