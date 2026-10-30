"""Lecture Song dans l'ISR natif : repetitions, mutes, fin et saut manuel."""
from pathlib import Path
source=(Path(__file__).parent/'test_direct_jump.py').read_text().split('\ndef steps(')[0]
exec(compile(source,__file__,'exec'))
ss=m['acid_articulation']['symbols']
reports=[]
for looping in (1,0):
 s=Seq(IMG);e=s.e;singleton=0x4f042000;e.w32(0x40fe4228,singleton);e.w32(singleton+16,PAT0-28);e.call(ss['sg_sync'])
 e.w32(ss['sg_song'],3);e.w32(ss['sg_song']+4,looping);e.u.mem_write(ss['sg_song']+8,bytes([0,2,0,0,1,1,5,0,0,3,2,0]))
 for i in (0,1):s.setpat(i,length=4)
 assert e.call(ss['sg_start'])[0]==1
 assert e.r32(ss['sg_active'])==1
 e.w32(0x4230877c,1);e.call(0x400542dc)
 seen=[];previous=None
 for tick in range(3000):
  s.isr();index=e.r32(0x40a78634)
  if index!=previous:
   current=e.r32(ss['sg_current']);seen.append((index,current,e.call(ss['sg_mutes'])[0]));previous=index
  if looping and len(seen)>=8:break
  if not looping and e.r32(ss['sg_end']):break
 assert [v[0] for v in seen[:6]]==[0,1,2,3,4,5],seen
 assert [v[1] for v in seen[:6]]==[0,0,1,2,2,2],seen
 assert [v[2] for v in seen[:6]]==[0,0,5,2,2,2],seen
 if looping:assert e.r32(ss['sg_active']) and not e.r32(ss['sg_end'])
 else:assert e.r32(ss['sg_end']) and not e.r32(0x40a7883c) and not e.r32(0x40a78874)
 e.call(ss['sg_cancel']);assert e.call(ss['sg_mutes'])[0]==0
 reports.append(dict(loop=looping,transitions=seen,ticks=tick))
# Une seule entree : terminer apres un cycle entier, pas au lancement.
s=Seq(IMG);e=s.e;singleton=0x4f042000;e.w32(0x40fe4228,singleton);e.w32(singleton+16,PAT0-28);e.call(ss['sg_sync']);s.setpat(0,length=4);s.setpat(1,length=4)
e.w32(ss['sg_song'],1);e.u.mem_write(ss['sg_song']+8,bytes([0,1,5,0]));assert e.call(ss['sg_start'])[0]==1
e.w32(0x800017ac,8);e.call(ss['sg_mute_irq']);assert e.u.reg_read(mk.UC_M68K_REG_D1)==13 and e.r32(0x800017ac)==8
e.w32(0x4230877c,1);e.call(0x400542dc);assert not e.r32(ss['sg_end'])
for tick in range(500):
 s.isr()
 if e.r32(ss['sg_end']):break
assert 50<tick<500 and not e.r32(ss['sg_active'])
assert e.call(ss['sg_start'])[0]==1;s.chain(1);assert not e.r32(ss['sg_active']) and e.call(ss['sg_mutes'])[0]==0
a.output.write_text(json.dumps(dict(native_ISR=True,cases=reports,single_row_stop_tick=tick,manual_chain_cancels=True,user_mutes_unchanged=True,hardware_tested=False),indent=2)+'\n');print('PASS native Song playback, one-row end, mute overlay and manual chain cancellation',flush=True)

