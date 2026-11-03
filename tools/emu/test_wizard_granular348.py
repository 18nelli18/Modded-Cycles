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
for mode in [3,4]:
 e.uc.mem_write(symbols['loop_mode']+4*track,struct.pack('>I',mode))
 for field in ['color','shape','sweep','contour']:
  for value in [0,64,127]:
   e.set(track,color=64,shape=64,sweep=64,contour=0);e.set(track,**{field:value});e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);pcm=e.block(1<<track)
   actual=int.from_bytes(e.uc.mem_read(E.VOICE0+track*E.VSTRIDE,4),'big');assert actual==6,actual
   state={k:int.from_bytes(e.uc.mem_read(symbols[k]+4*track,4),'big') for k in ['gr_pos','gr_len','gr_int','gr_spray','gr_speed']}
   if field=='contour':assert state['gr_spray']==(((count>>6)*(value*256))>>9),(mode,value,count,state)
   rows.append(dict(mode=mode,field=field,value=value,state=state,peak=int(np.abs(pcm[track]).max())))
print('Granular controls',rows,flush=True);print('gran_fill calls',calls,flush=True)
assert calls[0]>0
args.output.write_text(json.dumps(dict(sample_frames=count,controls=rows,granular_render_calls=calls[0],actual_machine=6,source_symbols=str(source)),indent=2)+'\n')
