/* Principal 2.53 : l'image servie est exactement le v189 fourni. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const site=path.resolve(__dirname,'..','docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const F='6a729fbf198b50768ec1bfade96d6627ab11f08cea210f452586927d207a3282',M='69e7ea9c3f7c35e7e22e33d757376bc473370d8a574f72d7afeac17cdcec8626';
const raw=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx')),meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
assert.equal(hash(raw),F);assert.equal(meta.fixed_image_sha256,F);assert.equal(meta.approved_source_sha256,F);assert.equal(meta.main_os_sha256,M);assert.equal(meta.release,'2.53');assert.equal(meta.release_notes,'release-notes-2.53.html');
const fixed=fs.readFileSync(path.join(site,'flasher/fixed-main-image.js'),'utf8');assert(fixed.includes(F)&&fixed.includes(M)&&fixed.includes(meta.stamp));
const idx=fs.readFileSync(path.join(site,'flasher/index.html'),'utf8');assert(idx.includes(`MC_BUILD='${meta.stamp}'`)&&idx.includes('release-notes-2.53.html'));
assert(fs.readFileSync(path.join(site,'assets/release.js'),'utf8').includes('"version": "2.53"'));
assert(fs.readFileSync(path.join(site,'flasher/midi-machine-release.js'),'utf8').includes('"version": "2.53"'));
assert(fs.existsSync(path.join(site,'flasher/release-notes-2.53.html')));
console.log('v189 delivery OK');
