"""Menus et popups v55 : constructeurs, dessin et destruction du vrai OS."""
import sys,struct,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT,boot
from lofi_ui import UI,SCRATCH,pix,DRAW_TEXT
from test_stereo_chorus_popup import Hooks
from unicorn import m68k_const as C,UC_HOOK_CODE
from PIL import Image
class PopupUI(UI):
 def _hook(self,uc,addr,size,data):
  if addr==0x4007700e:
   sp=uc.reg_read(C.UC_M68K_REG_A7);args=struct.unpack('>3I',uc.mem_read(sp+4,12));self.present=struct.unpack('>2I',uc.mem_read(args[1],8));ref=self.present[1];uc.mem_write(ref+4,struct.pack('>I',self.u32(ref+4)+1))
  super()._hook(uc,addr,size,data)

def main():
 for stem in sys.argv[1:]:
  m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());sy=m['fx_menu']['symbols'];im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));u=PopupUI(im,mem[0],end=0x40200000);u.call(0x400e7dbc);u.call(0x400ab7b8,1,count=50000000);u.hooks=Hooks(u.hooks)
  u.hooks.update({0x400d0974:('ui',0x91019000),0x400060d8:('controller',0x91019100),0x4007700e:('present',0),0x400cf866:('project',0x92080000),0x4006f73a:('delta',1),sy['fx_query_original']:('key',0),sy['fx_previous_draw']:('draw',0),0x400d0a10:('stopped',0)})
  kit,vt,get,data=0x92080000,0x92081000,0x92082000,0x92083000;u.uc.mem_write(kit+48,struct.pack('>I',vt));u.uc.mem_write(vt+40,struct.pack('>I',get));u.uc.mem_write(get,b'\x20\x3c'+struct.pack('>I',data)+b'\x4e\x75');u.uc.mem_write(0x40fe4178,struct.pack('>I',1))
  bmp,fb=SCRATCH+0x2000,SCRATCH+0x2100;texts=[];frames=[]
  def observe(uc,pc,size,data):
   sp=uc.reg_read(C.UC_M68K_REG_A7);a=struct.unpack('>7I',uc.mem_read(sp+4,28));texts.append(u.cstr(a[6]) if u.cstr(a[5])=='%s' else '')
  u.uc.hook_add(UC_HOOK_CODE,observe,begin=DRAW_TEXT,end=DRAW_TEXT)
  def picture():
   raw=bytes(u.uc.mem_read(fb,1024));return Image.frombytes('L',(128,64),bytes(0 if pix(raw,x,63-y) else 255 for y in range(64) for x in range(128)))
  for mode,fields in [(1,[0,1,2]),(2,[0,1,2]),(3,[0,1,2])]:
   u.uc.mem_write(sy['cr_mode'],struct.pack('>I',mode))
   for field in fields:
    u.call(sy['fx_show'],field);obj,ref=u.present;v=u.u32(obj);u.call(0x40070172,bmp,128,64,fb,0);texts.clear();u.call(u.u32(v+16),obj,bmp);assert u.sp_ok and not u.bad
    assert ['Rate','Bits','Crush Send'][field] in texts,texts
    pair=SCRATCH+0x18000;u.uc.mem_write(pair,struct.pack('>2I',obj,ref));u.call(0x400cf23c,pair+4);assert u.sp_ok and not u.bad
  for mode,fields in [(1,[3,4]),(2,[3,4]),(3,[6,7,8]),(4,[6,7,8,9]),(5,[3,4,5]),(6,[3,4,5])]:
   u.uc.mem_write(sy['ch_mode'],struct.pack('>I',mode))
   for field in fields:
    u.call(sy['fx_show'],field);obj,ref=u.present;v=u.u32(obj);u.call(0x40070172,bmp,128,64,fb,0);texts.clear();u.call(u.u32(v+16),obj,bmp);assert u.sp_ok and not u.bad
    if mode==4 and field in (6,9):
     frame=picture();assert frame.getextrema()==(0,255);frames.append(frame)
    pair=SCRATCH+0x18000;u.uc.mem_write(pair,struct.pack('>2I',obj,ref));u.call(0x400cf23c,pair+4);assert u.sp_ok and not u.bad
  for delay,rev,desc,label in [(1,0,26,'Crush Send'),(2,0,26,'Crush Send'),(0,1,27,'Chorus Send'),(0,2,27,'Chorus Send'),(0,3,27,'Vinyl Send')]:
   u.uc.mem_write(sy['cr_mode'],struct.pack('>I',delay));u.uc.mem_write(sy['ch_mode'],struct.pack('>I',rev));texts.clear();assert u.popup(desc,96<<8) is not None;assert label in texts,(label,texts)
  if m['fx_menu'].get('new_delays'):
   for mode,name in ([(5,'PING PONG'),(6,'SHIMMER 1'),(7,'SHIMMER 2')] if m['fx_menu'].get('octave_polish') else [(5,'PING PONG'),(6,'SHIMMER')]):
    u.uc.mem_write(sy['cr_mode'],struct.pack('>I',mode))
    for desc,label in [(26,'Delay Send'),(37,'Time'),(38,'Feedback')]:
     texts.clear();assert u.popup(desc,96<<8) is not None;assert name in texts and label in texts,(mode,desc,texts)
  # Les deux listes dessinees avec les primitives OS, highlight sans changer de mode.
  for slot,n in [(0,7),(1,len(m['fx_menu']['delay_selector_order']))]:
   u.uc.mem_write(sy['fx_menu_open'],struct.pack('>I',1));u.uc.mem_write(sy['fx_menu_slot'],struct.pack('>I',slot))
   for cursor in range(n):
    u.uc.mem_write(sy['fx_menu_cursor'],struct.pack('>I',cursor));u.call(0x40070172,bmp,128,64,fb,0);texts.clear();u.call(sy['fx_draw'],0,bmp);assert u.sp_ok and not u.bad;assert ('DELAY FX' if slot else 'REVERB FX') in texts
    if cursor==2:frames.append(picture())
  board=Image.new('L',(512,256*len(frames)),255)
  for i,frame in enumerate(frames):board.paste(frame.resize((512,256),Image.Resampling.NEAREST),(0,i*256))
  dest=ROOT/'output/firmware'/('fx-menu-preview-'+stem.rsplit('-',1)[-1]+'.png');board.save(dest)
  print('PASS 26 native popup lifecycles and 12 menu highlights, native rendering/stack/refcounts',stem,flush=True)
if __name__=='__main__':main()
