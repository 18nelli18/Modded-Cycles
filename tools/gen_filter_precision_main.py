"""Note 102 : promotion du candidat confirme par AveyCole, DSP identique au test."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 source=(ROOT/'tools/machines/track_filter/precision.js').read_text(encoding='utf-8')
 source=source.replace("f.status='experimental';delete f.hardwareTestedByOwner;","f.status='tested';f.hardwareTestedByOwner=true;")
 source=source.replace("status:'experimental',hardwareTestedByOwner:false","status:'tested',hardwareTestedByOwner:true")
 source=source.replace('Per-track filter — precision test','Per-track filter').replace('Filtre par piste — test precision','Filtre par piste')
 source=source.replace('Higher-precision ladder; checks bit-crushing reported on track 6.','Hardware tested repair for bit-crushed filtering on track 6.')
 source=source.replace('Ladder haute precision ; verifier le son ecrase sur la piste 6.','Correction testee sur machine du filtre quantifie sur piste 6.')
 source=source.replace('Experimental repair for coarse, bit-crushed audio','Hardware tested repair for coarse, bit-crushed audio')
 source=source.replace('Correction experimentale du son quantifie','Correction testee sur machine du son quantifie')
 source=source.replace('Test the same sound on tracks 5 and 6. Hardware verification pending.','Track 6 fix confirmed on hardware by AveyCole on 16 October 2026.')
 source=source.replace('Comparer le meme son sur pistes 5 et 6. Verification materielle attendue.','Correction piste 6 confirmee sur machine par AveyCole le 16/10/2026.')
 files={'filter-precision.js':source,'filter-precision-data.js':(ROOT/'build/filter-precision-data.js').read_text()}
 for name,text in files.items():
  path=ROOT/'docs/flasher'/name
  if a.check:assert path.read_text(encoding='utf-8')==text,path
  else:path.write_text(text,encoding='utf-8')
 print('PASS filtre principal : meme DSP que le candidat confirme')
if __name__=='__main__':main()
