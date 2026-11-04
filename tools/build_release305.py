"""Quatre editions3.05 : Track Swap sur le DSP approuve3.04, boot froid obligatoire."""
from pathlib import Path
import os,subprocess,sys,concurrent.futures
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'release305'
def build(pair):
 scope,edition=pair;out=WORK/'final'/scope/edition;out.mkdir(parents=True,exist_ok=True)
 cmd=[sys.executable,str(ROOT/'tools/rebuild300_pack.py'),'--reference',str(ROOT.parent/'release304/final'/scope/edition),'--capture',str(ROOT.parent/'release304/cold'/scope/edition),'--cycles','H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx','--output',str(out),'--release','3.05','--track-swap377','--compression-candidates','64','--compression-history','--compression-window','16777216','--compression-min-match','3']
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);(out/'build.log').write_text(p.stdout+p.stderr,encoding='utf-8');assert p.returncode==0,(pair,p.stdout,p.stderr)
 subprocess.run([sys.executable,str(ROOT/'tools/emu/capture_rebuild300_boot.py'),'--build',str(out),'--output',str(WORK/'cold'/scope/edition)],cwd=ROOT,check=True)
 print('PASS build/cold3.05',scope,edition,flush=True)
if __name__=='__main__':
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(build,[('main','full'),('main','lite'),('optional','full'),('optional','lite')]))
