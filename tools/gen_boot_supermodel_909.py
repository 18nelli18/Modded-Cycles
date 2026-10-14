#!/usr/bin/env python3
"""Variante séparée de l’animation SUPERMODEL, signature A.V. et 909 EDITION."""
import argparse,json,pathlib
import gen_boot_supermodel as G
from test_sdvintage import main_os_from_syx

def generate(stock):
 old=G.EDITION
 try:
  G.EDITION='909 EDITION';t=G.generate(stock)
 finally:G.EDITION=old
 t.update(id='supermodel-909-startup',name='SUPERMODEL by A.V. — 909 EDITION',conflicts=['boot-anim','supermodel-startup'],status='experimental')
 t['description']=['Animation SUPERMODEL, signature by A.V. et troisième ligne 909 EDITION. Même durée que le démarrage stock.']
 return t
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cycles',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();t=generate(main_os_from_syx(a.cycles));s=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==s
 else:out.write_text(s)
 print('Animation 909',len(bytes.fromhex(t['writes'][0]['new'])))
