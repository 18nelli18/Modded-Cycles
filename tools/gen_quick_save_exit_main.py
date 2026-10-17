"""Note116 : code save confirme ; placement exclusivement par le compositeur payload."""
import argparse,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 code=json.loads((ROOT/'docs/flasher-quick-save-test/quick-save-latch-data.js').read_text().split('=',1)[1].strip().rstrip(';'))['hex'];assert len(code)//2==92
 files={'docs/flasher/quick-save-exit-data.js':'window.MCQuickSaveExit='+json.dumps(dict(hex=code),separators=(',',':'))+';\n','docs/flasher/quick-save-exit.js':'// Note116 : aucun code dans un masque de donnees ; placement par performance-release.js.\nwindow.MCQuickSaveExitReady=Promise.resolve();\n'}
 for name,text in files.items():
  p=ROOT/name
  if a.check:assert p.read_text(encoding='utf-8')==text,name
  else:p.write_text(text,encoding='utf-8')
 print('PASS code save confirme92octets ; aucun masque partage')
if __name__=='__main__':main()
