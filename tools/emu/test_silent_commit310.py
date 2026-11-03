"""Vrai commit/dessin OS puis regression reentrante du guard SIL installe."""
from pathlib import Path
exec(compile(Path(__file__).with_name('test_silent_browse300.py').read_text(),__file__,'exec'))
guard=m['silent_commit_guard'];commit=guard['committing'];display=s['mb_display_machine'];patch=guard['patches'][0]
assert bytes(u.uc.mem_read(display,6)).hex()==patch['new']
outcomes={}
for variant in ('before','after'):
 u.uc.mem_write(display,bytes.fromhex(patch['old'] if variant=='before' else patch['new']))
 u.uc.ctl_remove_cache(display,display+160)
 u.uc.mem_write(commit,bytes(4));u.call(s['mb_cancel'])
 u.hooks[0x40012412]=('lane',0);u.hooks[0x4001e318]=('machine',0)
 u.call(0x400a2712,view,1,0,0);candidate=u.u32(s['mb_candidate'])
 u.uc.mem_write(commit,struct.pack('>I',1));u.hooks[0x4001e318]=('machine',4)
 shown=u.call(display,4,view);pending=u.u32(s['mb_pending']);still_committing=u.u32(commit)
 outcomes[variant]=dict(shown=shown,pending=pending,committing=still_committing)
 if variant=='before':assert not pending and not still_committing
 else:assert shown==4 and pending and still_committing and u.call(s['mb_step'],0,1)==candidate
 u.uc.mem_write(commit,bytes(4))
u.call(s['mb_cancel'])
print('PASS installed SIL guard: old display cancels active commit; new display preserves it')
a.output.write_text(json.dumps(dict(native_commit_and_graphics=True,stale_context_checks=True,reentrant_guard=outcomes,native_redraw_order_reproduced=False,audio_hooks_changed=False,hardware_tested=False),indent=2)+'\n')
