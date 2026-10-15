"""Vérifier l'orientation des deux icônes avec le vrai blit du firmware."""
import struct,pathlib
from render_midi_bank import DrawingRig,png
from chord_keys_pr87 import load_stock
r=DrawingRig(load_stock('firmware/model-cycles_OS1.13.syx'),{'writes':[]},{'writes':[],'symbols':{}})
bitmap,fb,obj,pix=0x93006000,0x93090000,0x93010000,0x93011000
for suffix,w,h,palette in [('A_48x33',48,33,0x4016ac78),('B_34x34',34,34,0x4017c20c)]:
 r.u.mem_write(fb,bytes(1024));r.call(0x40070172,bitmap,128,64,fb,0)
 r.u.mem_write(obj,struct.pack('>7I',0x401117c8,w,h,2,pix,palette,0));r.u.mem_write(pix,pathlib.Path('work/sample-wizard-main/src/sampler_icons/sampler_icon_'+suffix+'.bin').read_bytes());r.call(0x40071da4,bitmap,obj,64,32,1)
 b=bytes(r.u.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',b,(x*2+y//32)*4)[0]&(1<<(31-y%32)) else 255 for y in range(63,-1,-1) for x in range(128)];png('work/sample-wizard-main/native-hat-'+suffix+'.png',pixels)
print('PASS deux icônes tracées par le blit natif, aucune copie de routine firmware exportée.')
