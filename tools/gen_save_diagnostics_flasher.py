#!/usr/bin/env python3
"""Candidat isolé : diagnostic Save, mêmes sources que le pack MIDI autonome."""
import argparse,pathlib
import gen_performance_core_flasher as base
STAMP='2026-10-12-save-diagnostics'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--cycles',required=True);p.add_argument('--model-tg',required=True)
 p.add_argument('--output',default=str(base.ROOT/'docs/flasher-save-test'))
 a=p.parse_args();base.STAMP=STAMP
 base.BUNDLE_TEXT['en']['note']='Save diagnostics candidate: full-record read-back verification corrected. MIDI: INIT/OWNER/PATH/ROOT/DIR/SNAP/COMMIT/CREATE/DATA/OPEN/ALLOC/WRITE/FLUSH/CLOSE/DISK identifies a failing save stage. Persistence is not hardware confirmed. LFO2 quick assign is not included yet. Main and Test3 unchanged.'
 base.BUNDLE_TEXT['fr']['note']='Candidat diagnostic sauvegarde : comparaison intégrale corrigée, erreurs par étape. Persistance matérielle non confirmée. Quick assign LFO2 absent. Principal et Test3 inchangés.'
 files,_,count=base.generate(a.cycles,a.model_tg)
 out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
 for name,body in files.items():
  body=body.replace('Standalone Core Test','Save Diagnostics Test').replace('Essai noyau autonome','Diagnostic sauvegarde')
  (out/name).write_text(body.rstrip()+'\n')
 print('ok : candidat diagnostic isolé,',count,'références')
if __name__=='__main__':main()
