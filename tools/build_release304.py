"""Reversionner les quatre candidats UI374 confirmes, sans modifier leur DSP."""
from pathlib import Path
import concurrent.futures,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent/'release304'
def build(pair):
 scope,edition=pair
 variant='main' if scope=='main' and edition=='full' else 'main-lite' if scope=='main' else 'optional-all' if edition=='full' else 'optional-lite'
 source=(ROOT.parent/'wizard-pan-block376/exact-center/main/full') if scope=='main' and edition=='full' else (ROOT.parent/'wizard-pan375/fixed/optional-all/full') if scope=='optional' and edition=='full' else ROOT.parent/'baseline-ui374/final-v5'/variant/edition
 cold=(ROOT.parent/'wizard-pan-block376/exact-center/cold/main') if scope=='main' and edition=='full' else (ROOT.parent/'wizard-pan375/cold/fixed-optional') if scope=='optional' and edition=='full' else ROOT.parent/'baseline-ui374/cold-v5'/variant/edition
 out=WORK/'final'/scope/edition;out.mkdir(parents=True,exist_ok=True)
 cmd=[sys.executable,str(ROOT/'tools/rebuild300_pack.py'),'--reference',str(source),'--capture',str(cold),'--cycles','H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx','--output',str(out),'--release','3.04',*(['--wizard-pan371'] if scope=='optional' and edition=='full' else []),'--compression-candidates','64','--compression-history','--compression-window','16777216','--compression-min-match','3']
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);(out/'build.log').write_text(p.stdout+p.stderr);assert p.returncode==0,(pair,p.stdout,p.stderr)
 subprocess.run([sys.executable,str(ROOT/'tools/emu/capture_rebuild300_boot.py'),'--build',str(out),'--output',str(WORK/'cold'/scope/edition)],cwd=ROOT,check=True)
 print('PASS release3.04 build/cold',scope,edition,flush=True)
if __name__=='__main__':
 os.environ['PYTHONDONTWRITEBYTECODE']='1'
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(build,[('main','full'),('main','lite'),('optional','full'),('optional','lite')]))
