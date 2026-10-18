"""909 : preecoute exacte du principal, accroches conservees apres vrai boot.

La preecoute du navigateur/chargement sur appareil reste a verifier ; ceci
prouve la composition, les accroches et leur survie au bootstrap/cache.
"""
import argparse,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
import build
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',default='build/909-preview/all');a=p.parse_args()
 img,memories,recipes=boot_case(a.case)
 preview=next(t for t in recipes if t['id']=='wizard-sample-preview')
 root=HERE.parent.parent
 source=json.loads((root/'firmware/wizard-catalogue.json').read_text(encoding='utf-8'))['preview']
 assert preview['writes']==source['writes']
 for w in preview['writes']:
  raw=bytes.fromhex(w['new']);assert img[w['off']:w['off']+len(raw)]==raw,hex(build.BASE+w['off'])
 assert not any(t['id'].startswith('model-tg') for t in recipes)
 assert not any('br_load_address' in t.get('symbols',{}) for t in recipes)
 print('PASS preecoute identique au principal, toutes les accroches et routines preservees apres boot909, aucun Model-TG ou diagnostic')
 print('LIMITES : navigateur, fichiers samples et ecoute physique a confirmer sur appareil')
if __name__=='__main__':main()
