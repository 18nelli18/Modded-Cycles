/* Vraie page Chromium : fichiers officiels, image verifiee et telechargement exact. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs'),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const expected=fs.readFileSync(path.join(site,'flasher/all-features-usb-2ch-default.syx'));
assert.equal(hash(expected),'5111c5401520856496c9626598b6a10c4929e123052d512cc5384621b8ca73ab','released file must be the approved filter release with DX default Off and LTC/SIL labels');
const meta=JSON.parse(fs.readFileSync(path.join(site,'flasher/BUILD.json')));
const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.pdf':'application/pdf','.syx':'application/octet-stream','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{
 let name=decodeURIComponent(new URL(req.url,'http://localhost').pathname);if(name.endsWith('/'))name+='index.html';
 const file=path.resolve(site,'.'+name);
 if(!file.startsWith(site+path.sep)){res.writeHead(403).end();return;}
 try{res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(fs.readFileSync(file));}
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
    const target=path.join(root,'tmp','main-212-browser-download.syx');await download.saveAs(target);assert.equal(hash(fs.readFileSync(target)),hash(expected));
    const pdf=await context.request.get(new URL('shortcut-guide.pdf?v='+meta.stamp,base).href);assert(pdf.ok());assert.equal(hash(await pdf.body()),hash(fs.readFileSync(path.join(site,'flasher/shortcut-guide.pdf'))));
    console.log('PASS: official OS + required Syntakt upload -> exact 2.12 bytes and valid packets -> exact downloaded file',result.sha);
    console.log('PASS: guide download exact, no USB selector, no automatic hardware transfer');
   }
   assert.deepEqual(errors,[]);await context.close();
  }
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
