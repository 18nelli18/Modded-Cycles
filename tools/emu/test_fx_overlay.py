"""v57 : reproduit le double routage v56 ; overlay opaque et fond natif preserve."""
import sys,json,struct
from test_fx_menu_control import fixture
from boot_candidate import ROOT,boot
from test_stereo_chorus_popup import rig
from lofi_ui import SCRATCH,pix
from PIL import Image
for stem in sys.argv[1:]:
 for version in ('56','57'):
  candidate='validation/'+stem.rsplit('/',1)[-1].rsplit('-',1)[0]+'-v56' if version=='56' else stem;r,s,h,log,files,key,turn,data,bind=fixture(candidate);h.add(13);lean=json.loads((ROOT/'output/firmware'/(candidate+'.json')).read_text())['fx_menu'].get('lean_fx',False);r.w32(s['ch_mode'],7 if lean else 5);r.w32(s['cr_mode'],5 if lean else 3);calls=[]
  def route(a):calls.append(r.r32(s['fx_force_active']));return 0
  bind(s['fx_native_encoder'],route)
  for knob in (14,15):
   calls.clear();ret=turn(knob);assert (ret,calls)==((0,[1,0]) if version=='56' else (1,[1])),(candidate,knob,ret,calls)
 print('PASS reproduces v56 fallback and fixes both SETTINGS routes when native edit returns zero',stem,flush=True)
 u=rig(stem);m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());s=m['fx_menu']['symbols'];u.hooks.update({s['fx_previous_draw']:('background',0),s['fx_query_original']:('key',0),0x400d0a10:('busy',0)})
 bmp,fb=SCRATCH+0x2000,SCRATCH+0x2100;frames=[]
 for slot,n in ((0,len(m['fx_menu'].get('reverb_selector_order',[4,3,0,1,2,5,6]))),(1,len(m['fx_menu']['delay_selector_order']))):
  for cursor in range(n):
   baseline=u.popup(37,64<<8)[0];outs=[]
   for invert in (0,255):
    backdrop=bytes(v^invert for v in baseline);u.uc.mem_write(fb,backdrop)
    for name,val in [('fx_menu_open',1),('fx_menu_slot',slot),('fx_menu_cursor',cursor)]:u.uc.mem_write(s[name],struct.pack('>I',val))
    u.call(s['fx_draw'],0,bmp);assert u.sp_ok and not u.bad;out=bytes(u.uc.mem_read(fb,1024));outs.append(out)
    for x in range(128):
     for y in range(64):
      if not (10<=x<=119 and 4<=y<=59):assert pix(out,x,y)==pix(backdrop,x,y),('background overwritten',slot,cursor,x,y)
   for x in range(11,117):
    for y in range(7,59):assert pix(outs[0],x,y)==pix(outs[1],x,y),('transparent menu',slot,cursor,x,y)
   if cursor==2:
    frames.append(Image.frombytes('L',(128,64),bytes(0 if pix(outs[0],x,63-y) else 255 for y in range(64) for x in range(128))))
 board=Image.new('RGB',(1024,256),'#eeeeee')
 for i,im in enumerate(frames):board.paste(im.resize((512,256),Image.Resampling.NEAREST),(512*i,0))
 dest=ROOT/'output/firmware'/('fx-overlay-preview-'+stem.rsplit('-',1)[-1]+'.png');board.save(dest)
 print('PASS all overlay positions: native background outside box exact, inside fully opaque, stack intact',stem,flush=True)
