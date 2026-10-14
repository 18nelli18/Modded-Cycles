// Compression au chargement seulement ; recettes et hashes, aucun OS exporté.
const fs=require('fs'),assert=require('assert'),path=require('path');
const args=process.argv.slice(2),opt=(name,fallback)=>args.includes(name)?args[args.indexOf(name)+1]:fallback;
const M=require(path.resolve(opt('--builder','work/chord-independent-test/builder.js')));
const os=Uint8Array.from(fs.readFileSync(opt('--cycles','firmware/model-cycles_OS1.13.syx'))),st=Uint8Array.from(fs.readFileSync(opt('--syntakt','firmware/Syntakt_OS1.42.syx')));
const c=M.parseContainer(M.unwrap(os).stream),section=c.sections.find(s=>s.id===3),stock=M.aplibDepack(c.blob.slice(section.off,section.off+section.size)).data;
const cat=JSON.parse(fs.readFileSync(opt('--catalog','work/optional-all-catalog.json'))),rows={};
for(const t of cat){if(!t.append||!t.id.includes('-tg')||!t.id.includes('macro-acid')||t.append.compress!=='aplib')continue;
 const ap={...t.append,compress_cost:512},old=M.buildPayload(t.append,st,stock),packed=M.buildPayload(ap,st,stock);
 const unpack=x=>M.aplibDepack(Uint8Array.from([...new Uint8Array(8),...x])).data;
 assert.deepEqual(unpack(old),unpack(packed));assert(packed.length<=0x401f8f76-0x401bf8c0,t.id+' cannot fit');
 rows[t.id]={compress_cost:512,p:M.hex(M.sha256(packed)),stored:packed.length};console.log('PASS',t.id,old.length,'->',packed.length);
}
const output=opt('--output','work/midi-independent-engine-compression.json'),text=JSON.stringify(rows,null,1);
if(args.includes('--check'))assert.equal(fs.readFileSync(output,'utf8'),text);else fs.writeFileSync(output,text);
