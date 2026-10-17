"""Note 107 : vrais boots/cache navigateur, noyaux propres copies exactement en SRAM."""
import pathlib,sys,json
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_current_audio import boot
import mcengine as E
ROOT=HERE.parents[1]
def main():
 d=json.loads((ROOT/'build/swarm-lite/swarm-lite-data.js').read_text().split('=',1)[1].strip().rstrip(';'))

 for name in ('all-midi','all-no-midi'):
  _,rt,ts,ram=boot('build/swarm-lite-main/'+name,with_sram=True)
  mapping=json.loads((ROOT/'build/swarm-lite-main'/name).with_suffix('.json').read_text())['swarmMap']
  assert len(mapping)==6
  for e in d['exact']+d['edits']:
   at=next(p['dest'] for p in mapping if p['source']==e['source']);off=at-0x46700000
   expected=bytes.fromhex(e['hex']);assert rt[off:off+len(expected)]==expected,(name,hex(e['source']),'payload')
   stage=off+0x43000000;run=next(run+stage-lo for lo,run,n in E.SRAM_BANKS if lo<=stage<lo+n)
   assert ram[run-0x80000000:run-0x80000000+len(expected)]==expected,(name,hex(run),'SRAM')
  print('PASS vrai boot/cache : six regions exactes payload et SRAM',name,flush=True)
if __name__=='__main__':main()
