#!/usr/bin/env python3
"""ChordKeys sur main : TG conservé, Banque et moteurs facultatifs pour Chord."""
import argparse,copy,hashlib,json,pathlib,shutil
import ref_mainos
STAMP='2026-10-14-main-chord-optional-machines'
def generate(base,out,prototype,hooks):
 shutil.copytree(base,out,dirs_exist_ok=True)
 p=copy.deepcopy(prototype);p['id']='chord-keys-supermodel';p['requires']=['model-tg-st'];p['pending']=['hardware_verification'];p['flashable']=True
 refs={'w':hashlib.sha256(ref_mainos.writes_bytes(p)).hexdigest(),'p':hashlib.sha256(bytes.fromhex(p['append']['compressed_hex'])).hexdigest()}
 main_recipe=copy.deepcopy(p)
 hooks={k:v for k,v in hooks.items() if v['tg']}
 s=(out/'bundle.js').read_text();old="document.addEventListener('change',event=>{if(event.target.id==='feat-chord-keys'&&event.target.checked)document.getElementById('select-all').click();},true);";assert s.count(old)==1;s=s.replace(old,'// Chord ne sélectionne plus tous les mods.')
 old="if(['feat-syntakt','feat-macro','feat-acid'].includes(event.target.id)&&!event.target.checked){const c=document.getElementById('feat-chord-keys');if(c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}}";assert s.count(old)<=1;s=s.replace(old,'')
 tail='\n// Chord TG seulement : les chemins Banque existants restent inchangés.\n(()=>{const prototype='+json.dumps(p,separators=(',',':'))+';const engines='+json.dumps(hooks,separators=(',',':'))+';const ref='+json.dumps(refs)+';\n'
 tail+='''const app=window.MCFlasherApp,on=app.isSelected,previous=window.MCMainClearResolve,originalRef=app.REF_MODS[prototype.id];let activeRef=ref;
window.MCMainClearResolve=out=>{out=previous(out);if(!on('chord-keys')||on('midi-bank-bundle'))return out;
 if(!on('model-tg'))throw Error('ChordKeys requires Model-TG');
 const ids={'scale-gen-queued':'scale-gen-st-queued','sample-preview':'sample-preview-st','scramble':'scramble-st','scramble-gen-queued':'scramble-st-gen-queued'};out=out.map(t=>ids[t.id]?window.MC_TWEAKS.tweaks.find(x=>x.id===ids[t.id]):t);
 const engine=out.find(t=>Object.hasOwn(engines,t.id));let recipe=prototype;activeRef=ref;
 if(engine){recipe={...prototype,writes:prototype.writes.filter(w=>w.off!==306).concat([engines[engine.id].hook]),requires:prototype.requires.concat([engine.id])};activeRef={w:engines[engine.id].w,p:ref.p};}
 return out.map(t=>t.id===prototype.id?recipe:t);};
const r={};for(const field of ['w','p'])Object.defineProperty(r,field,{enumerable:true,get:()=>on('midi-bank-bundle')?originalRef[field]:activeRef[field]});app.REF_MODS[prototype.id]=r;
const f=window.MC_TWEAKS.features.find(f=>f.id==='chord-keys');f.requires='model-tg';f.with={};
window.MC_TWEAKS.features.find(f=>f.id==='model-tg').with={...window.MC_TWEAKS.features.find(f=>f.id==='model-tg').with,'chord-keys':'model-tg-st'};
const old=Object.getOwnPropertyDescriptor(f,'desc');const extra={en:' ChordKeys requires Model-TG, but does not require MIDI Bank or Syntakt, MACRO or ACID machines. The existing MIDI Bank integration is preserved.',fr:' ChordKeys nécessite Model-TG, sans imposer Banque MIDI ni machines Syntakt, MACRO ou ACID. Intégration Banque existante conservée.'};
Object.defineProperty(f,'desc',{configurable:true,get:()=>old.get.call(f)+(extra[document.documentElement.lang]||extra.en)});
for(const k of Object.keys(app.REF_MAINOS))if(k.includes(prototype.id))delete app.REF_MAINOS[k];app.applyLang(document.documentElement.lang||'en');
})();
'''
 (out/'bundle.js').write_text(s+tail)
 p=out/'builder.js';s=p.read_text();old='    if (BASE + full.length !== parseInt(ap.at, 16)) throw new Error("l’image ne finit pas où le tweak l’attend");'.replace('l’image',"l'image").replace('l’attend',"l'attend")
 new="""    const target=parseInt(ap.at,16),end=BASE+full.length;
    if(t.id==='chord-keys-supermodel'&&ap.zero_pad_from==='0x401aa140'&&target===0x401f8f76&&end>=0x401aa140&&end<target&&target<=END_LIMIT){const padding=new Uint8Array(target-end);full=concat(full,padding);fullDirty=concat(fullDirty,new Uint8Array(padding.length).fill(1));}
"""+old
 assert s.count(old)==1;p.write_text(s.replace(old,new))
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-14-main-lfo-clear-midi-lights',STAMP))
 (out/'source/chord-tg-optional-machines.json').write_text(json.dumps({'recipe':main_recipe,'engine_hooks':hooks,'ref':refs},indent=1)+'\n')
 with (out/'ABOUT.md').open('a') as f:f.write('\nChordKeys can be selected with Model-TG alone. It does not select MIDI Bank, Syntakt, MACRO or ACID automatically. Bank selections retain their existing dependencies and firmware. TG-only Chord combinations remain awaiting hardware verification.\n')
 for name,text in [('quick-reference.md','ChordKeys requires Model-TG. MIDI Bank and extra synth machines are optional for ChordKeys; checking it does not select all mods.'),('quick-reference-fr.md','ChordKeys nécessite Model-TG. Banque MIDI et machines supplémentaires sont facultatives pour ChordKeys ; sa sélection ne coche plus tous les mods.')]:
  p=out/name;p.write_text(p.read_text()+'\n'+text+'\n')
 print('ok : Chord TG sans Banque/machines imposées ; chemin Banque conservé')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('base-dir','output','prototype','engine-hooks'):p.add_argument('--'+n,required=True)
 a=p.parse_args();read=lambda f:json.loads(pathlib.Path(f).read_text());generate(pathlib.Path(a.base_dir),pathlib.Path(a.output),read(a.prototype),read(a.engine_hooks))
if __name__=='__main__':main()
