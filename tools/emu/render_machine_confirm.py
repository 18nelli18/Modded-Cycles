"""Menu principal sur le vrai Bitmap/MenuView/polices, trois selections."""
from pathlib import Path
source=(Path(__file__).parent/'test_acid_articulation_ui.py').read_text(encoding='utf-8').split('r,files,bind=fixture();')[0]
exec(compile(source,__file__,'exec'))
bc.ROOT=R/'output/native-screen-cache'
from render_midi_bank import png
OriginalRig=fx.Rig
class NativeDrawing(OriginalRig):
 def stub(self,u,addr,size,data):
  if addr in (0x40070dea,0x40071a04,0x400423e4):return
  return super().stub(u,addr,size,data)
fx.Rig=NativeDrawing
r,files,bind=fixture();s=m['activity_masks']['symbols']
for at,fn in [(0x400802ec,lambda a:0),(0x400cf044,lambda a:0),(0x400f4dc6,lambda a:1),(0x400f4e22,lambda a:0)]:bind(at,fn)
r.call(0x400e7dbc)
canvas,fb=0x931d0000,0x931d1000;r.call(0x40070172,canvas,128,64,fb,0)

for key,value in [('menu',1),('gc_level',1),('gc_page',0),('sx_submenu',0),('du_page',0),('mq_page',0)]:r.w32(s[key],value)
for cursor in (0,1,12):
 r.w32(s['gc_tree_cursor'],cursor);r.u.mem_write(fb,bytes(1024));r.call(s['mb_global_draw'],0,canvas)
 raw=bytes(r.u.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
 png(a.output.with_name(a.output.stem+'-'+str(cursor)+'.png'),pixels)
print('PASS native Global Mac screen rendering',flush=True)
