"""Note 104 : petit stage PIC, aucune nouvelle fonction musicale."""
import argparse,json,pathlib,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();cross=next(c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'as'))
 with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
  d=pathlib.Path(temp);(d/'link.ld').write_text('SECTIONS { .text 0 : SUBALIGN(2) { *(.text) } }')
  subprocess.run([cross+'as','-march=cfv4e','-o',str(d/'code.o'),str(ROOT/'tools/machines/beat_repeat/capacity_boot.s')],check=True)
  subprocess.run([cross+'ld','-T',str(d/'link.ld'),'-o',str(d/'code.elf'),str(d/'code.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(d/'code.elf'),str(d/'code.bin')],check=True)
  sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm',str(d/'code.elf')],text=True).splitlines() if len(v:=line.split())==3 and v[2].startswith('capacity_')}
  raw=(d/'code.bin').read_bytes();text='window.MCNoMidiCapacity='+json.dumps(dict(hex=raw.hex(),symbols=sy),separators=(',',':'))+';\n'
 target=ROOT/'build/no-midi-capacity-data.js'
 if a.check:assert target.read_text()==text
 else:target.write_text(text)
 print('PASS stage copie Wizard',len(raw),'octets')
if __name__=='__main__':main()
