/* Variantes signees : module FX intact, masque exact et deux transports Samples. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const B=require('../docs/flasher/builder.js'),F=require('../docs/flasher/flasher.js'),O=require('../docs/flasher-optional/optional-builder.js');
const [cyclesPath,samplesPath,outDir]=process.argv.slice(2);assert(cyclesPath&&samplesPath&&outDir);
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),dir=path.join(root,'docs/flasher-optional'),context={window:{}};
for(const name of ['recipe.js','editions.js'])vm.runInNewContext(fs.readFileSync(path.join(dir,name),'utf8'),context);
const recipe=context.window.MCOptionalRecipe,editions=context.window.MCOptionalBaseEditions;
const full=fs.readFileSync(path.join(site,editions.full.file)),lite=fs.readFileSync(path.join(site,editions.lite.file)),cycles=fs.readFileSync(cyclesPath),samples=fs.readFileSync(samplesPath),prepared=O.prepare(full,lite,cycles,recipe);
fs.mkdirSync(outDir,{recursive:true});const rows=[];
const original=O.unpack(full).main,end=new DataView(original.buffer,original.byteOffset).getUint32(0x40195ad0-0x40000400,false)-0x40000400;
const moduleOffset=end+0x46900000-0x467ab360,moduleSize=editions.full.per_track_fx_code_bytes;assert(moduleSize>0);
for(const mask of [0,O.ALL,1,1<<(21-6),1<<(17-6),(1<<(14-6))|(1<<(12-6)),O.ALL&~(1<<(21-6)),0x55555]){
 const result=prepared.build(mask),unpacked=O.unpack(result.raw);assert(F.verify(result.raw).count>0);assert(result.flashBytes<=0x1c0000);
 if(mask&&mask!==O.ALL){const variantEnd=new DataView(unpacked.main.buffer,unpacked.main.byteOffset).getUint32(0x40195ad0-0x40000400,false)-0x40000400,offset=variantEnd+0x46900000-0x467ab360;assert.deepEqual(unpacked.main.subarray(offset,offset+moduleSize),original.subarray(moduleOffset,moduleOffset+moduleSize));assert.equal(new DataView(unpacked.main.buffer,unpacked.main.byteOffset).getUint32(recipe.mask_main_offset,false),mask);}
 const name='mask-'+mask.toString(16).padStart(5,'0');fs.writeFileSync(path.join(outDir,name+'.syx'),result.raw);
 for(const mode of ['cycles','samples']){
  const converted=B.modsForSamples(result.raw,cycles,samples,mode),c=O.unpack(converted.raw);assert(F.verify(converted.raw).count>0);assert(c.container.blob.length<=0x1c0000);assert.equal(converted.modsSha,result.mainOsSha);
  fs.writeFileSync(path.join(outDir,name+'-samples-'+mode+'.syx'),converted.raw);
 }
 rows.push({mask,sha256:result.syxSha256,main_sha256:result.mainOsSha,flash_bytes:result.flashBytes,per_track_fx_module_unchanged:true,samples_transports:2});
 console.log('PASS mask',mask.toString(16),'signed image, intact track FX and both Samples transports');
}
for(const mask of [-1,0x80000,1.5,NaN])assert.throws(()=>prepared.build(mask),/Invalid/);
fs.writeFileSync(path.join(outDir,'variants.json'),JSON.stringify({release:editions.full.release,variants:rows,template_mask_literals:prepared.locations,hardware_tested:false},null,2)+'\n');
