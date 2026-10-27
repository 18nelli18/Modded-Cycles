/* Vrai navigateur : choix d'edition, exigences fichiers et courses asynchrones. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),docs=path.join(root,'docs'),meta=JSON.parse(fs.readFileSync(path.join(docs,'flasher/BUILD.json')));
const [cyclesPath,syntaktPath]=process.argv.slice(2);assert(cyclesPath&&syntaktPath,'cycles.syx syntakt.syx');
(async()=>{
 const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://localhost'),p=path.resolve(docs,'.'+decodeURIComponent(u.pathname)+(u.pathname.endsWith('/')?'index.html':''));if(!p.startsWith(docs+path.sep)){res.writeHead(403).end();return}fs.readFile(p,(err,data)=>{if(err){res.writeHead(404).end();return}const mime={'.html':'text/html','.js':'text/javascript','.css':'text/css'}[path.extname(p)];if(mime)res.setHeader('content-type',mime);res.end(data)});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,...(process.env.MC_BROWSER?{executablePath:process.env.MC_BROWSER}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:960}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{navigator.requestMIDIAccess=async()=>({inputs:new Map(),outputs:new Map(),addEventListener(){}})});
  await page.goto(`http://127.0.0.1:${server.address().port}/flasher/`);await page.waitForFunction(()=>window.MCFlasherApp&&window.MCFirmwareImages);
  await page.evaluate(()=>MCFlasherApp.applyLang('en'));
  assert.equal(await page.locator('#firmware-edition').inputValue(),'full');await page.locator('#firmware-edition').selectOption('lite');
  assert(await page.locator('#lite-info').isVisible());assert(!(await page.locator('.fixed-features').isVisible()));assert(!(await page.locator('#drop3-wrap').isVisible()));
  await page.evaluate(raw=>MCFlasherApp.loadOs(new Uint8Array(raw),'model-cycles_OS1.13.syx'),Array.from(fs.readFileSync(cyclesPath)));
  await page.waitForFunction(()=>MCFlasherApp.state.fw?.edition==='lite');
  assert.equal(await page.evaluate(()=>MCBuilder.hex(MCBuilder.sha256(MCFlasherApp.state.fw.raw))),meta.editions.lite.syxSha256);
  assert.equal(await page.evaluate(()=>MCFlasherApp.state.fw.name),'Supermodel_Lite_2.56.syx');
  await page.locator('#firmware-edition').selectOption('full');assert(await page.locator('.fixed-features').isVisible());assert(await page.locator('#drop3-wrap').isVisible());
  assert.equal(await page.evaluate(()=>MCFlasherApp.state.fwError),'needs_syntakt');
  await page.evaluate(raw=>MCFlasherApp.loadSyntakt(new Uint8Array(raw),'Syntakt_OS1.42.syx'),Array.from(fs.readFileSync(syntaktPath)));
  await page.waitForFunction(()=>MCFlasherApp.state.fw?.edition==='full');assert.equal(await page.evaluate(()=>MCBuilder.hex(MCBuilder.sha256(MCFlasherApp.state.fw.raw))),meta.editions.full.syxSha256);
  // Un ancien chargement Full finit apres la selection Lite.
  await page.evaluate(()=>{const original=MCFirmwareImageLoad;window.MCFirmwareImageLoad=async edition=>{if(edition==='full')await new Promise(r=>setTimeout(r,300));return original(edition)};MCFlasherApp.state.cache={};MCFlasherApp.setEdition('full');setTimeout(()=>MCFlasherApp.setEdition('lite'),60)});
  await page.waitForFunction(()=>MCFlasherApp.state.fw?.edition==='lite');await page.waitForTimeout(500);assert.equal(await page.evaluate(()=>MCFlasherApp.state.fw.edition),'lite');
  await page.evaluate(()=>{MCFlasherApp.state.sending=true;MCFlasherApp.render()});assert(await page.locator('#firmware-edition').isDisabled());assert.equal(await page.evaluate(()=>MCFlasherApp.setEdition('full')),false);
  await page.evaluate(()=>{MCFlasherApp.state.sending=false;MCFlasherApp.render();MCFlasherApp.applyLang('fr')});assert((await page.locator('#firmware-edition option[value=lite]').textContent()).includes('origine'));
  await page.evaluate(()=>MCFlasherApp.applyLang('en'));await page.screenshot({path:path.join(root,'../release256-ui.png'),fullPage:true});
  assert.deepEqual(errors,[]);console.log('PASS real browser: Full/Lite selector, Lite without Syntakt, exact downloads, stale completion, sending lock and French labels');
 }finally{await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error(e);process.exitCode=1});
