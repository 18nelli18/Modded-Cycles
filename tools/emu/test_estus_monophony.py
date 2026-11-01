"""Audit du binaire ESTUS : six etats fixes, retriggers locaux, reset isole."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split('held=set();')[0]
exec(compile(src,__file__,'exec'))
es=m['estus']['symbols'];pool=es['v_'];stride=164;rows=0
for track in range(6):
 for engine in range(8):
  for t in range(6):r.call(es['lxr178_reset'],t)
  params=0x931b2000
  data=[0]*15;data[11:15]=[64<<8,64<<8,64<<8,engine<<8]
  r.u.mem_write(params,struct.pack('>15h',*data));r.call(es['lxr_params'],track,params)
  for retrig in range(12):
   before=bytes(r.u.mem_read(pool,6*stride));r.u.mem_write(es['dr_trig']+track,b'\1');r.call(es['lxr_fill'],track,65536,24)
   after=bytes(r.u.mem_read(pool,6*stride));assert r.u.mem_read(es['dr_trig']+track,1)==b'\0'
   assert before[:track*stride]==after[:track*stride] and before[(track+1)*stride:]==after[(track+1)*stride:]
   assert r.r32(pool+track*stride)==engine+1
   rows+=1
  before=bytes(r.u.mem_read(pool,6*stride));r.call(es['lxr178_reset'],track);after=bytes(r.u.mem_read(pool,6*stride))
  assert after[track*stride:(track+1)*stride]==bytes(stride)
  assert before[:track*stride]==after[:track*stride] and before[(track+1)*stride:]==after[(track+1)*stride:]
a.output.write_text(json.dumps(dict(cases=rows,tracks=6,engines=8,voice_bytes=stride,one_voice_per_track=True,synthesis_changes=False,hardware_tested=False),indent=2)+'\n')
print('PASS',rows,'ESTUS compiled retriggers: one fixed voice per track, all eight engines, isolated resets')
