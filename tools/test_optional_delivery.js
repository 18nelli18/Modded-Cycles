/* Livraison optionnelle : risques visibles, descriptions, pins et code propres. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'docs/flasher-optional'),B=require('../docs/flasher/builder.js'),O=require('../docs/flasher-optional/optional-builder.js');
const run=name=>{const context={window:{}};vm.runInNewContext(fs.readFileSync(path.join(dir,name),'utf8'),context);return context.window};
const recipe=run('recipe.js').MCOptionalRecipe,editions=run('editions.js').MCOptionalBaseEditions,descriptions=run('machine-descriptions.js').MCOptionalDescriptions;
const html=fs.readFileSync(path.join(dir,'index.html'),'utf8'),main=fs.readFileSync(path.join(root,'docs/flasher/index.html'),'utf8');
assert(main.includes('id="optional-flasher-link"')&&main.includes('href="../flasher-optional/"'));
assert(html.includes('Only some combinations have been tested on hardware. Use this version at your own risk.'));
assert(html.includes('Seules certaines combinaisons ont été testées sur matériel. Utilisez cette version à vos risques et périls.'));
assert(html.includes('<base href="../flasher/">'));assert(!html.includes('../../../machine-optional/'));
assert.equal(Object.keys(descriptions).length,19);for(const d of Object.values(descriptions))assert(d.en.length>20&&d.fr.length>20);
assert.equal(editions.full.syxSha256,'c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6');assert.equal(editions.lite.syxSha256,'0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e');
const [cycles]=process.argv.slice(2);assert(cycles,'official Cycles OS 1.13 path required');
const prepared=O.prepare(fs.readFileSync(path.join(root,'docs/flasher',editions.full.file)),fs.readFileSync(path.join(root,'docs/flasher',editions.lite.file)),fs.readFileSync(cycles),recipe);
for(const mask of [0,0x40001,0x7ffff]){const result=prepared.build(mask);assert.equal(B.hex(B.sha256(result.raw)),mask===0?editions.lite.syxSha256:mask===0x7ffff?editions.full.syxSha256:result.syxSha256);assert(result.flashBytes<=0x1c0000);}
console.log('PASS public optional link, bilingual hardware-risk text, 19 machine descriptions, exact pins and actual exported builder');
