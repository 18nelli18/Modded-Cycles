/* Principal approuve sur Samples : deux transports, layout, HMAC et sections. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const b=require('../docs/flasher/builder.js');
const [cyclesPath,samplesPath,outDir]=process.argv.slice(2);
assert(cyclesPath&&samplesPath&&outDir,'cycles.syx samples.syx output-directory');
const root=path.resolve(__dirname,'..'),meta=JSON.parse(fs.readFileSync(path.join(root,'docs/flasher/BUILD.json')));
const fixed=fs.readFileSync(path.join(root,'docs/flasher',meta.fixed_image)),cycles=fs.readFileSync(cyclesPath),samples=fs.readFileSync(samplesPath);
assert.equal(b.hex(b.sha256(samples)),'e11859b68deb7e5e3fe86ab32581212093849c4be5d3950add011eac398a2ce8');
assert.equal(b.hex(b.sha256(fixed)),meta.fixed_image_sha256);
function unpack(raw){const u=b.unwrap(raw),c=b.parseContainer(u.stream);return {u,c,section:id=>{const s=c.sections.find(x=>x.id===id);return c.blob.subarray(s.off,s.off+s.size);}};}
const official=unpack(samples),original=unpack(fixed),originalMain=b.aplibDepack(original.section(3)).data;
assert(b.BASE+originalMain.length>0x40200000,'reproduire exactement la grande image');
fs.mkdirSync(outDir,{recursive:true});let prior;
for(const mode of ['cycles','samples']){
 const result=b.modsForSamples(fixed,cycles,samples,mode),out=unpack(result.raw),main=b.aplibDepack(out.section(3),{bootLayout:true}).data;
 assert.equal(out.u.product,mode==='cycles'?0x11:0x0f);assert.equal(result.raw[8],mode==='cycles'?0x0c:0x0a);
 assert.equal(result.modsSha,meta.main_os_sha256);assert.equal(main.length,originalMain.length);assert(out.c.blob.length<=0x1c0000);
 for(const s of official.c.sections)if(s.id!==3)assert.deepEqual(out.section(s.id),official.section(s.id));
 const changes=[];for(let i=0;i<main.length;i++)if(main[i]!==originalMain[i])changes.push(i);
 assert(changes.length>0&&changes.every(i=>i>=0x401296b2-b.BASE&&i<0x401296b2-b.BASE+32));
 if(prior)assert.deepEqual(out.c.blob,prior);prior=out.c.blob;
 fs.writeFileSync(path.join(outDir,`fixed-main-for-samples-${mode}.syx`),result.raw);
 console.log('PASS',mode,'transport; unchanged Samples bootstrap/updater; only32 key bytes differ; HMAC/content/packet reread; safe bootstrap layout;',main.length,'MAIN bytes,',out.c.blob.length,'flash bytes');
}
// Une vraie collision avec l'entree non lue reste refusee, meme valide en aPLib.
const packed=b.aplibPack(new Uint8Array(0x240000)),unsafe=new Uint8Array(packed.length+8);unsafe.set(packed,8);
fs.writeFileSync(path.join(outDir,'unsafe-bootstrap.aplib'),unsafe);
assert.equal(b.aplibDepack(unsafe).data.length,0x240000);
assert.throws(()=>b.aplibDepack(unsafe,{bootLayout:true}),/bootstrap/);
console.log('PASS oversized highly-compressed image rejected when output would overwrite unread bootstrap source');
// Executer aussi le branchement reel de prepareFirmware pour les deux choix UI.
(async()=>{
 const vm=require('node:vm'),app=fs.readFileSync(path.join(root,'docs/flasher/app.js'),'utf8');
 const prepare=app.slice(app.indexOf('function prepareFirmware() {'),app.indexOf('// Model:Samples OS in the Model:Cycles container'));
 for(const machine of ['cos','smp']){
  let pending;const st={mode:'mods',machine,os:{stock:true,raw:cycles,sha:b.hex(b.sha256(cycles))},syntakt:{version:'1.42'},samplesOs:{raw:samples,sha:b.hex(b.sha256(samples))}};
  const context={st,dropOrphans:()=>{},onSamples:()=>true,log:()=>{},window:{MCBuilder:b,MCFlasher:require('../docs/flasher/flasher.js'),MC_RELEASES:[{version:meta.release}],MCFixedMainImageMeta:{syxSha256:meta.fixed_image_sha256,mainOsSha:meta.main_os_sha256},MCFixedMainImageReady:Promise.resolve(fixed),MCFixedMainImageLoad:async()=>new Uint8Array(fixed)},buildCached:(key,make)=>{pending=make(cycles);}};
  vm.runInNewContext(prepare+'\nprepareFirmware();',context);const fw=await pending;
  assert.equal(fw.machine,machine);assert.equal(unpack(fw.raw).u.product,machine==='cos'?0x11:0x0f);assert(fw.name.includes('for-samples_'));
  console.log('PASS actual prepareFirmware branch:',machine==='cos'?'Model:Samples already on Cycles OS':'Model:Samples on its own OS');
 }
})().catch(e=>{console.error(e);process.exitCode=1;});
