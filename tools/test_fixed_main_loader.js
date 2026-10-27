/* Charger le vrai v189, simuler ancien cache/corruption/panne, garder le SHA. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/flasher'),builder=require(path.join(site,'builder.js')),flasher=require(path.join(site,'flasher.js'));
const meta=JSON.parse(fs.readFileSync(path.join(site,'BUILD.json'))),raw=new Uint8Array(fs.readFileSync(path.join(site,meta.fixed_image)));
const code=fs.readFileSync(path.join(site,'fixed-main-image.js'),'utf8'),bad=raw.slice();bad[100]^=1;
async function scenario(responses){
 const calls=[];const win={location:{href:'https://aveycole.github.io/Modded-Cycles/flasher/'},MCBuilder:builder,MCFlasher:flasher};
 vm.runInNewContext(code,{window:win,URL,Uint8Array,fetch:async(url,options)=>{calls.push({url,options});const r=responses.shift();if(r instanceof Error)throw r;if(!r)return {ok:false};return {ok:true,arrayBuffer:async()=>r.slice().buffer};}});
 return {win,calls};
}
(async()=>{
 assert.equal(builder.hex(builder.sha256(raw)),meta.fixed_image_sha256);assert(flasher.verify(raw).count>0);
 let x=await scenario([raw]);let got=await x.win.MCFixedMainImageReady;assert.equal(builder.hex(builder.sha256(got)),meta.fixed_image_sha256);assert.equal(x.calls.length,1);assert(x.calls[0].url.endsWith(meta.fixed_image));assert.equal(x.calls[0].options.cache,'no-store');
 const app=fs.readFileSync(path.join(site,'app.js'),'utf8'),make=app.match(/const makeFixed = \(\) => [\s\S]*?\n    \}\);/);assert(make);
 const appContext={window:x.win,meta:x.win.MCFixedMainImageMeta,release:'2.53'};vm.runInNewContext(make[0]+'\nglobalThis.prepared=makeFixed();',appContext);const prepared=await appContext.prepared;assert.equal(prepared.name,'Supermodel_2.53.syx');assert.equal(builder.hex(builder.sha256(prepared.raw)),meta.fixed_image_sha256);
 got[100]^=1;got=await x.win.MCFixedMainImageLoad();assert.equal(builder.hex(builder.sha256(got)),meta.fixed_image_sha256);assert.equal(x.calls.length,1);
 x=await scenario([bad,raw]);got=await x.win.MCFixedMainImageReady;assert.equal(builder.hex(builder.sha256(got)),meta.fixed_image_sha256);assert.equal(x.calls.length,2);assert(x.calls[1].url.includes('/89557e1/'));
 x=await scenario([null,raw]);await x.win.MCFixedMainImageReady;assert.equal(x.calls.length,2);
 x=await scenario([bad,bad]);await assert.rejects(x.win.MCFixedMainImageReady,/checksum mismatch/);assert.equal(x.calls.length,2);
 x=await scenario([new Error('offline'),new Error('offline'),raw]);await assert.rejects(x.win.MCFixedMainImageReady,/offline/);got=await x.win.MCFixedMainImageLoad();assert.equal(builder.hex(builder.sha256(got)),meta.fixed_image_sha256);
 console.log('PASS exact v189: immutable URL, stale/corrupt/404 fallback, corrupt-both rejection, retry after failure, independent buffers and SysEx packets');
})().catch(e=>{console.error(e);process.exitCode=1;});
