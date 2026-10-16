"""Note 105 : promotion du test 4 confirme sur machine par AveyCole."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 s=(ROOT/'tools/machines/track_filter/load.js').read_text(encoding='utf-8')
 s=s.replace("f.status='experimental';f.hardwareTestedByOwner=false;","f.status='tested';f.hardwareTestedByOwner=true;").replace("status:'experimental',hardwareTestedByOwner:false","status:'tested',hardwareTestedByOwner:true")
 s=s.replace('Per-track filter — busy playback test','Per-track filter').replace('Filtre par piste — test lecture chargee','Filtre par piste')
 s=s.replace('Reduced processing work; same filter sound. Test busy patterns and ticks.','Reduced filter workload; hardware tested with optimized beat repeat.').replace('Calcul allege, meme son. Verifier patterns charges et ticks.','Charge filtre allegee ; teste sur machine avec beat repeat optimise.')
 s=s.replace('Experimental test for distortion and ticks','Hardware-tested repair for distortion and ticks').replace('Test experimental des distorsions et ticks','Correction testee sur machine des distorsions et ticks')
 s=s.replace('Hardware verification pending.','Confirmed on hardware by AveyCole on 16 October 2026.').replace('Verification materielle attendue.','Confirme sur machine par AveyCole le 16/10/2026.')
 files={'filter-load.js':s,'filter-load-data.js':(ROOT/'build/filter-load-data.js').read_text(encoding='utf-8'),'beat-repeat-data.js':(ROOT/'docs/flasher-filter-load-test/beat-repeat-data.js').read_text(encoding='utf-8')}
 for name,text in files.items():
  target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8')==text,name
  else:target.write_text(text,encoding='utf-8')
 print('PASS principal : filtre et repeat identiques au test 4 confirme')
if __name__=='__main__':main()
