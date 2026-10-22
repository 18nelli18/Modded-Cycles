"""Les47 noms MACRO : vrai popup/police, bornes de pixels et edition inchangee."""
import json,struct,sys
from pathlib import Path
from boot_candidate import ROOT,boot
from lofi_ui import UI,POPUP_SLOT
from render_midi_bank import png
from unicorn import UC_HOOK_CODE,m68k_const as C

def rig(stem):
 im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'))
 r=UI(im,mem[0],end=0x40200000);assert r.init_ok;r.call(0x400e7dbc)
 return r

def bit(raw,x,y):return bool(struct.unpack_from('>I',raw,(x*2+y//32)*4)[0]&(1<<(31-y%32)))
def save(path,raw):
 pixels=[0 if bit(raw,x,63-y) else 255 for y in range(64) for x in range(128)]
 png(path,pixels)

version='v17' if '--number' in sys.argv else 'v16'
for prefix in ['all-features','no-filter']:
 stem=prefix+'-macro-names-test-'+version;m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())
 numbered=m.get('macro_model_number',False)
 old=rig(prefix+'-machine-identity-test-v15');r=rig(stem)
 assert old.lookup(12,5,False)==r.lookup(12,5,False)==102
 texts=[]
 def observe(u,pc,size,data):
  sp=u.reg_read(C.UC_M68K_REG_A7);a=struct.unpack('>7I',u.mem_read(sp+4,28))
  texts.append((a[1],a[2],a[3],r.cstr(a[6])))
 r.uc.hook_add(UC_HOOK_CODE,observe,begin=0x40071a04,end=0x40071a04)
 # Un bitmap deux fois plus large permet de mesurer le texte SANS le tronquer.
 bmp,fb,txt,fmt=0x91010000,0x91011000,0x91012000,0x91012100
 r.call(0x40070172,bmp,256,64,fb,0);r.uc.mem_write(fmt,b'%s\0')
 for model in m['macro_model_names']:
  shown=model['lines']+([str(model['index'])] if numbered else [])
  ys=([52,42,32] if len(shown)==3 else [47,34]) if numbered else ([49,37] if len(shown)==2 else [43])
  for line,y in zip(shown,ys):
   r.uc.mem_write(fb,bytes(2048));r.uc.mem_write(txt,line.encode()+b'\0')
   r.call(0x40071a04,bmp,0x40ea14cc,96,y,2,fmt,txt)
   raw=bytes(r.uc.mem_read(fb,2048));xs=[x for x in range(256) if any(raw[x*8:x*8+8])]
   assert xs and min(xs)>=66 and max(xs)<=125,(model,line,min(xs),max(xs))
   occupied_y=[yy for yy in range(64) if any(bit(raw,x,yy) for x in xs)]
   assert occupied_y and min(occupied_y)>=30 and max(occupied_y)<=60,(model,line,occupied_y)
  texts.clear();new,_=r.popup(102,model['index']<<8);assert r.sp_ok and not r.bad
  previous,_=old.popup(102,model['index']<<8)
  named=[x for x in texts if x[0]==0x40ea14cc]
  assert [x[3] for x in named]==shown,(model,named)
  assert [x[2] for x in named]==ys,(model,named)
  for x in range(128):
   for y in range(64):
    if x<64 or y<(29 if numbered else 32):assert bit(new,x,y)==bit(previous,x,y),(model,x,y)
  save(ROOT/f'output/firmware/{stem}-model-{model["index"]}.png',new)
 print('PASS',prefix,'all47 names'+(' and indexes' if numbered else '')+' fully inside x66..125/y30..60; native popup stack, left side and lower markers preserved',flush=True)
 for desc in [0,42,43,51,52,53,54,55,101,103,104,105,26,27,29,25,23,22,39,37]:
  for value in [0,64<<8,127<<8]:
   a=old.popup(desc,value);b=r.popup(desc,value)
   assert a==b,(prefix,desc,value)
 print('PASS',prefix,'60 other parameter popup frames pixel-exact, including MACRO fine/Lo-Fi and other machine controls',flush=True)
 for model in range(47):
  for delta in [-256,0,256]:
   a=old.edit_func(102,model<<8,delta);b=r.edit_func(102,model<<8,delta)
   assert a is not None and a==b,(prefix,model,delta,a,b)
 print('PASS',prefix,'141 native model edits/limits exact; underlying values unchanged',flush=True)
