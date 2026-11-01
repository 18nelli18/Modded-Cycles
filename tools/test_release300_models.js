/* Parite de livraison Cycles/Samples : MAIN identique hors32octets cles natifs. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const B=require('../docs/flasher/builder.js'),F=require('../docs/flasher/flasher.js');
const [cyclesPath,samplesPath,outDir]=process.argv.slice(2),cycles=fs.readFileSync(cyclesPath),samples=fs.readFileSync(samplesPath);
fs.mkdirSync(outDir,{recursive:true});const rows=[];
const base=process.argv[5]||path.resolve(outDir,'../filter');
const inputs=[['main-full','main/full'],['main-lite','main/lite'],['optional-full','optional/full'],['optional-lite','optional/lite']].map(([n,p])=>[n,path.join(base,p,process.argv[6]||'Supermodel_3.00_Filter_Regression_Experimental.syx')]);
for(const [name,file] of inputs){
 const raw=fs.readFileSync(file),u=B.unwrap(raw),c=B.parseContainer(u.stream),sec=c.sections.find(s=>s.id===3),before=B.aplibDepack(c.blob.subarray(sec.off,sec.off+sec.size),{bootLayout:true}).data;
 for(const mode of ['cycles','samples']){
  const r=B.modsForSamples(raw,cycles,samples,mode),u=B.unwrap(r.raw),c=B.parseContainer(u.stream),s=c.sections.find(s=>s.id===3),after=B.aplibDepack(c.blob.subarray(s.off,s.off+s.size),{bootLayout:true}).data;
  const refRaw=samples,refU=B.unwrap(refRaw),ref=B.parseContainer(refU.stream);
  for(const section of c.sections.filter(x=>x.id!==3)){const expected=ref.sections.find(x=>x.id===section.id);assert(expected);assert.deepEqual(c.blob.subarray(section.off,section.off+section.size),ref.blob.subarray(expected.off,expected.off+expected.size),'native bootstrap/updater changed');}
  assert.equal(after.length,before.length);let changes=0;for(let i=0;i<before.length;i++)if(before[i]!==after[i]){assert(i>=0x401296b2-B.BASE&&i<0x401296b2-B.BASE+32);changes++;}
  assert(changes>0);assert.equal(B.invalidMessages(r.raw).length,0);assert(F.verify(r.raw).count>0);assert(c.blob.length<=0x1c0000);
  rows.push({name,mode,changedMainBytes:changes,sha:B.hex(B.sha256(r.raw)),flash:c.blob.length});console.log('PASS Samples transport',name,mode,c.blob.length);
 }
}
fs.writeFileSync(path.join(outDir,'proof.json'),JSON.stringify({release:'3.00',hardware_tested:false,rows},null,2)+'\n');
