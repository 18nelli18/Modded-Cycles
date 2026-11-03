from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))

from unicorn import UC_HOOK_CODE
source=Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/build/volume-pan-toggle/volume-pan-toggle-test.json');old=json.loads(source.read_text());symbols={k:int(v,16) for t in old['composedTweaks'] for k,v in t.get('symbols',{}).items()}
track=3;slot=int.from_bytes(e.uc.mem_read(symbols['track_slot']+4*track,4),'big');assert slot<64
count=int.from_bytes(e.uc.mem_read(symbols['slot_count']+4*slot,4),'big');assert count>0
for t in range(6):
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=6 if t==track else 0,note=60,decay=110,punch=0);e.uc.mem_write(E.VOICE0+t*E.VSTRIDE+56,struct.pack('>I',1))

e.uc.mem_write(symbols['loop_mode']+4*track,struct.pack('>I',3));e.set(track,color=64,shape=0,sweep=127,contour=64)
# Le flag+56 est partage avec l'etat du trig precedent. Installer d'abord
# la machine sur un bloc sans trig, puis presenter un vrai front montant.
e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.block(0)
rows=[]
for b in range(32):
 e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);pcm=e.block(1<<track if b==0 else 0)
 rows.append(dict(block=b,peak=int(np.abs(pcm[track]).max()),gr_on=bytes(e.uc.mem_read(symbols['gr_on']+track,1)).hex(),quiet=bytes(e.uc.mem_read(0x4673205e+track,1)).hex(),gr_cd=int.from_bytes(e.uc.mem_read(symbols['gr_cd']+4*track,4),'big')))
print(rows,flush=True)
assert max(r['peak'] for r in rows)>100000,'Aucun signal granular audible dans le banc'
args.output.write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
