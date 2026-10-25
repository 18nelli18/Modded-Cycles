"""Dixieme ligne native : toggle par source, navigation et rendu Off/On."""
from pathlib import Path
import runpy,struct,sys
R0=Path(__file__).resolve().parent
version=sys.argv[1] if len(sys.argv)>1 else 'v128';sys.argv=[str(R0/'test_sidechain_ui122.py'),version]
g=runpy.run_path(str(R0/'test_sidechain_ui122.py'))
r,d,u=g['r'],g['d'],g['u'];click,turn=g['click'],g['turn'];data=g['data'];width=g['width']
r.w32(d['du_page'],1);r.w32(d['du_edit'],0)
for source in range(6):
 r.w32(data+4,source);r.w32(d['du_row'],9);at=d['du_config']+5*source;before=bytes(r.u.mem_read(d['du_config'],30))
 click();after=bytes(r.u.mem_read(d['du_config'],30));expected=bytearray(before);expected[5*source]^=64;assert after==bytes(expected)
 assert not r.r32(d['du_edit']);click();assert bytes(r.u.mem_read(d['du_config'],30))==before
r.w32(d['du_row'],8);turn(1,1);assert r.r32(d['du_row'])==9;turn(1,1);assert r.r32(d['du_row'])==0;turn(1,-1);assert r.r32(d['du_row'])==9
print('PASS Mute DATA toggles only current source, keeps targets, never enters numeric editing; tenth-row navigation wraps safely',flush=True)
from PIL import Image
canvas,fb=g['canvas'],g['fb'];panels=[]
for flag in (0,64):
 u.uc.mem_write(d['du_config'],bytes([62|flag,12,4,2,15]+[0,9,0,0,6]*5));u.uc.mem_write(d['du_row'],struct.pack('>I',9));u.uc.mem_write(fb,bytes(1024))
 u.call(d['du_sub_draw'],0,canvas);assert not u.bad and u.sp_ok
 raw=bytes(u.uc.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)];panels.append(Image.frombytes('L',(128,64),bytes(pixels)))
assert 72+width('Mute')+4<=119-max(width('On'),width('Off'))
image=Image.new('L',(264,64),128)
for i,p in enumerate(panels):image.paste(p,(136*i,0))
path=R0.parents[1]/'output/sidechain128-mute.png';image.resize((1056,256),Image.Resampling.NEAREST).save(path)
print('PASS native128x64 Mute Off/On renders, font bounds and drawing ABI',path,flush=True)
