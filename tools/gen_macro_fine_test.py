"""Note129 : rendre un accordage fin MACRO sans remplacer son controle lo-fi."""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
import gen_macro as gm
from gen_seq_gen import symbols
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-18-macro-fine-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();cross=gm.gx.CROSS
 with tempfile.TemporaryDirectory() as folder:
  d=pathlib.Path(folder);objects=[]
  for name in ('fine.c','fine.S','fine_draw.S'):
   out=d/(name+'.o');gm.gx.run([cross+'gcc',*gm.gx.CFLAGS,'-std=c99','-c',str(ROOT/'tools/machines/macro'/name),'-o',str(out)]);objects.append(str(out))
  (d/'x.ld').write_text('SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } .bss : { *(.bss*) } }')
  gm.gx.run([cross+'ld','--emit-relocs','-T',str(d/'x.ld'),'-o',str(d/'x.elf'),*objects]);gm.gx.run([cross+'objcopy','-O','binary',str(d/'x.elf'),str(d/'x.bin')])
  raw=(d/'x.bin').read_bytes();sy=symbols(cross,d/'x.elf');rel=gm.gx.run([cross+'readelf','-rW',str(d/'x.elf')]);offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)]
  assert all(int.from_bytes(raw[i:i+4],'big')<len(raw) for i in offsets)
  data=dict(hex=raw.hex(),symbols=sy,reloc=offsets)
 out=ROOT/'docs/flasher-macro-fine-test';out.mkdir(exist_ok=True)
 files={f.name:f.read_bytes() for f in (ROOT/'docs/flasher').iterdir() if f.is_file()}
 files['macro-fine-data.js']=('window.MCMacroFine='+json.dumps(data,separators=(',',':'))+';\n').encode();files['macro-fine.js']=(ROOT/'tools/web/macro-fine.js').read_bytes()
 for name in ('beat-diagnostic-data.js','beat-diagnostic.js'):files[name]=(ROOT/'docs/flasher-machine-combinations-test'/name).read_bytes()
 text=files['index.html'].decode();text=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,text);text=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",text)
 notice='<p role="note"><strong data-l="en">MACRO fine-tune test.</strong><strong data-l="fr">Test accordage fin MACRO.</strong> <span data-l="en">Fixed full-feature preset; MIDI B-side bank remains optional. Hold SETTINGS and turn PITCH on MACRO for fine pitch (about0.78cent per step). FUNC + PITCH still controls Lo-Fi. Normal PITCH turns retain the fine offset; saving uses the native pitch value. CPU/CUT diagnostic included when Syntakt engines and beat repeat are selected. Main and909 unchanged. Hardware verification pending.</span><span data-l="fr">Preset complet fixe ; banque MIDI B facultative. Maintenir SETTINGS et tourner PITCH sur MACRO : accordage fin (environ0,78cent par pas). FUNC + PITCH conserve le Lo-Fi. PITCH normal conserve la fraction fine ; sauvegarde dans la hauteur native. Diagnostic CPU/CUT si moteurs Syntakt et beat repeat sont choisis. Principal et909 inchanges. Verification materielle attendue.</span></p>'
 text=text.replace('<main class="wrap fl">','<main class="wrap fl">'+notice).replace('../assets/release.js?','macro-fine-release.js?');text=re.sub(r'<title>.*?</title>','<title>MACRO fine-tune test</title>',text,count=1)
 text=text.replace('</body>',''.join(f'<script src="{name}?v={STAMP}"></script>' for name in ('beat-diagnostic-data.js','beat-diagnostic.js','macro-fine-data.js','macro-fine.js'))+'</body>');files['index.html']=text.encode()
 files['macro-fine-release.js']=('window.MC_RELEASES='+json.dumps([dict(version='MACRO-fine-test.1',date='2026-10-18',changes=[dict(en='SETTINGS + PITCH adds fine pitch on MACRO without changing FUNC + PITCH Lo-Fi. Native pitch storage and synthesis retained; diagnostic included. Hardware verification pending.',fr='SETTINGS + PITCH accorde finement MACRO sans changer le Lo-Fi FUNC + PITCH. Stockage hauteur et synthese natifs conserves ; diagnostic inclus. Verification materielle attendue.')])])+';\n').encode()
 files['BUILD.json']=(json.dumps(dict(stamp=STAMP,scope='test-only',diagnostics=True,hardware_verified=False,released_flashers_unchanged=True,fine_combo='SETTINGS + PITCH',lofi_combo='FUNC + PITCH'),indent=2)+'\n').encode()
 for name,raw in files.items():
  istext=pathlib.Path(name).suffix in ('.js','.html','.css','.json','.md','.txt')
  if istext:raw=raw.replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n'
  if a.check:assert ((out/name).read_bytes().replace(b'\r\n',b'\n') if istext else (out/name).read_bytes())==raw,name
  else:(out/name).write_bytes(raw)
 print('PASS test MACRO fine genere :',len(data['hex'])//2,'octets UI seuls')
if __name__=='__main__':main()
