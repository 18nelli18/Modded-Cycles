#!/usr/bin/env python3
"""Promouvoir le test ACID sur le retour matériel explicite d’AveyCole."""
import argparse,pathlib,shutil
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--test',required=True);p.add_argument('--output',required=True);a=p.parse_args();out=pathlib.Path(a.output);shutil.copytree(a.test,out,dirs_exist_ok=True)
 for f in out.iterdir():
  if f.is_file() and f.suffix in ['.js','.html','.md']:
   s=f.read_text().replace('2026-10-14-acid-fade-test','2026-10-14-main-acid-fade').replace('New fade-in awaits hardware testing.','Retrigger fade-in hardware tested.').replace('Nouveau fondu à vérifier sur matériel.','Fondu au retrig vérifié sur matériel.')
   if f.name=='bundle.js':s=s.replace("f.status='experimental';f.credit={kind:'by',who:'Kevin Shallvari","f.status='tested';f.credit={kind:'by',who:'Kevin Shallvari")
   f.write_text(s)
 print('ok : ACID hardware-tested sur main ; firmware identique au test')
if __name__=='__main__':main()
