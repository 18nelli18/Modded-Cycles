"""Rendu du vrai code ColdFire sur Bitmap128x64, cas de largeur maximale."""
from pathlib import Path
source=(Path(__file__).parent/'test_acid_articulation_ui.py').read_text().split('r,files,bind=fixture();')[0]
exec(compile(source,__file__,'exec'))
from render_midi_bank import png
OriginalRig=fx.Rig
class NativeDrawing(OriginalRig):
 def stub(self,u,addr,size,data):
  if addr==0x40070dea:return
  return super().stub(u,addr,size,data)
fx.Rig=NativeDrawing
r,files,bind=fixture();canvas,fb=0x931d0000,0x931d1000;r.call(0x40070172,canvas,128,64,fb,0)
r.w32(s['sg_song'],4);r.u.mem_write(s['sg_song']+8,bytes([32,1,0,0,32,1,5,0,32,1,63,0,95,64,21,0]));r.w32(s['sg_cursor'],3)
rectangles=[]
def check(u,pc,size,data):
 sp=u.reg_read(C.UC_M68K_REG_A7);v=struct.unpack('>6I',u.mem_read(sp+4,24));assert 0<=v[1]<=v[3]<128 and 0<=v[2]<=v[4]<64,v;rectangles.append(v)
from unicorn import UC_HOOK_CODE
r.u.hook_add(UC_HOOK_CODE,check,begin=0x40070dea,end=0x40070dea)
r.call(s['sg_grid_draw'],0,canvas)
raw=bytes(r.u.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
png(a.output,pixels);print('PASS native grid render,',len(rectangles),'rectangles inside128x64',flush=True)

