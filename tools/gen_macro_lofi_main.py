"""Note119 : promotion du port MACRO approuve, sans dependance diagnostic."""
import argparse,pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 s=(ROOT/'tools/web/macro-lofi.js').read_text(encoding='utf-8').replace('Port test de 18nelli18','Port confirme de 18nelli18').replace('Promise.all([window.MCPerformanceReleaseReady,window.MCBeatDiagnosticReady])','Promise.resolve(window.MCPerformanceReleaseReady)').replace("id:'macro-lofi-test'","id:'macro-lofi'").replace("status:'experimental'","status:'tested'").replace('MACRO — lo-fi gesture test','MACRO').replace('MACRO — test geste lo-fi','MACRO').replace(' Test only.','').replace(' Test seulement.','')
 for name,text in {'macro-lofi.js':s,'macro-lofi-data.js':(ROOT/'docs/flasher-macro-lofi-test/macro-lofi-data.js').read_text(encoding='utf-8')}.items():
  target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8').replace('\r\n','\n')==text,name
  else:target.write_text(text,encoding='utf-8')
 print('PASS approved MACRO release adapter, no diagnostic dependency')
if __name__=='__main__':main()
