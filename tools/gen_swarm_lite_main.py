"""Note 107 : promotion du Swarm trois oscillateurs choisi par AveyCole."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 for name,source in [('swarm-lite-data.js',ROOT/'build/swarm-lite/swarm-lite-data.js'),('swarm-lite.js',ROOT/'tools/machines/syntakt_load/main.js')]:
  text=source.read_text(encoding='utf-8');target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8')==text,name
  else:target.write_text(text,encoding='utf-8')
 print('PASS principal : Swarm LITE trois oscillateurs, sans changement filtre/repeat/regulateur')
if __name__=='__main__':main()
