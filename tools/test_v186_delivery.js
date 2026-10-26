/* Principal 2.52 : l'image servie est exactement le v186 fourni. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site=path.resolve(__dirname,'..','docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const F='5ec78631f29a4ffcaedac2d940eb6c7d87fa28de1b231e974c8e27f90704c4cb',M='6be17c5d328fc87ffed9b585df853410ef0976a18ffee97d9f958a91983518d3';
const raw=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx')),meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
assert.equal(hash(raw),F);assert.equal(meta.fixed_image_sha256,F);assert.equal(meta.approved_source_sha256,F);assert.equal(meta.main_os_sha256,M);assert.equal(meta.release,'2.52');assert.equal(meta.release_notes,'release-notes-2.52.html');
const fixed=fs.readFileSync(path.join(site,'flasher/fixed-main-image.js'),'utf8');assert(fixed.includes(F)&&fixed.includes(M)&&fixed.includes(meta.stamp));
const idx=fs.readFileSync(path.join(site,'flasher/index.html'),'utf8');assert(idx.includes(`MC_BUILD='${meta.stamp}'`)&&idx.includes('release-notes-2.52.html'));
assert(fs.readFileSync(path.join(site,'assets/release.js'),'utf8').includes('"version": "2.52"'));
assert(fs.readFileSync(path.join(site,'flasher/midi-machine-release.js'),'utf8').includes('"version": "2.52"'));
assert(fs.existsSync(path.join(site,'flasher/release-notes-2.52.html')));
console.log('v186 delivery OK');
