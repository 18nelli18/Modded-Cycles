"""Menu natif122 : gestes, cinq cibles et rendu pixels reels."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
from boot_candidate import boot
from lofi_ui import UI
from PIL import Image
version=sys.argv[1] if len(sys.argv)>1 else 'v130';stem='staging/all-features-polivoks-cpu-trim-test-'+version;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());d=m['sidechain']['symbols'];sx=m['scramble_mask']['symbols'];r,s,h,l,files,key,turn,data,bind=fixture(stem);r.s.update(d);r.s.update(sx);s.update(d)
bind(0x40012412,lambda a:r.r32(data+4));menu=m['symbols']['menu'];row=m['symbols']['row']
def key(code,flags=1):r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call(m['symbols']['wf_key'],EVENT)
def turn(knob,delta):r.delta=delta;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,knob,0,0));return r.call(sx['sx_encoder'],EVENT)
def click():key(32,1);key(32,16)
r.w32(menu,1);r.w32(row,7);click();assert r.r32(d['du_page'])==1
for src in range(6):
 r.w32(data+4,src);r.u.mem_write(d['du_config']+5*src,bytes([0,9,0,0,6]))
 for sub in range(5):r.w32(d['du_row'],sub);click()
 assert r.u.mem_read(d['du_config']+5*src,1)[0]==(63&~(1<<src))
for sub,hi in [(7,15),(8,7),(9,3),(10,15)]:
 r.w32(d['du_row'],sub);click();assert r.r32(d['du_edit'])==1
 turn(1,999);assert r.u.mem_read(d['du_config']+25+(sub-6),1)[0]==hi
 turn(1,-999);assert r.u.mem_read(d['du_config']+25+(sub-6),1)[0]==0
 key(12);key(12,16);assert not r.r32(d['du_edit']) and r.r32(d['du_page'])
key(12);key(12,16);assert not r.r32(d['du_page']) and r.r32(menu) and r.r32(row)==7
turn(1,1);assert r.r32(row)==0;turn(1,-1);assert r.r32(row)==7
r.w32(row,6);click();assert r.r32(sx['sx_submenu']);before=bytes(r.u.mem_read(sx['sx_masks'],6));click();assert bytes(r.u.mem_read(sx['sx_masks'],6))!=before
key(12);key(12,16);bind(d['du_root_draw'],lambda a:0);r.call(sx['sx_draw'],0,0);assert '/Scramble.cfg' not in files
print('PASS native key/encoder chain: all6sources choose only5others, 4control limits, BACK edit/submenu/root, eighth row, Scramble submenu retained',flush=True)
im,mem=boot(R/'output/firmware'/(stem+'.syx'));u=UI(im,mem[0],end=0x40200000);assert u.init_ok;u.call(0x400e7dbc);u.hooks.update({0x400cf866:('project',0x920a0000),0x40012412:('track',0)})
canvas,fb=0x920c0000,0x920c1000;u.call(0x40070172,canvas,128,64,fb,0);u.uc.mem_write(d['du_config'],bytes([62,12,4,2,15]+[0,9,0,0,6]*5));panels=[]
for name,fn,selected in [('root',d['du_root_draw'],7),('targets',d['du_sub_draw'],0),('targets-bottom',d['du_sub_draw'],4),('controls',d['du_sub_draw'],10)]:
 u.uc.mem_write(row,struct.pack('>I',selected));u.uc.mem_write(d['du_row'],struct.pack('>I',selected));u.uc.mem_write(fb,bytes(1024));u.call(fn,0,canvas);assert not u.bad and u.sp_ok,(name,u.bad)
 raw=bytes(u.uc.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)];img=Image.frombytes('L',(128,64),bytes(pixels));panels.append(img)
out=Image.new('L',(128*4+8*3,64),128)
for i,img in enumerate(panels):out.paste(img,(i*136,0))
path=Path(__file__).resolve().parent/'sidechain-lab/menus.png';out.resize((2144,256),Image.Resampling.NEAREST).save(path)
print('PASS four real native menu renders and drawing ABI',path,flush=True)
if m['sidechain'].get('control_label_x')==72:
 controls=Image.new('L',(128*4+8*3,64),128)
 for i,selected in enumerate(range(7,11)):
  u.uc.mem_write(d['du_row'],struct.pack('>I',selected));u.uc.mem_write(fb,bytes(1024));u.call(d['du_sub_draw'],0,canvas);assert not u.bad and u.sp_ok
  raw=bytes(u.uc.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
  controls.paste(Image.frombytes('L',(128,64),bytes(pixels)),(i*136,0))
 controls.resize((2144,256),Image.Resampling.NEAREST).save(path.with_name('controls.png'))
 print('PASS all four selected control rows rendered natively',flush=True)
def width(text):
 addr,pointer=0x920d000c,0x920d1000
 u.uc.mem_write(addr-12,struct.pack('>III',len(text),len(text),0)+text.encode()+b'\0');u.uc.mem_write(pointer,struct.pack('>I',addr))
 return u.call(0x40072102,0x40140ab0,0xffffffff,pointer)
assert width(m['sidechain'].get('menu_label','Sidechain'))<=61
labels=m['sidechain'].get('control_labels',['Depth','Atk','Hold','Rel']);label_x=m['sidechain'].get('control_label_x',65)
for label,values in zip(labels,[[str((i*100+7)//15)+'%' for i in range(16)],[str(i)+'ms' for i in m['sidechain']['attack_ms']],[str(i)+'ms' for i in m['sidechain']['hold_ms']],['10ms','750ms','1s','1.5s','2s','3s']]):
 assert label_x+width(label)+4<=126-max(map(width,values)),(label,values)
if m['sidechain'].get('target_label')=='Trk.':
 assert 72+max(width('Trk. '+str(i)) for i in range(1,7))+4<119
else:
 assert 65+width('Track')+4<=109-max(width(str(i)) for i in range(1,7))
print('PASS native font widths: menu label, five target rows and complete control ranges fit without label/value overlap',flush=True)
if m['sidechain'].get('label_left'):
 from unicorn import UC_HOOK_CODE,m68k_const as C
 seen=[]
 def label_call(uc,pc,size,user):
  sp=uc.reg_read(C.UC_M68K_REG_A7);args=struct.unpack('>7I',uc.mem_read(sp+4,28))
  if bytes(uc.mem_read(args[5],3))==b'%s\0':
   text=bytes(uc.mem_read(args[6],16)).split(b'\0')[0].decode('ascii',errors='replace')
   if text in (m['sidechain']['menu_label'],'>'):seen.append((text,args[2],args[4]))
 u.uc.mem_write(row,struct.pack('>I',7))
 h=u.uc.hook_add(UC_HOOK_CODE,label_call,begin=0x40071a04,end=0x40071a04);u.call(d['du_root_draw'],0,canvas);u.uc.hook_del(h)
 pos=next(x for x in seen if x[0]==m['sidechain']['menu_label']);arrow=seen[-1]
 assert pos==(m['sidechain']['menu_label'],72,0x10) and arrow[0]=='>' and arrow[2]==4
 assert pos[1]+width(pos[0])+4<arrow[1]-width('>')
 print('PASS native S.Chn label left x72 matches other rows, separate > arrow and no overlap/clipping',flush=True)

r.w32(menu,1);r.w32(d['du_page'],1);r.w32(d['du_edit'],0)
for source in range(6):
 r.w32(data+4,source);before=bytes(r.u.mem_read(d['du_config'],30));prior=r.u.mem_read(d['du_fx'],6)[source]
 for selected,mask in ((5,1),(6,2)):
  r.w32(d['du_row'],selected);click();assert r.u.mem_read(d['du_fx'],6)[source]==(prior^mask)
  assert not r.r32(d['du_edit']);assert bytes(r.u.mem_read(d['du_config'],30))==before
  click();assert r.u.mem_read(d['du_fx'],6)[source]==prior
 r.w32(d['du_row'],11);click();assert r.u.mem_read(d['du_config']+5*source,1)[0]==(before[5*source]^64);click()
r.w32(d['du_row'],10);turn(1,1);assert r.r32(d['du_row'])==11;turn(1,1);assert r.r32(d['du_row'])==0;turn(1,-1);assert r.r32(d['du_row'])==11
key(5);assert not r.r32(menu) and not r.r32(d['du_page'])
print('PASS Rev./Del. toggle per source without numeric editing or track/mute changes;12rows wrap and MACHINES still exits',flush=True)
panels=[]
for selected,fxmask,mute in [(5,0,0),(5,1,0),(6,2,0),(11,3,64)]:
 u.uc.mem_write(d['du_config'],bytes([62|mute,12,4,2,15]+[0,9,0,0,6]*5));u.uc.mem_write(d['du_fx'],bytes([fxmask,0,0,0,0,0]));u.uc.mem_write(d['du_row'],struct.pack('>I',selected));u.uc.mem_write(fb,bytes(1024));u.call(d['du_sub_draw'],0,canvas);assert not u.bad and u.sp_ok
 raw=bytes(u.uc.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)];panels.append(Image.frombytes('L',(128,64),bytes(pixels)))
image=Image.new('L',(536,64),128)
for i,panel in enumerate(panels):image.paste(panel,(136*i,0))
path=R/'output/sidechain-returns130.png';image.resize((2144,256),Image.Resampling.NEAREST).save(path)
assert 72+max(width('Rev.'),width('Del.'))+4<119
print('PASS real128x64 return checkboxes and Mute rendered with font bounds',path,flush=True)
