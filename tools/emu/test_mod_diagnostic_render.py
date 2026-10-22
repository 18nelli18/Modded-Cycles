"""Rendu natif final : DX Off/On, valeurs LTC et SIL sans chevauchement."""
import json,struct
from boot_candidate import ROOT,boot
from lofi_ui import UI
from render_midi_bank import png
from unicorn import UC_HOOK_CODE,m68k_const as C
for stem in ['all-features-dx-ltc-main-212']:
 p=ROOT/'output/firmware'/(stem+'.syx');m=json.loads(p.with_suffix('.json').read_text());sy=m['symbols'];dx=m['dx_symbols'];im,mem=boot(p);r=UI(im,mem[0],end=0x40200000);assert r.init_ok;r.call(0x400e7dbc)
 canvas,fb=0x920c0000,0x920c1000;r.call(0x40070172,canvas,128,64,fb,0);r.uc.mem_write(sy['row'],struct.pack('>I',5));texts=[]
 def observe(u,pc,size,data):
  sp=u.reg_read(C.UC_M68K_REG_A7);a=struct.unpack('>7I',u.mem_read(sp+4,28));texts.append(r.cstr(a[6]) if r.cstr(a[5])=='%s' else r.cstr(a[5]))
 r.uc.hook_add(UC_HOOK_CODE,observe,begin=0x40071a04,end=0x40071a04)
 r.uc.mem_write(sy['lm_enabled'],struct.pack('>I',1))
 r.uc.mem_write(sy['wf_stock'],struct.pack('>I',0))
 for on in [0,1,2]:
  r.uc.mem_write(sy['row'],struct.pack('>I',0 if on==2 else 5))
  texts.clear();r.uc.mem_write(dx['dx_enabled'],struct.pack('>I',on));r.uc.mem_write(fb,bytes(1024));r.call(dx['dx_menu_draw'],0,canvas);assert not r.bad
  if on<2:assert ('On' if on else 'Off') in texts,texts
  if on==2:assert 'SIL' in texts and 'Silent' not in texts,texts
  assert 'LTC' in texts and 'Latch' not in texts,texts
  raw=bytes(r.uc.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
  png(ROOT/f'output/firmware/{stem}-dx-{on}.png',pixels)
  print('PASS native MenuView and values',stem,on,texts,flush=True)
