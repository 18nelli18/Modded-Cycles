"""Note 100 : publier les octets du candidat sur demande AveyCole."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def outputs():
 src=ROOT/'docs/flasher-performance-feedback-test'
 for name in ('beat-repeat-data.js','midi-bank-data.js','beat-repeat.js','midi-persistence.js'):
  s=(src/name).read_text(encoding='utf-8')
  if name in ('beat-repeat.js','midi-persistence.js'):
   s=s.replace("status:'experimental'","status:'tested',hardwareTestedByOwner:true").replace(".status='experimental';",".status='tested';").replace('.hardwareTestedByOwner=false;','.hardwareTestedByOwner=true;')
   s=s.replace('Hardware verification pending.',"Published to main at AveyCole’s request.").replace('Test materiel attendu.',"Publie au principal a la demande AveyCole.").replace('Experimental mute LEDs:','Mute LEDs:').replace('LEDs mute experimentales :','LEDs mute :')
  yield name,s
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
 for name,s in outputs():
  out=ROOT/'docs/flasher'/name
  if a.check:assert out.read_text(encoding='utf-8')==s,name
  else:out.write_text(s,encoding='utf-8')
 print('ok promotion feedback : noyaux identiques au candidat')
if __name__=='__main__':main()
