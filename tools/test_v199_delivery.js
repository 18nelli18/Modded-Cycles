/* Principal2.55 : image approuvee199, bornes de chargement et caches coherents. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),b=require(path.join(site,'builder.js')),f=require(path.join(site,'flasher.js'));
const hash=x=>crypto.createHash('sha256').update(x).digest('hex'),meta=JSON.parse(fs.readFileSync(path.join(site,'BUILD.json')));
assert.equal(meta.release,'2.55');assert.equal(meta.fixed_image_sha256,'c37e8a1a97a6849ff094a095caac5de54b39d9cc03ca0e88396b629d17bba05b');
const raw=fs.readFileSync(path.join(site,meta.fixed_image));assert.equal(hash(raw),meta.fixed_image_sha256);assert.equal(hash(fs.readFileSync(path.join(site,meta.fixed_image_legacy))),meta.fixed_image_sha256);
assert.equal(meta.approved_source_sha256,meta.fixed_image_sha256);assert(f.verify(raw).count>0);
const pkg=b.parseContainer(b.unwrap(raw).stream),s=pkg.sections.find(x=>x.id===3),main=b.aplibDepack(pkg.blob.subarray(s.off,s.off+s.size),{bootLayout:true}).data;
assert.equal(hash(main),meta.main_os_sha256);assert(pkg.blob.length<=0x1c0000,'flash capacity regression');
assert(meta.page_warp&&meta.page_length_grid_hidden&&meta.page_warp_hardware_verified);
assert(meta.page_length&&meta.page_length_inactive_steps_dark&&meta.estus_advanced_native_plocks&&meta.samples_bootstrap_layout_guard);
const html=fs.readFileSync(path.join(site,'index.html'),'utf8'),loader=fs.readFileSync(path.join(site,'fixed-main-image.js'),'utf8');
assert(html.includes(`MC_BUILD='${meta.stamp}'`)&&html.includes('release-notes-2.55.html')&&html.includes('builder.js?v='+meta.stamp));
assert(loader.includes(meta.fixed_image_sha256)&&loader.includes(meta.main_os_sha256)&&loader.includes(meta.fixed_image)&&loader.includes(meta.stamp));
for(const p of ['docs/assets/release.js','docs/flasher/midi-machine-release.js'])assert(fs.readFileSync(path.join(root,p),'utf8').includes('"version": "2.55"'));
assert(fs.existsSync(path.join(site,meta.release_notes)));
console.log('PASS v199 delivery: approved bytes, legacy/immutable files, native safe-decompression layout, flash capacity, metadata and cache stamp');
