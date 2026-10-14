#!/usr/bin/env python3
"""Retirer la Banque MIDI de main après les problèmes de performance signalés.

La Banque reste dans l’édition909 dédiée ; Out/Thru et les autres mods sont conservés.
"""
import argparse,pathlib,shutil,re
STAMP='2026-10-14-main-bank-909-exclusive'
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',required=True);a=p.parse_args();base=pathlib.Path(a.base);out=pathlib.Path(a.output);shutil.copytree(base,out,dirs_exist_ok=True)
tail='''
// Banque MIDI exclusive à l’édition909 : aucune sélection ni charge Banque sur main.
(()=>{
 const a=window.MCFlasherApp,tw=window.MC_TWEAKS,box=document.getElementById('feat-midi-bank-bundle');
 if(box&&box.checked){box.checked=false;box.dispatchEvent(new Event('change',{bubbles:true}));}
 tw.features=tw.features.filter(f=>f.id!=='midi-bank-bundle');
 tw.tweaks=tw.tweaks.filter(t=>!t.id.startsWith('midi-bank-bundle'));
 const previous=window.MCMainClearResolve;
 window.MCMainClearResolve=out=>(previous?previous(out):out).filter(t=>!t.id.startsWith('midi-bank-bundle'));
 const f=tw.features.find(f=>f.id==='chord-keys'),d=Object.getOwnPropertyDescriptor(f,'desc');
 Object.defineProperty(f,'desc',{configurable:true,get:()=>d.get.call(f)
 .replace('This experimental placement uses the MIDI Bank bundle; selecting it selects the compatible full bundle. MIDI Bank data remains RAM-only.','')
 .replace('Ce placement expérimental utilise le bundle Banque MIDI ; le cocher sélectionne le bundle complet compatible. Les données de Banque MIDI restent en RAM.','')
 .replace('The existing MIDI Bank integration is preserved.','').replace('Intégration Banque existante conservée.','')});
 a.applyLang(document.documentElement.lang||'en');
})();
'''
f=out/'bundle.js';f.write_text(f.read_text()+tail)
f=out/'index.html';s=f.read_text();note='''<div class="notice" role="note"><span data-l="en">MIDI OUT Bank is now exclusive to the <a href="../flasher-supermodel-909/">Supermodel 909 edition</a> due to performance issues in the standard Supermodel build.</span><span data-l="fr">La Banque MIDI OUT est désormais exclusive à l’<a href="../flasher-supermodel-909/">édition Supermodel 909</a>, en raison de problèmes de performance dans Supermodel standard.</span></div>'''
s=re.sub(r'<div class="notice" role="note">.*?</div>',lambda _:note,s,count=1,flags=re.S)
s=s.replace('MIDI Bank data is RAM-only and lost on power-off. ','').replace('Les données de la banque MIDI restent en RAM et sont perdues à extinction. ','')
s=s.replace('2026-10-14-main-chord-ref-fix',STAMP);f.write_text(s)
print('Banque retirée de main ; lien909 et note EN/FR')
