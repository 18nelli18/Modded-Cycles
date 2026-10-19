"""Genere les recettes propres de la promotion MIDI/Chord, sans diagnostic.
Compiler gen_midi_safety.py, gen_midi_idle.py et gen_cut_endpoint.py avant ceci.
"""
import argparse,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 load=lambda path:json.loads((ROOT/path).read_text(encoding='utf8'))
 d=dict(entry=load('build/midi-safety/catalogue.json'),module={'chord':load('build/midi-safety/data.json')['chord']},idle=load('build/midi-idle/data.json'),fade=load('build/cut-endpoint/data.json'),fadeLoop={'old_loop':'71524c04080024c0988153836af2'})
 files={'midi-safety-data.js':'window.MCMidiSafetyData='+json.dumps(d,separators=(',',':'))+';\n','midi-safety-release.js':(ROOT/'tools/web/midi-safety-release.js').read_text(encoding='utf8')}
 for name,text in files.items():
  path=ROOT/'docs/flasher'/name
  if a.check:assert path.read_text(encoding='utf8')==text,name
  else:path.write_text(text,encoding='utf8')
 print('PASS recettes MIDI/Chord release, aucun diagnostic')
if __name__=='__main__':main()
