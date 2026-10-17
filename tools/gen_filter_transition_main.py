"""Note112 : promotion du filtre confirme, sans aucun outil diagnostic."""
import argparse,hashlib,json,pathlib,re,struct
from gen_filter_precision import generate,ROOT
STAMP='2026-10-17-filter-wizard-main'
JS='''// Note112 : correction confirmee sur appareil ; aucun diagnostic embarque.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCFilterTransition,previous=window.MCMainClearResolve,n=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 const feature=window.MC_TWEAKS.features.find(f=>f.id==='track-filter');feature.status='tested';feature.hardwareTestedByOwner=true;
 a.registerFeatureTexts('track-filter',{en:{label:'Per-track filter',short:'Hardware tested: clean filtering after leaving Sample Wizard.',desc:'Prevents an obsolete second filter pass on added machines after switching away from Sample Wizard. Retains the efficient four-pole filter, cutoff, resonance and neutral bypass. Confirmed on hardware by AveyCole on 17 October 2026.'},fr:{label:'Filtre par piste',short:'Teste sur machine : filtre propre apres Sample Wizard.',desc:'Supprime un ancien second passage filtre sur les machines ajoutees apres sortie de Sample Wizard. Conserve le filtre quatre poles efficace, la coupure, la resonance et le bypass neutre. Confirme sur machine par AveyCole le 17/10/2026.'}});
 window.MCMainClearResolve=input=>previous(input).map(t=>{
  if(!a.isSelected('track-filter'))return t;
  if(t.id==='wizard-continuous-filter')return {...t,status:'tested',hardwareTestedByOwner:true};
  if(t.id!=='sample-wizard')return t;
  const result=JSON.parse(JSON.stringify(t)),f=d.filter,p=result.append.parts.find(p=>p.hex&&n(p.dest)<=f.at&&f.at+f.size<=n(p.dest)+p.hex.length/2);if(!p)throw Error('Filter transition: body missing');
  const i=2*(f.at-n(p.dest));if(hash(b.fromHex(p.hex.slice(i,i+2*f.size)))!==f.old_sha256)throw Error('Filter transition: body guard');p.hex=p.hex.slice(0,i)+f.hex+p.hex.slice(i+2*f.size);
  const c=d.inner_call,q=result.append.parts.find(p=>p.hex&&n(p.dest)<=c.at&&c.at+4<=n(p.dest)+p.hex.length/2);if(!q)throw Error('Filter transition: call missing');const j=2*(c.at-n(q.dest));if(q.hex.slice(j,j+8)!==c.old)throw Error('Filter transition: call guard');q.hex=q.hex.slice(0,j)+c.new+q.hex.slice(j+8);
  delete result.append.compressed_hex;a.REF_MODS[result.id]={w:hash(b.writesBytes(result)),p:hash(b.buildPayload(result.append,null,null))};result.status='tested';result.hardwareTestedByOwner=true;return result;
 });a.applyLang(document.documentElement.lang||'en');
})();
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 filt=generate(ROOT/'tools/machines/track_filter/fast.s');old=json.loads((ROOT/'docs/flasher/filter-load-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'));filt['old_sha256']=hashlib.sha256(bytes.fromhex(old['hex'])).hexdigest();assert 'mode_address' not in filt
 w=json.loads((ROOT/'firmware/wizard-catalogue.json').read_text())['variants']['0']['wizard'];sy={k:int(v,16) for k,v in w['symbols'].items()};at=sy['ah_mid']+6;off=at-int(w['append']['dest'],16);call=bytes.fromhex(w['append']['parts'][0]['hex'])[off:off+4];assert call[:2]==b'\x61\x00' and at+2+struct.unpack('>h',call[2:])[0]==sy['gflt_run']
 data=dict(filter=filt,inner_call=dict(at=at,old=call.hex(),new='4e714e71'))
 files={'filter-transition-data.js':'window.MCFilterTransition='+json.dumps(data,separators=(',',':'))+';\n','filter-transition.js':JS}
 for name,text in files.items():
  target=ROOT/'docs/flasher'/name
  if a.check:assert target.read_text(encoding='utf-8').replace('\r\n','\n')==text,name
  else:target.write_text(text,encoding='utf-8')
 target=ROOT/'docs/flasher/index.html';s=target.read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 if 'src="filter-transition-data.js?' not in s:s=s.replace('</body>',f'<script src="filter-transition-data.js?v={STAMP}"></script><script src="filter-transition.js?v={STAMP}"></script></body>')
 assert not any(x in s for x in ('audio-load-data.js','beat-diagnostic-data.js','diagnostic-release.js'))
 if a.check:assert target.read_text(encoding='utf-8')==s
 else:target.write_text(s,encoding='utf-8')
 print('PASS principal : noyau',filt['code_size'],'octets, appel double retire, aucun diagnostic')
if __name__=='__main__':main()
