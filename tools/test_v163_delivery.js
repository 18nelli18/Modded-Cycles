/* Principal 2.49 : l'image servie est exactement le v163 approuve. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site=path.resolve(__dirname,'..','docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const F='952b5b70dc095e3e68a68df0562d08fa300f4eca48775439d4a776f04e7d222f',M='4ac6a3c4cb0712e2a2bf80d17a8bc1b5c36326df02286c6860048eb7c133b410';
const raw=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx')),meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
assert.equal(hash(raw),F);assert.equal(meta.fixed_image_sha256,F);assert.equal(meta.approved_source_sha256,F);assert.equal(meta.main_os_sha256,M);assert.equal(meta.release,'2.49');assert.equal(meta.release_notes,'release-notes-2.49.html');
const fixed=fs.readFileSync(path.join(site,'flasher/fixed-main-image.js'),'utf8');assert(fixed.includes(F)&&fixed.includes(M)&&fixed.includes(meta.stamp));
const idx=fs.readFileSync(path.join(site,'flasher/index.html'),'utf8');assert(idx.includes(`MC_BUILD='${meta.stamp}'`)&&idx.includes('release-notes-2.49.html'));
assert(fs.readFileSync(path.join(site,'assets/release.js'),'utf8').includes('"version": "2.49"'));
assert(fs.readFileSync(path.join(site,'flasher/midi-machine-release.js'),'utf8').includes('"version": "2.49"'));
assert(fs.existsSync(path.join(site,'flasher/release-notes-2.49.html')));
console.log('v163 delivery OK');
