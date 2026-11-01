"""Dummy : vraie boucle native, silence exact et PCM des autres pistes conserve."""
from pathlib import Path
src=Path(__file__).with_name('test_stock_machine_parity.py').read_text()
exec(compile(src,__file__,'exec'))
d=meta['dummy300'];s=d['symbols'];assert e.uc.mem_read(0x400a7d96,6)==b'\x4e\xf9'+struct.pack('>I',s['dy_voice'])
e.set(0,machine=28)
for b in range(32):
 before=stock.block(0);after=e.block(1)
 assert not np.any(after[0]),('Dummy audible',b)
 for t in range(1,6):assert np.array_equal(before[t],after[t]),('Other machine changed',b,t)
assert int.from_bytes(e.uc.mem_read(E.PARAMS+14+18,1),'big')==28
print('PASS Dummy: 32 repeatedly triggered blocks exactly zero; other five machines PCM exact',flush=True)
proof=json.loads(args.output.read_text());proof.update(dummy_blocks=32,dummy_output_exact_zero=True,other_tracks_pcm_exact=True);args.output.write_text(json.dumps(proof,indent=2)+'\n')
