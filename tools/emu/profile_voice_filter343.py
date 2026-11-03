"""Compter les coefficients reels du filtre natif dans deux cas six pistes."""
from pathlib import Path
s=Path(__file__).with_name('test_rebuild300_cold_audio.py').read_text().split('events=[]')[0]
exec(compile(s,__file__,'exec'))
from collections import Counter
from unicorn import UC_HOOK_CODE
decoded=emac.disasm(str(W/'final-sram.bin'),0x80000000,0x80001c5c,0x800074b4)
for at in list(e.emac.fast):
 if 0x80000000<=at<0x80010000:e.emac.fast.pop(at,None);e.emac.next.pop(at,None)
for module in meta.get('sram_audio',{}).get('modules',[]):
 raw=W/(module['name']+'-live.bin');raw.write_bytes(e.uc.mem_read(module['at'],module['bytes']))
 decoded.update(emac.disasm(str(raw),module['at'],module['at'],module['at']+module['bytes']))
valid={at for at,(size,mn,op) in decoded.items() if mn in ('macl','msacl','macw','msacw','movclrl') or (mn=='movel' and any(x in op for x in ['%acc','%macsr','%mask']))}
slow=e.emac._slow
native_detours=[]
for key in ['voice_filter_unroll','native_finish','phase_loop','native_biquad']:
 for patch in meta.get(key,{}).get('patches',[]):
  at=patch['at']
  if bytes.fromhex(patch['new']).startswith(b'\x4e\xf9'):
   native_detours.append((at,at+6))
   for old in list(e.emac.fast):
    if at<=old<at+6:e.emac.fast.pop(old,None);e.emac.next.pop(old,None)
def guard(uc,at):
 if 0x80000000<=at<0x80010000 and at not in valid:return
 if any(lo<=at<hi for lo,hi in native_detours):return
 return slow(uc,at)
e.emac._slow=guard;e.emac.install(decoded)
coefficients=Counter()
def observe(uc,at,size,data):
 sp=uc.reg_read(C.UC_M68K_REG_A7);p=int.from_bytes(uc.mem_read(sp+8,4),'big');coefficients[struct.unpack('>3I',uc.mem_read(p,12))]+=1
e.uc.hook_add(UC_HOOK_CODE,observe,begin=0x400a9d4e,end=0x400a9d4e)
rows=[]
saved=json.loads((R.parent/'device-captures/decoded/sounds.json').read_text())[:6]
for name in ['six_defaults','captured_sounds']:
 coefficients.clear()
 for t in range(6):
  e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE)
  if name=='six_defaults':e.machine_defaults(t,t);e.set(t,machine=t,note=48+3*t,punch=1,decay=110)
  else:
   words=saved[t]['words'];e.uc.mem_write(E.PARAMS+14+66*t,struct.pack('>33H',*words));e.set(t,**{key:words[slot]/256 for key,slot in E.SLOT.items()},note=60)
 for t in range(6):e.uc.mem_write(E.VOICE0+t*E.VSTRIDE+56,struct.pack('>I',1))
 for block in range(8):e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.block(63 if block==0 else 0)
 row=dict(case=name,calls=sum(coefficients.values()),coefficients=[dict(values=[hex(x) for x in k],count=v) for k,v in coefficients.most_common()]);rows.append(row);print(row,flush=True)
args.output.write_text(json.dumps(dict(cases=rows,synthetic_triggers=True,hardware_cycles=False),indent=2)+'\n')
