from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))

from ui_fixes348 import apply,CLOCK,INTRO_TIME,UI_GRAN
from unicorn import UC_HOOK_CODE
native=bytearray(e.uc.mem_read(0x40000400,0x1ffc00));runtime=bytearray(e.uc.mem_read(0x46700000,0x300000));d=apply(meta,native,runtime,W/'module');e.uc.mem_write(d['code'],bytes(runtime[d['code']-0x46700000:d['code']-0x46700000+d['code_bytes']]))
old=json.loads(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());us={k:int(v,16) for t in old['composedTweaks'] for k,v in t.get('symbols',{}).items()}
selected=0;lookups=[0];invalidates=[0]
def stub(uc,pc,*unused):
 if pc==0x400cf866:result=0x40810000;lookups[0]+=1
 elif pc==0x4000eb90:result=0x40811000
 elif pc==0x40012412:result=selected
 else:
  result=0
  if pc==0x40076082:invalidates[0]+=1
 sp=uc.reg_read(C.UC_M68K_REG_A7);uc.reg_write(C.UC_M68K_REG_D0,result);uc.reg_write(C.UC_M68K_REG_PC,int.from_bytes(uc.mem_read(sp,4),'big'));uc.reg_write(C.UC_M68K_REG_A7,sp+4)
for at in [0x400cf866,0x4000eb90,0x40012412,0x40076082,us['sg_q_service'],us['led_hook']]:e.uc.hook_add(UC_HOOK_CODE,stub,begin=at,end=at)
def patch(enabled):
 for p in d['patches']:e.uc.mem_write(p['at'],bytes.fromhex(p['new'] if enabled else p['old']));e.uc.ctl_remove_cache(p['at'],p['at']+len(bytes.fromhex(p['old'])))
def names():
 result=[]
 for ident in [46,62,73,74]:
  pointer=int.from_bytes(e.uc.mem_read(us['param_table']+ident*56+44,4),'big');result.append(bytes(e.uc.mem_read(pointer,32)).split(b'\0')[0].decode())
 return result
selected=3;e.uc.mem_write(us['loop_mode']+4*selected,struct.pack('>I',3));e.uc.mem_write(UI_GRAN,bytes(4));e.uc.reg_write(C.UC_M68K_REG_D1,1);e.uc.reg_write(C.UC_M68K_REG_SR,0x2000);e.call(us['apply_names']);baseline=names();assert baseline==['Sample Start','Sample End','Filter','Res'],baseline
def table_names(key):
 return [bytes(e.uc.mem_read(int.from_bytes(e.uc.mem_read(us[key]+28*i+4,4),'big'),32)).split(b'\0')[0].decode() for i in range(4)]
patch(True);rows=[]
expected={0:['Sample Start','Sample End','Filter','Res'],1:['Sample Start','Sample End','Filter','Res'],2:['Sample Start','Sample End','Filter','Res'],3:['Position','Grain Size','Density','Spray'],4:['Speed','Grain Size','Density','Spray'],5:table_names('pluck_swap'),6:table_names('wave_swap')}
for selected in range(6):
 for mode in range(7):
  e.uc.mem_write(us['loop_mode']+4*selected,struct.pack('>I',mode));e.uc.mem_write(us['fx_sel']+4*selected,bytes(4));e.uc.mem_write(UI_GRAN,bytes(4))
  before=bytes(e.uc.mem_read(us['loop_mode'],24));e.uc.reg_write(C.UC_M68K_REG_D1,1);e.uc.reg_write(C.UC_M68K_REG_SR,0x2000);e.call(us['apply_names']);values=names()
  assert values==expected[mode],(selected,mode,values);assert e.uc.mem_read(us['loop_mode'],24)==before;rows.append(dict(track=selected,mode=mode,labels=values))
before=lookups[0];e.uc.mem_write(UI_GRAN,struct.pack('>I',1));e.uc.reg_write(C.UC_M68K_REG_D1,1);e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(us['apply_names']);assert lookups[0]==before
# Le cache reste disponible en IRQ, sans getters UI. La restauration stock ignore le mode.
e.uc.reg_write(C.UC_M68K_REG_D1,0);e.uc.reg_write(C.UC_M68K_REG_SR,0x2000);e.call(us['apply_names']);assert lookups[0]==before
print('PASS42 Wizard labels, stale-cache reproduction, no UI getter in IRQ/stock restore',flush=True)
clockrows=[]
for enabled in (False,True):
 patch(enabled);start=0xffff0000;e.uc.mem_write(CLOCK,struct.pack('>I',100));e.uc.mem_write(0xfc07000c,struct.pack('>I',start))
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2000);e.uc.emu_start(d['genie_open_clock'],d['genie_open_clock']+12,count=2)
 assert int.from_bytes(e.uc.mem_read(INTRO_TIME,4),'big')==(start if enabled else 100)
 e.uc.mem_write(us['sg_obj'],struct.pack('>I',0x40812000));e.uc.mem_write(us['sg_intro'],struct.pack('>I',1));old_invalid=invalidates[0]
 for elapsed in [d['timeout_ticks']-1,d['timeout_ticks'],d['timeout_ticks']+1]:
  e.uc.mem_write(0xfc07000c,struct.pack('>I',(start+elapsed)&0xffffffff));e.uc.reg_write(C.UC_M68K_REG_SR,0x2000);e.call(us['sg_tick']);shown=int.from_bytes(e.uc.mem_read(us['sg_intro'],4),'big')
  assert shown==(0 if enabled and elapsed>=d['timeout_ticks'] else 1),(enabled,elapsed,shown)
  clockrows.append(dict(patched=enabled,elapsed=elapsed,intro=shown))
 assert invalidates[0]-old_invalid==(1 if enabled else 0)
print('PASS Genie frozen audio clock; timeout boundary and GPT wrap; one invalidate',flush=True)
args.output.write_text(json.dumps(dict(label_cases=rows,baseline_stale_labels=baseline,IRQ_getters_blocked=True,clock_cases=clockrows,module=d,audio_hooks=False),indent=2)+'\n')
