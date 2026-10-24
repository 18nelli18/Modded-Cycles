/* Vraie page Chromium : fichiers officiels, image verifiee et telechargement exact. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const expected=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx'));
assert.equal(hash(expected),'bb566c59d353fb11ac2f7edce74723d7fba5346e2934bb8f5ea4210cee405e4c','released file must be the approved regular shared-filter v94');
const meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
assert.equal(meta.cloud,false);assert.equal(meta.ps1_reverb,true);assert(!meta.delay_modes.includes('CLOUD'));assert(meta.chorus_modes.includes('PS1'));assert.equal(meta.speak_words,128);assert.equal(meta.combined_fx_modes,false);assert.deepEqual(meta.shimmer_modes,[]);assert.deepEqual(meta.delay_modes,['PHASER','DUCK','DUB','PING PONG','DELAY','CRUSH 1','CRUSH 2']);

const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.pdf':'application/pdf','.syx':'application/octet-stream','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{
 let name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);if(name.endsWith('/'))name+='index.html';
 const file=path.resolve(site,'.'+name);
 if(!file.startsWith(site+path.sep)){res.writeHead(403).end();return;}
 try{const data=fs.readFileSync(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(data);}
 catch(e){res.writeHead(404).end();}
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const base=process.env.TEST_LIVE_URL||`http://127.0.0.1:${server.address().port}/flasher/`;
 const browser=await chromium.launch({executablePath:process.env.TEST_BROWSER_PATH||(process.platform==='win32'?'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe':chromium.executablePath()),headless:true});
 try{
  for(const corrupt of [false,true]){
   const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(String(e)));
   if(corrupt)await page.route('**/all-features-usb-2ch-default.syx?*',async route=>{
    const bad=Buffer.from(expected);bad[1000]^=1;await route.fulfill({body:bad,contentType:'application/octet-stream'});
   });
   await page.goto(base+'?v='+meta.stamp,{waitUntil:'load'});
   await page.waitForFunction(()=>!!window.MCFlasherApp&&!!window.MCFixedMainImageReady);
   await page.evaluate(async()=>await Promise.all(Object.keys(window).filter(k=>k.endsWith('Ready')&&window[k]?.then).map(k=>window[k])));
   assert.match(await page.locator('#credits').innerText(),/Glycinate/,'Feral author credit missing');
   assert.match(await page.locator('#credits-list').innerText(),/PPPCCC/);assert.equal(await page.locator('#credits-list a[href="https://github.com/18nelli18/Modded-Cycles"]').count(),1);
   assert(await page.locator('a[href="release-notes-2.34.html"]').count()>0,'release notes link missing');
   assert.equal(await page.locator('#fixed-six-usb').count(),0,'web USB build selector returned');
   assert.equal(await page.locator('a[href^="shortcut-guide.pdf"]').count(),1,'one canonical PDF guide link required');
   await page.setInputFiles('#file',path.join(root,'firmware/model-cycles_OS1.13.syx'));
   await page.waitForFunction(()=>!!window.MCFlasherApp.state.os);
   assert.equal(await page.evaluate(()=>window.MCFlasherApp.state.fwError),'needs_syntakt');
   assert.equal(await page.locator('#drop3-wrap').isVisible(),true,'Syntakt file request missing');
   await page.setInputFiles('#file3',path.join(root,'firmware/Syntakt_OS1.42.syx'));
   await page.waitForFunction(()=>{const s=window.MCFlasherApp.state;return s.syntakt&&!s.building&&(s.fw||s.fwError&&s.fwError!=='needs_syntakt');},{timeout:60000});
   const result=await page.evaluate(()=>{
    const a=window.MCFlasherApp,s=a.state;
    return {error:s.fwError,sha:s.fw&&window.MCBuilder.hex(window.MCBuilder.sha256(s.fw.raw)),main:s.fw?.sha,packets:s.fw&&window.MCFlasher.verify(s.fw.raw).count,disabled:document.getElementById('flash').disabled};
   });
   if(corrupt){assert.match(result.error,/checksum mismatch/);assert(!result.sha);console.log('PASS: mismatching firmware is rejected, no fallback composition');}
   else{
    assert.equal(result.sha,hash(expected));assert.equal(result.sha,meta.fixed_image_sha256);assert.equal(result.main,meta.main_os_sha256);assert(result.packets>0);assert(result.disabled);
    const downloaded=page.waitForEvent('download');await page.locator('#download').click({force:true});const download=await downloaded;
    const target=path.join(root,'tmp','main-233-browser-download.syx');await download.saveAs(target);assert.equal(hash(fs.readFileSync(target)),hash(expected));
    const pdf=await context.request.get(new URL('shortcut-guide.pdf?v='+meta.stamp,base).href);assert(pdf.ok());assert.equal(hash(await pdf.body()),hash(fs.readFileSync(path.join(site,'flasher/shortcut-guide.pdf'))));
    console.log('PASS: official OS + required Syntakt upload -> exact 2.33 bytes and valid packets -> exact downloaded file',result.sha);
    console.log('PASS: guide download exact, no USB selector, no automatic hardware transfer');
   }
   assert.deepEqual(errors,[]);await context.close();
  }
  const notes=await browser.newPage();
  await notes.goto(new URL('release-notes-2.34.html',base).href,{waitUntil:'load'});
  const text=await notes.locator('main').innerText();
  for(const term of ['GATED','HALL','LEGACY','PS1','Pre-delay'])assert(text.includes(term),term);
  assert.doesNotMatch(text,/machinedrum|f card|card graphic/i);
  assert.equal(await notes.locator('h1 [data-l="en"]').isVisible(),true);
  await notes.locator('[data-lang="fr"]').click();
  assert.equal(await notes.locator('h1 [data-l="fr"]').isVisible(),true);
  assert.equal(await notes.locator('h1 [data-l="en"]').isVisible(),false);
  const mainLink=notes.locator('main a').last();await mainLink.click();
  await notes.waitForFunction(()=>!!window.MCFlasherApp);
  console.log('PASS: linked 2.34 release notes, EN/FR switch, Glycinate credit and return to main');
  await notes.close();
  const guide=await browser.newPage();
  await guide.goto(new URL('shortcut-guide.html?v='+meta.stamp,base).href,{waitUntil:'load'});
  for(const width of [1100,390]){
   await guide.setViewportSize({width,height:1000});
   for(const lang of ['en','fr']){
    await guide.locator('[data-lang="'+lang+'"]').click();
    const article=guide.locator('article[data-l="'+lang+'"]');assert(await article.isVisible());
    const words=await article.innerText();for(const term of ['Elder','Chorus','Crush','Vinyl','Rate','Bits','Glycinate','Fors','PING PONG','SPEAK','FUTURE','PS1'])assert(words.includes(term),term);
    assert.equal(await article.locator('tbody tr').count(),96);
    assert(await guide.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'guide horizontal overflow');
   }
  }
  await guide.close();
  console.log('PASS: current EN/FR shortcut guide,controls and all 128 words, desktop/mobile without clipping');

 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
