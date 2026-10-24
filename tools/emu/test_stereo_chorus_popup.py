"""Deux lignes chorus avec vrai graphique natif, pixels hors titre et DSP v38 exacts."""
import sys,json,struct,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_junior_integration import parts,ROOT
from lofi_ui import UI,POPUP_SLOT,DRAW_SPRITE,DRAW_TEXT,SCRATCH,pix
from unicorn import UC_HOOK_CODE,m68k_const as C
from PIL import Image
class Hooks(dict):
 def __setitem__(self,k,v):
  if k!=DRAW_SPRITE:super().__setitem__(k,v)
 def __delitem__(self,k):
  if k!=DRAW_SPRITE:super().__delitem__(k)
def rig(stem):
 from boot_candidate import boot
 im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));u=UI(im,mem[0],end=0x40200000);assert u.init_ok
 u.call(0x400e7dbc);u.call(0x400ab7b8,1,count=50000000);assert u.sp_ok and not u.bad
 u.hooks=Hooks(u.hooks);return u

def main():
 reports=[];frames=[]
 for nf in ('','nf'):
  stem=('no-filter-wizard-polivoks-cpu-trim-test-' if nf else 'all-features-polivoks-cpu-trim-test-')+'v39'+nf
  m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());sy=m['stereo_chorus']['symbols'];u=rig(stem);texts=[]
  def observe(uc,pc,size,data):
   sp=uc.reg_read(C.UC_M68K_REG_A7);a=struct.unpack('>7I',uc.mem_read(sp+4,28));texts.append((a[1],a[2],a[3],u.cstr(a[6])))
  u.uc.hook_add(UC_HOOK_CODE,observe,begin=DRAW_TEXT,end=DRAW_TEXT)
  native=sy['ch_previous_popup'];new=sy['ch_popup']
  u.uc.mem_write(sy['ch_mode'],struct.pack('>I',1));u.call(sy['ch_labels'])
  for mode in (1,2):
   u.uc.mem_write(sy['ch_mode'],struct.pack('>I',mode))
   for desc in (39,40):
    art=set()
    for value in (0,42,64,127):
     u.uc.mem_write(POPUP_SLOT,struct.pack('>I',native));a=u.popup(desc,value<<8);assert a is not None
     u.uc.mem_write(POPUP_SLOT,struct.pack('>I',new));texts.clear();b=u.popup(desc,value<<8);assert b is not None
     assert [t for t in texts if t[0]==0x40ea14cc]==[(0x40ea14cc,32,52,'ChI' if mode==1 else 'ChII'),(0x40ea14cc,32,40,'Speed' if desc==39 else 'Depth')]
     assert b[0]!=a[0]
     for x in range(128):
      for y in range(64):
       if x>=64 or y<33:assert pix(a[0],x,y)==pix(b[0],x,y),(mode,desc,value,x,y)
     graphic=tuple(pix(b[0],x,y) for x in range(64) for y in range(33))
     assert any(graphic);art.add(graphic)
     # Inversion finale de la moitie gauche : vrai appel du parent 0x4001e74e.
     bmp=SCRATCH+0x2000;u.call(0x40070f6e,bmp,0,0,63,63,0xffffffff)
     raw=bytes(u.uc.mem_read(bmp+0x100,1024));pixels=bytes(0 if pix(raw,x,63-y) else 255 for y in range(64) for x in range(128))
     im=Image.frombytes('L',(128,64),pixels)
     if not nf and value in (42 if desc==39 else 64,):
      im.save(ROOT/f'output/chorus/v39-{mode}-{desc}.png');frames.append(im.resize((512,256),Image.Resampling.NEAREST))
    assert len(art)>1,'animation lost'
  # Hors chorus : delegation pixel-exacte y compris MACRO et sa numerotation.
  for mode,descs in [(0,[39,40,102]),(1,[0,42,43,51,52,102,103]),(2,[37,38,102])]:
   u.uc.mem_write(sy['ch_mode'],struct.pack('>I',mode));u.call(sy['ch_labels'])
   for desc in descs:
    for value in (0,64,127):
     if desc==102 and value==127:continue
     u.uc.mem_write(POPUP_SLOT,struct.pack('>I',native));a=u.popup(desc,value<<8)
     u.uc.mem_write(POPUP_SLOT,struct.pack('>I',new));b=u.popup(desc,value<<8)
     assert a==b and a is not None,(mode,desc,value)
  oldbuild=ROOT/('output/firmware/governor-recovery-v38'+nf);newbuild=ROOT/('output/firmware/governor-recovery-v39'+nf)
  for obj in ('chorus.c.o','control.c.o','hooks.S.o'):assert (oldbuild/obj).read_bytes()==(newbuild/obj).read_bytes(),obj
  old=json.loads((ROOT/'output/firmware'/(stem.replace('v39','v38')+'.json')).read_text())['stereo_chorus']['symbols']
  for key in ('ch_chorus','ch_fx','ch_state','ch_mode','ch_process'):assert old[key]==sy[key],key
  reports.append(dict(candidate=stem,sha256=m['sha256'],audio_objects_exact_v38=True,native_animated_sprites_preserved=True,right_pixels_and_markers_exact=True,non_chorus_macro_popups_exact=True,two_lines_native_fonts=True))
  print('PASS deux lignes, vrais sprites animes, droite/reperes exacts, delegation Reverb/MACRO, objets audio v38 exacts',stem,flush=True)
 board=Image.new('RGB',(1060,548),(36,39,44))
 for i,im in enumerate(frames):board.paste(im,(12+(i//2)*524,12+(i%2)*268))
 board.save(ROOT/'output/chorus/chorus-v39-native-preview.png')
 (ROOT/'output/firmware/chorus-popup-proof-v39.json').write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
