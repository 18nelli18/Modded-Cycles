/* Vrai navigateur :22choix, fichier MD local, verrou et pins2.62 des variantes. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),docs=path.join(root,'docs'),[cycles,md,out]=process.argv.slice(2);assert(cycles&&md&&out);fs.mkdirSync(out,{recursive:true});
(async()=>{
 const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://localhost'),file=path.resolve(docs,'.'+decodeURIComponent(u.pathname)+(u.pathname.endsWith('/')?'index.html':''));if(!file.startsWith(docs+path.sep)){res.writeHead(403).end();return}fs.readFile(file,(e,data)=>{if(e){res.writeHead(404).end();return}res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.syx':'application/octet-stream'})[path.extname(file)]||'application/octet-stream');res.end(data)})});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{
  browser=await chromium.launch({headless:true,executablePath:process.env.EDGE_BINARY||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const page=await browser.newPage({viewport:{width:1280,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{navigator.requestMIDIAccess=async()=>({inputs:new Map(),outputs:new Map(),addEventListener(){}});localStorage.setItem('mc-lang','en')});
  await page.goto('http://127.0.0.1:'+server.address().port+'/flasher-optional/');await page.waitForFunction(()=>window.MCOptionalUI&&window.MCFlasherApp);
  assert.equal(await page.locator('#optional-grid input').count(),22);assert.equal(await page.locator('#optional-grid input:checked').count(),19);
  await page.locator('#file').setInputFiles(cycles);await page.waitForFunction(()=>MCOptionalUI.result?.mask===0x7ffff&&!MCOptionalBusy,{},{timeout:90000});
  await page.locator('#optional-all').click();await page.waitForFunction(()=>!!MCOptionalFailed);assert.equal(await page.evaluate(()=>MCOptionalUI.result),null);
  await page.locator('#optional-md-file').setInputFiles(md);await page.waitForFunction(()=>MCOptionalUI.result?.mask===0x3fffff&&!MCOptionalBusy,{},{timeout:120000});
  assert.equal(await page.evaluate(()=>MCFirmwareImages.full.startup_title.version),'2.62');assert.equal(await page.evaluate(()=>MCOptionalUI.result.machinedrum),true);
  await page.screenshot({path:path.join(out,'all-22.png'),fullPage:true});
  await page.locator('#optional-none').click();await page.waitForFunction(()=>MCOptionalUI.result?.mask===0&&!MCOptionalBusy);
  assert.equal(await page.evaluate(()=>MCOptionalUI.result.syxSha256===MCOptionalBaseEditions.lite.syxSha256),true);
  await page.locator('#optional-grid input[data-machine="25"]').check();await page.waitForFunction(()=>MCOptionalUI.result?.mask===0x80000&&!MCOptionalBusy,{},{timeout:120000});
  assert.equal(await page.locator('#optional-grid input:checked').count(),1);
  await page.locator('#optional-md-file').setInputFiles({name:'invalid.syx',mimeType:'application/octet-stream',buffer:Buffer.alloc(64)});await page.waitForFunction(()=>!!MCOptionalFailed);assert.equal(await page.evaluate(()=>MCFlasherApp.state.fw),null);assert.equal(await page.evaluate(async()=>{try{await MCFirmwareImageLoad('full');return false}catch{return true}}),true);
  await page.locator('#optional-md-file').setInputFiles(md);await page.waitForFunction(()=>MCOptionalUI.result?.mask===0x80000&&!MCOptionalBusy,{},{timeout:120000});
  await page.evaluate(()=>{MCFlasherApp.state.sending=true;MCOptionalRender(MCFlasherApp.state)});assert(await page.locator('#optional-md-file').isDisabled());assert(await page.locator('#optional-grid input[data-machine="25"]').isDisabled());
  assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'browser-proof.json'),JSON.stringify({choices:22,default_19_preserved:true,MD_file_required:true,all_and_kick_only:true,None_exact_Lite:true,invalid_MD_rejected:true,startup262:true,sending_locked:true,page_errors:errors,hardware_tested:false},null,2)+'\n');console.log('PASS real browser22choices, local MD file, all/none/kick, invalid-file rejection and sending lock');
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error(e);process.exit(1)});
