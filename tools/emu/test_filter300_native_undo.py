"""Filtre3.00 : clear/Undo des sons par les vrais setters et presse-papiers natifs."""
from pathlib import Path
import argparse,inspect,json,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
import boot_candidate as bc
import test_fx_menu_control as fx
from unicorn import m68k_const as C
metadata=json.loads((a.build/'BUILD.json').read_text());bc.ROOT=a.output.parent/'cache';fx.metadata=metadata;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
text=(R/'tools/emu/test_filter_defaults.py').read_text().split('# Nouveau contexte')[0]
text=text.replace("m=json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text())",'m=metadata')
text=text.replace("u.mem_map(0x80000000,0x20000)","")
text=text.replace(";u=r.u\n", """;u=r.u
u.mem_map(0x80000000,0x20000)
for off,at,n in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):u.mem_write(at,bytes(u.mem_read(0x46700000+off,n)))
bind(0x40000542,lambda args:0);u.reg_write(C.UC_M68K_REG_A0,0x931b0000);r.call(metadata['complete_irq_accounting']['boot_target'])
""",1)
text=text.replace('def seed_filters():\n seedall()',"def seed_filters():\n r.call(metadata['filter_pattern300']['symbols']['fp_sync']);seedall()")
old=sys.argv
try:
 sys.argv=['test','v211'];exec(compile(text,'native-filter-undo','exec'),{'__file__':str(R/'tools/emu/test_filter_defaults.py'),'metadata':metadata,'C':C})
finally:sys.argv=old
a.output.write_text(json.dumps(dict(sha256=metadata['sha256'],native_sound_clear_undo=True,new_sound_defaults=True,native_pattern_clear=True,hardware_tested=False),indent=2)+'\n')
