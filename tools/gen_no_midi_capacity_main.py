"""Note 104 : promotion demandee, packing identique et statut MIDI experimental."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 files={'no-midi-capacity.js':ROOT/'tools/machines/beat_repeat/capacity.js','no-midi-capacity-data.js':ROOT/'build/no-midi-capacity-data.js','midi-experimental-status.js':ROOT/'tools/machines/midi_lanes/experimental_status.js'}
 for name,source in files.items():
  text=source.read_text(encoding='utf-8');target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8')==text,target
  else:target.write_text(text,encoding='utf-8')
 print('PASS principal : packing identique au test ; MIDI experimental')
if __name__=='__main__':main()
