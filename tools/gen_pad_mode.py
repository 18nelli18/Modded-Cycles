"""Note130 : compiler uniquement le menu des pads ; aucun code filtre ni hook audio."""
import argparse,json,pathlib,re,tempfile
import gen_macro as gm
from gen_seq_gen import symbols
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();cross=gm.gx.CROSS
 with tempfile.TemporaryDirectory() as folder:
  d=pathlib.Path(folder);objects=[]
  for name in ('control.c','hooks.S','menu.S'):
   obj=d/(name+'.o');gm.gx.run([cross+'gcc',*gm.gx.CFLAGS,'-DWF_PAD_ONLY=1','-fno-optimize-sibling-calls','-std=c99','-c',str(ROOT/'tools/machines/wizard_control'/name),'-o',str(obj)]);objects.append(str(obj))
  (d/'x.ld').write_text('SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } . = ALIGN(4); .bss : { *(.bss*) *(COMMON) } . = ALIGN(4); wf_end = .; }')
  gm.gx.run([cross+'ld','--emit-relocs','-T',str(d/'x.ld'),'-o',str(d/'x.elf'),*objects]);gm.gx.run([cross+'objcopy','-O','binary',str(d/'x.elf'),str(d/'x.bin')]);sy=symbols(cross,d/'x.elf');raw=(d/'x.bin').read_bytes();raw+=bytes(sy['wf_end']-len(raw));rel=gm.gx.run([cross+'readelf','-rW',str(d/'x.elf')]);offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)];assert all(int.from_bytes(raw[i:i+4],'big')<len(raw) for i in offsets)
 assert not any(name in sy for name in ('wf_cut','wf_res','wf_value','wf_before','wf_after'))
 files={'pad-mode-data.js':'window.MCPadMode='+json.dumps(dict(hex=raw.hex(),symbols=sy,reloc=offsets),separators=(',',':'))+';\n','pad-mode.js':(ROOT/'tools/web/pad-mode.js').read_text(encoding='utf-8')}
 for name,text in files.items():
  out=ROOT/'docs/flasher'/name;text=text.replace('\r\n','\n').rstrip()+'\n'
  if a.check:assert out.read_text(encoding='utf-8')==text,name
  else:out.write_text(text,encoding='utf-8')
 print('PASS pads seulement :',len(raw),'octets ; aucune routine filtre/capture/audio')
if __name__=='__main__':main()
