/* Vraie page : versions,19choix, generation All/None/mixte et verrou d'envoi. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),docs=path.join(root,'docs'),[cycles,out]=process.argv.slice(2);assert(cycles&&out);fs.mkdirSync(out,{recursive:true});
(async()=>{
 const server=http.createServer((req,res)=>{const url=new URL(req.url,'http://localhost');const file=path.resolve(docs,'.'+decodeURIComponent(url.pathname)+(url.pathname.endsWith('/')?'index.html':''));if(!file.startsWith(docs+path.sep)){res.writeHead(403).end();return;}fs.readFile(file,(e,data)=>{if(e){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.syx':'application/octet-stream'})[path.extname(file)]||'application/octet-stream');res.end(data);});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{
  browser=await chromium.launch({headless:true,executablePath:process.env.EDGE_BINARY||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
  const page=await browser.newPage({viewport:{width:1280,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{navigator.requestMIDIAccess=async()=>({inputs:new Map(),outputs:new Map(),addEventListener(){}});localStorage.setItem('mc-lang','en');});
  const base='http://127.0.0.1:'+server.address().port;
  await page.goto(base+'/flasher/');await page.waitForFunction(()=>window.MCFlasherApp&&window.MCFirmwareImages);
  assert.equal((await page.locator('[data-rel="version"]').first().innerText()).trim(),'2.58');assert.equal(await page.evaluate(()=>MCFirmwareImages.full.startup_title.version),'2.58');
  await page.screenshot({path:path.join(out,'main257.png'),fullPage:false});
  await page.goto(base+'/flasher-optional/');await page.waitForFunction(()=>window.MCOptionalUI&&window.MCFlasherApp);
  assert.equal((await page.locator('[data-rel="version"]').first().innerText()).trim(),'2.58');assert.equal(await page.locator('#optional-grid input').count(),19);
  for(const id of [21,17])assert.equal(await page.locator(`#optional-grid input[data-machine="${id}"]`).count(),1);
  await page.locator('#file').setInputFiles(cycles);await page.waitForFunction(()=>MCOptionalUI.result&&!window.MCOptionalBusy,{},{timeout:60000});
  let result=await page.evaluate(()=>({mask:MCOptionalUI.result.mask,sha:MCOptionalUI.result.syxSha256}));assert.equal(result.mask,0x7ffff);
  await page.locator('#optional-none').click();await page.waitForFunction(()=>MCOptionalUI.result?.mask===0&&!MCOptionalBusy);assert.equal(await page.evaluate(()=>MCOptionalUI.result.syxSha256===MCOptionalBaseEditions.lite.syxSha256),true);
  await page.locator('#optional-grid input[data-machine="21"]').check();await page.waitForFunction(()=>MCOptionalUI.result?.mask===0x8000&&!MCOptionalBusy);
  assert.equal(await page.locator('#optional-grid input:checked').count(),1);
  await page.locator('#optional-all').click();await page.waitForFunction(()=>MCOptionalUI.result?.mask===0x7ffff&&!MCOptionalBusy);
  const before=await page.evaluate(()=>{MCFlasherApp.state.sending=true;MCOptionalRender(MCFlasherApp.state);return MCOptionalUI.mask;});
  assert.equal(await page.locator('#optional-grid input:disabled').count(),19);assert.equal(await page.evaluate(()=>MCOptionalUI.setMask(0)),false);assert.equal(await page.evaluate(()=>MCOptionalUI.mask),before);
  await page.evaluate(()=>{MCFlasherApp.state.sending=false;MCOptionalRender(MCFlasherApp.state);});
  await page.screenshot({path:path.join(out,'optional257.png'),fullPage:false});assert.deepEqual(errors,[]);
  fs.writeFileSync(path.join(out,'browser-proof.json'),JSON.stringify({release:'2.58',main_and_optional_displayed:true,machine_choices:19,all_none_legacy_only:true,sending_locked:true,page_errors:errors,hardware_tested:false},null,2)+'\n');
  console.log('PASS real browser: main/Optional2.58,19choices,All/None/Legacy-only and sending lock');
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
