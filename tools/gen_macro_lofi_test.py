"""Note119 : port test du geste MACRO lo-fi de 18nelli18, sans changer le principal."""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
from gen_seq_gen import symbols
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-17-macro-lofi-test-1'
UPSTREAM='d89267a'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();cross=next(c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'gcc'))
 with tempfile.TemporaryDirectory() as temp:
  d=pathlib.Path(temp);subprocess.run([cross+'gcc','-mcpu=54418','-c',str(ROOT/'tools/machines/macro/lofi_test.s'),'-o',str(d/'x.o')],check=True);(d/'x.ld').write_text('SECTIONS { .text 0 : { *(.text*) } }');subprocess.run([cross+'ld','--emit-relocs','-T',str(d/'x.ld'),'-o',str(d/'x.elf'),str(d/'x.o')],check=True);subprocess.run([cross+'objcopy','-O','binary',str(d/'x.elf'),str(d/'x.bin')],check=True);sy=symbols(cross,d/'x.elf');raw=(d/'x.bin').read_bytes();rel=subprocess.check_output([cross+'readelf','-rW',str(d/'x.elf')],text=True);offsets=[int(m.group(1),16) for m in re.finditer(r'^([0-9a-f]+)\s+\S+\s+R_68K_32\b',rel,re.M)];assert all(int.from_bytes(raw[i:i+4],'big')<len(raw) for i in offsets);data=dict(hex=raw.hex(),symbols=sy,reloc=offsets,upstream=UPSTREAM)
 target=ROOT/'docs/flasher-macro-lofi-test';temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else target;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher-machine-combinations-test').iterdir():
  if f.is_file():shutil.copyfile(f,out/f.name)
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s);s=s.replace('Modded Cycles — machine combinations test','Modded Cycles — MACRO lo-fi test')
 intro='<p><strong data-l="en">MACRO lo-fi control test.</strong><strong data-l="fr">Test controle lo-fi MACRO.</strong> <span data-l="en">18nelli18’s fix: hold FUNC and turn PITCH on MACRO. Left reduces sample rate (46K–4K), right reduces bit depth (12B–2B); centre is OFF. The setting appears in the value popup. Includes machine-combinations test 3 fixes and optional CPU/CUT diagnostics. Main unchanged.</span><span data-l="fr">Correction de 18nelli18 : maintenir FUNC et tourner PITCH sur MACRO. A gauche frequence reduite (46K–4K), a droite profondeur reduite (12B–2B) ; centre OFF. Valeur affichee dans la fenetre. Corrections du test3 des combinaisons et diagnostics CPU/CUT facultatifs conserves. Principal inchange.</span></p>'
 s=re.sub(r'(<main class="wrap fl">)<p>.*?</p>',lambda m:m.group(1)+intro,s,count=1,flags=re.S);s=s.replace('</body>',f'<script src="macro-lofi-data.js?v={STAMP}"></script><script src="macro-lofi.js?v={STAMP}"></script></body>');(out/'index.html').write_text(s,encoding='utf-8');(out/'macro-lofi-data.js').write_text('window.MCMacroLofi='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8');shutil.copyfile(ROOT/'tools/web/macro-lofi.js',out/'macro-lofi.js')
 (out/'test-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='MACRO-lofi-test.1',date='2026-10-17',changes=[dict(en='Ports 18nelli18’s FUNC + PITCH MACRO rate/bit reduction control and value popup. Test only; optional diagnostics retained; main unchanged.',fr='Integre le controle MACRO de 18nelli18 : FUNC + PITCH pour frequence/bits et valeur affichee. Test seulement ; diagnostics facultatifs conserves ; principal inchange.')])])+';\n',encoding='utf-8')
 (out/'TEST-NOTES.md').write_text('MACRO lo-fi test only. Hold FUNC and turn PITCH: centre OFF, left 46K..4K, right 12B..2B. Port of 18nelli18 commits cd905ac and 62fb099 (MIT). Existing machine-combinations test 3 fixes and optional CPU/CUT diagnostics retained. Main 1.85 unchanged. Hardware confirmation pending.\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,scope='test-only',upstream=UPSTREAM,source='cd905ac + 62fb099',audio_unchanged=True,main_unchanged=True),indent=2)+'\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 print('PASS MACRO lo-fi test generator',len(raw),'bytes')
if __name__=='__main__':main()
