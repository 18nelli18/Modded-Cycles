"""Recette3.06 : FX master sans ligne Mod, INV et Swap corrige sur quatre editions.

Les references et captures3.05 restent privees ; utiliser Python3.12+,
Unicorn et la toolchain ColdFire comme pour build_release305.py.
"""
from pathlib import Path
import argparse,os,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,default=ROOT.parent/'release306-no-telephone/final')
    p.add_argument('--capture',type=Path,default=ROOT.parent/'release306-no-telephone/cold')
    p.add_argument('--cycles',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT.parent/'release306')
    a=p.parse_args();os.environ['PYTHONDONTWRITEBYTECODE']='1'
    for scope in ('main','optional'):
        for edition in ('full','lite'):
            folder=a.output/'final'/scope/edition;cold=a.output/'cold'/scope/edition
            subprocess.run([sys.executable,str(ROOT/'tools/rebuild300_pack.py'),
                '--reference',str(a.reference/scope/edition),'--capture',str(a.capture/scope/edition),
                '--cycles',str(a.cycles),'--output',str(folder),'--release','3.06',
                '--wizard-pan371',
                '--compression-candidates','64','--compression-history','--compression-window','16777216',
                '--compression-min-match','3'],cwd=ROOT,check=True)
            subprocess.run([sys.executable,str(ROOT/'tools/emu/capture_rebuild300_boot.py'),
                '--build',str(folder),'--output',str(cold)],cwd=ROOT,check=True)
            for script,extra in [('test_gov_policy372.py',[]),
                ('test_wizard_func385.py',['--output',str(a.output/'proof'/scope/edition/'live.json')]),
                ('test_fx_mst_save379.py',['--output',str(a.output/'proof'/scope/edition/'fx.json')]),
                ('test_track_swap_ui377.py',['--output',str(a.output/'proof'/scope/edition/'swap.json')])]:
                subprocess.run([sys.executable,str(ROOT/'tools/emu'/script),'--build',str(folder),
                    '--capture',str(cold),*extra],cwd=ROOT,check=True)

if __name__=='__main__':main()
