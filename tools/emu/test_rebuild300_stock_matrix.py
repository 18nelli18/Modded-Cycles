"""Parite PCM stock : valeurs variees, PUNCH, retrigs et note-offs.

Le meme demarrage froid et la meme copie SRAM que la preuve de base.
Ne mesure pas les cycles ni le comportement du sequenceur sur le materiel.
"""
from pathlib import Path
source=Path(__file__).with_name('test_rebuild300_cold_audio.py').read_text().split('events=[]')[0]
exec(compile(source,__file__,'exec'))
import random
rng=random.Random(300);rows=[];cases=[]
for block in range(96):
    if block%8==0:
        settings=[]
        for track in range(6):
            values=dict(machine=track,note=rng.choice((36,48,60,72,84)),pitch=rng.choice((32,64,96)),
                        finetune=64,color=rng.choice((0,3,32,64,96,127)),shape=rng.choice((0,16,43,80,127)),
                        sweep=rng.choice((0,24,64,100,127)),contour=rng.choice((0,24,64,100,127)),
                        decay=rng.choice((28,64,110,127)),punch=(block//8)%2,gate=0)
            settings.append(values)
            for eng in (stock,e):eng.set(track,**values)
        cases.append(settings)
    trigger=63 if block%8==0 else (1<<((block//8)%6) if block%8==4 else 0)
    release=63 if block%8==6 else 0
    audio=[]
    for eng in (stock,e):
        eng.uc.reg_write(C.UC_M68K_REG_SR,0x2700);audio.append(eng.block(trigger,release))
    row=[int(np.max(np.abs(audio[0][t].astype(np.int64)-audio[1][t].astype(np.int64)))) for t in range(6)]
    rows.append(row)
    if any(row):break
args.output.write_text(json.dumps(dict(blocks=len(rows),settings=cases,max_difference=max(map(max,rows)),differences=rows,hardware_tested=False),indent=2)+'\n')
assert not any(any(row) for row in rows),(len(rows),rows[-1])
print('PASS six stock machines, 12 parameter sets each, PUNCH on/off, retrigs and note-offs: exact PCM',flush=True)
