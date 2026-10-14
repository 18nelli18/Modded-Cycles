#!/usr/bin/env python3
"""Page diagnostic garde startup : modifie seulement les backends sans TG.

La page principale ne change pas. Correction matérielle non confirmée.
"""
import argparse,hashlib,json,pathlib,shutil
from gen_midi_startup_guard import generate as guard
from midi_catalog_compact import compact,restore,JS_DECODER
STAMP='2026-10-14-midi-startup-guard'

def generate(base,out,matrix):
 shutil.copytree(base,out,dirs_exist_ok=True);patches={}
 for row in json.loads((matrix/'matrix.json').read_text()):
  if row['tg']:continue
  key=row['key'];data=guard(json.loads((matrix/(key+'.json')).read_text()));b=data['bank']
  patches[key]={'append':b['append'],'symbols':b['symbols'],'p':hashlib.sha256(bytes.fromhex(b['append']['compressed_hex'])).hexdigest()}
 encoded=compact(patches);assert restore(encoded)==patches
 tail='\n// Diagnostic : différer services B et protéger LED avant singletons UI.\n(()=>{'+JS_DECODER+'const patches=unpackCatalogue('+json.dumps(encoded,separators=(',',':'))+');\n'
 tail+='''const app=window.MCFlasherApp,on=id=>app.isSelected(id),previous=window.MCMidiIndependentResolve;
const key=()=>['model-tg','scale-gen','lfo-secondary','scramble','chord-keys'].map(id=>on(id)?'1':'0').join('');let active=null;
window.MCMidiIndependentResolve=out=>{const resolved=previous(out);active=null;
 if(!on('midi-bank-bundle')||on('model-tg'))return resolved;
 active=patches[key()];if(!active)throw Error('Missing startup diagnostic backend');
 return resolved.map(t=>t.id==='midi-bank-bundle'?{...t,append:active.append,symbols:active.symbols}:t);
};
const old=app.REF_MODS['midi-bank-bundle'],ref={};Object.defineProperty(ref,'w',{enumerable:true,get:()=>old.w});Object.defineProperty(ref,'p',{enumerable:true,get:()=>active?active.p:old.p});app.REF_MODS['midi-bank-bundle']=ref;
for(const k of Object.keys(app.REF_MAINOS))if(k.includes('midi-bank-bundle'))delete app.REF_MAINOS[k];
})();
'''
 p=out/'bundle.js';p.write_text(p.read_text()+tail)
 for p in out.iterdir():
  if p.is_file() and p.suffix in ('.js','.html','.md'):p.write_text(p.read_text().replace('2026-10-14-scramble-independent',STAMP))
 p=out/'index.html';s=p.read_text().replace('Experimental standalone SCRAMBLE and independent MIDI Bank. Model-TG and extra machines are optional. Main unchanged. MIDI Bank remains RAM-only.','Startup diagnostic for the reported white-screen freeze without Model-TG. B-side background services start after opening B; early LED callbacks are guarded. Hardware fix not yet confirmed. Main unchanged.').replace('Test SCRAMBLE autonome et Banque MIDI indépendante. TG et machines facultatifs. Flasher principal inchangé. Banque MIDI en RAM.','Diagnostic écran blanc sans TG : services B après ouverture, callbacks LED protégés. Correction matérielle non confirmée. Flasher principal inchangé.');p.write_text(s)
 (out/'source/midi-startup-guard.json').write_text(json.dumps(encoded,ensure_ascii=False,indent=1)+'\n')
 (out/'ABOUT.md').write_text('# MIDI startup guard diagnostic\n\nReported white-screen freeze without Model-TG. Protect early LED callbacks and defer B-side background services until B-side is first opened. Main unchanged. Hardware result unknown; RAM-only MIDI Bank.\n\nDiagnostic écran blanc sans TG. LED protégées, services B différés jusqu’à première ouverture. Main inchangé. Résultat matériel inconnu ; Banque en RAM.\n')
 print('ok :',len(patches),'backends diagnostic ; résultat matériel inconnu')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('base-dir','output','matrix'):p.add_argument('--'+name,required=True)
 a=p.parse_args();generate(pathlib.Path(a.base_dir),pathlib.Path(a.output),pathlib.Path(a.matrix))
if __name__=='__main__':main()
