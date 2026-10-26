/* Principal 2.50 : l'image servie est exactement le v164 approuve. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site=path.resolve(__dirname,'..','docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const F='b5afb6e34b0fcaa0f1b32536781ce132a7228c965f7132a85e203d181d6326a0',M='47fe78cc738784f0719cc48d7358518ac4d0b5683b57f7d3cd28450077e1b7ce';
const raw=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx')),meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
assert.equal(hash(raw),F);assert.equal(meta.fixed_image_sha256,F);assert.equal(meta.approved_source_sha256,F);assert.equal(meta.main_os_sha256,M);assert.equal(meta.release,'2.50');assert.equal(meta.release_notes,'release-notes-2.50.html');
const fixed=fs.readFileSync(path.join(site,'flasher/fixed-main-image.js'),'utf8');assert(fixed.includes(F)&&fixed.includes(M)&&fixed.includes(meta.stamp));
const idx=fs.readFileSync(path.join(site,'flasher/index.html'),'utf8');assert(idx.includes(`MC_BUILD='${meta.stamp}'`)&&idx.includes('release-notes-2.50.html'));
assert(fs.readFileSync(path.join(site,'assets/release.js'),'utf8').includes('"version": "2.50"'));
assert(fs.readFileSync(path.join(site,'flasher/midi-machine-release.js'),'utf8').includes('"version": "2.50"'));
assert(fs.existsSync(path.join(site,'flasher/release-notes-2.50.html')));
console.log('v164 delivery OK');
