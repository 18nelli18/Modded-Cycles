"""Note116 : ne jamais executer le code save dans l'etat vivant de ChordKeys."""
import argparse,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
JS='''// Note116 : le masque40187528 contient live/prepared_modifiers ChordKeys, pas un cave.
(()=>{const b=window.MCBuilder,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));window.MCQuickSaveRoomReady=(window.MCArpZeroReady||window.MCMidiCursorReady).then(()=>{const previous=window.MCMidiBankCompose;window.MCMidiBankCompose=(...args)=>{const prior=previous(...args);if(!prior.tweaks.some(t=>t.id==='quick-save-exit'))return prior;const r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}},q=r.tweaks.find(t=>t.id==='quick-save-exit'),owner=r.tweaks.find(t=>t.id==='control-all-beat-repeat');if(!owner)throw Error('Quick-save room test: select Control All Beat Repeat');const ptr=q.writes.find(w=>w.off===0x40100c44-0x40000400),code=q.writes.find(w=>w.off===0x40187528-0x40000400);if(q.writes.length!==3||!ptr||ptr.new!=='40187528'||!code||code.new.length!==184)throw Error('Quick-save room: layout guard');const at=(n(owner.append.dest)+owner.append.size+15)&~15;owner.append.parts.push({dest:'0x'+h(at),hex:code.new});owner.append.size=at+code.new.length/2-n(owner.append.dest);q.writes=[{...ptr,new:h(at)}];q.symbols.qs_exit='0x'+h(at);owner.symbols.qs_exit='0x'+h(at);const loader=owner.writes.find(w=>w.off+0x40000400===window.MCBeatRepeat.boot.at),raw=b.fromHex(loader.new);new DataView(raw.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,owner.append.size,false);loader.new=b.hex(raw);const c=b.parseContainer(b.unwrap(args[1]).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;r.refMods[q.id]={w:hash(b.writesBytes(q))};r.refMods[owner.id]={w:hash(b.writesBytes(owner)),p:hash(b.buildPayload(owner.append,args[2],stock))};return r;};});})();
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 for folder,stamp in [('flasher-midi-entry-test','2026-10-17-midi-entry-test-4'),('flasher-arp-zero-test','2026-10-17-arp-zero-test-2')]:
  d=ROOT/'docs'/folder;s=(d/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',stamp,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{stamp}'",s)
  if 'src="quick-save-room.js?' not in s:s=s.replace('</body>',f'<script src="quick-save-room.js?v={stamp}"></script></body>')
  for name,text in {'quick-save-room.js':JS,'index.html':s}.items():
   if a.check:assert (d/name).read_text(encoding='utf-8')==text,name
   else:(d/name).write_text(text,encoding='utf-8')
 print('PASS test relocation save ; donnees ChordKeys preservees')
if __name__=='__main__':main()
