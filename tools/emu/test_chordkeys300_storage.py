"""Audit ChordKeys Optional : vrai cycle natif sauvegarde/chargement de pattern."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(src,__file__,'exec'))
assert not m.get('chordkeys_removed')
ck={k:int(v,0) for k,v in json.loads((R/'docs/flasher/source/integration-chord-keys.json').read_text())['symbols'].items()}
r.u.mem_map(0x93200000,0x100000)
b1,b2,serialized=0x93200000,0x93210000,0x93220000
r.u.mem_write(b1,bytes(30710));r.call(0x400615e8,b1,0);h1=b1+30642
words=[0x80000000|(t<<28)|((24+t)<<21)|sum(((t+d)%5)<<(3*d) for d in range(7)) for t in range(6)]
r.w32(h1+32,0x434b0300|0x25)
for t,w in enumerate(words):r.w32(h1+40+4*t,w)
assert [r.call(ck['ck_storage_read'],h1,t) for t in range(6)]==words
r.u.mem_write(serialized,bytes(14800));assert r.call(0x4005ba0a,serialized,b1,0)==1

r.u.mem_write(b2,b'\xa5'*30710);assert r.call(0x4005b894,b2,serialized,73)==1

actual=[r.call(ck['ck_storage_read'],b2+30642,t) for t in range(6)];assert actual==words,(actual,words)
assert r.r32(b2+30642+32)==0x434b0425

# Simuler plusieurs redemarrages : caches RAM vides avant chaque decodage.
cs=m['chord_storage300'];sy=cs['symbols'];pl=m['page_length']['symbols']
for iteration in range(3):
 r.u.mem_write(cs['bss'],bytes(cs['bss_end']-cs['bss']))
 r.u.mem_write(b1,bytes(r.u.mem_read(b2,30710)));r.u.mem_write(b1+30642+60,bytes([80,87,12,243]))
 assert r.call(0x4005ba0a,serialized,b1,0)==1
 r.u.mem_write(b2,b'\xa5'*30710);assert r.call(0x4005b894,b2,serialized,73)==1
 assert [r.call(ck['ck_storage_read'],b2+30642,t) for t in range(6)]==words
 assert r.call(pl['pl_length'],b2+30642)==12 and r.call(pl['pl_warp'],b2+30642)==1
 assert r.r32(b2+30642+32)==0x434b0425
# Vrais setters UI et notification native : six pistes, tous les champs.
obj=0x93240000;vt=obj+256;current=[b2+30642];r.w32(obj,vt);r.w32(obj+16,current[0]);notify=0x93241000;r.w32(vt+16,notify);notifications=[]
bind(cs['aliases']['cs_object'],lambda args:obj);bind(cs['aliases']['cs_ui_header'],lambda args:current[0]);bind(cs['aliases']['cs_audio_header'],lambda args:current[0]);bind(notify,lambda args:notifications.append(args[0]) or 0)
import random
rng=random.Random(300);tests=0
for t in range(6):
 for i in range(80):
  word=(rng.randrange(2)<<31)|(rng.randrange(7)<<28)|(rng.randrange(24,49)<<21)|sum(rng.randrange(5)<<(3*d) for d in range(7))
  page=bytes(r.u.mem_read(current[0]+60,4));r.call(ck['ck_ui_config_set'],t,word)
  assert r.call(ck['ck_ui_config_get'],t)==word
  assert r.call(ck['ck_audio_config'],t)==word
  assert bytes(r.u.mem_read(current[0]+60,4))==page
  r.call(ck['ck_ui_midi_set'],t,i&1);assert r.call(ck['ck_ui_midi_get'],t)==(i&1);assert r.call(ck['ck_audio_midi_get'],t)==(i&1)
  words[t]=word;tests+=1
assert len(notifications)==tests*2
assert r.call(0x4005ba0a,serialized,b2,0)==1
r.u.mem_write(cs['bss'],bytes(cs['bss_end']-cs['bss']));r.u.mem_write(b1,b'\xa5'*30710)
assert r.call(0x4005b894,b1,serialized,12)==1
assert [r.call(ck['ck_storage_read'],b1+30642,t) for t in range(6)]==words
assert r.r32(b1+30642+32)==0x434b043f

# Des anciens patterns ayant deja perduT6 migrentT1..5 sans les effacer.
legacy=0x93250000;r.u.mem_write(legacy,bytes(64));r.w32(legacy+32,0x434b0305)
for t,w in enumerate(words[:5]):r.w32(legacy+40+4*t,w)
r.w32(legacy+60,0x504c10ef);r.call(ck['ck_storage_load'],current[0],legacy)
assert [r.call(ck['ck_storage_read'],current[0],t) for t in range(6)]==words[:5]+[48<<21]
print('PASS ChordKeys: three native save/load cycles with RAM reset, independent Page Length/Warp,',tests,'UI/audio/MIDI settings cases and legacy migration',flush=True)
a.output.write_text(json.dumps(dict(native_pattern_roundtrip=True,reboots=3,ui_cases=tests,all_six_tracks=True,page_length_and_warp_preserved=True,midi_bits=True,legacy_migration=True,source_syx=m['sha256'],hardware_tested=False),indent=2)+'\n')
