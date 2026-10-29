/* Livraison Full/Lite : SHA, capacite, bootstrap, metadonnees et texte protege. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),b=require(path.join(site,'builder.js')),f=require(path.join(site,'flasher.js'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex'),meta=JSON.parse(fs.readFileSync(path.join(site,'BUILD.json')));
assert.equal(meta.release,'2.57');assert.deepEqual(Object.keys(meta.editions),['full','lite']);
const pinned={full:'c7f9ca5765910ed6f3276664f71540c93d307572ca018318596ff6f2155fcc9b',lite:'4bc535b78454601abd66352a9e4e78b52ae637eb64aec786ce9159ac07d02488'};
for(const [id,m] of Object.entries(meta.editions)){
 const raw=fs.readFileSync(path.join(site,m.file));assert.equal(hash(raw),pinned[id]);assert.equal(hash(raw),m.syxSha256);assert(f.verify(raw).count>0);
 const pkg=b.parseContainer(b.unwrap(raw).stream),s=pkg.sections.find(x=>x.id===3),main=b.aplibDepack(pkg.blob.subarray(s.off,s.off+s.size),{bootLayout:true}).data;
 assert.equal(hash(main),m.mainOsSha);assert(pkg.blob.length<=0x1c0000,'flash capacity regression');assert(m.new_clear_filter_defaults);assert.equal(m.ui_idle_saves,true);assert.equal(m.release,meta.release);assert.equal(m.requiresSyntakt,id==='full');
 console.log('PASS',id,'approved image, packets, exact MAIN, safe native bootstrap layout and flash capacity',pkg.blob.length);
}
assert.equal(hash(fs.readFileSync(path.join(site,meta.fixed_image_legacy))),meta.fixed_image_sha256);
assert.equal(meta.editions.full.syxSha256,meta.fixed_image_sha256);assert.equal(meta.editions.full.mainOsSha,meta.main_os_sha256);
const html=fs.readFileSync(path.join(site,'index.html'),'utf8'),loader=fs.readFileSync(path.join(site,'fixed-main-image.js'),'utf8');
assert(html.includes(`MC_BUILD='${meta.stamp}'`)&&html.includes(meta.release_notes)&&html.includes('builder.js?v='+meta.stamp));
const blurb=html.slice(html.indexOf('<div class="fixed-features">'),html.indexOf('<div class="super-toolbar">'));
assert.equal(hash(blurb),'0427d0a2b828f098b818ebce1507e9ad5076f21e24bd8fcb078602c11fbd00a4');
for(const m of Object.values(meta.editions))for(const v of [m.file,m.syxSha256,m.mainOsSha])assert(loader.includes(v));
for(const p of ['docs/assets/release.js','docs/flasher/midi-machine-release.js'])assert(fs.readFileSync(path.join(root,p),'utf8').includes('"version": "2.57"'));
assert(fs.existsSync(path.join(site,meta.release_notes)));assert(fs.existsSync(path.join(site,'lite.html')));
console.log('PASS Full/Lite metadata, immutable assets, legacy alias, release stamps and approved cleaned description');
