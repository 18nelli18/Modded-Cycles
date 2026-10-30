/* Recette MD : donnees locales, masques, signatures et recovery conserve. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const B=require('../docs/flasher/builder.js'),F=require('../docs/flasher/flasher.js'),O=require('../docs/flasher-optional/optional-builder.js'),M=require('../docs/flasher-optional/machinedrum-builder.js');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'docs/flasher-optional'),ctx={window:{}};
for(const name of ['recipe.js','editions.js','machinedrum-data.js'])vm.runInNewContext(fs.readFileSync(path.join(dir,name),'utf8'),ctx);
const recipe=ctx.window.MCOptionalMDData,selection=ctx.window.MCOptionalRecipe,editions=ctx.window.MCOptionalBaseEditions;
const [cyclesFile,mdFile,out]=process.argv.slice(2);assert(cyclesFile&&mdFile&&out);fs.mkdirSync(out,{recursive:true});
const full=fs.readFileSync(path.join(root,'docs/flasher',editions.full.file)),cycles=fs.readFileSync(cyclesFile),md=fs.readFileSync(mdFile);
const original=O.unpack(full),rows=[];
for(const mask of [0x80000,0x100000,0x200000,0x380000,0x3fffff]){
 const result=M.build(full,cycles,md,mask,recipe,selection),parsed=O.unpack(result.raw);
 assert(F.verify(result.raw).count>0);assert(result.flashBytes<=0x1c0000);assert.equal(result.release,'2.62');
 for(const s of original.container.sections){if(s.id===3)continue;const n=parsed.container.sections.find(n=>n.id===s.id);assert.deepEqual(parsed.container.blob.slice(n.off,n.off+n.size),original.container.blob.slice(s.off,s.off+s.size));}
 fs.writeFileSync(path.join(out,'mask-'+mask.toString(16)+'.syx'),result.raw);
 rows.push({mask,sha256:result.syxSha256,main_sha256:result.mainOsSha,flash_bytes:result.flashBytes,release:result.release});console.log('PASS MD mask',mask.toString(16),result.flashBytes,'flash bytes',result.syxSha256);
}
assert.throws(()=>M.build(full,cycles,new Uint8Array(64),0x80000,recipe,selection),/Machinedrum/);
for(const mask of [-1,0x400000,0.5,NaN])assert.throws(()=>M.validateMask(mask));
fs.writeFileSync(path.join(out,'variants.json'),JSON.stringify({release:'2.62',variants:rows,hardware_tested:false},null,2)+'\n');
