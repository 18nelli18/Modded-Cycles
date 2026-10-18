"""Machine MIDI : notes live natives, canaux et ports, sans ordonnanceur B.

Getters projet et pilotes physiques instrumentes ; helpers natifs note-on/off,
routeur et worker reels. Ne couvre pas encore les CC ni la sequence complete.
"""
import argparse,json,pathlib,struct,sys
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_UNMAPPED,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import build,syntakt,gen_sdvintage_7th as g7,gen_midi_machine_core as core
BASE=0x40000400;STACK=0x9300e000;STOP=0x9300f000
PROJECT=0x92100000;SOUND=0x92080000;OBJECT=0x92080100;VT=0x92060200;TRACK_DATA=0x92090000;TRACK=PROJECT+5192+112

class Rig:
 def __init__(self,img,runtime,pay):
  self.u=u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
  for at,size in [(0x40000000,0x02400000),(0x92000000,0x2000000),(0x80000000,0x20000),(pay,0x100000)]:u.mem_map(at,size)
  u.mem_write(BASE,img);u.mem_write(pay,runtime);u.reg_write(mk.UC_M68K_REG_SR,0x2000)
  u.hook_add(UC_HOOK_MEM_UNMAPPED,lambda u,access,at,size,value,data:print('UNMAPPED',hex(at),'PC',hex(u.reg_read(mk.UC_M68K_REG_PC)),flush=True) or False)
  self.output=[];self.queue=[];self.channel=0;self.destination=3;self.machine=6;self.hooks={}
  for at,fn in {0x40012e82:lambda a:self.channel,0x40044e6c:lambda a:self.destination,0x400cf866:lambda a:PROJECT,0x4000eb9c:lambda a:OBJECT,0x40009c1a:lambda a:OBJECT+0x1000*a[1],0x92060300:lambda a:self.word(a[0]+16)}.items():self.stub(at,fn)
  for at,fn in {0x400cf9a8:lambda a:0x92040000,0x400cfd0e:lambda a:0x92041000,0x4000eb90:lambda a:PROJECT+48}.items():self.stub(at,fn)
  for at in (0x40012412,0x4007faf4,0x4006bdfe,0x4008171e,0x4008145e,0x400032ca,0x400032da,0x40001f58,0x400019ec,0x40001a38):self.stub(at,lambda a:0)
  for lane in range(6):
   self.word(OBJECT+0x1000*lane,VT);self.word(OBJECT+0x1000*lane+16,SOUND+0x1000*lane)
  self.word(VT+40,0x92060300);self.word(0x40fe4228,PROJECT)
  self.word(VT+40,0x92060300)
  # Sons et pistes ont des structures differentes ; le getter ne les confond pas.
  self.stub(0x92060310,lambda a:TRACK_DATA)
  self.word(VT+256+40,0x92060310)
  for lane in range(6):self.word(TRACK+88*lane,VT+256)
  self.word(0x40a7887c,0x92010000)
  self.stub(0x40001584,lambda a:self.send('DIN',a));self.stub(0x40003396,lambda a:self.send('USB',a))
  self.stub(0x40001fba,self.enqueue);u.hook_add(UC_HOOK_CODE,self.dequeue,begin=0x4000204c,end=0x4000204c)
  self.call(0x4008a55a);self.queue.clear()
 def word(self,at,value=None):
  if value is None:return int.from_bytes(self.u.mem_read(at,4),'big')
  self.u.mem_write(at,struct.pack('>I',value&0xffffffff))
 def ret(self,value=0):
  sp=self.u.reg_read(mk.UC_M68K_REG_A7);self.u.reg_write(mk.UC_M68K_REG_D0,value&0xffffffff);self.u.reg_write(mk.UC_M68K_REG_PC,self.word(sp));self.u.reg_write(mk.UC_M68K_REG_A7,sp+4)
 def stub(self,at,fn):
  def run(u,pc,size,data):
   sp=u.reg_read(mk.UC_M68K_REG_A7);args=struct.unpack('>8I',u.mem_read(sp+4,32));self.ret(fn(args) or 0)
  self.u.hook_add(UC_HOOK_CODE,run,begin=at,end=at)
 def send(self,port,args):self.output.append((port,bytes(self.u.mem_read(args[1],args[0]))));return 0
 def enqueue(self,args):assert args[0]==0x40fcb2ec;self.queue.append(args[1]);return 0
 def dequeue(self,u,pc,size,data):
  if self.queue:self.ret(self.queue.pop(0))
  else:u.reg_write(mk.UC_M68K_REG_PC,STOP)
 def call(self,fn,*args):
  saved={getattr(mk,'UC_M68K_REG_'+name):self.u.reg_read(getattr(mk,'UC_M68K_REG_'+name)) for name in ('D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6')}
  self.u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*[x&0xffffffff for x in args]));self.u.reg_write(mk.UC_M68K_REG_A7,STACK);self.u.emu_start(fn,STOP,count=1000000)
  assert self.u.reg_read(mk.UC_M68K_REG_PC)==STOP
  assert self.u.reg_read(mk.UC_M68K_REG_A7)==STACK+4,hex(fn)
  assert all(self.u.reg_read(reg)==value for reg,value in saved.items()),('ABI',hex(fn))
  return self.u.reg_read(mk.UC_M68K_REG_D0)

def prove(stock,t,recipes,st=None):
 machine_id=t['machine_names'].index('MIDI Out')
 img,_=build.apply_writes(stock,recipes);rt=build.payload_runtime(t,stock,st);r=Rig(bytes(img),rt,int(t['append']['dest'],16))
 baseline=Rig(stock,rt,int(t['append']['dest'],16))
 for machine in list(range(6))+[machine_id]:
  for value in (0,1,2,255):
   results=[]
   for rig in (baseline,r):
    rig.machine=machine;rig.u.mem_write(SOUND+38,struct.pack('>H',machine<<8));rig.u.mem_write(TRACK_DATA+720,bytes((value,)))
    results.append(rig.call(0x40016e90,TRACK))
   assert results[1]==(1 if machine==machine_id else results[0]),(machine,value,results)
 r.u.mem_write(TRACK_DATA+720,b'\0')
 print('PASS MOut automatique MIDI seulement ; six autres slots identiques au getter stock')
 for mask in range(64):
  for lane in range(6):r.u.mem_write(SOUND+0x1000*lane+38,bytes((machine_id if mask>>lane&1 else lane,0)))
  for lane in range(6):assert r.call(0x40016e90,TRACK+88*lane)&255==bool(mask>>lane&1),(mask,lane)
 print('PASS 64 selections de machines mixtes, sorties independantes sur les six pistes')
 for lane in range(6):r.u.mem_write(SOUND+0x1000*lane+38,bytes((machine_id,0)))
 for lane in range(6):
  for channel in range(16):
   r.channel=channel;r.output.clear();params=[0]*33;params[9]=machine_id<<8;r.u.mem_write(SOUND+0x1000*lane+20,struct.pack('>33H',*params));r.u.mem_write(0x800015ae+66*lane,struct.pack('>33H',*params))
   for pad in (False,True):
    r.output.clear();note=36+lane;r.call(0x4001d05e if pad else 0x40019e7a,0,lane,note,97,0xffffffff);r.call(0x4001d0fc if pad else 0x40019c84,0,lane,note)
    expected=[bytes((0x90|channel,note,97)),bytes((0x80|channel,note,0))]
    assert [p for port,p in r.output if port=='DIN']==expected,(lane,channel,pad,r.output)
    assert [p for port,p in r.output if port=='USB']==expected
 print('PASS 192 native keyboard/pad MIDI note pairs, six track slots, 16 channels, DIN+USB')
 for lane in range(6):
  for pad in (False,True):
   r.output.clear();r.channel=2;r.destination=3;r.u.mem_write(SOUND+0x1000*lane+38,bytes((machine_id,0)))
   r.call(0x4001d05e if pad else 0x40019e7a,0,lane,60,99,0xffffffff)
   r.u.mem_write(SOUND+0x1000*lane+38,bytes((lane,0)));r.channel=9;r.destination=0
   r.call(0x4001d0fc if pad else 0x40019c84,0,lane,60)
   for port in ('DIN','USB'):assert [p for dest,p in r.output if dest==port]==[bytes((0x92,60,99)),bytes((0x82,60,0))],(lane,pad,r.output)
 print('PASS 12 relachements apres changement machine/canal/port, destination de l attaque preservee')
 r.u.mem_write(SOUND+38,bytes((machine_id,0)));r.channel=5;r.destination=0;r.output.clear()
 r.call(0x40019e7a,0,0,60,90,0xffffffff);r.destination=3;r.call(0x40019c84,0,0,60)
 assert not r.output,r.output
 r.call(0x40019e7a,0,0,60,90,0xffffffff);r.call(0x40019e7a,0,0,60,91,0xffffffff);r.call(0x40019c84,0,0,60)
 for port in ('DIN','USB'):assert [p for dest,p in r.output if dest==port]==[bytes((0x95,60,90)),bytes((0x85,60,0)),bytes((0x95,60,91)),bytes((0x85,60,0))]
 print('PASS port OFF capture et nouvelles attaques de la meme note sans relachement intermediaire')
 for lane in range(6):
  for pad in (False,True):
   for enabled in (0,1):
    outputs=[]
    for rig in (baseline,r):
     rig.channel=3;rig.destination=3;rig.output.clear();rig.u.mem_write(SOUND+0x1000*lane+38,bytes((lane,0)));rig.u.mem_write(TRACK_DATA+720,bytes((enabled,)))
     rig.call(0x4001d05e if pad else 0x40019e7a,0,lane,48,80,0xffffffff);rig.call(0x4001d0fc if pad else 0x40019c84,0,lane,48)
     outputs.append(rig.output[:])
    assert outputs[0]==outputs[1],(lane,pad,enabled,outputs)
 print('PASS sorties stock inchangees avec MOut ON/OFF ; pile et registres preserves')
 print('PASS profil',len(t['machine_names']),'machines, slot MIDI',machine_id)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--catalogue',action='store_true');args=parser.parse_args()
 root=HERE.parent.parent;stock=g7.cycles_main(str(root/'firmware/model-cycles_OS1.13.syx'))
 zones=[(site-build.BASE+2,site-build.BASE+len(bytes.fromhex(old))) for site,old,name in core.LIVE_HOOKS]+[(0x40016e92-build.BASE,0x40016e96-build.BASE)]
 sure,branches=build.refs_into(stock,zones);assert not sure and not branches,(sure,branches)
 print('PASS aucun pointeur ni branchement entrant au milieu des cinq accroches natives')
 t=json.loads((root/'build/midi-machine/core.json').read_text());prove(stock,t,[t])
 if args.catalogue:
  entry=json.loads((root/'build/midi-machine/catalogue-1023-1.json').read_text())
  prove(stock,entry['engine'],[entry['wizard'],entry['engine']],syntakt.dsp_image(str(root/'firmware/Syntakt_OS1.42.syx')))
 print('LIMITES : peripheriques simules ; CC, full sequence, UI and saving still pending')
if __name__=='__main__':main()
