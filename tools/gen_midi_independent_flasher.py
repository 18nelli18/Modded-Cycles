#!/usr/bin/env python3
"""Page test Banque facultative : 32 backends vérifiés, UI de transfert conservée.

Aucune publication automatique ; fichiers officiels toujours fournis localement.
"""
import argparse,copy,hashlib,json,pathlib,shutil,struct,tempfile
import build,ref_mainos
from chord_keys_pr87 import load_stock
from midi_catalog_compact import compact,restore,JS_DECODER
STAMP='2026-10-13-midi-bank-independent'
def digest(t):return hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()
def generate(base,out,matrix,catalog,stock,compression):
 shutil.copytree(base,out,dirs_exist_ok=True);rows=json.loads((matrix/'matrix.json').read_text());variants={};engines={}
 for e in catalog:
  if not e.get('append') or not e['id'].startswith(('syntakt-','macro','acid')):continue
  tg='-tg' in e['id'];expected=bytes.fromhex('4ef9'+next(t for t in catalog if t['id']=='model-tg-st')['symbols']['boot_extra_hook'][2:]) if tg else bytes.fromhex('4feffff048d700f04ef9400004ba');hits=[]
  for w in e['writes']:
   body=bytes.fromhex(w['new'])
   for i in range(0,len(body)-len(expected)+1,2):
    if body[i:i+len(expected)]==expected:hits.append(w['off']+i)
  assert len(hits)==1,(e['id'],hits)
  engines[e['id']]={'tg':tg,'hook':dict(off=hits[0],old=expected.hex(),new='4ef9401907a4'+'4e71'*((len(expected)-6)//2))}
  if e['id'] in compression:engines[e['id']]['compression']=compression[e['id']]
 for row in rows:
  key=row['key'];v=json.loads((matrix/(key+'.json')).read_text());b=v['bank'];b['id']='midi-bank-bundle';b['flashable']=True;b['pending']=['hardware_verification'];b.pop('prototype_only',None);v['refs']={};v['engine_refs']={}
  for t in [v['core']]+v['supports']+[b]:
   r={'w':digest(t)}
   if t.get('append'):r['p']=hashlib.sha256(build.payload_image(t,bytes.fromhex(t['append']['parts'][0]['hex']))).hexdigest()
   v['refs'][t['id']]=r
  for e in catalog:
   if e['id'] not in engines or engines[e['id']]['tg']!=row['tg']:continue
   alt=copy.deepcopy(b);direct=306 if row['tg'] else 304
   alt['writes']=[w for w in b['writes'] if w['off']!=direct]+[engines[e['id']]['hook']]
   alt['requires']=b['requires']+[e['id']]
   build.apply_writes(stock,[v['core'],e]+v['supports']+[alt])
   v['engine_refs'][e['id']]=digest(alt)
  variants[key]=v
 bundle=(out/'bundle.js').read_text();begin=bundle.index("const uiCore=['model-tg'");end=bundle.index("a.applyLang(document.documentElement.lang||'en');",begin)
 bundle=bundle[:begin]+"// Banque indépendante : aucun groupe forcé.\n"+bundle[end:]
 encoded=compact(variants);assert restore(encoded)==variants
 tail='\n// Banque facultative : backends propres et références générés en Python.\n(()=>{'+JS_DECODER+'const variants=unpackCatalogue('+json.dumps(encoded,separators=(',',':'))+');const engines='+json.dumps(engines,separators=(',',':'))+';\n'
 tail+='''const app=window.MCFlasherApp,tw=window.MC_TWEAKS;
const on=id=>app.isSelected(id);
const key=()=>['model-tg','scale-gen','lfo-secondary','scramble','chord-keys'].map(id=>on(id)?'1':'0').join('');
const cache=new Map();let active=null;
window.MCMidiIndependentResolve=out=>{
 if(!on('midi-bank-bundle')){active=null;return out;}
 const k=key(),engine=out.find(t=>Object.hasOwn(engines,t.id)),id=k+':'+(engine?.id||'');
 let v=cache.get(id);
 if(!v){v=JSON.parse(JSON.stringify(variants[k]));
  if(engine){const e=engines[engine.id];if(e.tg!==(k[0]==='1'))throw Error('MIDI Bank machine backend mismatch');
   const direct=k[0]==='1'?306:304;
   v.bank.writes=v.bank.writes.filter(w=>w.off!==direct).concat([e.hook]);
   v.bank.requires=v.bank.requires.concat([engine.id]);v.refs[v.bank.id].w=v.engine_refs[engine.id];}
  cache.set(id,v);}
 active=v;
 const skip=t=>t.id==='midi-bank-bundle'||t.id==='performance-core'||t.id.startsWith('model-tg')||t.id.startsWith('scale-gen')||t.id.startsWith('scramble')||t.id==='lfo-secondary'||t.id==='chord-keys-supermodel';
 return out.filter(t=>!skip(t)).map(t=>engines[t.id]?.compression?{...t,append:{...t.append,compress_cost:engines[t.id].compression.compress_cost,stored:engines[t.id].compression.stored}}:t).concat([v.core],v.supports,[v.bank]).sort((a,b)=>a.order-b.order);
};
const ids=new Set(Object.values(variants).flatMap(v=>Object.keys(v.refs)).concat(Object.keys(engines).filter(id=>engines[id].compression)));
for(const id of ids){const previous=app.REF_MODS[id]||{},ref={};
 for(const field of ['w','p'])Object.defineProperty(ref,field,{enumerable:true,get:()=>on('midi-bank-bundle')?((active||variants[key()]).refs[id]?.[field]??engines[id]?.compression?.[field]??previous[field]):previous[field]});app.REF_MODS[id]=ref;}
const bank=tw.features.find(f=>f.id==='midi-bank-bundle');bank.requires=null;bank.status='experimental';bank.excludes=['lfo-plus'];
for(const id of ['scale-gen','scramble']){const f=tw.features.find(f=>f.id===id),previous=f.requires;Object.defineProperty(f,'requires',{configurable:true,get:()=>on('midi-bank-bundle')?null:previous});}
for(const k of Object.keys(app.REF_MAINOS))if(k.includes('midi-bank-bundle')||k.includes('performance-core'))delete app.REF_MAINOS[k];
app.applyLang(document.documentElement.lang||'en');
})();
'''
 (out/'bundle.js').write_text(bundle+tail)
 p=out/'app.js';s=p.read_text();old='  return out;\n}\nfunction chosenLabels()';new="  return window.MCMidiIndependentResolve ? window.MCMidiIndependentResolve(out) : out;\n}\nfunction chosenLabels()";assert s.count(old)==1;s=s.replace(old,new).replace('chosenTweaks, chosenLabels, CATS };','chosenTweaks, chosenLabels, CATS, isSelected: isOn };')
 text={'en':{'label':'MIDI OUT Bank — independent test','short':'Parallel six-track MIDI sequencer; Model-TG, Genie, A-side Second LFO and machines are optional.','desc':'Experimental independent support. FUNC + SETTINGS + TRACK enters/exits B-side. SETTINGS + PAGE opens Sequence Genie when selected. SETTINGS + a gray knob chooses its CC; hold a TRIG and turn its knob to lock a value. B-side retains its own two CC LFOs, notes, slides, retrigger, chance and live recording. Data is RAM-only; hardware verification required.','note':'No extra synth machines or support mods are selected automatically. Data does not persist after power-off.'},'fr':{'label':'Banque MIDI OUT — test indépendant','short':'Six séquences MIDI parallèles ; TG, Genie, LFO2 audio et machines facultatifs.','desc':'Support indépendant expérimental. FUNC + SETTINGS + TRACK ouvre/ferme B. SETTINGS + PAGE ouvre Genie si coché. SETTINGS + potentiomètre gris choisit le CC ; tenir un TRIG et tourner son potentiomètre verrouille une valeur. B conserve ses deux LFO CC, notes, slides, retrigger, chance et enregistrement live. Données en RAM ; test matériel requis.','note':'Aucune machine ou mod de support automatiquement coché. Données perdues à extinction.'}}
 at=s.index('window.MCFlasherApp =');s=s[:at]+'for(const L of ["en","fr"])Object.assign(FEAT[L]["midi-bank-bundle"],'+json.dumps(text,ensure_ascii=False)+'[L]);\n'+s[at:];p.write_text(s)
 p=out/'builder.js';s=p.read_text();old="(t.id==='midi-bank-bundle'&&ap.zero_pad_from==='0x401bf8c0'&&end>=0x401bf8c0)";new="(t.id==='midi-bank-bundle'&&ap.at==='0x401f8f76'&&['0x401bf8c0','0x401aa140'].includes(ap.zero_pad_from)&&end>=parseInt(ap.zero_pad_from,16))";assert s.count(old)==1;p.write_text(s.replace(old,new))
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-13-chord-independent-startup',STAMP))
 p=out/'index.html';s=p.read_text().replace('Experimental independent ChordKeys selections. Model-TG, MIDI Bank and extra machines are optional for ChordKeys. Main unchanged. MIDI Bank remains RAM-only.','Experimental independent MIDI Bank selections. Model-TG, Sequence Genie, Second LFO, SCRAMBLE and machines are optional. Main unchanged. MIDI Bank remains RAM-only.').replace('Test ChordKeys indépendant : Model-TG, Banque MIDI et machines facultatifs pour ChordKeys. Flasher principal inchangé. Banque MIDI en RAM.','Test Banque MIDI indépendante : TG, Genie, LFO2, SCRAMBLE et machines facultatifs. Flasher principal inchangé. Banque MIDI en RAM.');p.write_text(s)
 (out/'source/midi-independent-matrix.json').write_text(json.dumps(encoded,indent=1,ensure_ascii=False)+'\n')
 (out/'ABOUT.md').write_text('# Independent MIDI Bank test\n\nExperimental selectable backends. MIDI Bank no longer forces Model-TG, Sequence Genie, Second LFO, SCRAMBLE, Live MIDI OUT+THRU or extra machines. MIDI data is RAM-only. Physical MIDI/USB timing requires hardware verification. Main unchanged.\n\nBackends facultatifs expérimentaux. Banque MIDI sans mods ou machines forcés. Données en RAM. Timing MIDI/USB physique à vérifier. Flasher principal inchangé.\n')
 print('ok : page candidate,',len(variants),'backends,',sum(len(v['engine_refs']) for v in variants.values()),'chaînes moteur vérifiées ; non publiée')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--matrix',required=True);p.add_argument('--catalog',required=True);p.add_argument('--cycles',required=True);p.add_argument('--engine-compression',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();target=pathlib.Path(a.output)
 with tempfile.TemporaryDirectory() as d:
  out=pathlib.Path(d)/'page' if a.check else target
  generate(pathlib.Path(a.base_dir),out,pathlib.Path(a.matrix),json.loads(pathlib.Path(a.catalog).read_text()),load_stock(a.cycles),json.loads(pathlib.Path(a.engine_compression).read_text()))
  if a.check:
   for f in out.rglob('*'):
    if f.is_file():assert f.read_bytes()==(target/f.relative_to(out)).read_bytes(),str(f)

if __name__=='__main__':main()
