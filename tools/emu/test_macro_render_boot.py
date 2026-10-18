"""Note124 : vrai boot navigateur ; seule la boucle162octets change en RAM."""
import argparse,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
ROOT=HERE.parent.parent
def main():
 p=argparse.ArgumentParser();p.add_argument('--prefix',required=True);a=p.parse_args();d=json.loads((ROOT/'build/macro-optimization/macro-halfband-data.js').read_text().split('=',1)[1].strip().rstrip(';'));old=bytes.fromhex(d['old']);new=bytes.fromhex(d['hex'])
 _,before,_=boot_case(a.prefix+'-before');_,after,_=boot_case(a.prefix+'-after');assert len(before)==len(after);hits=0
 for (x,raw),(y,changed) in zip(before,after):
  assert x==y and len(raw)==len(changed);hits+=changed.count(new);assert raw==changed.replace(new,old),(hex(x),'autres octets runtime modifies')
 assert hits==1;print('PASS vrai bootstrap, taille/adresses runtime identiques, seul noyau MACRO162octets change:',a.prefix)
if __name__=='__main__':main()
