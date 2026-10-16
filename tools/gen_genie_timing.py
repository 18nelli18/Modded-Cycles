"""Note 103 : helper propre pour la frontiere MIDI, sans nouvelles allocations."""
import argparse,json,pathlib,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='build/genie-timing-data.js');p.add_argument('--check',action='store_true');a=p.parse_args()
 cross=next(c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'as'))
 with tempfile.TemporaryDirectory(dir=ROOT/'build') as temp:
  d=pathlib.Path(temp);(d/'link.ld').write_text('QUEUE_MODE = 0x11223344; BANK_CONT = 0x22334455; SECTIONS { .text 0 : SUBALIGN(2) { *(.text) } }')
  subprocess.run([cross+'as','-march=cfv4e','-o',str(d/'code.o'),str(ROOT/'tools/machines/seq_gen/timing_boundary.s')],check=True)
  subprocess.run([cross+'ld','-T',str(d/'link.ld'),'-o',str(d/'code.elf'),str(d/'code.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(d/'code.elf'),str(d/'code.bin')],check=True)
  raw=(d/'code.bin').read_bytes();assert len(raw)<=64
  reloc={name:[i for i in range(0,len(raw)-3,2) if raw[i:i+4]==bytes.fromhex(sig)] for name,sig in [('mode','11223344'),('cont','22334455')]};assert len(reloc['mode'])==1 and len(reloc['cont'])==2
  text='window.MCGenieTiming='+json.dumps(dict(hex=raw.hex(),reloc=reloc),separators=(',',':'))+';\n'
  target=ROOT/a.output
  if a.check:assert target.read_text()==text
  else:target.write_text(text)
 print('PASS helper timing',len(raw),'octets ; D1/stack preserves')
if __name__=='__main__':main()
