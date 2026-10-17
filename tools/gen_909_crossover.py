"""Note117 : mises a jour croisees du principal1.83, profil909 conserve."""
import argparse,json,pathlib,re,subprocess
import html
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASELINE='41fa13db315fd80cac29ab224c12a0c0a26e9d36'
STAMP='2026-10-17-909-arp-both'
PATCH='''// Note117 : reperer les copies Wizard dans le payload merge, puis appliquer les correctifs gardes.
(()=>{const b=window.MCBuilder,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
if(!window.MC909CurrentData.features.includes('arp'))window.MC909CurrentData.features.push('arp');
window.MC909CrossoverReady=window.MC909CurrentReady.then(()=>{
 if(!window.MC909CurrentLabels.includes('Arpeggiator A + B'))window.MC909CurrentLabels.push('Arpeggiator A + B');
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  const bank=r.tweaks.find(t=>t.id==='midi-out-bank');if(!bank)throw Error('909 crossover: MIDI bank missing');
  function locate(at,len){
   const find=(x,size=len)=>bank.append.parts.find(p=>p.hex&&n(p.dest)<=x&&x+size<=n(p.dest)+p.hex.length/2);
   let p=find(at);if(p)return [p,at-n(p.dest)];
   const stage=n(bank.symbols.midi_current_stage),part=find(stage,1),offset=stage-n(part.dest)+window.MCMidiCurrent.boot.symbols.midi_current_copies,raw=b.fromHex(part.hex),v=new DataView(raw.buffer);
   for(let k=0;k<8;k++){const src=v.getUint32(offset+12*k,false),dest=v.getUint32(offset+12*k+4,false),words=v.getUint32(offset+12*k+8,false);if(!src)break;if(dest<=at&&at+len<=dest+4*words){const moved=src+at-dest;p=find(moved);if(p)return [p,moved-n(p.dest)];}}
   throw Error('909 crossover: mapped Wizard code missing '+at.toString(16));
  }
  const q=window.MCQuickSave,[qp,qi]=locate(q.at,q.size);if(qp.hex.slice(2*qi,2*(qi+q.size))!==q.old)throw Error('909 crossover: quick-save body guard');qp.hex=qp.hex.slice(0,2*qi)+q.hex+qp.hex.slice(2*(qi+q.size));
  const d=window.MCFilterTransition,f=d.filter,[fp,fi]=locate(f.at,f.size),old=fp.hex.slice(2*fi,2*(fi+f.size)),digest=hash(b.fromHex(old));
  if(digest!==f.old_sha256)throw Error('909 crossover: filter body guard '+digest);
  fp.hex=fp.hex.slice(0,2*fi)+f.hex+fp.hex.slice(2*(fi+f.size));
  const c=d.inner_call,[cp,ci]=locate(c.at,4);if(cp.hex.slice(2*ci,2*ci+8)!==c.old)throw Error('909 crossover: inner filter call guard');cp.hex=cp.hex.slice(0,2*ci)+c.new+cp.hex.slice(2*ci+8);
  delete bank.append.compressed_hex;delete bank.append.stored;
  const container=b.parseContainer(b.unwrap(args[1]).stream),section=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(section.off,section.off+section.size)).data;
  r.refMods[bank.id]={w:hash(b.writesBytes(bank)),p:hash(b.buildPayload(bank.append,args[2],stock))};
  const repeat=r.tweaks.find(t=>t.id==='control-all-beat-repeat');if(repeat){const source=n(bank.append.at)+b.buildPayload(bank.append,args[2],stock).length;repeat.append.at='0x'+h(source);const w=repeat.writes.find(w=>w.off+0x40000400===window.MCBeatRepeat.boot.at),raw=b.fromHex(w.new);new DataView(raw.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,source,false);w.new=b.hex(raw);r.refMods[repeat.id]={w:hash(b.writesBytes(repeat)),p:hash(b.buildPayload(repeat.append,args[2],stock))};}
  return r;
 };
__PERFORMANCE__
});})();
'''
def inline(s):
 s=html.escape(s,quote=False);s=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',s);return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
def render(s):
 """Tables et titres des references, sans dependance Markdown externe."""
 out=[];table=False
 for line in s.splitlines():
  if line.startswith('|'):
   if re.fullmatch(r'[|:\- ]+',line):continue
   cells=[x.strip() for x in line.strip('|').split('|')];tag='td' if table else 'th'
   if not table:out.append('<div class="table-wrap"><table>');table=True
   out.append('<tr>'+''.join(f'<{tag}>{inline(c)}</{tag}>' for c in cells)+'</tr>');continue
  if table:out.append('</table></div>');table=False
  if not line.strip():continue
  m=re.match(r'^(#{1,3}) (.+)',line)
  out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>' if m else '<p>'+inline(line)+'</p>')
 if table:out.append('</table></div>')
 return '\n'.join(out)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'docs/flasher-supermodel-909';main=ROOT/'docs/flasher'
 names=['filter-transition-data.js','quick-save-data.js','quick-save-exit-data.js','midi-cursor-data.js','arp-zero-data.js','no-midi-capacity.js','preview-chord.js','quick-reference.md','quick-reference-fr.md','shortcut-guide.html']
 files={name:(main/name).read_text(encoding='utf-8') for name in names}
 # Le profil909 ne comprend pas les banques de machines du principal.
 for lang,name in [('en','quick-reference.md'),('fr','quick-reference-fr.md')]:
  text=files[name];start='## Performance and sound' if lang=='en' else '## Performance et son';end='## Hardware-confirmed changes' if lang=='en' else '## Changements confirmés';text=text[text.index(start):text.index(end)]
  text='\n'.join(line for line in text.splitlines() if not re.match(r'\| (?:MACRO lo-fi|Lo-fi MACRO|ChordKeys) \|',line))
  text=text.replace('Arpeggiator / ChordKeys settings','A/B arpeggiator settings').replace('Access the added direction/octave or ChordKeys options, according to the installed feature.','On either side, set arp direction and Oct0–3. Oct0 uses only held notes.').replace('Arpeggiator performance','A/B arpeggiator performance').replace('Arpege / reglages ChordKeys','Reglages arpege A/B').replace('Options ajoutees direction/octaves ou ChordKeys selon la fonction installee.','Cotes A et B : direction et Oct0–3 ; Oct0 joue seulement les notes tenues.').replace('Jeu de l arpege','Jeu de l arpege A/B')
  if lang=='en':intro='# Supermodel 909 — feature and shortcut overview\n\n909.4 · 17 October 2026\n\nFixed 909 Edition: six 909 voices, Sample Wizard, ACID, per-track filter, slide trigs, Sequence Genie, SCRAMBLE, Second LFO, MIDI Out Bank with saving, combined MIDI OUT + THRU, latching mute, Control All Config, Control All Beat Repeat, A/B arpeggiators and 909 startup. Load official Cycles OS1.13 and four local WAVs for closed/open hats, crash and ride. No sample audio is hosted.\n\nShared features match main1.83: the filter transition repair, stock permanent save (hold FUNC + SETTINGS), A/B Oct0, first-entry B playback and one recording cursor. Each MIDI lane keeps its length and speed. Main hardware-confirmed fixes; 909 integration checked in emulation. No diagnostic display in this release.\n\nStop before saving MIDI and wait for MIDI SAVED. Saved MIDI loads only when entering B-side with playback stopped; sidecar files are outside Elektron SysEx backups.\n\nAdded shortcuts below; stock-style transport/copy/clear/paste omitted. TRIG = step key, pad = track pad, DATA = LEVEL/DATA.\n\n'
  else:intro='# Supermodel 909 — fonctions et raccourcis\n\n909.4 · 17 octobre 2026\n\nProfil fixe909 : six voix909, Sample Wizard, ACID, filtre par piste, slides, Sequence Genie, SCRAMBLE, Second LFO, Banque MIDI avec sauvegarde, MIDI OUT + THRU, mutes verrouilles, Control All Config, Control All Beat Repeat, arpegiateurs A/B et demarrage909. Charger OS Cycles1.13 officiel et quatre WAV locaux : hats ferme/ouvert, crash et ride. Aucun sample audio heberge.\n\nFonctions partagees alignees sur main1.83 : correction transition filtre, sauvegarde permanente stock (tenir FUNC + SETTINGS), Oct0 A/B, premiere entree B en lecture et curseur REC unique. Chaque voie MIDI garde longueur et vitesse. Corrections main confirmees sur machine ; integration909 verifiee en emulation. Aucun affichage diagnostic dans cette version.\n\nArreter avant sauvegarde MIDI et attendre MIDI SAVED. Le MIDI sauvegarde charge uniquement en entrant B, lecture arretee ; fichiers annexes hors backups SysEx Elektron.\n\nRaccourcis ajoutes ci-dessous ; transports/copies/effacements/collages stock omis. TRIG = pas, pad = piste, DATA = LEVEL/DATA.\n\n'
  files[name]=intro+text+'\n'
 prefix=(main/'shortcut-guide.html').read_text(encoding='utf-8').split('<main>',1)[0].replace('Feature and shortcut overview — Supermodel','Feature and shortcut overview — Supermodel 909')
 files['shortcut-guide.html']=prefix+'<main>'+''.join('<article data-l="'+lang+'">'+render(files[name])+'</article>' for lang,name in [('en','quick-reference.md'),('fr','quick-reference-fr.md')])+'</main></html>\n'
 files['guide.html']=files['shortcut-guide.html']
 files['909-crossover.js']=PATCH.replace('__PERFORMANCE__',(main/'performance-release.js').read_text(encoding='utf-8'))
 s=subprocess.check_output(['git','show',BASELINE+':docs/flasher-supermodel-909/index.html'],cwd=ROOT).decode('utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 head,tail=s.split('<section',1);head=re.sub(r'<p\b(?=[^>]*class="alert")[^>]*>.*?</p>','',head,flags=re.S);s=head+'<section'+tail;s=s.replace('href="../flasher/shortcut-guide.html"','href="shortcut-guide.html"')
 scripts=['filter-transition-data.js','quick-save-data.js','quick-save-exit-data.js','midi-cursor-data.js','arp-zero-data.js','909-crossover.js'];s=s.replace('</body>',''.join(f'<script src="{name}?v={STAMP}"></script>' for name in scripts)+'</body>')
 link='<p class="quick-reference"><a href="shortcut-guide.html?v='+STAMP+'"><span data-l="en">Updated feature and shortcut overview</span><span data-l="fr">Fonctions et raccourcis actualises</span></a></p>'
 s=s.replace('<div id="errbar"',link+'<div id="errbar"',1);s=s.replace('Hardware tested</span><span data-l="fr">Teste sur machine','909 kit hardware tested · shared features from main1.83</span><span data-l="fr">Kit909 teste sur machine · fonctions partagees de main1.83');files['index.html']=s
 files['909-release.js']='window.MC_RELEASES='+json.dumps([dict(version='909.4',date='2026-10-17',changes=[dict(en='Adds the A-side arpeggiator: Oct0 now works on both A and B. Retains main1.83 filter, quick-save and MIDI entry/cursor repairs. Keeps the six 909 voices, four local WAVs, Sample Wizard and existing feature set. No diagnostics.',fr='Ajoute l arpegiateur A : Oct0 fonctionne desormais sur A et B. Conserve les corrections filtre, sauvegarde et entree/curseur MIDI de main1.83. Six voix909, quatre WAV locaux, Sample Wizard et fonctions existantes conserves. Aucun diagnostic.')])],ensure_ascii=False)+';\n'
 meta=json.loads(subprocess.check_output(['git','show',BASELINE+':docs/flasher-supermodel-909/BUILD.json'],cwd=ROOT));meta.update(shared_features_main_version='1.83',shared_features_updated='2026-10-17',diagnostics=False,arpeggiator_sides=['A','B'],hardware_tested_version='909.2',shared_feature_port_validation='emulation; source fixes hardware-confirmed in main1.83');files['BUILD.json']=json.dumps(meta,indent=2)+'\n'
 files['ABOUT.md']='Supermodel 909 909.4: shared features updated to main1.83. Existing hardware-tested six-voice 909 profile and four local WAV inputs preserved. Main hardware-confirmed filter, quick-save and MIDI entry/cursor/Oct0 repairs integrated; 909 combination verified in emulation. No diagnostics, firmware or audio hosted.\n'
 for name,text in files.items():
  p=out/name
  if a.check:assert p.read_text(encoding='utf-8').replace('\r\n','\n')==text.replace('\r\n','\n'),name
  else:p.write_text(text,encoding='utf-8')
 print('PASS 909 crossover : profil fixe conserve, modules main1.83, sans diagnostics')
if __name__=='__main__':main()
