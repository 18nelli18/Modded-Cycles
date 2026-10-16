"""Note 102 : candidat filtre seul ; principal et ChpHzrd inchanges."""
import argparse,json,pathlib,re,shutil,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-16-filter-precision-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 expected=ROOT/'docs/flasher-filter-precision-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(tmp.name) if tmp else expected;out.mkdir(exist_ok=True)
 for src in (ROOT/'docs/flasher').iterdir():
  if src.is_file() and src.suffix!='.wav':shutil.copyfile(src,out/src.name)
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en"><strong>Experimental filter precision repair.</strong> Compare the same sound on tracks 5 and 6 while lowering cutoff. Check quiet notes and tails, resonance, and neutral bypass. Main is unchanged.</span><span data-l="fr"><strong>Correction experimentale de precision du filtre.</strong> Comparer le meme son sur pistes 5 et 6 en baissant la coupure. Verifier notes faibles, queues, resonance et bypass neutre. Principal inchange.</span></p>')
 s=s.replace('href="convert.html"','href="../flasher/convert.html"').replace('../assets/release.js?','precision-release.js?').replace('</body>',f'<script src="filter-precision-data.js?v={STAMP}"></script><script src="filter-precision.js?v={STAMP}"></script></body>')
 (out/'index.html').write_text(s,encoding='utf-8');shutil.copyfile(a.data,out/'filter-precision-data.js');shutil.copyfile(ROOT/'tools/machines/track_filter/precision.js',out/'filter-precision.js')
 (out/'precision-release.js').write_text('window.MC_RELEASES='+json.dumps([{'version':'1.75-filter-preview.1','date':'2026-10-16','changes':[{'en':'Test repair: higher-precision per-track ladder addresses coarse quantization when cutoff is lowered. Compare tracks 5 and 6, quiet signals, resonance and full-open bypass. Main unchanged; hardware verification pending.','fr':'Test : ladder par piste haute precision contre la quantification quand la coupure baisse. Comparer pistes 5/6, niveaux faibles, resonance et bypass ouvert. Principal inchange ; test materiel attendu.'}]}],ensure_ascii=False)+';\n',encoding='utf-8')
 for name in ('ABOUT.md','TEST-NOTES.md'):(out/name).write_text('Experimental filter precision repair. Select Per-track filter, compare the same sound on tracks 5 and 6, and lower cutoff. Try quiet/loud sounds, resonance, tails and exact full-open/zero-resonance bypass. Wizard sample filter remains separate. Main unchanged; hardware verification pending.\n\nCorrection experimentale de precision du filtre. Activer Filtre par piste, comparer le meme son sur pistes 5 et 6 en baissant la coupure. Tester niveaux faibles/forts, resonance, queues et bypass ouvert/resonance nulle. Filtre propre Wizard separe. Principal inchange ; test materiel attendu.\n',encoding='utf-8')
 for src in out.iterdir():
  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')
 if a.check:
  for src in out.iterdir():assert (expected/src.name).read_bytes()==src.read_bytes(),src.name
 print('ok page filtre test seule ; principal inchange')
if __name__=='__main__':main()
