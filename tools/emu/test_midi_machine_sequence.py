"""Vraie file audio : locks CC avant lissage, puis worker hors interruption.

Producteur/evenements/extraction/application des locks restent natifs. Horloge,
canal/port et mailbox sont instrumentes. Pas de second sequenc eur B.
"""
import json,pathlib,struct,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_arp import Audio,KIT
from unicorn import UC_HOOK_CODE,m68k_const as mk
import gen_sdvintage_7th as g7
ROOT=HERE.parent.parent;FRAME=0x800015ae;RAW=0x420c0000

class Sequence(Audio):
 def __init__(self,stock,data,pay=0x46800000,prepared=False):
  image=bytearray(stock);self.s={k:int(v,16) for k,v in data['symbols'].items()}
  if not prepared:
   site=0x4005919e;assert image[site-0x40000400:site-0x40000400+6].hex()=='42b940a78e18'
   image[site-0x40000400:site-0x40000400+6]=b'\x4e\xf9'+struct.pack('>I',self.s['mm_sequence_hook'])
   site=0x40058f3c;assert image[site-0x40000400:site-0x40000400+8].hex()=='4fef000c60000262'
   image[site-0x40000400:site-0x40000400+8]=b'\x4e\xf9'+struct.pack('>I',self.s['mm_lock_only_hook'])+b'\x4e\x71'
  super().__init__(bytes(image),payload=(pay,bytes.fromhex(data['hex'])))
  self.queue=[];self.sent=[]
  self.stub(0x400cf866,lambda a:0x42300000);self.stub(0x40012e82,lambda a:a[1]);self.stub(0x40082686,lambda a:4)
  self.stub(0x40001fba,lambda a:self.queue.append(a[1]) or 0)
  self.stub(0x400826b0,self.send_cc)
  self.uc.mem_write(0x40fcb2ec,bytes(16))
  for lane in range(6):
   params=[0]*33;params[9]=data.get('machine',6)<<8;params[32]=0x4d49
   for k in range(12):params[11+k]=(k+1)*128+64
   raw=struct.pack('>33H',*params)
   self.uc.mem_write(FRAME+66*lane,raw);self.uc.mem_write(KIT+28+100*lane+20,raw)
 def stub(self,at,fn):
  def run(u,pc,size,data):
   sp=u.reg_read(mk.UC_M68K_REG_A7);args=struct.unpack('>8I',u.mem_read(sp+4,32));u.reg_write(mk.UC_M68K_REG_D0,fn(args) or 0);u.reg_write(mk.UC_M68K_REG_PC,self.r32(sp));u.reg_write(mk.UC_M68K_REG_A7,sp+4)
  self.uc.hook_add(UC_HOOK_CODE,run,begin=at,end=at)
 def send_cc(self,args):
  assert not self.uc.reg_read(mk.UC_M68K_REG_SR)&0x700
  self.sent.append(bytes(self.uc.mem_read(args[1],args[0])));return 0
 def sequence(self,lane=0,cc=74,value=17,lock_only=False,on=1):
  locks=self.e.call(0x40091e66);self.uc.mem_write(RAW,b'\xff'*68)
  self.uc.mem_write(RAW+22,struct.pack('>H',(cc+1)*128+value));self.e.call(0x4005487c,locks,RAW,0,0)
  event=self.e.call(0x40091eb6)
  for offset,val in ((4,on),(8,lane),(12,1),(28,60),(40,1 if lock_only else 0x10081),(52,91),(60,127),(72,locks)):self.w32(event+offset,val)
  self.uc.mem_write(event+20,b'\1');self.uc.mem_write(event+22,b'\x61\0')
  self.e.call(0x40092116,event);return self.run()
 def drain(self):
  self.uc.reg_write(mk.UC_M68K_REG_SR,0x2000)
  while self.queue:
   token=self.queue.pop(0)
   if token==self.s['mm_wakeup']:assert self.e.call(self.s['mm_cc_worker'],token)==1
  self.uc.reg_write(mk.UC_M68K_REG_SR,0x2700)

def main():
 stock=g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx'));data=json.loads((ROOT/'build/midi-machine/controls-ui.json').read_text());r=Sequence(stock,data)
 for lane in range(6):
  r.sent.clear();assert r.sequence(lane,74,17+lane)==1<<lane
  assert not r.sent,'Writer atteint depuis audio IRQ';assert r.queue
  r.drain();assert bytes((0xb0|lane,74,17+lane)) in r.sent,(lane,r.sent)
 print('PASS six trigs par vraie file audio : numero/valeur locks avant lissage, CC seulement dans worker IPL0')
 r.sent.clear();assert r.sequence(0,71,127,True)==0;r.drain()
 assert bytes((0xb0,71,127)) in r.sent,(r.sent,struct.unpack('>33H',r.uc.mem_read(FRAME,66)))
 print('PASS vrai lock-only : CC transmis sans attaque audio ou deuxieme horloge')
 r.sent.clear();assert r.sequence(0,71,1,on=2)==0;r.drain();assert not r.sent
 print('PASS evenement note-off ne regenere pas les CC')
if __name__=='__main__':main()
