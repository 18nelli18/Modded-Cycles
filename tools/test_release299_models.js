/* Parite de livraison Cycles/Samples : MAIN identique hors32octets cles natifs. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const B=require('../docs/flasher/builder.js'),F=require('../docs/flasher/flasher.js');
const [cyclesPath,samplesPath,outDir]=process.argv.slice(2),cycles=fs.readFileSync(cyclesPath),samples=fs.readFileSync(samplesPath);
const root=path.resolve(__dirname,'..'),main=JSON.parse(fs.readFileSync(path.join(root,'docs/flasher/BUILD.json'))),opt=JSON.parse(fs.readFileSync(path.join(root,'docs/flasher-optional/BUILD.json')));
fs.mkdirSync(outDir,{recursive:true});const rows=[];
const inputs=[...Object.entries(main.editions).map(([k,v])=>['main-'+k,path.join(root,'docs/flasher',v.file)]),...Object.entries(opt.base_editions).map(([k,v])=>['optional-'+k,path.join(root,'docs/flasher',v.file)])];
for(const f of ['opt-mask-1.syx','opt-mask-55555.syx','md-mask-3fffff.syx'])inputs.push([path.basename(f,'.syx'),path.resolve(root,'../release299/delivery',f)]);
for(const [name,file] of inputs){
 const raw=fs.readFileSync(file),u=B.unwrap(raw),c=B.parseContainer(u.stream),sec=c.sections.find(s=>s.id===3),before=B.aplibDepack(c.blob.subarray(sec.off,sec.off+sec.size),{bootLayout:true}).data;
 for(const mode of ['cycles','samples']){
  const r=B.modsForSamples(raw,cycles,samples,mode),u=B.unwrap(r.raw),c=B.parseContainer(u.stream),s=c.sections.find(s=>s.id===3),after=B.aplibDepack(c.blob.subarray(s.off,s.off+s.size),{bootLayout:true}).data;
  assert.equal(after.length,before.length);let changes=0;for(let i=0;i<before.length;i++)if(before[i]!==after[i]){assert(i>=0x401296b2-B.BASE&&i<0x401296b2-B.BASE+32);changes++;}
  assert(changes>0);assert.equal(B.invalidMessages(r.raw).length,0);assert(F.verify(r.raw).count>0);assert(c.blob.length<=0x1c0000);
  rows.push({name,mode,changedMainBytes:changes,sha:B.hex(B.sha256(r.raw)),flash:c.blob.length});console.log('PASS model delivery',name,mode,c.blob.length);
 }
}
fs.writeFileSync(path.join(outDir,'proof.json'),JSON.stringify({release:'2.99',hardware_tested:false,rows},null,2)+'\n');
