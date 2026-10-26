"""156/157 : vrais pixels des menus natifs avec leurs titres et lignes."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_stereo_chorus_popup import rig
from lofi_ui import SCRATCH,pix
from unicorn import m68k_const as C
from PIL import Image
v=sys.argv[1] if len(sys.argv)>1 else 'v156';stem='staging/all-features-polivoks-cpu-trim-test-'+v;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());s=m['groove_strum']['symbols'];b=m['symbols'];u=rig(stem);u.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
def wr(a,n):u.uc.mem_write(a,struct.pack('>I',n))
bmp,fb=SCRATCH+0x2000,SCRATCH+0x2100;u.call(0x40070172,bmp,128,64,fb,0);wr(0x40fe4178,0);wr(b['menu'],1)
out=W/('private-'+v);out.mkdir(exist_ok=True)
cases=[('groove','gc_sub_draw',0),('groove-scroll','gc_sub_draw',4)] if v=='v156' else [('mod','gc_top_draw',0),('global','gc_global_draw',0),('global-scroll','gc_global_draw',7),('track','gc_track_draw',0),('groove','gc_sub_draw',0),('human','gc_human_draw',1)]
for name,fn,row in cases:
 wr(s['gc_row'],row)
 if 'gc_tree_cursor' in s:wr(s['gc_tree_cursor'],row);wr(s['gc_level'],1 if name.startswith('global') else 2 if name=='track' else 0);wr(s['gc_page'],2 if name=='human' else 1)
 u.uc.mem_write(fb,bytes(1024));u.call(s[fn],0,bmp);assert u.sp_ok and not u.bad,(name,u.bad)
 raw=bytes(u.uc.mem_read(fb,1024));assert any(raw),name
 im=Image.frombytes('L',(128,64),bytes(0 if pix(raw,x,63-y) else 255 for y in range(64) for x in range(128)));im.resize((768,384),Image.Resampling.NEAREST).save(out/(name+'.png'))
 print('PASS native menu pixels and stack',v,name,flush=True)
