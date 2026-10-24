/* Regression des cartouches hors plage ; aucune voix Yamaha dans le depot. */
const fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const L=require('../docs/flasher/legacy-import.js');
function checksum(raw){let sum=0;for(let i=6;i<4102;i++)sum+=raw[i];raw[4102]=(-sum)&127;return raw;}
function blank(){const raw=new Uint8Array(4104);raw.set([240,67,0,9,32,0]);raw[4103]=247;return checksum(raw);}
const clean=blank(),p=L.parse(clean);assert.equal(p.names.length,32);assert.equal(p.adjustments.length,0);assert.deepEqual(p.raw,clean);assert.notEqual(p.raw,clean);
// Tous les octets7bits sont soit preserves, soit bornes dans la voix cible.
for(let at=0;at<128;at++){
 const raw=blank(),slot=6;raw[6+128*slot+at]=127;checksum(raw);const before=new Uint8Array(raw),parsed=L.parse(raw);
 assert.deepEqual(raw,before);assert.equal(L.parse(parsed.raw).adjustments.length,0);
 for(const a of parsed.adjustments)assert.equal(a.slot,7);
 for(let i=0;i<4104;i++)if(parsed.raw[i]!==raw[i])assert(i===4102||(i>=6+128*slot&&i<6+128*(slot+1)));
 const packet=L.packet(raw,3,'Compatibility');assert.equal(packet.length,4121);assert.equal(packet[6],3);assert.equal(packet[0],240);assert.equal(packet[4120],247);
 assert.equal(packet.slice(2,4120).reduce((a,b)=>a+b,0)&127,0);
 assert.deepEqual(packet.slice(23,4119),parsed.raw.slice(6,4102));
}
const bad=blank();bad[10]=1;assert.throws(()=>L.parse(bad),/checksum/);
const high=blank();high[6]=128;checksum(high);assert.throws(()=>L.parse(high),/7-bit/);
assert.throws(()=>L.parse(new Uint8Array(163)),/32-voice/);assert.throws(()=>L.packet(clean,16,'bad'),/1–16/);
if(process.env.MC_TEST_DX7_COMPAT_BANK){
 const raw=fs.readFileSync(process.env.MC_TEST_DX7_COMPAT_BANK),before=Buffer.from(raw),parsed=L.parse(raw);
 assert.equal(parsed.names.length,32);assert.equal(parsed.names[19],'TIMPANI');assert.deepEqual(parsed.adjustments,[{slot:20,field:'operator 2 parameter 6',from:127,to:99}]);
 assert(raw.equals(before));assert.equal(L.parse(parsed.raw).adjustments.length,0);
 const changed=[];for(let i=0;i<raw.length;i++)if(raw[i]!==parsed.raw[i])changed.push(i);
 assert.deepEqual(changed,[6+19*128+4*17+6,4102]);
 const out=path.join(__dirname,'../output/import-check');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'rom3a-packet.bin'),L.packet(raw,0,'ROM3A'));
 console.log('PASS supplied ROM3A: all 32 voices, one TIMPANI correction plus checksum, original unchanged');
}
console.log('PASS all 128 packed offsets, isolated compatibility adjustment, original immutability, checksums and malformed-bank rejection');
