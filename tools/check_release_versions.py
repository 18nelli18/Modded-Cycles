"""Refuser une livraison dont le titre et le flasheur divergent, ou sans nouvelle version."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mtlib import aplib,container
from mtlib.syx import unwrap
def version(v):return tuple(map(int,v.split('.')))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',default='origin/main');p.add_argument('--git',default='git');a=p.parse_args()
 for scope,key in [('flasher','editions'),('flasher-optional','base_editions')]:
  relative='docs/'+scope+'/BUILD.json';m=json.loads((ROOT/relative).read_text())
  old=json.loads(subprocess.check_output([a.git,'show',a.base+':'+relative],cwd=ROOT,text=True))
  changed=any(m[key][e]['syxSha256']!=old[key][e]['syxSha256'] for e in ('full','lite'))
  if changed:assert version(m['release'])>version(old['release']),'Nouvelle image sans nouvelle version: '+scope
  for edition,entry in m[key].items():
   assert entry['release']==m['release']==entry['startup_title']['version']
   raw=(ROOT/'docs/flasher'/entry['file']).read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest()
   assert sha(raw)==entry['syxSha256']
   pkg=container.parse(unwrap(raw)[0]);s=next(s for s in pkg['sections'] if s['id']==3);image=aplib.depack(pkg['blob'][s['off']:s['off']+s['size']])[0]
   title=entry['startup_title'];off=title['code']-0x40000400
   assert sha(image[off:off+title['code_bytes']])==title['sha256'],'Titre compile different: '+scope+' '+edition
   print('PASS',scope,edition,'flasher/title',m['release'],'image et code du titre verifies',flush=True)
if __name__=='__main__':main()
