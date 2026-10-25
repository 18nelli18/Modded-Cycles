"""Menu natif122 : gestes, cinq cibles et rendu pixels reels."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
from boot_candidate import boot
from lofi_ui import UI
from PIL import Image
version=sys.argv[1] if len(sys.argv)>1 else 'v122';stem='staging/all-features-polivoks-cpu-trim-test-'+version;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());d=m['sidechain']['symbols'];sx=m['scramble_mask']['symbols'];r,s,h,l,files,key,turn,data,bind=fixture(stem);r.s.update(d);r.s.update(sx);s.update(d)
bind(0x40012412,lambda a:r.r32(data+4));menu=m['symbols']['menu'];row=m['symbols']['row']
def key(code,flags=1):r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call(m['symbols']['wf_key'],EVENT)
def turn(knob,delta):r.delta=delta;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,knob,0,0));return r.call(sx['sx_encoder'],EVENT)
def click():key(32,1);key(32,16)
r.w32(menu,1);r.w32(row,7);click();assert r.r32(d['du_page'])==1
for src in range(6):
 r.w32(data+4,src);r.u.mem_write(d['du_config']+5*src,bytes([0,9,0,0,6]))
 for sub in range(5):r.w32(d['du_row'],sub);click()
 assert r.u.mem_read(d['du_config']+5*src,1)[0]==(63&~(1<<src))
for sub,hi in [(5,15),(6,7),(7,3),(8,15)]:
 r.w32(d['du_row'],sub);click();assert r.r32(d['du_edit'])==1
 turn(1,999);assert r.u.mem_read(d['du_config']+25+(sub-4),1)[0]==hi
 turn(1,-999);assert r.u.mem_read(d['du_config']+25+(sub-4),1)[0]==0
 key(12);key(12,16);assert not r.r32(d['du_edit']) and r.r32(d['du_page'])
key(12);key(12,16);assert not r.r32(d['du_page']) and r.r32(menu) and r.r32(row)==7
turn(1,1);assert r.r32(row)==0;turn(1,-1);assert r.r32(row)==7
r.w32(row,6);click();assert r.r32(sx['sx_submenu']);before=bytes(r.u.mem_read(sx['sx_masks'],6));click();assert bytes(r.u.mem_read(sx['sx_masks'],6))!=before
key(12);key(12,16);bind(d['du_root_draw'],lambda a:0);r.call(sx['sx_draw'],0,0);assert '/Scramble.cfg' not in files
print('PASS native key/encoder chain: all6sources choose only5others, 4control limits, BACK edit/submenu/root, eighth row, Scramble submenu retained',flush=True)
im,mem=boot(R/'output/firmware'/(stem+'.syx'));u=UI(im,mem[0],end=0x40200000);assert u.init_ok;u.call(0x400e7dbc);u.hooks.update({0x400cf866:('project',0x920a0000),0x40012412:('track',0)})
canvas,fb=0x920c0000,0x920c1000;u.call(0x40070172,canvas,128,64,fb,0);u.uc.mem_write(d['du_config'],bytes([62,12,4,2,15]+[0,9,0,0,6]*5));panels=[]
for name,fn,selected in [('root',d['du_root_draw'],7),('targets',d['du_sub_draw'],0),('targets-bottom',d['du_sub_draw'],4),('controls',d['du_sub_draw'],8)]:
 u.uc.mem_write(row,struct.pack('>I',selected));u.uc.mem_write(d['du_row'],struct.pack('>I',selected));u.uc.mem_write(fb,bytes(1024));u.call(fn,0,canvas);assert not u.bad and u.sp_ok,(name,u.bad)
 raw=bytes(u.uc.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)];img=Image.frombytes('L',(128,64),bytes(pixels));panels.append(img)
out=Image.new('L',(128*4+8*3,64),128)
for i,img in enumerate(panels):out.paste(img,(i*136,0))
path=R/'output/sidechain122-menus.png';out.resize((2144,256),Image.Resampling.NEAREST).save(path)
print('PASS four real native menu renders and drawing ABI',path,flush=True)
def width(text):
 addr,pointer=0x920d000c,0x920d1000
 u.uc.mem_write(addr-12,struct.pack('>III',len(text),len(text),0)+text.encode()+b'\0');u.uc.mem_write(pointer,struct.pack('>I',addr))
 return u.call(0x40072102,0x40140ab0,0xffffffff,pointer)
assert width('Sidechain')<=61
for label,values in [('Depth',[str((i*100+7)//15)+'%' for i in range(16)]),('Atk',[str(i)+'ms' for i in m['sidechain']['attack_ms']]),('Hold',[str(i)+'ms' for i in m['sidechain']['hold_ms']]),('Rel',['10ms','750ms','1s','1.5s','2s','3s'])]:
 assert 65+width(label)+4<=126-max(map(width,values)),(label,values)
assert 65+width('Track')+4<=109-max(width(str(i)) for i in range(1,7))
print('PASS native font widths: full Sidechain, five target rows and complete control ranges fit without label/value overlap',flush=True)
