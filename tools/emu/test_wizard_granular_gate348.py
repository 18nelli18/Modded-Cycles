from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))

from unicorn import UC_HOOK_CODE
source=Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/build/volume-pan-toggle/volume-pan-toggle-test.json');old=json.loads(source.read_text());symbols={k:int(v,16) for t in old['composedTweaks'] for k,v in t.get('symbols',{}).items()}
track=3;slot=int.from_bytes(e.uc.mem_read(symbols['track_slot']+4*track,4),'big');assert slot<64
count=int.from_bytes(e.uc.mem_read(symbols['slot_count']+4*slot,4),'big');assert count>0
for t in range(6):
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=6 if t==track else 0,note=60,decay=110,punch=0);e.uc.mem_write(E.VOICE0+t*E.VSTRIDE+56,struct.pack('>I',1))
calls=[0];e.uc.hook_add(UC_HOOK_CODE,lambda *unused:calls.__setitem__(0,calls[0]+1),begin=symbols['gran_fill'],end=symbols['gran_fill']);rows=[]
for mode in range(7):
 e.uc.mem_write(symbols['loop_mode']+4*track,struct.pack('>I',mode));before=calls[0]
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.block(0)
 hit=calls[0]-before;assert bool(hit)==(mode in [3,4]),(mode,hit)
 rows.append(dict(mode=mode,granular_calls=hit))
print('PASS granular DSP gated by playback mode',rows,flush=True)
args.output.write_text(json.dumps(dict(cases=rows,granular_only_in_modes_3_4=True),indent=2)+'\n')
