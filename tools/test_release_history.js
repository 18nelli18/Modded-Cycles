/* Historique : vrai rendu partage, deux langues et versions precedentes. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'docs/assets/site.js'),'utf8');
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.attributes={};this.textContent='';}
 appendChild(child){this.children.push(child);return child;}
 append(...children){this.children.push(...children);}
 replaceChildren(){this.children=[];}
 setAttribute(k,v){this.attributes[k]=v;}
 set innerHTML(value){assert.equal(value,'');this.children=[];}
}
const ctx={window:{},document:{createElement:tag=>new Element(tag)},root:{lang:'en'}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'docs/assets/release.js'),'utf8'),ctx);
const history=new Element(),changes=new Element(),version=new Element(),date=new Element();
const elements={'[data-rel=history]':[history],'[data-rel=changes]':[changes],'[data-rel=version]':[version],'[data-rel=date]':[date]};
ctx.$$=selector=>elements[selector]||[];ctx.lang=()=>ctx.root.lang;
const start=source.indexOf('function fmtDate('),end=source.indexOf('\nrenderRelease();',start);
vm.runInContext(source.slice(start,end),ctx);
const releases=ctx.window.MC_RELEASES;assert.equal(releases[0].version,'3.06');assert(releases.some(r=>r.version==='3.02'));
for(const language of ['en','fr']){
 ctx.root.lang=language;ctx.renderRelease();
 assert.equal(version.textContent,'3.06');assert.equal(history.children.length,releases.length);
 assert.equal(history.children[0].open,true);assert(history.children[0].children[0].textContent.startsWith('3.06'));
 assert.equal(history.children[0].children[1].children[0].textContent,releases[0].changes[0][language]);
 assert(history.children.some(section=>section.children[0].textContent.startsWith('3.02')));
 assert.equal(new Set(history.children.map(section=>section.id)).size,releases.length);
}
for(const file of ['docs/index.html','docs/flasher/index.html','docs/flasher-optional/index.html']){
 const html=fs.readFileSync(path.join(root,file),'utf8');assert(html.includes('What changed in this version…'));assert(html.includes('version-history.html'));assert(html.includes('guide306'));
}
console.log('PASS release history: preserved '+releases.length+' entries, current changes, EN/FR render, unique anchors and page links');
