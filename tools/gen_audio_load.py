"""Note 112 : filtre exact et garde slides MIDI, copie test avec diagnostic."""
import argparse,hashlib,json,pathlib,re,shutil,subprocess,tempfile
from gen_filter_precision import generate,ROOT
from gen_beat_repeat import generate as generate_repeat
import sys
sys.path.insert(0,str(ROOT/'tools/emu'))
from test_sdvintage import main_os_from_syx
STAMP='2026-10-17-audio-load-test-6'
def module():
 cross=next(c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'gcc'))
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);src=ROOT/'tools/machines/audio_load'
  for f in ('slides.c','trampoline.s'):subprocess.run([cross+'gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-common','-fno-stack-protector','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror','-c',str(src/f),'-o',str(p/(f+'.o'))],check=True)
  subprocess.run([cross+'gcc','-mcpu=54418','-c',str(src/'native_index.s'),'-o',str(p/'index.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'index.o'),str(p/'index.bin')],check=True)
  assert (p/'index.bin').read_bytes().hex()=='a38248420282000000ff'
  (p/'link.ld').write_text('SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } .bss : { *(.bss*) } . = ALIGN(4); ao_end = .; }')
  subprocess.run([cross+'ld','--emit-relocs','-T',str(p/'link.ld'),'-o',str(p/'e'),str(p/'slides.c.o'),str(p/'trampoline.s.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'e'),str(p/'raw')],check=True)
  sy={x[2]:int(x[0],16) for line in subprocess.check_output([cross+'nm','--defined-only',str(p/'e')],text=True).splitlines() if len(x:=line.split())==3}
  raw=(p/'raw').read_bytes();raw+=bytes(sy['ao_end']-len(raw));rel=subprocess.check_output([cross+'readelf','-rW',str(p/'e')],text=True)
  offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)]
  return dict(hex=raw.hex(),symbols=sy,reloc=offsets)
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 filt=generate(ROOT/'tools/machines/track_filter/diagnostic.s');old=json.loads((ROOT/'docs/flasher/filter-load-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'));filt['old_sha256']=hashlib.sha256(bytes.fromhex(old['hex'])).hexdigest()
 repeat=generate_repeat([],ROOT/'tools/machines/audio_load');original=json.loads((ROOT/'docs/flasher/beat-repeat-data.js').read_text(encoding='utf-8').split('window.MCBeatRepeat=',1)[1].strip().rstrip(';'));repeat['boot']=original['boot'];repeat['redirect']=original['redirect'];stock=main_os_from_syx(str(ROOT/'firmware/model-cycles_OS1.13.syx'));native=dict(at=0x400a82e2,end=0x400a835e,branch=0x400a832c,old_sha256=hashlib.sha256(stock[0x400a82e2-0x40000400:0x400a835e-0x40000400]).hexdigest(),index_hex='a38248420282000000ff');data=dict(filter=filt,slides=module(),repeat=repeat,native=native,native_pair=dict(at=0x400a816e,end=0x400a8204,branch=0x400a81e4,old_sha256=hashlib.sha256(stock[0x400a816e-0x40000400:0x400a8204-0x40000400]).hexdigest()));target=ROOT/'docs/flasher-audio-load-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(tmp.name) if tmp else target;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher-beat-diagnostic-test').iterdir():
  if f.is_file():shutil.copyfile(f,out/f.name)
 (out/'audio-load-data.js').write_text('window.MCAudioLoad='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8');shutil.copyfile(ROOT/'tools/web/audio-load.js',out/'audio-load.js')
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('Main flasher — beat repeat diagnostic test','Main flasher — broader audio load test').replace('Beat repeat load diagnostic test.','Audio load optimization test.').replace('Test diagnostic charge beat repeat.','Test optimisation charge audio.')
 extra='<p><span data-l="en">Filter-state diagnostic: hold FUNCTION when releasing TRACK + RETRIG for track 6 F/Q/K/M (coefficients and last incoming MACSR). Compare clean and crushed states at cutoff 126, resonance 0. This test adds observation, not a claimed repair. Also shares identical track fade calculations during repeat transitions, tests lower-cost filter scheduling with and without resonance, and skips empty MIDI CC-slide scans. Filter samples/states and MIDI scheduling are compared against main in emulation. CPU/CUT diagnostic retained; select its checkbox and at least one SY engine. Native oscillator changes from test 2 are removed; both filter paths schedule useful work between EMAC and result reads. Main remains unchanged.</span><span data-l="fr">Diagnostic filtre : maintenir FUNCTION en relachant TRACK + RETRIG pour F/Q/K/M piste 6. Comparer propre/degrade, cutoff 126 et resonance 0. Observation seulement. Partage aussi les calculs de fondu repeat identiques, allege l ordonnancement filtre avec et sans resonance et evite les balayages slides CC vides. Samples/etats filtre et cadence MIDI compares au principal en emulation. Diagnostic CPU/CUT conserve ; cocher sa carte et au moins un moteur SY. Changements oscillateurs natifs du test 2 retires ; les deux chemins filtre preparent du travail entre EMAC et lecture du resultat. Principal inchange.</span></p>'
 s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+extra).replace('</body>',f'<script src="audio-load-data.js?v={STAMP}"></script><script src="audio-load.js?v={STAMP}"></script></body>');(out/'index.html').write_text(s,encoding='utf-8')
 (out/'diagnostic-release.js').write_text('window.MC_RELEASES=[{version:"Audio-load-test.6",date:"2026-10-17",changes:[{en:"Adds a read-only track 6 filter coefficient and incoming MACSR snapshot with FUNCTION during repeat-combo release. CPU/CUT retained. No claimed distortion repair; hardware comparison needed.",fr:"Ajoute un releve piste 6 coefficients filtre et MACSR entrant avec FUNCTION au relachement du combo repeat. CPU/CUT conserves. Aucune correction de distorsion revendiquee."}]}];\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 build=ROOT/'build/audio-load';build.mkdir(exist_ok=True);(build/'data.json').write_text(json.dumps(data),encoding='utf-8');(build/'repeat-data.json').write_text(json.dumps(repeat),encoding='utf-8');(build/'filter-data.js').write_text('window.MCFilterFast='+json.dumps(filt)+';\n',encoding='utf-8');print('PASS candidat charge audio, filtre',filt['code_size'],'octets')
if __name__=='__main__':main()
