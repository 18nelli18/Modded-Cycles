"""Wizard3.00 : CTRL-ALL pendant31pas vides, reset natif et note suivante."""
from pathlib import Path
src=Path(__file__).with_name('test_wizard_plock_priority.py').read_text()
src=src.replace("r,files,bind=fixture();r.u.mem_map(0x80000000,0x20000)","""r,files,bind=fixture();r.u.mem_map(0x80000000,0x20000)
for off,at,n in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):r.u.mem_write(at,bytes(r.u.mem_read(0x46700000+off,n)))
bind(0x40000542,lambda a:0);r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);r.call(m['complete_irq_accounting']['boot_target'])
""")
src=src.replace(" step[0]=1;r.call(0x40058308,0,frame,sound(0));", """ for empty_step in range(1,32):
  step[0]=empty_step
  assert r.call(s['aa_face_encoder'],0,EVENT)==77
  assert r16(frame+14+2*slot)==8888,('held loop overridden',slot,empty_step)
  assert r.r32(0x800011e8+4*(7+slot))==8888<<16
 step[0]=32;r.call(0x40058308,0,frame,sound(0));""")
src=src.replace('slots_tested=32,','slots_tested=32,sustain_empty_steps=31,active_note_bitmap=True,')
exec(compile(src,__file__,'exec'))
