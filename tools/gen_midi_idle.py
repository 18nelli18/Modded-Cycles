"""Raccourci vers les LFO audio lorsque aucune machine MIDI n’est active."""
import argparse,pathlib,tempfile,subprocess,shutil,re,json
from gen_seq_gen import symbols
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
 cross=next(c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'gcc'))
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);src=ROOT/'tools/machines/midi_idle/idle.s'
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'x.o'),str(src)],check=True)
  (p/'x.ld').write_text('SECTIONS { .text 0 : { *(.text*) } }')
  subprocess.run([cross+'ld','--emit-relocs','-T',str(p/'x.ld'),'-o',str(p/'x.elf'),str(p/'x.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'x.elf'),str(p/'x.bin')],check=True)
  raw=(p/'x.bin').read_bytes();sy=symbols(cross,p/'x.elf');rel=subprocess.check_output([cross+'readelf','-rW',str(p/'x.elf')],text=True)
  offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)]
  assert all(int.from_bytes(raw[i:i+4],'big')<len(raw) for i in offsets)
 text=json.dumps(dict(hex=raw.hex(),symbols=sy,reloc=offsets),separators=(',',':'))
 out=ROOT/'build/midi-idle';out.mkdir(exist_ok=True)
 if a.check:assert (out/'data.json').read_text(encoding='utf-8')==text
 else:(out/'data.json').write_text(text,encoding='utf-8')
 print('PASS MIDI idle helper',len(raw),'octets, aucun scan LFO MIDI inutile')
if __name__=='__main__':main()
