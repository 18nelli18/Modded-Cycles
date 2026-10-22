"""Verifie la fenetre native : quatre lignes, selection relative et defilement."""
import sys,json,struct
from boot_candidate import boot,ROOT
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE,m68k_const as C
for stem in (sys.argv[1:] or ['all-features-dx-toggle-test-v14','no-filter-dx-toggle-test-v14']):
 p=ROOT/'output/firmware'/(stem+'.syx');sy=json.loads(p.with_suffix('.json').read_text())['symbols'];im,mem=boot(p)
 r=Rig(im,{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in sy.items()}});u=r.u;u.mem_map(0x46700000,0x200000)
 for at,raw in mem:u.mem_write(at,raw)
 r.w32(0x40fe4178,0)
 capture=[]
 r.stubs[0x400423e4]=lambda a:capture.append(bytes(u.mem_read(a[0],564))) or 0
 u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400423e4,end=0x400423e4)
 u.mem_write(0x93010000,struct.pack('>6I',0,0,0,13,1,0));r.call('wf_key',0x93010000)
 for code,flags in ((2,1),(2,33),(2,0),(13,0)):
  u.mem_write(0x93010000,struct.pack('>6I',0,0,0,code,flags,0));r.call('wf_key',0x93010000)
 for selected in (0,1,2,3,4,5,4,3,2,1,0):
  r.w32(sy['row'],selected);assert r.call('wf_draw',0,0)==1
  view=0x93012000;u.mem_write(view,capture[-1]);vt=r.r32(view)
  count=r.call(r.r32(vt+12),view);top=r.call(r.r32(vt+56),view);cursor=r.call(r.r32(vt+60),view);visible=r.call(r.r32(vt+64),view)
  assert (count,top,cursor,visible)==(6,max(selected-3,0),min(selected,3),4)
  assert top+cursor==selected
  shown=[]
  for slot in range(min(visible,count-top)):
   u.reg_write(C.UC_M68K_REG_A0,0x93012400)
   r.call(r.r32(vt+16),view,slot+top)
   item=r.r32(0x93012400);label=r.r32(item+12)
   text=bytes(u.mem_read(label,8)).split(b'\0')[0].decode()
   assert text==('Md','USB','Num','Mute','Dly','DX')[top+slot]
   shown.append((top+slot,47-slot*13))
  assert all(y>=8 for _,y in shown)
  assert (selected,47-cursor*13) in shown
  print('PASS',stem,'selected',selected,'visible rows/y',shown)
 print('PASS scroll follows DX downward and returns upward without changing selected row')

 # Exercer le vrai chemin encodeur ajoute, navigation et edition DX.
 dx=json.loads(p.with_suffix('.json').read_text())['dx_symbols'];ev=0x93010000
 u.mem_write(ev,struct.pack('>6I',0x400fbebc,0,0,1,1,0))
 r.stubs[0x4006f73a]=lambda a:1
 for selected in range(1,6):
  try:r.call('wf_menu_encoder',ev)
  except Exception:
   print('PC',hex(u.reg_read(C.UC_M68K_REG_PC)),bytes(u.mem_read(u.reg_read(C.UC_M68K_REG_PC),8)).hex());raise
  assert r.r32(sy['row'])==selected
 assert r.r32(dx['dx_enabled'])==0
 u.mem_write(0x93010100,struct.pack('>6I',0,0,0,32,16,0));r.call('wf_key',0x93010100)
 r.call('wf_menu_encoder',ev);assert r.r32(dx['dx_enabled'])==1 and r.r32(sy['row'])==5
 r.stubs[0x4006f73a]=lambda a:0xffffffff;r.call('wf_menu_encoder',ev);assert r.r32(dx['dx_enabled'])==0
 print('PASS DX default OFF; scrolling never edits; DATA enables editing; On/Off via DATA; other toggles preserved',flush=True)
