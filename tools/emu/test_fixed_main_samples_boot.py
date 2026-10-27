"""Principal2.53 : vrai bootstrap Samples, HMAC et parite Python/JavaScript.

--cycles officiel.syx --samples officiel.syx --outputs repertoire du test JS.
Aucune ecriture sur le materiel ; fichiers firmware uniquement en entree.
"""
from pathlib import Path
import sys,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from mtlib import aplib,container
from mtlib.syx import unwrap
from test_crossflash_samples import boot,verify,VERIFY,find_verify
import crossflash as X
def read(p):
 raw=Path(p).read_bytes();c=container.parse(unwrap(raw)[0]);parts={s['id']:c['blob'][s['off']:s['off']+s['size']] for s in c['sections']};return raw,c,parts
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cycles',required=True);parser.add_argument('--samples',required=True);parser.add_argument('--outputs',required=True,type=Path);a=parser.parse_args()
 smp=X.load(a.samples,'samples');cyc=X.load(a.cycles,'cycles')
 _,c,parts=read(a.outputs/'main-253-for-samples-cycles.syx');main=aplib.depack(parts[3],bootstrap_gap=0x40200000-X.MAIN_BASE)[0]
 entry,ram,checks=boot(smp[3][2],c['blob'],main_size=len(main))
 assert entry==0x40000400 and ram==main and not checks
 print('PASS actual unmodified Samples bootstrap loads all',len(main),'MAIN bytes, including source/output overlap; exact RAM and native entry',flush=True)
 assert verify(main,*VERIFY['cycles'],c['blob'])==1
 assert verify(cyc[3][3],*VERIFY['cycles'],c['blob'])==4
 print('PASS native converted Cycles update verification accepts Samples signature; native original Cycles rejects it',flush=True)
 assert verify(smp[3][3],*find_verify(smp[3][3]),c['blob'])==1
 print('PASS native Samples OS verification accepts the same container for first installation',flush=True)
 _,base,source=read(ROOT/'docs/flasher/Supermodel_2.53_6a729fbf198b.syx')
 plain={k:aplib.depack(v)[0] if k in (2,3) else v for k,v in source.items()}
 python_raw,sha=X.cycles_for_samples((cyc[0],base,source,plain),smp)
 assert python_raw==(a.outputs/'main-253-for-samples-samples.syx').read_bytes() and sha==hashlib.sha256(main).hexdigest()
 print('PASS Python/JavaScript conversion byte-identical, including safe layout and complete SysEx/container/HMAC',flush=True)
 unsafe=(a.outputs/'unsafe-bootstrap.aplib').read_bytes();assert len(aplib.depack(unsafe)[0])==0x240000
 try:aplib.depack(unsafe,bootstrap_gap=0x40200000-X.MAIN_BASE)
 except ValueError as error:assert 'bootstrap' in str(error)
 else:raise AssertionError('unsafe bootstrap layout accepted')
 print('PASS Python also rejects real unread-source overlap',flush=True)
if __name__=='__main__':main()
