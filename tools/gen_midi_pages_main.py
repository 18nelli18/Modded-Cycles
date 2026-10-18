"""Note120 : promotion approuvee des LEDs/longueurs B sans diagnostic."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 # Sources approuvees figees : les essais suivants ne doivent pas modifier le principal.
 for name in ('midi-page-leds.js','midi-page-leds-data.js'):
  text=(ROOT/'tools/web'/name.replace('midi-page-leds','midi-pages-approved')).read_text(encoding='utf-8')
  target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8').replace('\r\n','\n')==text,name
  else:target.write_text(text,encoding='utf-8')
 print('PASS approved MIDI pages release, diagnostic dependency excluded')
if __name__=='__main__':main()
