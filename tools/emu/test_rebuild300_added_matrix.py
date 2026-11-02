"""Rendu deterministe des machines ajoutees pour comparaison entre deux builds.

Conserve le PCM localement, hors depot ; aucun cycle materiel n'est deduit.
"""
from pathlib import Path
source=Path(__file__).with_name('test_rebuild300_cold_audio.py').read_text().split('events=[]')[0]
exec(compile(source,__file__,'exec'))
import hashlib
machines=(13,14,24,7,8,9);peaks=[0]*6;pcm=bytearray()
for block in range(32):
    if block%8==0:
        for track,machine in enumerate(machines):
            e.set(track,machine=machine,note=(48,60,67,72)[block//8],pitch=64,finetune=64,
                  color=(16,64,96,120)[block//8],shape=(24,64,100,127)[block//8],sweep=(32,64,96,127)[block//8],
                  contour=(24,64,96,120)[block//8],decay=100,punch=(block//8)%2,gate=0)
    e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
    audio=e.block(63 if block%8==0 else 0,63 if block%8==6 else 0)
    peaks=[max(peaks[t],int(np.max(np.abs(audio[t])))) for t in range(6)]
    pcm+=audio.astype('>i4').tobytes()
assert all(x>1000 for x in peaks),peaks
args.output.with_suffix('.pcm').write_bytes(pcm)
args.output.write_text(json.dumps(dict(machines=machines,blocks=32,peaks=peaks,pcm_sha256=hashlib.sha256(pcm).hexdigest(),hardware_tested=False),indent=2)+'\n')
print('PASS six added machines audible, deterministic PCM captured',hashlib.sha256(pcm).hexdigest(),flush=True)
