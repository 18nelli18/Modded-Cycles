"""Test séparé : nouvelle option Genie, autres pages et main inchangés."""
import pathlib,shutil,json,hashlib
from midi_catalog_compact import compact,JS_DECODER
P=pathlib.Path('work/genie-queue-choice');out=P/'page';shutil.copytree('work/sample-wizard-options-page',out,dirs_exist_ok=True)
recipes=json.load(open(P/'recipes.json'));refs=json.load(open(P/'refs.json'));original=json.load(open(P/'base.json'));changes=[dict(off=w['off'],was=next(o['new'] for o in original['writes'] if o['off']==w['off']),now=w['new'],guard=w['old']) for w in recipes['wizard']['writes'] if any(o['off']==w['off'] and o['new']!=w['new'] for o in original['writes'])]
(out/'queue-choice.js').write_text('window.MCGenieQueueChoice=(function(){'+JS_DECODER+'return unpackCatalogue('+json.dumps(compact(dict(recipes=recipes,refs=refs,changes=changes)),separators=(',',':'))+');})();\n'+'''(()=>{
 const a=window.MCFlasherApp,c=window.MCGenieQueueChoice,old=window.MCMainClearResolve,prior={...a.REF_MODS},cache=new Map();
 const hex=b=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join(''),hash=t=>hex(window.MCBuilder.sha256(window.MCBuilder.writesBytes(t)));
 window.MCMainClearResolve=out=>old(out).map(t=>{
  if(!a.isSelected('scale-gen')||!t.symbols?.sg_q_hook)return t;
  const ref=prior[t.id];if(!ref||hash(t)!==ref.w)throw Error('Genie queue: original reference mismatch');
  const key=ref.w,hit=cache.get(key);let r;
  if(hit)r=hit;else{
   r=JSON.parse(JSON.stringify(t));
   for(const ch of c.changes){
    const w=r.writes.find(w=>w.off<=ch.off&&ch.off+ch.was.length/2<=w.off+w.new.length/2);if(!w)throw Error('Genie queue: missing guarded range');
    const i=(ch.off-w.off)*2;const extension=ch.now.startsWith(ch.was)&&ch.now.length>ch.was.length; if(w.new.slice(i,i+ch.was.length)!==ch.was&&!extension)throw Error('Genie queue: code guard mismatch');
    if(ch.now.length>ch.was.length&&i+ch.was.length!==w.new.length)throw Error('Genie queue: unsafe extension');
    w.new=w.new.slice(0,i)+(extension?w.new.slice(i,i+ch.was.length)+ch.now.slice(ch.was.length):ch.now)+w.new.slice(i+ch.was.length);
    if(ch.now.length>ch.was.length)w.old+=ch.guard.slice(ch.was.length);
   }
   for(let i=0;i<r.writes.length;i++)for(let j=i+1;j<r.writes.length;j++){const x=r.writes[i],y=r.writes[j];if(x.off<y.off+y.new.length/2&&y.off<x.off+x.new.length/2)throw Error('Genie queue: overlapping extension');}
   r.status='experimental';cache.set(key,r);
  }
  a.REF_MODS[t.id]={w:hash(r),...(ref.p?{p:ref.p}:{})};return r;
 });
 const f=window.MC_TWEAKS.features.find(f=>f.id==='scale-gen');if(f)f.status='experimental';
 a.applyLang(document.documentElement.lang||'en');
})();''')
p=out/'app.js';s=p.read_text();needle="GUIDE_OF['sample-wizard']='sample-wizard';";extra='''
FEAT.en['scale-gen'].short='Generate notes now, or queue them for the next page / full loop.';
FEAT.en['scale-gen'].desc='SETTINGS + PAGE opens Sequence Genie. Generate is the first row; Queue at is directly beneath it. Click DATA to edit Queue at, turn to choose Loop (default) or Page, then click to finish. Loop waits for the selected track to wrap to step 1. Page waits for the next 16-step boundary (17, 33, 49, or step 1). Viewing another page does not trigger it. Stopped generation remains immediate. Works on stock and Sample Wizard tracks; Wizard keeps its sample and playback mode.';
FEAT.fr['scale-gen'].short='Génération immédiate ou différée à la prochaine page / boucle entière.';
FEAT.fr['scale-gen'].desc='SETTINGS + PAGE ouvre Genie. Generate est en première ligne, Queue at juste dessous. Cliquer DATA, choisir Loop (défaut) ou Page, puis confirmer. Loop attend le retour au pas 1 de la piste choisie ; Page attend le prochain début de page (17, 33, 49 ou 1). Changer la page affichée ne déclenche rien. À l’arrêt, génération immédiate. Compatible stock et Wizard ; sample et mode conservés.';
''';assert needle in s;s=s.replace(needle,needle+extra);p.write_text(s)
p=out/'index.html';s=p.read_text().replace('2026-10-15-wizard-selectable-options-2','2026-10-15-genie-queue-page-loop');start=s.index('<p class="alert">');end=s.index('</p>',start)+4;s=s[:start]+'''<p class="alert"><span data-l="en"><strong>Sequence Genie: Queue at Page / Loop — experimental hardware test.</strong> Select Sequence Generator, optionally Sample Wizard and your other features. SETTINGS + PAGE → Queue at (below Generate): click DATA, choose Page or Loop, click to finish. Main and the previous test remain unchanged.</span><span data-l="fr"><strong>Sequence Genie : Queue at Page / Loop — test matériel expérimental.</strong> Choisir le générateur, Wizard et les autres fonctions souhaitées. SETTINGS + PAGE → Queue at, sous Generate : cliquer DATA, choisir Page ou Loop, confirmer. Main et le test précédent restent inchangés.</span></p>'''+s[end:];s=s.replace('</body>','<script src="queue-choice.js?v=2026-10-15-genie-queue-page-loop"></script></body>');p.write_text(s)
source=out/'source/queue-choice';source.mkdir(parents=True,exist_ok=True)
for name in ['choice.s','generate.py','test-native.py','page.py']:shutil.copy(P/name,source/name)
(source/'README.md').write_text('Experimental Queue at selector. Loop (default) commits before selected-track step 1; Page also permits 17/33/49. Native phase/timing/snapshot validation and atomic commit remain intact. Uses four verified free tails of existing redirected Genie masks, without enlarging the sampler or changing startup. New code is not hardware tested.\n')
files=[]
for e in json.load(open('work/sample-wizard-options/publish-files.json')):
 p=out/pathlib.Path(e['local']).relative_to('work/sample-wizard-options-page');b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-genie-queue-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
for p in [out/'queue-choice.js',*source.iterdir()]:
 b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-genie-queue-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
(P/'publish-files.json').write_text(json.dumps(files));print('Prepared',len(files),'test-only files')
