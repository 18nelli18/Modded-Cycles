#!/usr/bin/env python3
"""Exécute boot, entrée Banque, clavier et scheduler pour les 32 backends."""
import argparse,json,pathlib,subprocess,sys

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--matrix',required=True);p.add_argument('--build-module',required=True);p.add_argument('--logs',required=True);a=p.parse_args();root=pathlib.Path(a.matrix);logs=pathlib.Path(a.logs);logs.mkdir(parents=True,exist_ok=True)
 for row in json.loads((root/'matrix.json').read_text()):
  key=row['key'];args=[sys.executable,'tools/emu/test_midi_independent_candidate.py','--cycles',a.cycles,'--candidate',str(root/(key+'.json')),'--build-module',a.build_module]
  with (logs/(key+'.log')).open('w') as f:result=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
  if result.returncode:print((logs/(key+'.log')).read_text());raise SystemExit(result.returncode)
  if row['chord']:
   with (logs/(key+'-chord.log')).open('w') as f:result=subprocess.run([sys.executable,'tools/emu/test_midi_optional_chord.py','--cycles',a.cycles,'--candidate',str(root/(key+'.json'))],stdout=f,stderr=subprocess.STDOUT)
   if result.returncode:print((logs/(key+'-chord.log')).read_text());raise SystemExit(result.returncode)
  print('PASS',key,'boot/clavier/scheduler'+('/Chord' if row['chord'] else ''),flush=True)
if __name__=='__main__':main()
