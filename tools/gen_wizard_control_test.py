"""Test130 : filtre Control All sur sample locks et choix des pads en menu natif."""
import argparse,json,pathlib,re,tempfile
import gen_macro as gm
from gen_seq_gen import symbols
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-wizard-control-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();cross=gm.gx.CROSS
 with tempfile.TemporaryDirectory() as folder:
  d=pathlib.Path(folder);objects=[]
  for name in ('control.c','hooks.S','menu.S'):
   obj=d/(name+'.o');gm.gx.run([cross+'gcc',*gm.gx.CFLAGS,'-fno-optimize-sibling-calls','-std=c99','-c',str(ROOT/'tools/machines/wizard_control'/name),'-o',str(obj)]);objects.append(str(obj))
  (d/'x.ld').write_text('SECTIONS { .text 0 : { *(.text*) *(.rodata*) } . = ALIGN(4); .data : { *(.data*) } . = ALIGN(4); .bss : { *(.bss*) *(COMMON) } . = ALIGN(4); wf_end = .; }')
  gm.gx.run([cross+'ld','--emit-relocs','-T',str(d/'x.ld'),'-o',str(d/'x.elf'),*objects]);gm.gx.run([cross+'objcopy','-O','binary',str(d/'x.elf'),str(d/'x.bin')]);sy=symbols(cross,d/'x.elf');raw=(d/'x.bin').read_bytes();raw+=bytes(sy['wf_end']-len(raw));rel=gm.gx.run([cross+'readelf','-rW',str(d/'x.elf')]);offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)];assert all(int.from_bytes(raw[i:i+4],'big')<len(raw) for i in offsets)
 files={f.name:f.read_bytes() for f in (ROOT/'docs/flasher').iterdir() if f.is_file()}
 for name in ('beat-diagnostic-data.js','beat-diagnostic.js'):files[name]=(ROOT/'docs/flasher-machine-combinations-test'/name).read_bytes()
 preset=files['midi-machine-main.js'].decode().replace('pageReady,window.MCLfoDestinationsReady','pageReady,window.MCLfoDestinationsReady,window.MCBeatDiagnosticReady').replace("'startup-animation','boot-anim','audio-load-diagnostic'","'startup-animation','boot-anim'").replace("select('audio-load-diagnostic',false)","select('audio-load-diagnostic',true)");files['midi-machine-main.js']=preset.encode()
 files['wizard-control-data.js']=('window.MCWizardControl='+json.dumps(dict(hex=raw.hex(),symbols=sy,reloc=offsets),separators=(',',':'))+';\n').encode();files['wizard-control-test.js']=(ROOT/'tools/web/wizard-control-test.js').read_bytes()
 html=files['index.html'].decode();html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=html.replace('<script src="midi-machine-main.js?',f'<script src="beat-diagnostic-data.js?v={STAMP}"></script><script src="beat-diagnostic.js?v={STAMP}"></script><script src="midi-machine-main.js?')
 html=html.replace('</body>',f'<script src="wizard-control-data.js?v={STAMP}"></script><script src="wizard-control-test.js?v={STAMP}"></script></body>')
 notice='<p role="note"><strong data-l="en">Sample-lock filter + pad selection test.</strong><strong data-l="fr">Test filtre des sample locks et selection des pads.</strong> <span data-l="en">TRACK + MACHINES + SWEEP/CONTOUR: Control All filter also overrides Sample Wizard sample-locked steps on tracks that change. Samples and slices stay intact; no additional filter pass. Overrides are live session state, not saved. SETTINGS + TRACK opens Pad Setup: press DATA, then turn to choose Silent or Stock; BACK exits. Pad mode resets to Silent after reboot. CPU/CUT diagnostics included. Main and 909 unchanged.</span><span data-l="fr">TRACK + MACHINES + SWEEP/CONTOUR : le filtre Control All agit aussi sur les sample locks Wizard des pistes modifiees. Samples et slices conserves ; aucun filtre supplementaire. Overrides live non sauvegardes. SETTINGS + TRACK ouvre Pad Setup : presser DATA puis tourner pour Silent ou Stock ; BACK ferme. Retour Silent apres redemarrage. Diagnostic CPU/CUT inclus. Principal et909 inchanges.</span></p>'
 html=html.replace('<main class="wrap fl">','<main class="wrap fl">'+notice);files['index.html']=html.encode()
 files['midi-machine-release.js']=('window.MC_RELEASES='+json.dumps([dict(version='Wizard-control-test.1',date='2026-10-18',changes=[dict(en='Test Control All filter across Wizard sample locks and SETTINGS + TRACK Pad Setup (Silent/Stock). Live session settings, diagnostics retained; hardware verification pending.',fr='Test filtre Control All sur sample locks Wizard et Pad Setup SETTINGS + TRACK (Silent/Stock). Reglages live, diagnostic conserve ; verification materielle attendue.')])])+';\n').encode()
 files['BUILD.json']=(json.dumps(dict(stamp=STAMP,base='2026-10-18-macro-fine-main-196',scope='test-only',diagnostics=True,hardware_verified=False,sample_lock_filter=True,pad_selection_menu=True,settings_persistent=False),indent=2)+'\n').encode()
 out=ROOT/'docs/flasher-wizard-control-test';out.mkdir(exist_ok=True)
 for name,raw in files.items():
  istext=pathlib.Path(name).suffix in ('.js','.html','.css','.json','.md','.txt')
  if istext:raw=raw.replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n'
  if a.check:assert ((out/name).read_bytes().replace(b'\r\n',b'\n') if istext else (out/name).read_bytes())==raw,name
  else:(out/name).write_bytes(raw)
 print('PASS test Wizard Control All et menu pads genere, diagnostic inclus ; principal/909 inchanges')
if __name__=='__main__':main()
