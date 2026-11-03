"""Lecture des six vraies machines stock apres demarrage complet3.02."""
from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))
for t in range(6):
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.machine_defaults(t,t)
 e.set(t,machine=t,note=48+3*t,decay=110,punch=1,gate=0)
 e.uc.mem_write(E.VOICE0+t*E.VSTRIDE+56,struct.pack('>I',1))
e.block(0);peaks=[0]*6
for b in range(16):
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);out=e.block(63 if b==0 else 0)
 for t in range(6):
  assert int.from_bytes(e.uc.mem_read(E.VOICE0+t*E.VSTRIDE,4),'big')==t
  peaks[t]=max(peaks[t],int(np.max(np.abs(out[t].astype(np.int64)))))
assert all(p>1000 for p in peaks),peaks
args.output.write_text(json.dumps(dict(blocks=16,machines=list(range(6)),peaks=peaks,actual_voice_IDs_checked=True),indent=2)+'\n')
print('PASS six audible stock machines, actual voice IDs checked, sixteen blocks',peaks,flush=True)
