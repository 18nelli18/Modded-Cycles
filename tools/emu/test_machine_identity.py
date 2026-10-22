"""Cartes MACHINES natives : six stock exactes, douze identites distinctes."""
"""Ecran MACHINES reel : deux lignes/police natives, nom mutable sans influence."""
import struct,json
from boot_candidate import ROOT,boot
from lofi_ui import UI,STOP,STACK
from render_midi_bank import png
from unicorn import UC_HOOK_CODE,m68k_const as C

def render(stem,machine=6,mutable=b'Wizard\0',draw_icons=True):
 im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));u=UI(im,mem[0],end=0x40200000);assert u.init_ok
 u.call(0x400e7dbc)
 vec1,vec2=0x920a0000,0x920b0000
 for ptr,vec in [(0x40fe32cc,vec1),(0x40fe384c,vec2)]:
  u.uc.mem_write(ptr,struct.pack('>3I',vec,vec+168,vec+168))
 for i in range(6):
  u.call(0x40070172,vec1+28*i,48,33,0x4016adf8+0x180*i,0x4016ac78)
  u.call(0x40070172,vec2+28*i,34,34,0x4017c31c+0x110*i,0x4017c20c)
 u.call(0x401bf69c)
 canvas,fb,view=0x920c0000,0x920c1000,0x920d0000
 u.call(0x40070172,canvas,128,64,fb,0);u.uc.mem_write(fb,bytes(1024));u.uc.mem_write(view+108,struct.pack('>I',0x40ea14d4))
 u.uc.mem_write(0x401b11a8,mutable.ljust(18,b'\0'));texts=[];images=[]
 def observe(uc,pc,size,data):
  if pc==0x400a2680:uc.emu_stop();return
  sp=uc.reg_read(C.UC_M68K_REG_A7);a=struct.unpack('>8I',uc.mem_read(sp+4,32))
  if pc==0x40071a04:texts.append((u.cstr(a[6]),a[1],a[2],a[3],a[4]))
  if pc==0x40071da4:
   images.append(a[:5])
   if not draw_icons:
    uc.reg_write(C.UC_M68K_REG_PC,struct.unpack('>I',uc.mem_read(sp,4))[0]);uc.reg_write(C.UC_M68K_REG_A7,sp+4)
 for at in [0x400a2680,0x40071a04,0x40071da4]:u.uc.hook_add(UC_HOOK_CODE,observe,begin=at,end=at)
 sp=STACK-0x800;u.uc.mem_write(sp,bytes(256))
 for r,v in [(C.UC_M68K_REG_A7,sp),(C.UC_M68K_REG_D2,canvas),(C.UC_M68K_REG_D3,machine),(C.UC_M68K_REG_A2,view)]:u.uc.reg_write(r,v)
 u.uc.emu_start(0x400a25e0,STOP,count=2000000)
 assert u.uc.reg_read(C.UC_M68K_REG_PC)==0x400a2680
 assert u.uc.reg_read(C.UC_M68K_REG_A7)==sp
 assert u.uc.reg_read(C.UC_M68K_REG_D2)==canvas and u.uc.reg_read(C.UC_M68K_REG_D3)==machine
 assert not u.bad
 raw=bytes(u.uc.mem_read(fb,1024))
 return texts,images,raw


stem=__import__('sys').argv[1] if len(__import__('sys').argv)>1 else 'all-features-machine-identity-test-v15'
for machine in range(18):
 texts,images,raw=render(stem,machine)
 if machine<6:
  old=render('all-features-dx-ltc-main-212',machine)
  assert (texts,images,raw)==old, machine
 else:
  meta=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())
  left=meta['identity_stats']+28*(machine-6);right=meta['identity_icons']+28*(machine-6)
  assert any(a[1]==left for a in images),(machine,images,left)
  if machine==6:
   original=render('all-features-dx-ltc-main-212',machine)
   assert images[-1]==original[1][-1], 'chapeau natif remplace'
   # Moitie droite : aucun pixel du chapeau ni de son entourage ne change.
   assert raw[64*8:]==original[2][64*8:], 'chapeau natif modifie'
  else:assert any(a[1]==right for a in images),(machine,images,right)
 pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
 png(ROOT/f'output/firmware/{stem}-machine-{machine}.png',pixels)
 print('PASS',machine,texts[0][0],'native pixels/stack/registers; expected identity sprites' if machine>=6 else 'stock pixels exact',flush=True)
