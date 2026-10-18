"""Note120 : promotion approuvee des LEDs/longueurs B sans diagnostic."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 s=(ROOT/'tools/web/midi-page-leds.js').read_text(encoding='utf-8').replace('Promise.all([window.MCMacroLofiReady,window.MCBeatDiagnosticReady])','Promise.resolve(window.MCMacroLofiReady)').replace("id:'midi-page-leds-test'","id:'midi-page-leds'").replace("status:'experimental'","status:'tested'")
 for name,text in {'midi-page-leds.js':s,'midi-page-leds-data.js':(ROOT/'docs/flasher-midi-page-leds-test/midi-page-leds-data.js').read_text(encoding='utf-8')}.items():
  target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8').replace('\r\n','\n')==text,name
  else:target.write_text(text,encoding='utf-8')
 print('PASS approved MIDI pages release, diagnostic dependency excluded')
if __name__=='__main__':main()
