/* Livraison Full/Lite : SHA, capacite, bootstrap, metadonnees et texte protege. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),b=require(path.join(site,'builder.js')),f=require(path.join(site,'flasher.js'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex'),meta=JSON.parse(fs.readFileSync(path.join(site,'BUILD.json')));
assert.equal(meta.release,'2.56');assert.deepEqual(Object.keys(meta.editions),['full','lite']);
const pinned={full:'c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6',lite:'df9b8d2241e28df96f81d51b68fba171ac6bd8d09daf70233deb2b7b4d04cd3f'};
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
assert.equal(hash(blurb),'b6ab6a510ac726ddad5f5f53afea3e915ffa14c5813bc6ab8c5712b23e00fa7d');
for(const m of Object.values(meta.editions))for(const v of [m.file,m.syxSha256,m.mainOsSha])assert(loader.includes(v));
for(const p of ['docs/assets/release.js','docs/flasher/midi-machine-release.js'])assert(fs.readFileSync(path.join(root,p),'utf8').includes('"version": "2.56"'));
assert(fs.existsSync(path.join(site,meta.release_notes)));assert(fs.existsSync(path.join(site,'lite.html')));
console.log('PASS Full/Lite metadata, immutable assets, legacy alias, release stamps and unchanged protected blurb');
