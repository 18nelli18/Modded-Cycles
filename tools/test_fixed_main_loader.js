/* Deux editions : panne, cache obsolete, mauvais profil et copie defensive. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),builder=require(path.join(site,'builder.js')),flasher=require(path.join(site,'flasher.js'));
const meta=JSON.parse(fs.readFileSync(path.join(site,'BUILD.json'))),raw=Object.fromEntries(Object.entries(meta.editions).map(([id,m])=>[id,new Uint8Array(fs.readFileSync(path.join(site,m.file)))]));
const code=fs.readFileSync(path.join(site,'fixed-main-image.js'),'utf8'),app=fs.readFileSync(path.join(site,'app.js'),'utf8'),make=app.match(/const makeFixed = \(\) => [\s\S]*?\n    \}\);/);assert(make);
async function scenario(responses){
 const calls=[];const win={location:{href:'https://aveycole.github.io/Modded-Cycles/flasher/'},MCBuilder:builder,MCFlasher:flasher};
 vm.runInNewContext(code,{window:win,URL,Uint8Array,fetch:async(url,options)=>{calls.push({url,options});const r=responses.shift();if(r instanceof Error)throw r;if(!r)return {ok:false};return {ok:true,arrayBuffer:async()=>r.slice().buffer};}});
 return {win,calls};
}
(async()=>{
 for(const edition of ['full','lite']){
  const m=meta.editions[edition],r=raw[edition],bad=r.slice();bad[100]^=1;
  const run=async(responses)=>{const x=await scenario(edition==='lite'?[raw.full,...responses]:responses);if(edition==='lite')await x.win.MCFixedMainImageReady;return x;};
  let x=await run([r]);let got=await x.win.MCFirmwareImageLoad(edition);assert.equal(builder.hex(builder.sha256(got)),m.syxSha256);
  assert(x.calls.every(c=>c.options.cache==='no-store'));assert(x.calls.at(-1).url.endsWith(m.file));
  const ctx={window:x.win,meta:x.win.MCFirmwareImages[edition],edition,release:meta.release};vm.runInNewContext(make[0]+'\nglobalThis.prepared=makeFixed();',ctx);const prepared=await ctx.prepared;assert.equal(prepared.name,`Supermodel_${edition==='lite'?'Lite_':''}${meta.release}.syx`);assert.equal(builder.hex(builder.sha256(prepared.raw)),m.syxSha256);
  const count=x.calls.length;got[100]^=1;got=await x.win.MCFirmwareImageLoad(edition);assert.equal(builder.hex(builder.sha256(got)),m.syxSha256);assert.equal(x.calls.length,count);
  x=await run([bad,r]);await x.win.MCFirmwareImageLoad(edition);assert(x.calls.at(-1).url.includes('/'+meta.delivery_source_commit+'/'));
  x=await run([null,r]);await x.win.MCFirmwareImageLoad(edition);
  x=await run([bad,bad]);await assert.rejects(x.win.MCFirmwareImageLoad(edition),/checksum mismatch/);
  x=await run([new Error('offline'),new Error('offline'),r]);await assert.rejects(x.win.MCFirmwareImageLoad(edition),/offline/);got=await x.win.MCFirmwareImageLoad(edition);assert.equal(builder.hex(builder.sha256(got)),m.syxSha256);
  x=await run([raw[edition==='full'?'lite':'full'],raw[edition==='full'?'lite':'full']]);await assert.rejects(x.win.MCFirmwareImageLoad(edition),/checksum mismatch/);
  console.log('PASS',edition,'immutable loader, stale/corrupt/404 fallback, failure retry, wrong-edition rejection, defensive copies and actual app download');
 }
 const x=await scenario([raw.full,raw.lite]);await x.win.MCFixedMainImageReady;await x.win.MCFirmwareImageLoad('lite');await x.win.MCFirmwareImageLoad('full');await x.win.MCFirmwareImageLoad('lite');assert.equal(x.calls.length,2);await assert.rejects(x.win.MCFirmwareImageLoad('unknown'),/Unknown/);
 console.log('PASS editions have independent caches and invalid edition rejected');
})().catch(e=>{console.error(e);process.exitCode=1;});
