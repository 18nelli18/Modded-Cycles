"""Note117 : patches reels apres boot909, zones Wizard et payload save preserves."""
import argparse,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
ROOT=HERE.parents[1];BASE=0x40000400
def data(name):return json.loads((ROOT/'docs/flasher-supermodel-909'/name).read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--diagnostics',action='store_true');a=p.parse_args();img,memories,ts=boot_case(a.case)
 f=data('filter-transition-data.js');q=data('quick-save-data.js');code=data('quick-save-exit-data.js')['hex']
 for at,hexcode in [(f['filter']['at'],f['filter']['hex']),(f['inner_call']['at'],f['inner_call']['new']),(q['at'],q['hex'])]:
  raw=bytes.fromhex(hexcode);assert img[at-BASE:at-BASE+len(raw)]==raw,hex(at)
 save=next(t for t in ts if t['id']=='quick-save-exit');entry=int(save['symbols']['qs_exit'],16);assert int.from_bytes(img[0x40100c44-BASE:0x40100c48-BASE],'big')==entry
 assert entry>=0x43000000;assert any(at<=entry and raw[entry-at:entry-at+92].hex()==code for at,raw in memories)
 if not a.diagnostics:
  for t in ts:assert not any(key.startswith(('br_avg_','br_load_','br_filter_','br_cut_seen')) for key in t.get('symbols',{}))
 print('PASS boot909 : filtre rapide exact, second passage supprime, clavier save confirme et wrapper hors BSS'+(' ; diagnostic test autorise' if a.diagnostics else ', aucun diagnostic'))
if __name__=='__main__':main()
