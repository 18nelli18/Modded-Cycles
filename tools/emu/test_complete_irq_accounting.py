"""Verifier les crochets installes et conserver la protection de surcharge."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_latch.py').read_text(encoding='utf-8').split('held=set();')[0]
exec(compile(src,__file__,'exec'))
ig=m['complete_irq_accounting'];ps=m['per_track_fx']['symbols']
r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);r.call(ig['boot_target'])
for h in ig['late_hooks']:assert bytes(r.u.mem_read(h['at'],6))==b'\x4e\xf9'+struct.pack('>I',h['target'])
if not (m.get('bounded_burst_policy') or m.get('governor_key_optimization')):
 r.u.mem_map(0x80000000,0x20000)
 for off,at,n in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):r.u.mem_write(at,bytes(r.u.mem_read(0x46700000+off,n)))
bind(ps['mf_old_irq_end'],lambda args:0)
GB=0x46732000;GATE=0x8000e8a4;NOM=90112
source=Path(__file__).with_name('test_stock_voice_governor.py').read_text(encoding='utf-8');exec(source[source.index('def setup('):source.index('def overload(')])
rows=[]
for name,trace,expect in [('paired90',[(70,20),(85,5),(90,0)],False),('real_peak',[(80,15)]*3,not bool(m.get('deadline_headroom'))),('real_overload',[(80,28)]*12,True)]:
 setup(r,m,[0,1,2,3,4,0]);q=60*256//100
 for off,value in [(0x78,q),(0xf10,q*8),(0xf14,q*256),(0xf04,q)]:r.w32(GB+off,value)
 samples=[]
 for i,(head,tail) in enumerate(trace):
  start=1000000+i*NOM;r.w32(ps['gb_irq_active'],1);r.w32(ps['gb_irq_t0'],start)
  previous=r.r32(GB+0xf04);r.w32(0xfc07000c,start+NOM*head//100);r.call(ps['gb_audio_end']);assert r.r32(GB+0xf04)==previous
  end=start+NOM*(head+tail)//100;r.w32(0xfc07000c,end);r.call(ps['gb_irq_end'])
  assert not r.r32(ps['gb_irq_active']);assert r.r32(ps['gb_last_total'])==end-start
  samples.append(dict(load=r.r32(GB+0xf04)*100/256,fade=list(r.u.mem_read(GB+0x58,6))))
 assert bool(any(samples[-1]['fade']))==expect,(name,samples)
 rows.append(dict(case=name,samples=samples));print('PASS',name,samples,flush=True)
# L'appel hors IRQ reste operationnel.
setup(r,m,[0,1,2,3,4,0]);r.w32(ps['gb_irq_active'],0);r.w32(GB+0x80,1000000);r.w32(0xfc07000c,1000000+NOM);r.call(ps['gb_audio_end']);assert r.r32(GB+0xf04)>240
print('PASS installed hooks: defer until same IRQ end, real overload still fades, diagnostics record complete block, non-IRQ fallback preserved',flush=True)
a.output.write_text(json.dumps(dict(cases=rows,hardware_tested=False),indent=2)+'\n')
