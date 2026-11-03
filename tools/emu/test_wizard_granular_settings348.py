from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))

from unicorn import UC_HOOK_CODE
source=Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/build/volume-pan-toggle/volume-pan-toggle-test.json');old=json.loads(source.read_text());symbols={k:int(v,16) for t in old['composedTweaks'] for k,v in t.get('symbols',{}).items()}
track=3;slot=int.from_bytes(e.uc.mem_read(symbols['track_slot']+4*track,4),'big');assert slot<64
count=int.from_bytes(e.uc.mem_read(symbols['slot_count']+4*slot,4),'big');assert count>0

from itertools import product
sound=E.PARAMS+0x20000
from unicorn import UC_HOOK_CODE
calls=[0]
def lookup(uc,at,*unused):
 sp=uc.reg_read(C.UC_M68K_REG_A7);uc.reg_write(C.UC_M68K_REG_D0,sound);uc.reg_write(C.UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(C.UC_M68K_REG_A7,sp+4)
e.uc.hook_add(UC_HOOK_CODE,lookup,begin=symbols['sound_obj'],end=symbols['sound_obj'])
for lane,shape,direction,freeze in product(range(6),range(4),range(3),range(2)):
 e.uc.mem_write(sound,bytes(100))
 expected=dict(loop_mode=3,gr_shape=shape,gr_dir=direction,gr_frz=freeze)
 for k,v in expected.items():e.uc.mem_write(symbols[k]+4*lane,struct.pack('>I',v))
 e.uc.reg_write(C.UC_M68K_REG_D0,lane);e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(symbols['state_store'])
 packed=bytes(e.uc.mem_read(sound+72,4));assert packed!=bytes(4)
 for k in expected:e.uc.mem_write(symbols[k]+4*lane,bytes(4))
 e.uc.reg_write(C.UC_M68K_REG_D2,lane);e.uc.reg_write(C.UC_M68K_REG_A2,sound);e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(symbols['st_apply'])
 actual={k:int.from_bytes(e.uc.mem_read(symbols[k]+4*lane,4),'big') for k in expected};assert actual==expected,(lane,expected,actual,packed.hex())
 calls[0]+=1
labels={}
for key,expected in [('gran_swap',['Position','Grain Size','Density','Spray']),('strch_swap',['Speed','Grain Size','Density','Spray'])]:
 values=[]
 for i in range(4):
  row=struct.unpack('>7I',e.uc.mem_read(symbols[key]+28*i,28));values.append(bytes(e.uc.mem_read(row[1],32)).split(b'\0')[0].decode())
 assert values==expected,(key,values);labels[key]=values
print('PASS granular options:144 native serialization round trips, UI knob labels exact',labels,flush=True)
args.output.write_text(json.dumps(dict(cases=calls[0],mode_options_round_trip=True,labels=labels,scope='Native packing/unpacking; sound lookup mocked, no filesystem/power-cycle claimed'),indent=2)+'\n')
