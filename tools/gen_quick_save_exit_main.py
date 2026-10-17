"""Note113 : promotion du close confirme, masque sprite partage, aucun diagnostic."""
import argparse,hashlib,json,pathlib
import sprites
from mtlib import aplib,container
from mtlib.syx import unwrap
ROOT=pathlib.Path(__file__).resolve().parents[1];CAVE=0x40187528;STAMP='2026-10-17-quick-save-exit-main'
JS='''// Note113 : close confirme ; masque deja libere/efface par Wizard accepte avec garde.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCQuickSaveExit,previous=window.MCMainClearResolve,hash=x=>b.hex(b.sha256(x));window.MCMainClearResolve=input=>{const result=previous(input);if(!result.some(t=>t.id==='latching-mute')||result.some(t=>t.id===d.id))return result;const t=JSON.parse(JSON.stringify(d)),w=t.writes[2],bytes=b.fromHex(w.old),providers=new Set();for(const p of [...result].sort((x,y)=>x.order-y.order))for(const q of p.writes){const lo=Math.max(w.off,q.off),hi=Math.min(w.off+bytes.length,q.off+q.new.length/2);if(lo>=hi)continue;const code=b.fromHex(q.new);bytes.set(code.subarray(lo-q.off,hi-q.off),lo-w.off);providers.add(p.id);t.order=Math.max(t.order,p.order+1);}const old=b.hex(bytes);if(old!==w.old){if(!bytes.every(x=>x===0))throw Error('Quick save exit: sprite room occupied');w.old=old;}t.requires=[...new Set([...t.requires,...providers])];a.REF_MODS[t.id]={w:hash(b.writesBytes(t))};return result.concat(t).sort((x,y)=>x.order-y.order);};})();
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();stream,_=unwrap((ROOT/'firmware/model-cycles_OS1.13.syx').read_bytes());c=container.parse(stream);section=next(s for s in c['sections'] if s['id']==3);stock=aplib.depack(c['blob'][section['off']:section['off']+section['size']])[0];device=json.loads((ROOT/'tweaks/model-cycles_OS1.13/device.json').read_text());assert hashlib.sha256(stock).hexdigest()==device['section_sha256']
 assert stock[CAVE-sprites.BASE:CAVE-sprites.BASE+192]==stock[sprites.kept_of(CAVE)-sprites.BASE:sprites.kept_of(CAVE)-sprites.BASE+192], 'masques differents'
 code=json.loads((ROOT/'docs/flasher-quick-save-test/quick-save-latch-data.js').read_text().split('=',1)[1].strip().rstrip(';'))['hex'];assert len(code)//2==92
 tweak=dict(id='quick-save-exit',order=59,name='Fermer le mute apres sauvegarde rapide',description=['FUNCTION+SETTINGS long ferme la vue mute par son close natif, sans changer la sauvegarde.','Code confirme par AveyCole sur test3 le17/10/2026 ; placement dans masque sprite partage, sans diagnostic.','Generateur tools/gen_quick_save_exit_main.py ; note113.'],device='Model:Cycles',os='1.13',section=3,requires=['latching-mute'],conflicts=[],status='tested',hardwareTestedByOwner=True,writes=[dict(off=0x40100c44-sprites.BASE,old='40148744',new=CAVE.to_bytes(4,'big').hex()),sprites.redirect_write(CAVE),dict(off=CAVE-sprites.BASE,old=stock[CAVE-sprites.BASE:CAVE-sprites.BASE+92].hex(),new=code)],symbols=dict(qs_exit=hex(CAVE)))
 files={'tweaks/model-cycles_OS1.13/59-quick-save-exit.json':json.dumps(tweak,ensure_ascii=False,indent=1)+'\n','docs/flasher/quick-save-exit-data.js':'window.MCQuickSaveExit='+json.dumps(tweak,separators=(',',':'),ensure_ascii=False)+';\n','docs/flasher/quick-save-exit.js':JS}
 for name,text in files.items():
  p=ROOT/name
  if a.check:assert p.read_text(encoding='utf-8').replace('\r\n','\n')==text,name
  else:p.write_text(text,encoding='utf-8')
 print('PASS main quick-save exit :92 octets confirmes, sprite redirige, aucun diagnostic')
if __name__=='__main__':main()
