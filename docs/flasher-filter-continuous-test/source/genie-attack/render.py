"""Rendu du firmware propre assemblé, polices/primitives OS réelles."""
exec(open('work/genie-attack-test/test-native.py').read().split('# Bypass exact')[0])
from render_midi_bank import png
r.call(0x400e7dbc);bitmap=C.FAKE+0x70000;fb=C.FAKE+0x71000;r.uc.mem_write(fb,bytes(1024));r.call(0x40070172,bitmap,128,64,fb,0)
r.w32(ss['sg_intro'],0);r.w32(ss['sg_row'],0);r.w32(ss['sg_edit'],0);r.call(ss['sg_render'],C.VIEWOBJ,bitmap)
b=r.rd(fb,1024);pixels=[]
for y in range(63,-1,-1):
 for x in range(128):pixels.append(0 if struct.unpack_from('>I',b,(x*2+y//32)*4)[0]&(1<<(31-y%32)) else 255)
png(P+'genie-lamp.png',pixels)
print('PASS native OLED raster saved')
