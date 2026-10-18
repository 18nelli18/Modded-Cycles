"""Compiler le codec CC seul pour preuves ; aucun flasheur modifie."""
import argparse,json,pathlib,tempfile,subprocess
import gen_macro as gm
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--ui',action='store_true');a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  d=pathlib.Path(tmp);obj=d/'controls.o';elf=d/'controls.elf';binary=d/'controls.bin';ld=d/'controls.ld'
  gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-std=c99','-c',str(ROOT/'tools/machines/midi_machine/controls.c'),'-o',str(obj)])
  objects=[str(obj)]
  if a.ui:
   for name in ('ui.c','ui.S','storage.c','storage.S','worker.c','worker.S','settings.c','lfo.c','lfo.S'):
    o=d/(name+'.o');gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-std=c99','-c',str(ROOT/'tools/machines/midi_machine'/name),'-o',str(o)]);objects.append(str(o))
   popup=d/'popup.s';popup.write_text((ROOT/'tools/machines/beat_repeat/popup.s').read_text().replace('br_popup','mm_popup'))
   o=d/'popup.o';gm.gx.run([gm.gx.CROSS+'gcc',*gm.gx.CFLAGS,'-c',str(popup),'-o',str(o)]);objects.append(str(o))
  ld.write_text('SECTIONS { .text 0x46800000 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } .bss : { *(.bss*) } mm_controls_end = .; }')
  try:gm.gx.run([gm.gx.CROSS+'ld','-T',str(ld),'-e','mm_cc_edit','-o',str(elf),*objects])
  except subprocess.CalledProcessError as error:raise RuntimeError(error.stderr) from error
  gm.gx.run([gm.gx.CROSS+'objcopy','-O','binary',str(elf),str(binary)])
  sy={x[2]:hex(int(x[0],16)) for line in gm.gx.run([gm.gx.CROSS+'nm',str(elf)]).splitlines() if len(x:=line.split())==3 and x[2].startswith('mm_')}
  raw=binary.read_bytes();raw+=bytes(int(sy['mm_controls_end'],16)-0x46800000-len(raw))
  data=dict(hex=raw.hex(),symbols=sy)
 out=ROOT/('build/midi-machine/controls-ui.json' if a.ui else 'build/midi-machine/controls.json');text=json.dumps(data,separators=(',',':'))+'\n'
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('PASS codec CC compile, sans publication')
if __name__=='__main__':main()
