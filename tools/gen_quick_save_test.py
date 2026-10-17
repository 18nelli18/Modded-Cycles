"""Note113 : restaurer FUNC+SETTINGS maintenu, sans remplacer la sauvegarde stock."""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-17-quick-save-test-1'
JS='''// Note113 : laisser le natif traiter le long FUNC+SETTINGS sans accord de mod utilise.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCQuickSave,n=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 window.MCQuickSaveReady=window.MCAudioLoadReady.then(()=>{const previous=window.MCMainClearResolve;
 window.MCMainClearResolve=input=>previous(input).map(t=>{if(t.id!=='sample-wizard')return t;const result=JSON.parse(JSON.stringify(t)),p=result.append.parts.find(p=>p.hex&&n(p.dest)<=d.at&&d.at+d.size<=n(p.dest)+p.hex.length/2);if(!p)throw Error('Quick save: modifier body missing');const i=2*(d.at-n(p.dest));if(p.hex.slice(i,i+2*d.size)!==d.old)throw Error('Quick save: modifier body guard');p.hex=p.hex.slice(0,i)+d.hex+p.hex.slice(i+2*d.size);delete result.append.compressed_hex;a.REF_MODS[result.id]={w:hash(b.writesBytes(result)),p:hash(b.buildPayload(result.append,null,null))};result.status='experimental';result.hardwareTestedByOwner=false;return result;});});
})();
'''
def generate():
 w=json.loads((ROOT/'firmware/wizard-catalogue.json').read_text())['variants']['0']['wizard'];sy={k:int(v,16) for k,v in w['symbols'].items()};at=sy['kh_mod'];size=sy['kh_preset']-at;assert sy['mod_used']==sy['set_held']+4
 cross=next(c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'as'))
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'mod.o'),str(ROOT/'tools/machines/quick_save/mod.s')],check=True)
  (p/'mod.ld').write_text(f"SET_HELD = {sy['set_held']:#x}; KH_EAT = {sy['kh_eat']:#x}; SECTIONS {{ .text {at:#x} : {{ *(.text) }} }}")
  subprocess.run([cross+'ld','-T',str(p/'mod.ld'),'-o',str(p/'mod.elf'),str(p/'mod.o')],check=True);subprocess.run([cross+'objcopy','-O','binary',str(p/'mod.elf'),str(p/'mod.bin')],check=True);code=(p/'mod.bin').read_bytes()
 assert len(code)==size==50
 raw=bytes.fromhex(w['append']['parts'][0]['hex']);off=at-int(w['append']['dest'],16)
 return dict(at=at,size=size,old=raw[off:off+size].hex(),hex=code.hex(),symbols={k:sy[k] for k in ('kh_mod','kh_eat','key_hook','set_held','mod_used')})
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();data=generate();target=ROOT/'docs/flasher-quick-save-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(tmp.name) if tmp else target;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher-audio-load-test').iterdir():
  if f.is_file():shutil.copyfile(f,out/f.name)
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s);intro='<p><strong data-l="en">Stock quick-save gesture test:</strong><strong data-l="fr">Test raccourci sauvegarde stock :</strong> <span data-l="en">Hold FUNCTION + SETTINGS from the normal pattern screen, just like stock, to use its permanent-save path. Other SETTINGS chords remain protected. Uses the original save handling; verify the save survives a reboot. Test diagnostics retained. Main already has the confirmed filter repair without diagnostics.</span><span data-l="fr">Maintenir FUNCTION + SETTINGS depuis l ecran pattern normal, comme en version stock, pour sa sauvegarde permanente. Les autres accords SETTINGS restent proteges. Traitement sauvegarde original ; verifier apres redemarrage. Diagnostics conserves en test. Principal deja corrige sans diagnostics.</span></p>'
 s=re.sub(r'(<main class="wrap fl">)<p>.*?</p>',lambda m:m.group(1)+intro,s,count=1,flags=re.S).replace('broader audio load test','stock quick-save test').replace('</body>',f'<script src="quick-save-data.js?v={STAMP}"></script><script src="quick-save.js?v={STAMP}"></script></body>');(out/'index.html').write_text(s,encoding='utf-8');(out/'quick-save.js').write_text(JS,encoding='utf-8');(out/'quick-save-data.js').write_text('window.MCQuickSave='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8')
 release=[dict(version='Quick-save-test.1',date='2026-10-17',changes=[dict(en='Restore the stock FUNCTION + SETTINGS hold path; other used SETTINGS chords remain consumed. Original save handler retained. Hardware verification pending.',fr='Restaure FUNCTION + SETTINGS maintenu vers le traitement sauvegarde stock ; autres accords SETTINGS consommes conserves. Verification materielle attendue.')])];(out/'diagnostic-release.js').write_text('window.MC_RELEASES='+json.dumps(release,ensure_ascii=False)+';\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 build=ROOT/'build/quicksave';build.mkdir(exist_ok=True);(build/'data.json').write_text(json.dumps(data),encoding='utf-8');print('PASS test quick save :50 octets en place, sauvegarde native conservee, diagnostics seulement en test')
if __name__=='__main__':main()
