#!/usr/bin/env python3
"""Effacement UI A complet : locks natifs et flags SCRAMBLE/slide (note76).

--cycles OS1.13 officiel --catalog sélection intégrale --output recette.json.
Le masque doit rester libre avec chaque recette du catalogue fourni.
"""
import argparse,json,pathlib,shutil,struct,subprocess,tempfile
import build,sprites
from chord_keys_pr87 import load_stock
MASK=0x40195a7c
HOOK=0x40022dd0
def generate(stock,catalog):
 cross=next((x for x in ('m68k-elf-','m68k-linux-gnu-') if shutil.which(x+'as')),None)
 if cross is None:raise RuntimeError('binutils ColdFire requis')
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'step.o'),str(pathlib.Path(__file__).parent/'machines/scramble/step_delete.s')],check=True)
  (p/'step.ld').write_text('SECTIONS { .text '+hex(MASK)+' : { *(.text*) } }')
  subprocess.run([cross+'ld','-T',str(p/'step.ld'),'-e','sc_step_delete','-o',str(p/'step.elf'),str(p/'step.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'step.elf'),str(p/'step.bin')],check=True)
  code=(p/'step.bin').read_bytes()
 assert len(code)<=sprites.MASKS[MASK][0],len(code)
 for t in catalog:
  for w in t['writes']:
   lo=build.BASE+w['off'];hi=lo+len(bytes.fromhex(w['new']))
   assert not(max(lo,MASK)<min(hi,MASK+len(code)) or max(lo,HOOK)<min(hi,HOOK+6)),(t['id'],hex(lo))
 assert stock[HOOK-build.BASE:HOOK-build.BASE+6]==bytes.fromhex('4eb940017c4e')
 size,ptr,_,shared=sprites.MASKS[MASK]
 assert stock[MASK-build.BASE:MASK-build.BASE+size]==stock[shared-build.BASE:shared-build.BASE+size]
 t=dict(id='step-delete-reset',order=99,name='Suppression complète des locks du pas A',device='Model:Cycles',os='1.13',section=3,status='experimental',requires=[],conflicts=[],symbols={'sc_step_delete':hex(MASK)},writes=[dict(off=HOOK-build.BASE,old=stock[HOOK-build.BASE:HOOK-build.BASE+6].hex(),new=(b'\x4e\xb9'+struct.pack('>I',MASK)).hex()),dict(off=MASK-build.BASE,old=stock[MASK-build.BASE:MASK-build.BASE+len(code)].hex(),new=code.hex()),sprites.redirect_write(MASK)],description=['Effacer un trig en mode grille réinitialise ses champs/locks et retire SCRAMBLE/slide.','Le clavier et les conversions note/trigless restent natifs.'])
 build.apply_writes(stock,catalog+[t]);return t
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 stock=load_stock(a.cycles);t=generate(stock,json.loads(pathlib.Path(a.catalog).read_text())['tweaks']);s=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==s
 else:out.write_text(s)
 print('ok : wrapper UI '+str(len(bytes.fromhex(t['writes'][1]['new'])))+' octets, natif vérifié et catalogue sans chevauchement')
if __name__=='__main__':main()
