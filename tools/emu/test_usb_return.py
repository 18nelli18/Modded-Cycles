"""Reproduction native de la reception USB : chaque trame porte son numero."""
import sys,struct,json
from pathlib import Path
from boot_candidate import ROOT,boot
from test_usb_in import Usb,BLOCK,UFRAME,STAMP,SOF_T,FRINDEX,FRAME_NO
p=Path(sys.argv[1]).resolve();im,mem=boot(p);meta=json.loads(p.with_suffix('.json').read_text());sy=meta['symbols']
class Receive(Usb):
 def __init__(self,ch,fixed=False):
  self.rx=[];self.feedback=[];self.feedback_peak=0;super().__init__(im,ch);self.uc.mem_map(0x46700000,0x200000);self.uc.mem_map(0x4a300000,0x100000)
  for at,b in mem:self.uc.mem_write(at,b)
  for i in range(15):
   at,n,p2,p6=struct.unpack('>4I',self.uc.mem_read(sy['wf_usb_patches']+i*16,16));self.uc.mem_write(at,bytes(self.uc.mem_read(p2 if ch==2 else p6,n)))
  if meta.get('usb_return_fix'):
   from unicorn import UC_HOOK_CODE
   self.uc.hook_add(UC_HOOK_CODE,lambda u,pc,size,data:self._ret(0),begin=sy['wf_usb_push'],end=sy['wf_usb_push'])
   self.call(meta['usb_duplex_copy'],int(ch==6))
   assert self.r32(sy['wf_usb_six'])==int(ch==6)
   assert bytes(self.uc.mem_read(0x400025c9,1))==bytes([23 if ch==6 else 31])
  self.w32(0x4013e4dc,6<<16)
 def _prime(self,u,pc,size,data):
  sp=u.reg_read(__import__('unicorn').m68k_const.UC_M68K_REG_A7);ep,dtd=struct.unpack('>2I',u.mem_read(sp+4,8))
  if ep==7:self.queue.append(dtd)
  if ep==3:self.rx.append(dtd)
  if ep==6:
   assert dtd not in self.feedback,('feedback reused while queued',hex(dtd))
   assert 0x80009000<=dtd< (0x80009600 if self.ch==6 and meta.get('usb_return_fix') else 0x80009800)
   self.feedback.append(dtd);self.feedback_peak=max(self.feedback_peak,len(self.feedback))
  self._ret(0)
 def run_rx(self,blocks=1500,phase=0,packets=(6,)):
  self.call(0x40002862,1)
  for i in range(4):self.w32(0x404a0654+4*i,6<<16)
  self.call(0x40002778,1)
  tx_stats=dict(trous=0,sautées=0,doubles=0,trames=0);tx_previous=None
  frame=1;k=0;previous=None;errors=0;checked=0
  for n in range(blocks):
   now=n*BLOCK+phase
   while k*UFRAME<=now:
    t=k*UFRAME;self.w32(STAMP,(t//BLOCK)*BLOCK);self.w32(FRINDEX,k&0x3fff);self.w32(FRAME_NO,k>>3);self.w32(SOF_T+(k&31)*8,t% BLOCK)
    if self.queue:
     td=self.queue.pop(0);token=self.r32(td+4);data=bytes(self.uc.mem_read(self.r32(td+8),token>>16));self.w32(td+4,token&~0x80)
     cb=self.r32(td+36)
     if cb:self.call(cb)
     tx_previous=self._check(data,tx_previous,tx_stats if n>8 else dict(trous=0,sautées=0,doubles=0,trames=0))
    elif self.r32(0x404a0644) and n>8:tx_stats['trous']+=1
    if self.feedback:
     fd=self.feedback.pop(0);self.w32(fd+4,0)
    assert self.rx,'receive TD queue empty'
    dtd=self.rx.pop(0);buf=self.r32(dtd+8);count=packets[k%len(packets)];data=b''.join(struct.pack('<2I',i*16,i*16+1) for i in range(frame,frame+count));frame+=count
    self.uc.mem_write(buf,data);self.w32(dtd+48,buf);self.w32(dtd+4,(56-8*count)<<16)
    cb=self.r32(dtd+36)
    if cb:self.call(cb)
    k+=1
   self.w32(STAMP,n*BLOCK);self.call(0x4015c23c)
   self.call(0x40002ae0,0x40fe4b90,32)
   values=struct.unpack('>64I',self.uc.mem_read(0x40fe4b90,256))
   for left,right in zip(values[::2],values[1::2]):
    if not left:continue
    f=left>>4
    if n>8:
     errors+=int(right!=left+1 or (previous is not None and f!=previous+1));checked+=1
    previous=f
   self.fill(n);self.call(0x4015c2d6,0x40fe4b90,32)
  assert tx_stats['trous']==tx_stats['sautées']==tx_stats['doubles']==0,tx_stats
  assert tx_stats['trames']>8000,tx_stats
  assert not self.bad,self.bad
  return errors,checked
if __name__=='__main__':
 for ch in [2,6]:
  for packets in [(6,),(5,7,6),(7,5,6)]:
   for phase in [0,256,768,1535,4096,7936]:
    r=Receive(ch);bad,checked=r.run_rx(300,phase,packets)
    assert (bad>100 if ch==6 and not meta.get('usb_return_fix') else bad==0),(ch,phase,packets,bad)
    assert checked>9000
    if phase==7936:print('PASS DUPLEX',p.name,ch,packets,'six phases; expected baseline corruption' if ch==6 and not meta.get('usb_return_fix') else 'six phases; zero corrupt/discontinuous frames',flush=True)
