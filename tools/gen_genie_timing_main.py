"""Note 103 : promotion du timing confirme par AveyCole, firmware identique."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 text=(ROOT/'tools/machines/seq_gen/timing.js').read_text(encoding='utf-8')
 text=text.replace('Sequence Genie — timing test','Sequence Genie').replace('Sequence Genie — test timing','Sequence Genie')
 text=text.replace('Experimental restoration; hardware verification pending.','Hardware tested by AveyCole on 16 October 2026.')
 text=text.replace('Restauration experimentale ; verification materielle attendue.','Teste sur machine par AveyCole le 16/10/2026.')
 text=text.replace("feature.status='experimental';delete feature.hardwareTestedByOwner;","feature.status='tested';feature.hardwareTestedByOwner=true;")
 text=text.replace("bank.status='experimental';bank.hardwareTestedByOwner=false;","bank.status='tested';bank.hardwareTestedByOwner=true;")
 for name,value in {'genie-timing.js':text,'genie-timing-data.js':(ROOT/'build/genie-timing-data.js').read_text()}.items():
  target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8')==value,target
  else:target.write_text(value,encoding='utf-8')
 print('PASS promotion timing : seuls textes et statuts changes')
if __name__=='__main__':main()
