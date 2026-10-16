"""Note 99 : promotion du candidat 2 confirme sur machine par AveyCole."""
import argparse,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def outputs():
    src=ROOT/'docs/flasher-beat-repeat-test'
    for name in ('beat-repeat-data.js','LICENSE-Beat-Repeat.txt'):
        yield name,(src/name).read_text(encoding='utf-8')
    s=(src/'beat-repeat.js').read_text(encoding='utf-8')
    s=s.replace("status:'experimental'","status:'tested',hardwareTestedByOwner:true")
    s=s.replace('Experimental independent beat repeat.','Independent beat repeat.').replace('Hardware testing pending.','Hardware tested by AveyCole.')
    s=s.replace('Beat repeat autonome experimental.','Beat repeat autonome.').replace('Test materiel attendu.','Teste sur machine par AveyCole.')
    yield 'beat-repeat.js',s
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    for name,text in outputs():
        dest=ROOT/'docs/flasher'/name
        if a.check:assert dest.read_text(encoding='utf-8')==text,name
        else:dest.write_text(text,encoding='utf-8')
    print('ok promotion beat repeat : noyau test 2 identique')
if __name__=='__main__':main()
