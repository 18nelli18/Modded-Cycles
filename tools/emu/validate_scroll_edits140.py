"""Les editions voulues changent la banque, les bornes de defilement non."""
from pathlib import Path
W=Path(__file__).resolve().parents[2]
s=(W/'tools/emu/validate_scroll_roundtrip140.py').read_text()
setup=s[:s.index(' forward={0:values()}')]
checks=r'''
 def shape():return struct.unpack('>H',u.uc.mem_read(snd+44,2))[0]
 def set_shape(n):u.uc.mem_write(snd+44,struct.pack('>H',n*256))
 def expected_shape(machine,n):
  desc=u.call(0x4005a692,12,machine);base=m['tiny_extra']['descriptors']+56*desc
  lo,hi=struct.unpack('>ii',u.uc.mem_read(base+8,8));return max(lo,min(hi,n*256))
 for _ in range(6):turn(1)
 assert u.uc.mem_read(snd+38,1)[0]==6
 set_shape(20);turn(1);assert shape()==expected_shape(7,110),('Wizard leaked into synth',lane)
 turn(0xffffffff);assert shape()==20*256
 turn(1);assert shape()==expected_shape(7,110)
 for _ in range(16):turn(1)
 assert u.uc.mem_read(snd+38,1)[0]==17
 u.uc.mem_write(snd+40,struct.pack('>H',60*256));turn(0xffffffff)
 assert struct.unpack('>H',u.uc.mem_read(snd+40,2))[0]==64*256
 set_shape(8);turn(1)
 assert struct.unpack('>H',u.uc.mem_read(snd+40,2))[0]==60*256
 turn(0xffffffff);assert shape()==8*256
 for _ in range(22):turn(0xffffffff)
 assert u.uc.mem_read(snd+38,1)[0]==0 and shape()==8*256,('intentional synth edit lost',lane,shape())
 assert not u.bad
 print('PASS track',lane+1,'Wizard/MIDI edits isolated; PUNCH edit retained back to original synth',flush=True)
'''
exec(compile(setup+checks,str(W/'tools/emu/validate_scroll_roundtrip140.py'),'exec'))
