"""Silent3.00 : vrais commit/graphismes natifs et invalidation des candidats perimes."""
from pathlib import Path
src=Path(__file__).with_name('test_machine_confirm_native.py').read_text()
exec(compile(src,__file__,'exec'))
full=m['activity_masks']['full'];replacement=8 if full else 2;next_machine=9 if full else 3;previous_machine=7 if full else 1
s=m['activity_masks']['symbols'];u.uc.mem_write(s['mb_silent'],struct.pack('>I',1));pat=0x93930000
u.uc.mem_write(0x40a7887c,struct.pack('>I',pat));u.uc.mem_write(pat+30706,bytes(4))
u.hooks[0x40012412]=('lane',0);u.hooks[0x4001e318]=('machine',0);u.call(s['mb_cancel'])
for _ in range(3):u.call(0x400a2712,view,1,0,0)
assert u.u32(s['mb_candidate'])==3
# Un son remplace pendant la navigation devient la nouvelle origine.
u.hooks[0x4001e318]=('machine',replacement);u.call(0x400a2712,view,1,0,0);assert u.u32(s['mb_candidate'])==next_machine
# Meme machine dans un autre pattern : ne pas reprendre le candidat precedent.
u.uc.mem_write(pat+30706,struct.pack('>I',1));u.call(0x400a2712,view,1,0,0);assert u.u32(s['mb_candidate'])==next_machine
# Changement de piste et direction : un cran depuis le son de destination.
u.hooks[0x40012412]=('lane',1);u.call(0x400a2712,view,0xffffffff,0,0);assert u.u32(s['mb_candidate'])==previous_machine
# Une release d ecran doit aussi invalider le candidat de l ancien contexte.
u.hooks[0x4001e318]=('machine',4);assert u.call(s['mb_display_machine'],4,view)==4;assert not u.u32(s['mb_pending'])
u.call(0x400a2712,view,1,0,0);before=bytes(u.uc.mem_read(snd,100));u.uc.mem_write(pat+30706,struct.pack('>I',2));u.uc.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,32,1,0));u.call(0x400a292c,view,event)
assert bytes(u.uc.mem_read(snd,100))==before and not u.u32(s['mb_pending']),'DATA committed stale candidate'
print('PASS silent browsing: sound/pattern/track changes invalidate stale candidates; DATA never commits them')
a.output.write_text(json.dumps(dict(native_machine_commit=True,native_graphics_commands_exact=True,stale_sound=True,stale_pattern=True,track_change=True,stale_display=True,stale_DATA=True,hardware_tested=False),indent=2)+'\n')
