"""Test distinct demandé : sans filtre, lampe/mutes Genie et Attack."""
import json,pathlib,shutil,hashlib
P=pathlib.Path('work/genie-attack-test');out=P/'page';shutil.copytree('work/wizard-filter-integration/main-revoked',out,dirs_exist_ok=True);data=json.load(open(P/'data.json'))
script='window.MCGenieAttack='+json.dumps(data,separators=(',',':'))+';\n'+'''(()=>{
const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,c=window.MCGenieAttack,prev=window.MCMainClearResolve,prior={...a.REF_MODS};
const hash=t=>b.hex(b.sha256(b.writesBytes(t))),clone=t=>JSON.parse(JSON.stringify(t));
// Les helpers partagent le support Wizard ; les choix sans Wizard gardent leur code antérieur.
const feat={id:'synth-attack',label:'Synth Attack',status:'experimental',cat:'sound',requires:'sample-wizard',excludes:['lfo-plus'],variants:[{id:'synth-attack'}]};tw.features.push(feat);tw.tweaks.push({id:'synth-attack',order:62,requires:['sample-wizard'],writes:[]});
const lp=tw.features.find(f=>f.id==='lfo-plus');lp.excludes=[...new Set([...(lp.excludes||[]),'synth-attack'])];
window.MCMainClearResolve=out=>{
for(const [id,ref] of Object.entries(prior))a.REF_MODS[id]=ref;
out=prev(out);const attack=a.isSelected('synth-attack'),genie=a.isSelected('scale-gen')&&a.isSelected('sample-wizard');if(!attack&&!genie)return out;
const recipe=clone(c.recipe);recipe.requires=['sample-wizard'];if(attack)recipe.writes.push(...c.attack,...c.pool);
const result=out.filter(t=>t.id!=='synth-attack').map(t=>{
 const ref=a.REF_MODS[t.id];let n=null;
 if(genie&&t.id.startsWith('scale-gen')){
  if(hash(t)!==ref.w)throw Error('Genie UI: trusted reference mismatch');n=clone(t);
  for(const ch of c.sg){const off=ch.at-0x40000400,w=n.writes.find(w=>w.off<=off&&off+ch.old.length/2<=w.off+w.new.length/2);if(!w)throw Error('Genie UI: missing hook');const i=(off-w.off)*2;if(w.new.slice(i,i+ch.old.length)!==ch.old)throw Error('Genie UI: hook guard');w.new=w.new.slice(0,i)+ch.new+w.new.slice(i+ch.old.length);}
 }
 if(attack&&t.id==='sample-wizard'){
  if(hash(t)!==ref.w||b.hex(b.sha256(b.buildPayload(t.append,null,null)))!==ref.p)throw Error('Attack: trusted Wizard reference mismatch');n=clone(t);const p=n.append.parts[0];
  for(const ch of c.payload){const i=ch.off*2;if(p.hex.slice(i,i+ch.old.length)!==ch.old)throw Error('Attack codec guard');p.hex=p.hex.slice(0,i)+ch.new+p.hex.slice(i+ch.old.length);}
 }
 if(attack&&t.id==='chord-keys-supermodel'){
  if(hash(t)!==ref.w)throw Error('Attack: trusted ChordKeys reference mismatch');n=clone(t);n.writes=n.writes.filter(w=>![0x5b5c6,0x5b6d2].includes(w.off));
 }
 if(n)a.REF_MODS[n.id]={w:hash(n),...(n.append?{p:b.hex(b.sha256(b.buildPayload(n.append,null,null)))}:{})};return n||t;
});
recipe.writes.sort((x,y)=>x.off-y.off);a.REF_MODS[recipe.id]={w:hash(recipe)};return result.concat(recipe).sort((x,y)=>x.order-y.order);
};
a.applyLang(document.documentElement.lang||'en');
})();'''
(out/'genie-attack.js').write_text(script)
# Corriger la référence dynamique de queue lors des changements de sélection.
p=out/'queue-choice.js';s=p.read_text().replace('window.MCMainClearResolve=out=>old(out).map(t=>{','window.MCMainClearResolve=out=>{for(const [id,ref] of Object.entries(prior))a.REF_MODS[id]=ref;return old(out).map(t=>{').replace(' const f=window.MC_TWEAKS.features.find', ' };\n const f=window.MC_TWEAKS.features.find');p.write_text(s)
p=out/'app.js';s=p.read_text();needle="GUIDE_OF['sample-wizard']='sample-wizard';";s=s.replace(needle,needle+'''\nFEAT.en['synth-attack']={label:'Synth Attack',short:'MACHINES + DECAY adds an attack ramp to every synth/drum track.',desc:'With Sample Wizard support selected, hold MACHINES and turn DECAY to adjust Attack on stock and added synth/drum machines. Wizard retains its own attack. Zero is a bit-exact bypass. Supports sound saves and parameter locks. No shared filter is installed. Experimental: test the new attack ramp before relying on it.',shortcuts:['MACHINES + DECAY: Attack.','Hold a TRIG while adjusting to lock Attack.']};
FEAT.fr['synth-attack']={label:'Attack synth',short:'MACHINES + DECAY : rampe d’attaque sur chaque piste synth/drum.',desc:'Avec le support Wizard, tenir MACHINES et tourner DECAY pour Attack sur les synthés/drums stock et ajoutés. Wizard conserve son attaque. Zéro : bypass exact. Sauvegarde du son et locks. Aucun filtre partagé. Nouvelle rampe expérimentale, à tester.',shortcuts:['MACHINES + DECAY : Attack.','Tenir un TRIG pendant le réglage pour un lock.']};
''');p.write_text(s)
p=out/'index.html';s=p.read_text().replace('2026-10-15-filter-withdrawn','2026-10-15-genie-lamp-mute-attack');a=s.index('<p class="alert">');z=s.index('</p>',a)+4;s=s[:a]+'''<p class="alert"><span data-l="en"><strong>Genie lamp / mute lights + synth Attack test.</strong> Shared filter removed. Select Sample Wizard and Sequence Generator to test the restored S.G. lamp and FUNC + pad mute lights. Select Synth Attack for MACHINES + DECAY on synth/drum tracks. Existing options retain their hardware-tested designation; these new changes need hardware verification. Main and 909 stay unchanged by this test.</span><span data-l="fr"><strong>Test lampe/mutes Genie + Attack synth.</strong> Filtre partagé retiré. Wizard + Genie : lampe S.G. et voyants FUNC + pad. Attack synth : MACHINES + DECAY sur les pistes synth/drum. Options existantes testées ; changements nouveaux à vérifier sur machine. Main et 909 inchangés par ce test.</span></p>'''+s[z:];s=s.replace('</body>','<script src="genie-attack.js?v=2026-10-15-genie-lamp-mute-attack"></script></body>');p.write_text(s)
source=out/'source/genie-attack';source.mkdir(parents=True,exist_ok=True)
for name in ['generate.py','page.py','ui.s','attack.s']:shutil.copy(P/name,source/name)
files=[]
for e in json.load(open('work/wizard-filter-integration/revoke-files.json')):
 p=out/pathlib.Path(e['local']).relative_to('work/wizard-filter-integration/main-revoked');b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-genie-attack-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
for p in [out/'genie-attack.js',*source.iterdir()]:
 b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-genie-attack-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
(P/'publish-files.json').write_text(json.dumps(files));print(len(files),'separate test files')
