#!/usr/bin/env python3
"""Porter le bootstrap TG facultatif de note78 sur le main ACID actuel.

Les deux RAW Banque actuels (clear/Undo et LED inclus) restent identiques.
Seuls le chemin de démarrage, la réserve flash et les dépendances changent.
"""
import argparse,copy,hashlib,json,pathlib,shutil
import build,ref_mainos
CORE=['model-tg-st','scale-gen-st-queued','lfo-secondary','scramble-st-gen-queued','midi-live-both']
STAMP='2026-10-14-bank-optional-acid-test'
def generate(base,out):
 shutil.copytree(base,out,dirs_exist_ok=True);variants=json.loads((base/'source/main-clear-led-variants.json').read_text());refs={}
 for name,row in variants.items():
  for moved in [False,True]:
   for key in ['direct','0x4016cb1a','0x4016cb44','0x4016cb96']:
    t=copy.deepcopy(row['recipe']);t['requires']=CORE;t['writes']=[w for w in t['writes'] if w['off']!=0x4016cb96-build.BASE]
    t['writes'].append({'off':306 if key=='direct' else int(key,16)-build.BASE,'old':'401bf3d8' if key=='direct' else '4ef9401bf3d8','new':'401907a4' if key=='direct' else '4ef9401907a4'})
    if moved:
     for w in t['writes']:w['new']=w['new'].replace('401f8f76','401f8f8a')
    refs[name+('-moved' if moved else '')+'-'+key]=hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()
 p=out/'bundle.js';s=p.read_text();old='''document.addEventListener("change", event => {
  if (event.target.id === "feat-midi-bank-bundle" && event.target.checked) {
    document.getElementById("select-all").click();
  }
}, true);''';assert s.count(old)==1;s=s.replace(old,'// Banque TG : seuls les cinq supports nécessaires sont sélectionnés.')
 tail='\n// Bootstrap TG facultatif de note78 ; RAW Banque main inchangé.\n(()=>{const refs='+json.dumps(refs,separators=(',',':'))+';const core='+json.dumps(CORE)+';\n'
 tail+='''const a=window.MCFlasherApp,previous=window.MCMainClearResolve,oldRef=a.REF_MODS['midi-bank-bundle'];let current;
const ref={};for(const k of ['w','p'])Object.defineProperty(ref,k,{get:()=>k==='w'&&current?current:oldRef[k]});a.REF_MODS['midi-bank-bundle']=ref;
window.MCMainClearResolve=out=>{out=previous?previous(out):out;current=null;if(!a.isSelected('midi-bank-bundle'))return out;
 const engine=out.find(t=>t.id!=='midi-bank-bundle'&&t.append?.at==='0x401bf8c0');let key='direct';
 if(engine){const hits=[];for(const w of engine.writes)for(let i=0;i<w.new.length;i+=4)if(w.new.slice(i,i+12)==='4ef9401bf3d8')hits.push('0x'+(0x40000400+w.off+i/2).toString(16));if(hits.length!==1)throw Error('Unsupported machine bootstrap');key=hits[0];}
 return out.map(t=>{if(t.id!=='midi-bank-bundle')return t;const n=JSON.parse(JSON.stringify(t));n.requires=core;n.append.zero_pad_from='0x401bf8c0';n.writes=n.writes.filter(w=>w.off!==0x16cb96-0x400);n.writes.push({off:key==='direct'?306:parseInt(key,16)-0x40000400,old:key==='direct'?'401bf3d8':'4ef9401bf3d8',new:key==='direct'?'401907a4':'4ef9401907a4'});const name=(a.isSelected('chord-keys')?'chord':'plain')+(n.append.at==='0x401f8f8a'?'-moved':'')+'-'+key;current=refs[name];if(!current)throw Error('Unsupported bank source '+name);return n;});};
for(const [id,value]of [['model-tg','model-tg-st'],['sample-preview','sample-preview-st'],['scale-gen','scale-gen-st'],['scramble','scramble-st']]){const f=window.MC_TWEAKS.features.find(f=>f.id===id);f.with={...f.with,'midi-bank-bundle':value};}
const ui=['model-tg','scale-gen','lfo-secondary','scramble','midi-live-both'];
document.addEventListener('change',e=>{if(e.target.id==='feat-midi-bank-bundle'&&e.target.checked)for(const id of ui){const c=document.getElementById('feat-'+id);if(!c.checked){c.checked=true;c.dispatchEvent(new Event('change',{bubbles:true}));}}if(ui.some(id=>'feat-'+id===e.target.id)&&!e.target.checked){const c=document.getElementById('feat-midi-bank-bundle');if(c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}}},true);
a.applyLang(document.documentElement.lang||'en');})();
''';p.write_text(s+tail)
 p=out/'builder.js';s=p.read_text();needle='    if (BASE + full.length !== parseInt(ap.at, 16)) throw new Error("l\'image ne finit pas où le tweak l\'attend");';assert s.count(needle)==1;s=s.replace(needle,'''    if(t.id==='midi-bank-bundle'&&ap.zero_pad_from==='0x401bf8c0'&&BASE+full.length>=0x401bf8c0&&BASE+full.length<parseInt(ap.at,16)&&parseInt(ap.at,16)<=END_LIMIT){const pad=new Uint8Array(parseInt(ap.at,16)-BASE-full.length);full=concat(full,pad);fullDirty=concat(fullDirty,pad);}
'''+needle);p.write_text(s)
 texts={'en':'Syntakt, MACRO and ACID are optional. MIDI Bank requires Model-TG, Sequence Generator, Second LFO, SCRAMBLE and Live MIDI support. ChordKeys and USB6 remain optional.','fr':'Syntakt, MACRO et ACID sont facultatifs. Banque MIDI requiert Model-TG, générateur, Second LFO, SCRAMBLE et MIDI Live. ChordKeys et USB6 restent facultatifs.'};p=out/'app.js';s=p.read_text();at=s.index('window.MCFlasherApp =');s=s[:at]+'for(const L of ["en","fr"])FEAT[L]["midi-bank-bundle"].note='+json.dumps(texts,ensure_ascii=False)+'[L];\n'+s[at:];p.write_text(s)
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-14-main-acid-fade',STAMP))
 (out/'source/main-bank-optional-boot.json').write_text(json.dumps({'core':CORE,'refs':refs},indent=1)+'\n')
 print('ok : dépendances moteurs supprimées ; RAW main et TG conservés')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True);p.add_argument('--output',required=True);a=p.parse_args();generate(pathlib.Path(a.base),pathlib.Path(a.output))
if __name__=='__main__':main()
