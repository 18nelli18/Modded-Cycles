/* Les bases Optional sont versionnees et gardent leurs choix supplementaires. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),optional=path.join(root,'docs/flasher-optional');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const metadata=JSON.parse(fs.readFileSync(path.join(optional,'BUILD.json')));
assert.equal(metadata.release,'2.58');assert(metadata.per_track_fx);
assert.deepEqual(metadata.retained_extra_choices,['LEGACY','ChordKeys','Vinyl']);
const context={window:{}};
for(const name of ['editions.js','recipe.js'])vm.runInNewContext(fs.readFileSync(path.join(optional,name),'utf8'),context);
const editions=context.window.MCOptionalBaseEditions;
for(const [id,entry] of Object.entries(editions)){
 assert.equal(hash(fs.readFileSync(path.join(site,entry.file))),entry.syxSha256);
 assert.equal(entry.startup_title.version,metadata.release);assert(entry.per_track_fx);
 assert.equal(entry.legacy_removed,false);assert.equal(entry.chordkeys_removed,false);assert.equal(entry.vinyl_removed,false);
}
console.log('PASS Optional2.58 has per-track FX and retains its extra choices');
if(process.argv[2]){
 const O=require(path.join(optional,'optional-builder.js')),F=require(path.join(site,'flasher.js'));
 const full=fs.readFileSync(path.join(site,editions.full.file)),lite=fs.readFileSync(path.join(site,editions.lite.file));
 const prepared=O.prepare(full,lite,fs.readFileSync(process.argv[2]),context.window.MCOptionalRecipe);
 for(const [mask,sha] of [[0,editions.lite.syxSha256],[O.ALL,editions.full.syxSha256]])assert.equal(hash(prepared.build(mask).raw),sha);
 const a=prepared.build(1),b=prepared.build(1);assert.equal(hash(a.raw),hash(b.raw));assert(F.verify(a.raw).count>0);assert(a.flashBytes<=0x1c0000);
 console.log('PASS Optional none/all are exact updated bases; mixed selection has valid packets and capacity');
}
