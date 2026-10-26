/* Principal 2.51 : l'image servie est exactement le v175 approuve. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site=path.resolve(__dirname,'..','docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const F='99d392585a03a0f94cab0eb76fd1c16def0cc690230e909e821a09e01fa69bee',M='a04f16bf2037166cbab9f7d01d31bb04573bbf5b48c46432e96e69a04ae0e1f5';
const raw=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx')),meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
assert.equal(hash(raw),F);assert.equal(meta.fixed_image_sha256,F);assert.equal(meta.approved_source_sha256,F);assert.equal(meta.main_os_sha256,M);assert.equal(meta.release,'2.51');assert.equal(meta.release_notes,'release-notes-2.51.html');
const fixed=fs.readFileSync(path.join(site,'flasher/fixed-main-image.js'),'utf8');assert(fixed.includes(F)&&fixed.includes(M)&&fixed.includes(meta.stamp));
const idx=fs.readFileSync(path.join(site,'flasher/index.html'),'utf8');assert(idx.includes(`MC_BUILD='${meta.stamp}'`)&&idx.includes('release-notes-2.51.html'));
assert(fs.readFileSync(path.join(site,'assets/release.js'),'utf8').includes('"version": "2.51"'));
assert(fs.readFileSync(path.join(site,'flasher/midi-machine-release.js'),'utf8').includes('"version": "2.51"'));
assert(fs.existsSync(path.join(site,'flasher/release-notes-2.51.html')));
console.log('v175 delivery OK');
