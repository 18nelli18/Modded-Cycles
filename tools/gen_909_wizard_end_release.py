"""Publier le correctif End909 confirme sur machine, sans diagnostic (note128)."""
import argparse,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='c9bebcc1b899037967d241e66566bf894468d48a'
STAMP='2026-10-18-909-wizard-end-main'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'docs/flasher-supermodel-909'
 def original(name):return subprocess.check_output(['git','show',BASE+':docs/flasher-supermodel-909/'+name],cwd=ROOT).decode('utf-8')
 source=(ROOT/'tools/web/model909/wizard-end.js').read_text(encoding='utf-8')
 source=source.replace(',window.MCBeatDiagnosticReady','')
 source='\n'.join(line for line in source.splitlines() if "const el=document.getElementById('feat-audio-load-diagnostic')" not in line)+'\n'
 data=(ROOT/'docs/flasher-909-wizard-end-test/909-wizard-end-data.js').read_text(encoding='utf-8').replace('"diagnostics":true','"diagnostics":false')
 files={'909-wizard-end.js':source,'909-wizard-end-data.js':data}
 text=original('index.html');text=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,text);text=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",text)
 files['index.html']=text.replace('</body>',f'<script src="909-wizard-end-data.js?v={STAMP}"></script><script src="909-wizard-end.js?v={STAMP}"></script></body>')
 meta=json.loads(original('BUILD.json'));meta.update(sample_end_range_fixed=True,sample_end_validation='Hardware confirmed by AveyCole 2026-10-18',diagnostics=False);files['BUILD.json']=json.dumps(meta,indent=2)+'\n'
 releases=json.loads(original('909-release.js').split('=',1)[1].strip().rstrip(';'))
 releases.insert(0,dict(version='909.8',date='2026-10-18',changes=[dict(en='Sample Wizard Sample End now covers its full range, including Slice editing. Hardware confirmed by AveyCole. The 909 RC Type control retains its two positions. No diagnostics.',fr='Sample End de Sample Wizard couvre sa plage complete, edition Slice comprise. Confirme sur machine par AveyCole. RC Type909 conserve ses deux positions. Aucun diagnostic.')]))
 files['909-release.js']='window.MC_RELEASES='+json.dumps(releases,ensure_ascii=False)+';\n'
 for name,text in files.items():
  if a.check:assert (out/name).read_text(encoding='utf-8')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 print('PASS publication909 End : correctif confirme, aucun diagnostic')
if __name__=='__main__':main()
