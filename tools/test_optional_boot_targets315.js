/* Regression : vraies images Optional signees, trampoline WAVE avant/apres. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),opt=path.join(root,'docs/flasher-optional'),site=path.join(root,'docs/flasher');
const O=require('../docs/flasher-optional/optional-builder.js'),F=require('../docs/flasher/flasher.js'),B=require('../docs/flasher/builder.js');
const [cyclesFile,out]=process.argv.slice(2);assert(cyclesFile&&out);fs.mkdirSync(out,{recursive:true});
const ctx={window:{}};for(const file of ['recipe.js','editions.js','machinedrum-data.js'])vm.runInNewContext(fs.readFileSync(path.join(opt,file),'utf8'),ctx);
const fixed=ctx.window.MCOptionalRecipe,md=ctx.window.MCOptionalMDData,ed=ctx.window.MCOptionalBaseEditions;
for(const [name,patches] of [['optional',fixed.patches],['MD',md.clean_patches]]){
 let count=0;for(const p of patches){assert(!p.new.includes('4ef9467a9a96'),name+' stale staging continuation');if(p.new.includes('0c80000000054ef9401bf4d6'))count++;}assert.equal(count,1,name);
}
const broken=JSON.parse(JSON.stringify(fixed));let changes=0;
for(const p of broken.patches)if(p.new.includes('0c80000000054ef9401bf4d6')){p.new=p.new.replace('0c80000000054ef9401bf4d6','0c80000000054ef9467a9a96');changes++;}assert.equal(changes,1);
const full=fs.readFileSync(path.join(site,ed.full.file)),lite=fs.readFileSync(path.join(site,ed.lite.file)),cycles=fs.readFileSync(cyclesFile),original=O.unpack(full);
for(const [label,recipe] of [['before',broken],['after',fixed]]){
 const result=O.prepare(full,lite,cycles,recipe).build(0x47ffff),u=O.unpack(result.raw),state=O.clean.view(u.main),old=recipe.symbols.old_wave_predicate;
 assert.deepEqual(Buffer.from(state.read(old,6)),Buffer.from('0c8000000005','hex'));
 assert.deepEqual(Buffer.from(state.read(old+6,6)),Buffer.from(label==='before'?'4ef9467a9a96':'4ef9401bf4d6','hex'));
 // Sans MD, le predicat resident reste natif ; MD installe son gate ici.
 assert.deepEqual(Buffer.from(state.read(0x401bf4d0,6)),Buffer.from('0c8000000005','hex'));
 assert(F.verify(result.raw).count>0);assert(result.flashBytes<=0x1c0000);
 for(const s of original.container.sections){if(s.id===3)continue;const t=u.container.sections.find(t=>t.id===s.id);assert.deepEqual(Buffer.from(u.container.blob.slice(t.off,t.off+t.size)),Buffer.from(original.container.blob.slice(s.off,s.off+s.size)));}
 const folder=path.join(out,label);fs.mkdirSync(folder,{recursive:true});fs.writeFileSync(path.join(folder,'Optional_3.01_All_Choices_'+label+'.syx'),result.raw);
 const meta=JSON.parse(fs.readFileSync(path.join(root,'../release301/final/optional/full/BUILD.json')));meta.sha256=result.syxSha256;meta.main_os_sha256=result.mainOsSha;meta.optional_boot_test={label,mask:0x47ffff,symbols:recipe.symbols,hardware_tested:false};fs.writeFileSync(path.join(folder,'BUILD.json'),JSON.stringify(meta,null,2)+'\n');
 console.log('PASS actual browser Optional',label,'signature/recovery; WAVE target',state.read(old+8,4),result.syxSha256);
}
console.log('PASS both Optional and MD recipes contain the resident continuation; old failure image retained for native regression');
