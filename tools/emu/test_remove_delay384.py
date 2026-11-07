"""Sept delays reels, migration de l ancien ID et sauvegarde apres lecture."""
from pathlib import Path
source=Path(__file__).with_name('test_fx_live383.py').read_text(encoding='utf-8');exec(compile(source,__file__,'exec'))
order=m['remove_delay384']['delay_order'];assert order==[11,10,9,5,0,1,2]
rr,ss,held,log,ff,key,turn,data,bind=fx.fixture('unused')
for mode in order:
 for sign in (-1,1):
  rr.w32(ss['cr_mode'],mode);key(2);turn(15,sign);turn(15,sign);key(2,0);want=order[max(0,min(6,order.index(mode)+sign))];assert rr.r32(ss['cr_mode'])==want,(mode,sign,want)
for at in (0x40070efc,0x40070c4e,0x40070f6e):bind(at,lambda _:0)
for cursor in range(7):
 for entry,args in [('nv_overlay',(0,0)),('nv_overlay_canvas',(0,))]:
  rr.w32(ss['fx_menu_open'],1);rr.w32(ss['fx_menu_slot'],1);rr.w32(ss['fx_menu_cursor'],cursor);rr.texts.clear();rr.call(entry,*args);labels=[t[2] for t in rr.texts];assert not any('POTS' in str(t) for t in rr.texts);top=max(0,min(cursor-1,4));expected=[{11:'PHASER',10:'DUCK',9:'DUB',5:'PING PONG',0:'DELAY',1:'CRUSH 1',2:'CRUSH 2'}[v] for v in order[top:top+3]];assert all(v in labels for v in expected),(entry,cursor,labels,expected)
# Le fichier MFT historique avec ID12 reste valide ; seul son choix delay migre.
legacy=dict(files);name='/MFX_12345678.cfg';buf=bytearray(legacy[name]);buf[16+37]=buf[16+39]=12;buf[16+48+37]=buf[16+48+39]=12
import zlib
buf[12:16]=(zlib.crc32(buf[16:])&0xffffffff).to_bytes(4,'big');legacy[name]=bytes(buf)
r,s,files,projects=fixture(legacy);r.u.mem_write(CB,bytes(16));call(0x40061738,RAW);r.u.mem_write(SER,blob);assert call(0x4006a5a0,0x93018000,9,RAW,CB)&255;activate(0);call('mf_frame');assert r.r32(s['cr_mode'])==0
activate(1);assert r.r32(s['cr_mode'])==0
raw=(a.capture/'runtime.bin').read_bytes();old=m['per_track_fx']['symbols'];assert not any(raw[old['pots_process']-0x46700000:old['pots_reset']-0x46700000]);assert b'POTS\0' not in raw[m['per_track_fx']['code']-0x46700000:m['per_track_fx']['code']-0x46700000+m['per_track_fx']['code_bytes']]
print('PASS seven delay choices in both directions, both render paths, old saved-ID migration and DSP removal')

proof=json.loads(a.output.read_text());proof.update(seven_delay_choices=True,both_overlay_paths=True,legacy_id12_migration=True,DSP_removed=True);a.output.write_text(json.dumps(proof,indent=2)+'\n')
