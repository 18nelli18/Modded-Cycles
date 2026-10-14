#!/usr/bin/env python3
"""Clear/Undo LFO et LED B sur le flasher principal TG existant.

Aucun chargeur indépendant ni stockage disque ajouté. Une sortie isolée permet
les preuves avant publication ; le parent décide de la destination autorisée.
"""
import argparse,copy,hashlib,json,pathlib,shutil
import build,ref_mainos
STAMP='2026-10-14-main-lfo-clear-midi-lights'

def generate(base,out,plain,chord,chord_recipe):
 shutil.copytree(base,out,dirs_exist_ok=True);variants={}
 for key,t in [('plain',plain),('chord',chord)]:
  assert t['ram_only_rollback'] and int(t['symbols']['ML_TG_START'],16)==0x401ab750
  assert not {0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6}&{build.BASE+w['off'] for w in t['writes']}
  variants[key]={'recipe':t,'ref':{'w':hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest(),'p':hashlib.sha256(bytes.fromhex(t['append']['compressed_hex'])).hexdigest()}}
 ck=copy.deepcopy(chord_recipe);patch=chord['play_ui']['chord_primary'];row=next(w for w in ck['writes'] if w['off']==patch['off']);assert row['old']==patch['old'];row['new']=patch['new'];ck_ref={'w':hashlib.sha256(ref_mainos.writes_bytes(ck)).hexdigest()}
 tail='\n// Main TG conservé : clear/Undo LFO et lumières B, pas de sauvegarde.\n(()=>{const variants='+json.dumps(variants,separators=(',',':'))+';const chord='+json.dumps(ck,separators=(',',':'))+';const chordRef='+json.dumps(ck_ref)+';\n'
 tail+='''const app=window.MCFlasherApp,on=id=>app.isSelected(id),key=()=>on('chord-keys')?'chord':'plain';
window.MCMainClearResolve=out=>{if(!on('midi-bank-bundle'))return out;
 return out.map(t=>t.id==='midi-bank-bundle'?variants[key()].recipe:t.id===chord.id?chord:t);};
const ref={};for(const field of ['w','p'])Object.defineProperty(ref,field,{enumerable:true,get:()=>variants[key()].ref[field]});app.REF_MODS['midi-bank-bundle']=ref;app.REF_MODS[chord.id]=chordRef;
for(const k of Object.keys(app.REF_MAINOS))if(k.includes('midi-bank-bundle'))delete app.REF_MAINOS[k];
window.MC_TWEAKS.features.find(f=>f.id==='midi-bank-bundle').status='experimental';app.applyLang(document.documentElement.lang||'en');
})();
'''
 p=out/'bundle.js';p.write_text(p.read_text()+tail)
 p=out/'app.js';s=p.read_text();old='  return out;\n}\nfunction chosenLabels()';new='  return window.MCMainClearResolve ? window.MCMainClearResolve(out) : out;\n}\nfunction chosenLabels()';assert s.count(old)==1;s=s.replace(old,new);assert 'chosenTweaks, chosenLabels, CATS };' in s;s=s.replace('chosenTweaks, chosenLabels, CATS };','chosenTweaks, chosenLabels, CATS, isSelected: isOn };')
 at=s.index('window.MCFlasherApp =');extra={'en':'FUNC + PLAY clears the selected track and both LFOs; press again to undo. In B-side keyboard mode, recorded steps are hidden, held keys light up, and the playhead remains visible. New clear/Undo and light behavior awaits hardware verification.','fr':'FUNC + PLAY efface la piste sélectionnée et ses deux LFO ; répéter annule. Clavier B : pas enregistrés masqués, touches tenues éclairées, curseur visible. Nouveaux clear/Undo et lumières à vérifier sur machine.'}
 s=s[:at]+'for(const L of ["en","fr"])FEAT[L]["midi-bank-bundle"].desc += " " + '+json.dumps(extra,ensure_ascii=False)+'[L];\n'+s[at:];p.write_text(s)
 for p in out.iterdir():
  if p.is_file() and p.suffix in ('.js','.html','.md'):p.write_text(p.read_text().replace('2026-10-13-chordkeys-rotero-main',STAMP))
 (out/'source/main-clear-led-variants.json').write_text(json.dumps(variants,ensure_ascii=False,indent=1)+'\n')
 (out/'ABOUT.md').write_text('# Main-based LFO clear/Undo and MIDI lights\n\nUses the existing main Model-TG startup and support dependencies. No independent kernel or MIDI saving changes. FUNC + PLAY clear/Undo includes both LFOs on the selected A/B track. B keyboard mode hides recorded steps, lights held keys and preserves the playhead. New behaviors are not yet hardware verified.\n\nDémarrage et dépendances TG du main conservés. Pas de noyau indépendant ni sauvegarde MIDI. Clear/Undo des deux LFO par piste A/B ; pas masqués hors REC, touches live et curseur conservés. Nouveautés non vérifiées sur matériel.\n')
 print('ok : deux variantes sur base main TG ; aucune indépendance ni sauvegarde ajoutée')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('base-dir','output','plain','chord','chord-recipe'):p.add_argument('--'+name,required=True)
 a=p.parse_args();read=lambda f:json.loads(pathlib.Path(f).read_text());generate(pathlib.Path(a.base_dir),pathlib.Path(a.output),read(a.plain),read(a.chord),read(a.chord_recipe))
if __name__=='__main__':main()
