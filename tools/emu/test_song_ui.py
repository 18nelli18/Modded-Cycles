"""Editeur natif Song : ouverture, lignes, valeurs, mutes et fermeture."""
from pathlib import Path
source=(Path(__file__).parent/'test_acid_articulation_ui.py').read_text().split('r,files,bind=fixture();')[0]
exec(compile(source,__file__,'exec'))
r,files,bind=fixture();held=set();bind(s['aa_old_key'],lambda a:77);bind(s['aa_old_encoder'],lambda a:77);bind(0x4007faf4,lambda a:int(a[0] in held))
def state(name,v):r.w32(al[name],v)
def key(code,flags=1):r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call(s['aa_face_key'],0,EVENT) if r.r32(s['sg_page']) else r.call(s['sg_key'],EVENT)
def turn(knob,d):r.delta=d;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,knob,d&0xffffffff,0));return r.call(s['aa_face_encoder'],0,EVENT) if r.r32(s['sg_page']) else r.call(s['sg_encoder'],EVENT)
state('menu',1);state('gc_level',0);state('gc_tree_cursor',1);turn(1,1);assert r.r32(al['gc_tree_cursor'])==2
key(32);key(32,16);assert r.r32(s['sg_page'])==1 and r.r32(s['sg_song'])==1
turn(2,17);turn(3,2);assert bytes(r.u.mem_read(s['sg_song']+8,4))==bytes([17,3,0,0])
key(16);key(21);assert r.u.mem_read(s['sg_song']+10,1)[0]==33
key(15);assert r.r32(s['sg_song'])==2 and r.r32(s['sg_cursor'])==1
turn(2,1);assert r.u.mem_read(s['sg_song']+12,1)[0]==18
key(1);key(32);key(32,16);assert r.r32(s['sg_song']+4)==1
key(15);assert r.r32(s['sg_song'])==1 and r.r32(s['sg_cursor'])==0;key(1,0);held.clear()
key(12);assert not r.r32(s['sg_page']) and r.r32(al['gc_level'])==0
turn(1,1);assert r.r32(al['gc_tree_cursor'])==0
turn(1,-1);assert r.r32(al['gc_tree_cursor'])==2
a.output.write_text(json.dumps(dict(top_level_song=True,root_rows=3,row_editing=True,insert_delete=True,mutes=True,loop_toggle=True,hardware_tested=False),indent=2)+'\n');print('PASS top-level Song editor controls',flush=True)
