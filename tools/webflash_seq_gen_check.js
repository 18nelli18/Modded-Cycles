/* Flasher de test : catalogue complet, dépendance Model-TG, variantes,
 * langues, vérification des empreintes et builds officiels dans le navigateur.
 * NODE_PATH=<jsdom> node tools/webflash_seq_gen_check.js <Cycles.syx> <Syntakt.syx>
 * Aucun accès MIDI ni envoi vers du matériel. */
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const {pathToFileURL} = require("node:url");
const {JSDOM, VirtualConsole, ResourceLoader} = require("jsdom");
const root = path.resolve(__dirname, ".."), test = path.join(root, process.env.MC_TEST_PAGE || "docs/flasher");
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
class LocalFiles extends ResourceLoader {
  fetch(url, opts) { return url.startsWith("file:") ? super.fetch(url, opts) : null; }
}
async function main() {
  const errors = [], vc = new VirtualConsole();
  vc.on("jsdomError", e => errors.push(e.message));
  let midiRequests = 0;
  const dom = new JSDOM(fs.readFileSync(path.join(test, "index.html"), "utf8"), {
    url: pathToFileURL(path.join(test, "index.html")).href,
    runScripts: "dangerously", resources: new LocalFiles(), virtualConsole: vc,
    beforeParse(w) {
      Object.defineProperty(w, "isSecureContext", {value: true});
      Object.defineProperty(w.navigator, "language", {value: "en"});
      w.navigator.requestMIDIAccess = () => { midiRequests++; throw Error("No MIDI access allowed in this test"); };
      w.URL.createObjectURL = () => "blob:test"; w.URL.revokeObjectURL = () => {};
      w.addEventListener("error", e => errors.push(e.message));
    }
  });
  const w = dom.window, doc = w.document;
  for (let i=0; i<200 && !w.MCFlasherApp; i++) await pause(50);
  assert.ok(w.MCFlasherApp); assert.deepEqual(errors, []); assert.equal(midiRequests, 0);
  const production = {window: {}};
  vm.runInNewContext(fs.readFileSync(path.join(root, "docs/flasher/tweaks.js"), "utf8"), production);
  const old = production.window.MC_TWEAKS, tw = w.MC_TWEAKS, app = w.MCFlasherApp;
  const isTest = test !== path.join(root, "docs/flasher");
  const second = test.endsWith("flasher-test-2");
  if (isTest) { old.features = old.features.filter(f=>f.id!=="scramble"); old.tweaks=old.tweaks.filter(t=>!t.id.startsWith("scramble")); }
  for (const f of old.features) {
    const want = isTest && f.id === "scale-gen" ? {...f, status: "experimental"} : f;
    if (second && f.id === "scale-gen") want.queued = {"scale-gen":"scale-gen-queued","scale-gen-st":"scale-gen-st-queued"};
    assert.equal(JSON.stringify(tw.features.find(x=>x.id===f.id)), JSON.stringify(want));
    assert.ok(doc.getElementById("feat-"+f.id));
  }
  assert.equal(tw.features.length, old.features.length + (second ? 1 : 0));
  assert.equal(tw.tweaks.length, old.tweaks.length + (second ? 8 : 0));
  assert.match(doc.getElementById("mod-scale-gen").textContent, isTest ? /Experimental/ : /Tested/);
  if (isTest) assert.ok(doc.getElementById("test-build-notice"));
  console.log(`ok : all ${old.features.length} existing cards retained, generator included, no automatic MIDI request`);
  const click = id => doc.getElementById("feat-"+id).click();
  click("scale-gen");
  assert.ok(doc.getElementById("feat-model-tg").checked);
  assert.ok(app.chosenTweaks().some(t=>t.id==="scale-gen"));
  if (!isTest) {
    click("scramble");
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble-gen"));
    click("scale-gen");
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble"));
    click("scale-gen");
  }
  if (second) {
    assert.match(doc.getElementById("mod-scale-gen").textContent,/Sequence Generator/);
    const q=doc.getElementById("queue-scale-gen");
    assert.ok(q && doc.getElementById("mod-scale-gen").contains(q));
    assert.equal(q.checked,false);q.click();
    assert.ok(app.chosenTweaks().some(t=>t.id==="scale-gen-queued"));
    click("scramble");
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble-gen-queued"));
    doc.getElementById("queue-scale-gen").click();
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble-gen"));
  }
  click("macro");
  assert.ok(app.chosenTweaks().some(t=>t.id==="scale-gen-st"));
  assert.ok(app.chosenTweaks().some(t=>t.id==="model-tg-st"));
  if (!isTest) {
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble-st-gen"));
    click("scramble");
  }
  if (second) {
    doc.getElementById("queue-scale-gen").click();
    assert.ok(app.chosenTweaks().some(t=>t.id==="scale-gen-st-queued"));
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble-st-gen-queued"));
    doc.getElementById("queue-scale-gen").click();
    click("scale-gen");
    assert.ok(app.chosenTweaks().some(t=>t.id==="scramble-st"));
    click("scale-gen");
    click("scramble");
    console.log("ok : queued checkbox nested under Sequence Generator, both bases, all SCRAMBLE chains, standalone SCRAMBLE");
  }
  click("model-tg");
  assert.equal(doc.getElementById("feat-scale-gen").checked, false);
  app.applyLang("fr");
  assert.match(doc.getElementById("mod-scale-gen").textContent, /Générateur de séquence/);
  assert.ok(doc.querySelector(isTest ? '#mod-scale-gen a[href="guide.html#scale-gen"]' : '#mod-scale-gen a[href="../guide/#scale-gen"]'));
  assert.match(fs.readFileSync(path.join(root, "docs/guide/index.html"), "utf8"), /id="scale-gen"/);
  console.log("ok : automatic Model-TG dependency, combined variant, cascading deselection, French text and local guide");
  app.applyLang("en");
  app.loadOs(new Uint8Array(fs.readFileSync(process.argv[2])), "model-cycles_OS1.13.syx");
  app.loadSyntakt(new Uint8Array(fs.readFileSync(process.argv[3])), "Syntakt_OS1.42.syx");
  click("scale-gen");
  for(let i=0;i<600 && app.state.building;i++) await pause(50);
  assert.ok(app.state.fw && app.state.fw.kind==="built", app.state.fwError);
  assert.ok(app.state.fw.modsRef && app.state.fw.ref);
  console.log("ok : actual page builds generator from official OS with whole-image and per-mod checks");
  const keys = Object.keys(app.REF_MAINOS).filter(k=>k.includes("scale-gen"));
  assert.ok(keys.length>20);
  const chosenKeys = new Set([
    keys.find(k=>k==="model-tg+scale-gen"),
    keys.find(k=>k.includes("syntakt-tg-") && k.split("+").length===3),
    keys.filter(k=>k.includes("macro") && k.includes("syntakt-tg-")).sort((a,b)=>b.length-a.length)[0],
    keys.filter(k=>!k.includes("syntakt") && !k.includes("macro")).sort((a,b)=>b.length-a.length)[0]
  ]);
  if (!isTest) {
    chosenKeys.add(keys.find(k=>k==="model-tg+scale-gen+scramble-gen"));
    chosenKeys.add(keys.filter(k=>k.includes("scramble-st-gen")).sort((a,b)=>b.length-a.length)[0]);
  }
  for (const key of chosenKeys) {
    assert.ok(key, "reference case missing");
    const chosen = key.split("+").map(id=>tw.tweaks.find(t=>t.id===id));
    const out = w.MCBuilder.build(new Uint8Array(fs.readFileSync(process.argv[2])), tw.device, chosen,
      {syntakt: new Uint8Array(fs.readFileSync(process.argv[3])), refMods: app.REF_MODS, expectMainOsSha: app.REF_MAINOS[key]});
    assert.ok(out.modsChecked && out.raw.length>0);
    console.log("ok : browser full build + Python reference + all mod hashes: " + key);
  }
  if (isTest && doc.getElementById("select-all")) {
    doc.getElementById("select-all").click();
    for(let i=0;i<600 && app.state.building;i++) await pause(50);
    assert.ok(doc.getElementById("feat-model-tg").checked);
    assert.ok(doc.getElementById("feat-midi-live-both").checked);
    const ids = app.chosenTweaks().map(t=>t.id);
    assert.ok(ids.includes("model-tg-st") && ids.includes("midi-live-both"));
    assert.ok(!ids.includes("midi-both"));
    if(second) {
      assert.ok(ids.includes("scale-gen-st-queued") && ids.includes("scramble-st-gen-queued"));
      assert.equal(doc.getElementById("queue-scale-gen").checked,true);
    }
    assert.equal(doc.getElementById("feat-midi-both").checked, false);
    assert.ok(app.state.fw && app.state.fw.kind==="built", app.state.fwError);
    const first = ids.join();
    doc.getElementById("select-all").click();
    assert.equal(app.chosenTweaks().map(t=>t.id).join(), first);
    app.applyLang("fr");
    assert.equal(doc.getElementById("select-all").textContent, "Tout sélectionner");
    console.log("ok : Select all preserves Model-TG/live MIDI, builds full selection, repeats identically and translates");
  }
  const original = app.REF_MODS["scale-gen"].w;
  app.REF_MODS["scale-gen"].w = "0".repeat(64);
  assert.throws(()=>w.MCBuilder.build(new Uint8Array(fs.readFileSync(process.argv[2])), tw.device,
    ["model-tg", "scale-gen"].map(id=>tw.tweaks.find(t=>t.id===id)), {refMods:app.REF_MODS}), /reference/);
  app.REF_MODS["scale-gen"].w = original;
  assert.deepEqual(errors, []); assert.equal(midiRequests, 0);
  console.log(`ok : modified generator rejected; ${keys.length} generator combination references present`);
  dom.window.close();
}
main().catch(e=>{console.error(e);process.exit(1);});
