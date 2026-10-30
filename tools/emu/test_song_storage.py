"""Codec SGA1 natif compile, isolation des projets et CRC ; codecs amont simules."""
from pathlib import Path
source=(Path(__file__).parent/'test_acid_articulation_ui.py').read_text().split('r,files,bind=fixture();')[0]
exec(compile(source,__file__,'exec'))
r,files,bind=fixture();buf=0x94000000;r.u.mem_map(buf,0x1000);project=0x93171000;singleton=0x93170000;r.w32(0x40fe4228,singleton);r.w32(singleton+16,project)
base=bytearray((i*17)&255 for i in range(512));base[:8]=struct.pack('>II',0xbeefbace,6)
def encode(args):r.u.mem_write(args[0],bytes(base));return 1
bind(s['sg_old_encode'],encode);bind(s['sg_old_decode'],lambda a:1);bind(s['sg_old_new'],lambda a:1)
r.call(s['sg_sync']);r.call(s['aa_track_set'],2,100,0);r.w32(s['sg_song'],2);r.w32(s['sg_song']+4,1);r.u.mem_write(s['sg_song']+8,bytes([0,2,0,0,1,3,4,0]))
assert r.call(s['sg_encode'],buf,project,512,16,0)==1
saved=bytes(r.u.mem_read(buf,512));assert saved[:64]==base[:64] and saved[368:]==base[368:]
r.w32(singleton+16,project+1024);r.call(s['sg_sync']);assert r.call(s['aa_glide_get'],2)==1 and r.r32(s['sg_song'])==0
r.call(s['sg_decode'],project+1024,buf,0);assert r.call(s['aa_glide_get'],2)==100 and r.call(s['aa_legato_get'],2)==0 and r.r32(s['sg_song'])==2
bad=bytearray(saved);bad[80]^=1;r.u.mem_write(buf,bytes(bad));r.call(s['sg_decode'],project+1024,buf,0);assert r.r32(s['sg_song'])==0 and r.call(s['aa_glide_get'],2)==1
r.u.mem_write(buf,saved);bind(s['sg_old_decode'],lambda a:0);r.call(s['sg_decode'],project+1024,buf,0);assert r.r32(s['sg_song'])==0
a.output.write_text(json.dumps(dict(compiled_codec=True,native_upstream_codec_stubbed=True,only_reserved_padding_changed=True,track_settings_and_rows_roundtrip=True,project_isolation=True,corruption_defaults=True,decode_failure_preserved=True,hardware_tested=False),indent=2)+'\n');print('PASS song/ACID project record, roundtrip, isolation and CRC',flush=True)
