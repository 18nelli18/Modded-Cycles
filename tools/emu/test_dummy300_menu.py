"""Dummy : vrai setMachine, controles a zero et retour aux machines natives."""
from pathlib import Path
src=Path(__file__).with_name('test_machine_confirm_native.py').read_text()
exec(compile(src,__file__,'exec'))
d=m['dummy300'];s=d['symbols'];u.uc.reg_write(C.UC_M68K_REG_D2,0)
u.call(0x4001477e,obj,28,0,0)
assert u.uc.mem_read(snd+38,1)==b'\x1c',bytes(u.uc.mem_read(snd,100)).hex()
assert not any(u.uc.mem_read(snd+40,18)),bytes(u.uc.mem_read(snd+40,18)).hex()
commands=draw(28,0)
assert any(name=='image' and args[1]==s['dy_icon_bitmap'] for name,args in commands),commands
assert any(name=='image' and args[1]==s['dy_stats_bitmap'] for name,args in commands),commands
u.uc.reg_write(C.UC_M68K_REG_D2,0);u.call(0x4001477e,obj,0,0,0);assert u.uc.mem_read(snd+38,1)==b'\0'
assert not u.bad
print('PASS Dummy native selection, zero controls, native icon/stats drawing and return to Kick',flush=True)
a.output.write_text(json.dumps(dict(native_set=True,all_machine_controls_zero=True,native_icon_and_stats=True,return_to_stock=True,hardware_tested=False),indent=2)+'\n')
