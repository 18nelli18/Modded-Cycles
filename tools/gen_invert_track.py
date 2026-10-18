"""Note122 : selection silencieuse des pistes, patch fourni par AveyCole.

python3 tools/gen_invert_track.py [--check]
Un octet garde de OS1.13 ; aucune charge utile ni espace libre utilise.
"""
import argparse,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mtlib import aplib,container
from mtlib.syx import unwrap
OUT=ROOT/'tweaks/model-cycles_OS1.13/49-invert-track.json'
def recipe():
 return dict(id='invert-track',order=49,name='Pads silencieux, TRACK + pad joue',status='experimental',device='Model:Cycles',os='1.13',section=3,requires=[],conflicts=[],description=['Pads T1-T6 : appui simple selectionne sans son ; TRACK + pad selectionne et joue, avec le relais live record natif.','Navigateur de presets : apercu sonore par appui simple conserve ; TRACK + pad selectionne et joue.','Un octet beq vers bne a0x4001d374, sans payload. Contribution fournie par AveyCole. tools/gen_invert_track.py ; notes/122.'],writes=[dict(off=118644,old='67',new='66')])
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 raw=(ROOT/'firmware/model-cycles_OS1.13.syx').read_bytes();device=json.loads((ROOT/'tweaks/model-cycles_OS1.13/device.json').read_text())
 assert hashlib.sha256(raw).hexdigest()==device['stock_syx_sha256']
 stream,_=unwrap(raw);co=container.parse(stream);section=next(s for s in co['sections'] if s['id']==3);image,_=aplib.depack(co['blob'][section['off']:section['off']+section['size']]);assert image[118644:118646]==bytes.fromhex('67d8')
 text=json.dumps(recipe(),ensure_ascii=False,indent=2)+'\n'
 if a.check:assert OUT.read_text(encoding='utf-8')==text
 else:OUT.write_text(text,encoding='utf-8')
 print('PASS guarded invert-track recipe, exactly one changed byte')
if __name__=='__main__':main()
