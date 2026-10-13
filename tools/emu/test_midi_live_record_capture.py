#!/usr/bin/env python3
"""Capture B quantifiée/libre : exécution ColdFire et getters natifs OS."""
import argparse,pathlib,subprocess,tempfile,struct,json
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig,OBJ,RAW,SIGNAL
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');a=ap.parse_args()
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
 r.u.mem_map(0x80000000,0x20000)
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp)
  objects=[]
  for name in ('live_record_mode','live_record'):
   obj=p/(name+'.o');objects.append(str(obj))
   subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/ (name+'.s'))],check=True)
  defs={'mlp_obj':0x93060000,'ml_clock_state':0x93060004,'ml_pattern':0x93060008,'ml_play_pattern':0x9306000c,'ml_clock_durations':0x93060100}
  subprocess.run([cross+'ld','-Ttext=0x93050000','-Tdata=0x93058000',*[f'--defsym={k}={v}' for k,v in defs.items()],'-e','mllr_on','-o',str(p/'live.elf'),*objects],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'live.elf'),str(p/'live.bin')],check=True)
  r.u.mem_write(0x93050000,(p/'live.bin').read_bytes());r.s=symbols(cross,p/'live.elf')
 if a.tweak:
  t=json.loads(pathlib.Path(a.tweak).read_text())
  for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  for w in t['writes']:
   at=0x40000400+w['off']
   if 0x40100000<=at<0x401ab750:r.u.mem_write(at,bytes.fromhex(w['new']))
  r.s.update({k:int(v,16) for k,v in t['symbols'].items()})
  defs={k:r.s[k] for k in defs}
 r.stubs[SIGNAL]=lambda args:0
 ui=0x930a0000
 for addr,fn in ((0x400cf9a8,lambda args:ui),(0x4000eb90,lambda args:OBJ)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 pat,state=0x93070000,0x93071000;duration=5400000
 for key,value in (('mlp_obj',OBJ),('ml_clock_state',state),('ml_pattern',pat),('ml_play_pattern',pat)):
  r.w32(defs[key],value)
 r.u.mem_write(defs['ml_clock_durations'],struct.pack('>7I',21600000,10800000,duration,3600000,2700000,1800000,1350000))
 r.w32(0x40a7883c,1);r.w32(0x40a78874,0);r.u.mem_write(ui+359,b'\x01')
 def reset(quant=1,nextstep=1):
  r.u.mem_write(pat,bytes(1584));r.u.mem_write(state,bytes(52));r.w32(state,1);r.w32(RAW+180,quant)
  for lane in range(6):
   r.u.mem_write(pat+264*lane+4,b'\x10\x02');r.w32(state+4+8*lane,duration);r.w32(state+8+8*lane,nextstep)
 def onset(lane,now,packet=0x96647800):
  r.w32(0x8000184c,now);r.call('mllr_on',lane,packet)
 def step(lane,index):return bytes(r.u.mem_read(pat+264*lane+8+index*4,4))
 for lane in range(6):
  reset();onset(lane,duration//4);assert step(lane,0)==bytes((100,120,1,1))
  r.w32(0x8000184c,duration*2);r.call('mllr_off',lane);assert step(lane,0)==bytes((100,120,2,1))
  assert all(step(other,0)==bytes(4) for other in range(6) if other!=lane)
 reset();onset(0,3*duration//4);assert step(0,1)==bytes((100,120,1,1))
 reset(nextstep=0);onset(0,3*duration//4);assert step(0,0)==bytes((100,120,1,1))
 reset();onset(0,duration//4);r.w32(state+4,3*duration);r.w32(state+8,3);onset(0,2*duration+duration//4,0x96657800)
 assert step(0,0)[2]==2 and step(0,2)[:2]==bytes((101,120))
 reset(quant=0);onset(0,duration//4);assert step(0,0)==bytes((100,120,1,65))
 reset(quant=0);onset(0,duration+duration//4);assert step(0,1)==bytes((100,120,1,65))
 for packet in (0x86647800,0x96640000,0x96e47800,0x9664f800):
  reset();onset(0,duration//4,packet);assert step(0,0)==bytes(4)
 reset();onset(0,duration//4);r.u.mem_write(pat+8,b'\x3c\x40\x01\x01');r.w32(0x8000184c,3*duration);r.call('mllr_off',0);assert step(0,0)==bytes((60,64,1,1))
 reset();onset(0,duration//4);r.w32(state,2);r.w32(0x8000184c,20*duration);r.call('mllr_off',0);assert step(0,0)[2]==1
 print('ok : six voies isolées, notes/vélocité, quantification proche et wrap, retard 1/64, pas retardé, paquets invalides, édition concurrente, pause')
if __name__=='__main__':main()
