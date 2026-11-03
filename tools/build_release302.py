"""Construit les quatre editions3.02 et capture leur vrai demarrage."""
from pathlib import Path
import concurrent.futures,json,subprocess,sys,os
R=Path(__file__).resolve().parents[1];W=R.parent/'release302'
def build(pair):
 scope,ed=pair;dest=W/'final'/scope/ed;dest.mkdir(parents=True,exist_ok=True)
 args=[sys.executable,str(R/'tools/rebuild300_pack.py'),'--reference',str(R.parent/'fx-unroll302'/scope/ed),'--capture',str(R.parent/'fx-unroll302/cold'/scope/ed),'--cycles','H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx','--output',str(dest),'--release','3.02','--release302-fixes','--compression-candidates','8','--compression-history']
 result=subprocess.run(args,cwd=R,capture_output=True,text=True);(dest/'build.log').write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError((pair,result.stdout,result.stderr))
 subprocess.run([sys.executable,str(R/'tools/emu/capture_rebuild300_boot.py'),'--build',str(dest),'--output',str(W/'cold'/scope/ed)],cwd=R,check=True)
 print('PASS BUILD/COLD',scope,ed,flush=True)
 return pair
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(build,[('main','full'),('main','lite'),('optional','full'),('optional','lite')]))
