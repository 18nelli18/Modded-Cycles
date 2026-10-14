#!/usr/bin/env python3
"""Banque MIDI sans imposer les moteurs : bootstrap direct et réserve flash explicite.

--base-dir page --output page ; note78. Le RAW musical reste inchangé.
"""
import argparse,copy,json,pathlib,shutil,hashlib,tempfile
import build,ref_mainos
CORE=['model-tg-st','scale-gen-st-queued','lfo-secondary','scramble-st-gen-queued','midi-live-both']
STAMP='2026-10-13-midi-bank-optional-machines'
def generate(base,out,references=None):
 shutil.copytree(base,out,dirs_exist_ok=True)
 s=(out/'bundle.js').read_text();old='''document.addEventListener("change", event => {
  if (event.target.id === "feat-midi-bank-bundle" && event.target.checked) {
    document.getElementById("select-all").click();
  }
}, true);''';assert s.count(old)==1;s=s.replace(old,'// Banque seule : activer uniquement les dépendances nécessaires ci-dessous.')
 b=json.loads((out/'source/integration-midi-bank.json').read_text());native=[w for w in b['writes'] if w['off']!=0x4016cb96-build.BASE];variants={};refs={}
 for key in ['direct','0x4016cb1a','0x4016cb44','0x4016cb96']:
  w=copy.deepcopy(native)
  if key=='direct':w.append(dict(off=306,old='401bf3d8',new='401907a4'))
  else:w.append(dict(off=int(key,16)-build.BASE,old='4ef9401bf3d8',new='4ef9401907a4'))
  variants[key]=w;refs[key]=hashlib.sha256(ref_mainos.writes_bytes({'writes':w})).hexdigest()
 tail='\n// Machines facultatives : bootstrap et références vérifiés, note78.\n(()=>{const variants='+json.dumps(variants)+';const refs='+json.dumps(refs)+';const core='+json.dumps(CORE)+';\n'
 tail+='''const a=window.MCFlasherApp,b=window.MC_TWEAKS.tweaks.find(t=>t.id==='midi-bank-bundle');
function bootKey(){const e=a.chosenTweaks().find(t=>t.id!==b.id&&t.append?.at==='0x401bf8c0');if(!e)return 'direct';
 const hits=[];for(const w of e.writes){for(let i=0;i<w.new.length;i+=4)if(w.new.slice(i,i+12)==='4ef9401bf3d8')hits.push('0x'+(0x40000400+w.off+i/2).toString(16));}
 if(hits.length!==1||!variants[hits[0]])throw Error('Unsupported machine bootstrap');return hits[0];}
b.requires=core;b.append.zero_pad_from='0x401bf8c0';
Object.defineProperty(b,'writes',{get:()=>variants[bootKey()],configurable:true});
Object.defineProperty(a.REF_MODS[b.id],'w',{get:()=>refs[bootKey()],configurable:true});
for(const [id,v] of [['model-tg','model-tg-st'],['sample-preview','sample-preview-st'],['scale-gen','scale-gen-st'],['scramble','scramble-st']]){const f=window.MC_TWEAKS.features.find(f=>f.id===id);f.with={...f.with,'midi-bank-bundle':v};}
const uiCore=['model-tg','scale-gen','lfo-secondary','scramble','midi-live-both'];
window.MC_TWEAKS.features.find(f=>f.id===b.id).excludes=['lfo-plus'];
document.addEventListener('change',event=>{if(['feat-syntakt','feat-macro','feat-acid'].includes(event.target.id)&&!event.target.checked){const c=document.getElementById('feat-chord-keys');if(c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}}
 if(uiCore.map(id=>'feat-'+id).includes(event.target.id)&&!event.target.checked){const c=document.getElementById('feat-midi-bank-bundle');if(c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}}
 if(event.target.id==='feat-midi-bank-bundle'&&event.target.checked){for(const id of uiCore){const box=document.getElementById('feat-'+id);if(!box.checked){box.checked=true;box.dispatchEvent(new Event('change',{bubbles:true}));}}}},true);
a.applyLang(document.documentElement.lang||'en');
})();\n'''
 if references:tail+='\nObject.assign(window.MCFlasherApp.REF_MAINOS,'+json.dumps(references['refs'])+');\n'
 (out/'bundle.js').write_text(s+tail)
 for name in ['integration-midi-bank.json','integration-midi-bank-chord.json']:
  p=out/'source'/name;t=json.loads(p.read_text());t['requires']=CORE;t['writes']=variants['0x4016cb96'];t['append']['zero_pad_from']='0x401bf8c0';t['optional_machines']=True;p.write_text(json.dumps(t,ensure_ascii=False,indent=1)+'\n')
 if references:(out/'source/optional-reference-check.json').write_text(json.dumps(references,indent=1)+'\n')
 p=out/'builder.js';s=p.read_text();needle='''    if (BASE + full.length !== parseInt(ap.at, 16)) throw new Error("l'image ne finit pas où le tweak l'attend");''';assert s.count(needle)==1
 s=s.replace(needle,'''    const end=BASE+full.length, target=parseInt(ap.at,16);
    if(t.id==='midi-bank-bundle'&&ap.zero_pad_from==='0x401bf8c0'&&end>=0x401bf8c0&&end<target&&target<=END_LIMIT){const pad=new Uint8Array(target-end);full=concat(full,pad);fullDirty=concat(fullDirty,pad);}
'''+needle);p.write_text(s)
 texts={'en':{'note':'Syntakt, MACRO and ACID are optional. Selecting MIDI Bank enables its Model-TG, Sequence Generator, Second LFO, SCRAMBLE and Live MIDI support. ChordKeys still selects its full compatible integration; leave ChordKeys off for stock machines only.'},'fr':{'note':'Syntakt, MACRO et ACID sont facultatifs. Banque MIDI active ses supports Model-TG, générateur, Second LFO, SCRAMBLE et MIDI Live. ChordKeys sélectionne encore son intégration complète ; laissez-le décoché pour les machines stock seules.'}}
 p=out/'app.js';s=p.read_text();at=s.index('window.MCFlasherApp =');s=s[:at]+'for(const L of ["en","fr"])Object.assign(FEAT[L]["midi-bank-bundle"],'+json.dumps(texts,ensure_ascii=False)+'[L]);\n'+s[at:];p.write_text(s)
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-13-controls-baseline-lfo',STAMP))
 (out/'source/optional-midi-boot.json').write_text(json.dumps({'core_requires':CORE,'variants':variants,'refs':refs,'zero_pad_from':'0x401bf8c0'},indent=1)+'\n')
 with (out/'ABOUT.md').open('a') as f:f.write('\n## Optional machines\nSelecting MIDI Bank enables its five required support mods, without Syntakt, MACRO, ACID, ChordKeys or USB6. Machine choices remain optional. A zero-filled flash gap preserves the existing compressed-bank source address; musical RAM code is unchanged. ChordKeys keeps its current full-integration selection. Main remains unchanged.\n')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--references');p.add_argument('--check',action='store_true');a=p.parse_args();refs=json.loads(pathlib.Path(a.references).read_text()) if a.references else None
 with tempfile.TemporaryDirectory() as temp:
  target=pathlib.Path(a.output);out=pathlib.Path(temp)/'page' if a.check else target;generate(pathlib.Path(a.base_dir),out,refs)
  if a.check:
   for f in out.rglob('*'):
    if f.is_file():assert f.read_bytes()==(target/f.relative_to(out)).read_bytes(),str(f)
 print('ok : machines facultatives, quatre chemins boot référencés')
if __name__=='__main__':main()
