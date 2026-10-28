/* Publication principale : conserver les sources, bases et sorties optionnelles. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),optional=path.join(root,'docs/flasher-optional');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const tree=cp.execFileSync('git',['rev-parse','HEAD:docs/flasher-optional'],{cwd:root,encoding:'utf8'}).trim();
assert.equal(tree,'7017c6bb22ffe31c31bc2aab31569fea1acbccfd');
const context={window:{}};
for(const name of ['editions.js','recipe.js'])vm.runInNewContext(fs.readFileSync(path.join(optional,name),'utf8'),context);
const editions=context.window.MCOptionalBaseEditions;
for(const [id,sha] of Object.entries({full:'c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6',lite:'0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e'}))assert.equal(hash(fs.readFileSync(path.join(site,editions[id].file))),sha);
console.log('PASS optional tree and original Full215/Lite216 assets unchanged');
if(process.argv[2]){
 const O=require(path.join(optional,'optional-builder.js')),F=require(path.join(site,'flasher.js'));
 const full=fs.readFileSync(path.join(site,editions.full.file)),lite=fs.readFileSync(path.join(site,editions.lite.file));
 const prepared=O.prepare(full,lite,fs.readFileSync(process.argv[2]),context.window.MCOptionalRecipe);
 for(const [mask,sha] of [[0,editions.lite.syxSha256],[O.ALL,editions.full.syxSha256]])assert.equal(hash(prepared.build(mask).raw),sha);
 const a=prepared.build(1),b=prepared.build(1);assert.equal(hash(a.raw),hash(b.raw));assert(F.verify(a.raw).count>0);assert(a.flashBytes<=0x1c0000);
 console.log('PASS optional none/all remain exact original images; mixed selection builds with valid packets and capacity');
}
