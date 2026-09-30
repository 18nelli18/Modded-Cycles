/* Browser smoke test (jsdom) of the web flasher: loads the real page and its scripts,
 * fakes Web MIDI, and walks through the 4 steps (choose, OS file, connect over USB, flash).
 * Run through tools/webflash_smoke.sh (installs jsdom in a temp folder).
 *   node tools/webflash_smoke.js <synth_dir> [model-cycles_OS1.13.syx] [model-samples_OS1.13.syx] [Syntakt_OS1.41.syx]
 * The optional official files are told apart by their names. The Model:Cycles OS checks every
 * combination the page offers against its reference hash (REF_MAINOS in app.js; the SD VINTAGE
 * ones need the Syntakt OS too); with the Model:Samples OS, the "Samples OS" tab is checked end
 * to end (REF_SAMPLES_ON_CYCLES); with the Syntakt OS, the SD VINTAGE flow is. */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { JSDOM, VirtualConsole } = require("jsdom");

const FLASH = path.join(__dirname, "..", "docs", "flasher");
const SYNTH = process.argv[2];
const REAL = process.argv.slice(3);
const REAL_ST = REAL.find((f) => /syntakt/i.test(path.basename(f)));
const REAL_SMP = REAL.find((f) => /samples/i.test(path.basename(f)));
const REAL_OS = REAL.find((f) => f !== REAL_ST && f !== REAL_SMP);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function load({ midi = true, ports = true, secure = true, lang = "en", devName = "Elektron Model:Cycles" } = {}) {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => errors.push("jsdomError: " + ((e.detail && e.detail.message) || e.message || e)));
  const sent = [];
  const html = fs.readFileSync(path.join(FLASH, "index.html"), "utf8");
  const dom = new JSDOM(html, {
    url: pathToFileURL(path.join(FLASH, "index.html")).href,
    runScripts: "dangerously", resources: "usable", virtualConsole: vc,
    beforeParse(window) {
      Object.defineProperty(window, "isSecureContext", { value: secure, configurable: true });
      Object.defineProperty(window.navigator, "language", { value: lang, configurable: true });
      window.addEventListener("error", (e) => errors.push("window.onerror: " + ((e.error && e.error.message) || e.message)));
      window.addEventListener("unhandledrejection", (e) => errors.push("unhandled: " + ((e.reason && e.reason.message) || e.reason)));
      if (midi) {
        const outputs = new Map();
        if (ports) {
          outputs.set("dev", { id: "dev", name: devName, manufacturer: "Elektron", send: (d) => sent.push(d.length) });
          outputs.set("iface", { id: "iface", name: "USB MIDI Interface", manufacturer: "Acme", send: (d) => sent.push(d.length) });
        }
        window.navigator.requestMIDIAccess = () => Promise.resolve({ outputs, onstatechange: null });
      }
      window.URL.createObjectURL = () => "blob:x";
      window.URL.revokeObjectURL = () => {};
    },
  });
  await wait(300);
  return { dom, w: dom.window, doc: dom.window.document, errors, sent };
}

const text = (doc, id) => doc.getElementById(id).textContent;
async function settle(w) {
  for (let i = 0; i < 200 && w.MCFlasherApp.state.building; i++) await wait(50);
  await wait(60);
}

async function main() {
  let fail = 0;
  const check = (cond, msg) => { console.log((cond ? "  ok  " : "  FAIL ") + msg); if (!cond) fail++; };

  // 1. Page loads cleanly, everything is wired
  {
    const { w, doc, errors } = await load();
    check(errors.length === 0, "loads without JS error " + (errors.length ? JSON.stringify(errors) : ""));
    check(typeof w.MCBuilder === "object" && typeof w.MCFlasher === "object", "MCBuilder + MCFlasher present");
    const ids = w.MC_TWEAKS.tweaks.map((x) => x.id);
    check(ids.join() === "6ch-usbup,latching-mute,trig-preview,browser-scroll,sdvintage-exact,sdvintage-7th" && w.MC_TWEAKS.features.length === 5,
      "MC_TWEAKS: only USB-friendly tweaks (no 6ch-multiout, no clean-room sdvintage): " + ids.join());
    check(/build \d{4}-/.test(text(doc, "build-stamp")), "version stamp shown");
    const srcs = [...doc.querySelectorAll("script[src]")].map((x) => x.getAttribute("src"));
    check(srcs.length === 4 && srcs.every((x) => x.endsWith("?v=" + w.MC_BUILD)), "scripts loaded with ?v=<build> (no stale cache): " + srcs.join());
    check(doc.getElementById("compat").hidden, "no compatibility banner in a good browser");
    const feats = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    check(feats.join() === "feat-usb6,feat-latching-mute,feat-trig-preview,feat-browser-scroll,feat-sdvintage", "5 feature cards: " + JSON.stringify(feats));
    const tags = [...doc.querySelectorAll("#features .tag")].map((x) => x.textContent);
    check(tags.join() === "Tested,Tested,Tested,Tested,Tested", "every card is tagged Tested: " + tags.join());
    check(doc.getElementById("drop3-wrap").hidden, "Syntakt drop zone hidden until SD VINTAGE is ticked");
    doc.getElementById("feat-sdvintage").click();
    await wait(30);
    check(!doc.getElementById("drop3-wrap").hidden && /Drop Syntakt_OS1.41.syx/.test(text(doc, "drop3"))
      && /elektron\.se\/support-downloads\/syntakt/.test(doc.getElementById("step-file").innerHTML),
      "SD VINTAGE ticked -> Syntakt drop zone and download link");
    const radios = [...doc.querySelectorAll('input[name="var-sdvintage"]')];
    check(radios.map((r) => r.value).join() === "sdvintage-exact,sdvintage-7th" && radios[0].checked
      && /As a 7th machine, SDVtg/.test(text(doc, "features")) && /not tested on a Model:Cycles yet/.test(text(doc, "features")),
      "SD VINTAGE: two variants, in place of SNARE (default, tested) or 7th machine SDVtg (new)");
    doc.getElementById("feat-sdvintage").click();
    await wait(30);
    const credits = [...doc.querySelectorAll("#features .credit a")].map((a) => a.href);
    check(credits.length === 4 && credits[0] === "https://github.com/scottmetoyer/ms-multi-output"
      && credits.slice(1).every((h) => h === "https://github.com/drumkilla/elektron-model-tweaks"), "each card credits its author: " + JSON.stringify(credits));
    const list = [...doc.querySelectorAll("#credits-list a")].map((a) => a.textContent);
    check(list.join() === "scottmetoyer/ms-multi-output,drumkilla/elektron-model-tweaks,mischa85/elektron-firmware-tool,mxldyn/octamax",
      "credits section lists the 4 upstream repositories");
    doc.getElementById("feat-usb6").click();
    await wait(30);
    check(doc.querySelectorAll('input[name="var-usb6"]').length === 0, "6 channels: a single variant, no sub-choice");
    check(!!doc.getElementById("tab-samples") && doc.getElementById("panel-samples").hidden && doc.getElementById("drop2-wrap").hidden,
      "Samples OS tab present, its panel and second drop zone hidden in Mods");
    check(/Load your official OS file/.test(text(doc, "missing")), "flash button says what is missing: " + text(doc, "missing"));
    check(doc.getElementById("flash").disabled, "flash button disabled without a file");

    // language switch
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(/Qu'est-ce que tu veux installer/.test(text(doc, "h1s")) && doc.documentElement.lang === "fr", "FR switch translates the page");
    check(/Audio USB 6 canaux/.test(text(doc, "features")) && /Mode mute verrouillé/.test(text(doc, "features"))
      && /par drumkilla/.test(text(doc, "features")) && /le vrai moteur du Syntakt/.test(text(doc, "features"))
      && /Testé/.test(text(doc, "features")), "FR switch translates the feature cards and credits");
    check(/Crédits/.test(text(doc, "credits")) && /boîte à outils/.test(text(doc, "credits")), "FR switch translates the credits section");
    doc.querySelector('.lang button[data-lang="en"]').click();
    await wait(20);

    // Connection: USB only
    check(doc.querySelectorAll('input[name="method"]').length === 0 && !doc.getElementById("howto-midi")
      && !/MIDI IN|READY TO RECEIVE|TRIG 4/.test(text(doc, "step-connect")), "no MIDI IN route in step 3");
    check(/CONFIG › UPGRADE/.test(text(doc, "howto-usb")) && !doc.getElementById("howto-usb").hidden, "USB steps shown");
    doc.getElementById("allow").click();
    await wait(80);
    const sel = doc.getElementById("port");
    check(!sel.hidden && sel.value === "dev", "Allow MIDI -> Model:Cycles port preselected (" + sel.value + ")");
    check(/USB port is selected/.test(text(doc, "midi-status")), "status: " + text(doc, "midi-status").slice(0, 50));
    sel.value = "iface";
    sel.dispatchEvent(new w.Event("change"));
    await wait(20);
    check(/pick the port named/i.test(text(doc, "midi-status")), "another port -> warning");
  }

  // 1b. A Model:Cycles running the Samples OS shows up as "Model:Samples": it refuses a Model:Cycles firmware
  {
    const { doc } = await load({ devName: "Elektron Model:Samples" });
    doc.getElementById("allow").click();
    await wait(80);
    check(doc.getElementById("port").value === "dev" && /refuses a Model:Cycles firmware/.test(text(doc, "midi-status")),
      "Model:Samples port -> warning about the way back");
  }

  // 2. No Web MIDI (Firefox / Safari) -> clear banner
  {
    const { doc } = await load({ midi: false });
    check(!doc.getElementById("compat").hidden && /Chrome, Edge or Opera/.test(text(doc, "compat")), "no Web MIDI -> banner");
    check(doc.getElementById("allow").disabled, "no Web MIDI -> Allow button disabled");
  }

  // 3. Insecure context (file://) -> clear banner
  {
    const { doc } = await load({ secure: false });
    check(/secure page/i.test(text(doc, "compat")), "file:// -> banner: " + text(doc, "compat").slice(0, 40));
  }

  // 4. French browser -> French page
  {
    const { doc } = await load({ lang: "fr-FR" });
    check(doc.documentElement.lang === "fr" && /Flasher Model:Cycles/.test(text(doc, "step-flash") + doc.title), "fr-FR browser -> French page");
  }

  // 5. Build from a synthetic OS, then flash, then stop
  if (SYNTH) {
    const { w, doc, errors, sent } = await load();
    const raw = new Uint8Array(fs.readFileSync(path.join(SYNTH, "synth.syx")));
    const meta = JSON.parse(fs.readFileSync(path.join(SYNTH, "meta.json")));
    const app = w.MCFlasherApp;
    // the synthetic OS stands in for the official one
    w.MC_TWEAKS.device.section_sha256 = meta.section_sha256;
    w.MC_TWEAKS.device.stock_syx_sha256 = w.MCBuilder.hex(w.MCBuilder.sha256(raw));
    for (const k of Object.keys(app.REF_MAINOS)) delete app.REF_MAINOS[k];
    app.loadOs(raw, "synth.syx");
    await wait(20);
    check(/Official Model:Cycles OS 1.13 recognised/.test(text(doc, "file-status")), "OS file recognised as official");
    check(/Select a mod/.test(text(doc, "missing")), "no mod selected -> asks for one");
    doc.getElementById("feat-usb6").click();
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "built" && /Firmware ready/.test(text(doc, "file-status")), "mod checked -> firmware built automatically");
    app.setMode("restore");
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "stock", "Official firmware tab -> sends the OS unchanged");
    app.setMode("mods");
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "built", "back to Mods -> built firmware again (cache)");
    doc.getElementById("feat-sdvintage").click();
    await settle(w);
    check(!app.state.fw && app.state.fwError === "needs_syntakt" && /read from the official Syntakt OS/.test(text(doc, "file-status"))
      && /Load the official Syntakt OS file/.test(text(doc, "missing")), "SD VINTAGE without the Syntakt file -> asks for it");
    app.loadSyntakt(raw, "Syntakt_OS1.41.syx");
    await settle(w);
    check(!app.state.syntakt && /not the official Syntakt OS 1.41/.test(text(doc, "file3-status")), "a wrong file in the Syntakt zone is refused");
    doc.getElementById("feat-sdvintage").click();
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "built" && doc.getElementById("drop3-wrap").hidden, "SD VINTAGE unticked -> back to the 6-channel build");

    doc.getElementById("allow").click();
    await wait(80);
    check(/Tick the box/.test(text(doc, "missing")), "asks for the confirmation box");
    doc.getElementById("ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled, "flash button enabled when everything is ready");
    check(/via Elektron Model:Cycles/.test(text(doc, "summary")), "summary: " + text(doc, "summary"));

    // stop during a paced transfer
    doc.getElementById("flash").click();
    await wait(400);
    check(!doc.getElementById("stop").hidden && /Flashing/.test(text(doc, "flash")), "during transfer: Stop visible, button busy");
    doc.getElementById("stop").click();
    for (let i = 0; i < 40 && app.state.sending; i++) await wait(50);
    check(app.state.finished === "stopped" && /Stopped/.test(text(doc, "result")), "Stop -> clear 'stopped' message");

    // full transfer at pace 0
    const n0 = sent.length;
    doc.getElementById("pace").value = "0";
    doc.getElementById("pace").dispatchEvent(new w.Event("input"));
    doc.getElementById("flash").click();
    for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
    const total = w.MCFlasher.splitMessages(app.state.fw.raw).length;
    check(sent.length - n0 === total, `every packet sent (${sent.length - n0}/${total})`);
    check(app.state.finished === "ok" && /Transfer complete/.test(text(doc, "result")), "success message shown");
    check(/6 input channels/.test(text(doc, "result")), "6-channel hint after success");
    check(errors.length === 0, "no JS error during the flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  // 6. Real official OS: every combination the page offers must match its reference hash
  if (REAL_OS) {
    const { w, doc, errors } = await load();
    const app = w.MCFlasherApp;
    app.loadOs(new Uint8Array(fs.readFileSync(REAL_OS)), "model-cycles_OS1.13.syx");
    await wait(20);
    if (REAL_ST) app.loadSyntakt(new Uint8Array(fs.readFileSync(REAL_ST)), "Syntakt_OS1.41.syx");
    await wait(20);
    const boxes = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    const seen = new Set();
    for (let mask = 1; mask < 1 << boxes.length; mask++) {
      for (let k = 0; k < boxes.length; k++) {
        const cb = doc.getElementById(boxes[k]);           // re-query: the cards are re-rendered
        if (cb.checked !== !!(mask & (1 << k))) { cb.click(); await wait(5); }
      }
      await settle(w);
      const f = app.state.fw;
      if (!REAL_ST && doc.getElementById("feat-sdvintage").checked) {
        check(!f && app.state.fwError === "needs_syntakt", `real OS without the Syntakt OS: SD VINTAGE combination waits for it`);
        continue;
      }
      seen.add(app.state.buildKey);
      check(f && f.kind === "built" && f.ref, `real OS: ${app.state.buildKey} matches its reference hash`);
    }
    if (REAL_ST) {                                        // the other SD VINTAGE variant: 7th machine SDVtg
      for (let mask = 0; mask < 16; mask++) {
        for (let k = 0; k < boxes.length; k++) {
          const cb = doc.getElementById(boxes[k]);
          const want = boxes[k] === "feat-sdvintage" || !!(mask & (1 << k));
          if (cb.checked !== want) { cb.click(); await wait(5); }
        }
        const r7 = doc.querySelector('input[name="var-sdvintage"][value="sdvintage-7th"]');
        if (!r7.checked) { r7.click(); await wait(5); }
        await settle(w);
        const f = app.state.fw;
        seen.add(app.state.buildKey);
        check(f && f.kind === "built" && f.ref && app.state.buildKey.endsWith("sdvintage-7th"),
          `real OS: ${app.state.buildKey} matches its reference hash`);
      }
    }
    const offered = Object.keys(app.REF_MAINOS).filter((k) => REAL_ST || !k.includes("sdvintage"));
    check(seen.size === offered.length && offered.every((k) => seen.has(k)),
      `REF_MAINOS lists exactly the ${seen.size} combinations offered` + (REAL_ST ? "" : " (without SD VINTAGE: no Syntakt OS given)"));
    check(errors.length === 0, "no JS error with the real OS");
  }

  // 7. "Samples OS" tab with both official files
  if (REAL_OS && REAL_SMP) {
    const { w, doc, errors, sent } = await load();
    const app = w.MCFlasherApp;
    const cyc = new Uint8Array(fs.readFileSync(REAL_OS)), smp = new Uint8Array(fs.readFileSync(REAL_SMP));
    doc.getElementById("tab-samples").click();
    await wait(20);
    check(!doc.getElementById("panel-samples").hidden && !doc.getElementById("drop2-wrap").hidden
      && /Load both official OS files/.test(text(doc, "h2s")), "Samples OS tab: panel, second drop zone, step 2 title");
    app.loadSamples(cyc, "model-cycles_OS1.13.syx");               // wrong file in the second zone
    await wait(20);
    check(/not the official Model:Samples OS/.test(text(doc, "file2-status")), "a Cycles file in the Samples zone is refused");
    app.loadOs(smp, "model-samples_OS1.13.syx");                   // wrong file in the first zone
    await settle(w);
    check(/first file must be the official/.test(text(doc, "file-status")) && /first file must be/.test(text(doc, "missing")),
      "a Samples file in the Cycles zone is refused for this tab");
    app.loadOs(cyc, "model-cycles_OS1.13.syx");
    app.loadSamples(smp, "model-samples_OS1.13.syx");
    await settle(w);
    const f = app.state.fw;
    const sha = f && w.MCBuilder.hex(w.MCBuilder.sha256(f.raw));
    check(f && f.kind === "samples" && sha === app.REF_SAMPLES_ON_CYCLES, "both files -> reference build (" + (sha || "").slice(0, 16) + ")");
    check(/Model:Samples OS for your Model:Cycles/.test(text(doc, "file-status")) && /recognised/.test(text(doc, "file2-status")),
      "status lines for both files");
    doc.getElementById("allow").click();
    await wait(80);
    doc.getElementById("ack").click();
    await wait(20);
    check(/MIDI interface for the way back/.test(text(doc, "missing")) && doc.getElementById("flash").disabled,
      "flash blocked until the MIDI-interface box is ticked");
    doc.getElementById("samples-ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled && /Model:Samples OS \(for Model:Cycles\)/.test(text(doc, "summary")), "then ready: " + text(doc, "summary"));
    doc.getElementById("tab-mods").click();
    await settle(w);
    check(app.state.fw === null && /Select a mod/.test(text(doc, "missing")), "back to Mods: the Samples build is not sent");
    doc.getElementById("tab-samples").click();
    await settle(w);
    doc.getElementById("pace").value = "0";
    doc.getElementById("pace").dispatchEvent(new w.Event("input"));
    const n0 = sent.length;
    doc.getElementById("flash").click();
    for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
    check(sent.length - n0 === w.MCFlasher.splitMessages(app.state.fw.raw).length && /restarts as a Model:Samples/.test(text(doc, "result")),
      "full transfer + Samples message");
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(/OS Samples/.test(text(doc, "tab-samples")) && doc.getElementById("drop2-title").textContent === "model-samples_OS1.13.syx",
      "FR: tab translated, loaded file name kept");
    check(errors.length === 0, "no JS error in the Samples OS flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  // 8. SD VINTAGE with the official Model:Cycles and Syntakt files, up to the transfer
  if (REAL_OS && REAL_ST) {
    const { w, doc, errors, sent } = await load();
    const app = w.MCFlasherApp;
    const cyc = new Uint8Array(fs.readFileSync(REAL_OS)), syn = new Uint8Array(fs.readFileSync(REAL_ST));
    app.loadOs(cyc, "model-cycles_OS1.13.syx");
    doc.getElementById("feat-sdvintage").click();
    await settle(w);
    app.loadSyntakt(cyc, "model-cycles_OS1.13.syx");               // wrong file in the Syntakt zone
    await settle(w);
    check(!app.state.syntakt && /not the official Syntakt/.test(text(doc, "file3-status")) && !app.state.fw, "a Cycles file in the Syntakt zone is refused");
    app.loadSyntakt(syn, "Syntakt_OS1.41.syx");
    await settle(w);
    const f = app.state.fw;
    check(f && f.kind === "built" && f.ref && f.sdv && /recognised/.test(text(doc, "file3-status"))
      && /SD VINTAGE, the real Syntakt engine/.test(text(doc, "file-status")), "Syntakt file -> reference build " + (f ? f.name : ""));
    doc.getElementById("allow").click();
    await wait(80);
    check(/Tick the box/.test(text(doc, "missing")) && doc.getElementById("flash").disabled, "asks for the confirmation box");
    doc.getElementById("ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled && doc.getElementById("step-choose").classList.contains("done"), "then ready: " + text(doc, "summary"));
    doc.getElementById("pace").value = "0";
    doc.getElementById("pace").dispatchEvent(new w.Event("input"));
    const n0 = sent.length;
    doc.getElementById("flash").click();
    for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
    check(sent.length - n0 === w.MCFlasher.splitMessages(app.state.fw.raw).length && /Syntakt's SD VINTAGE/.test(text(doc, "result")),
      "full transfer + SD VINTAGE message");
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(doc.getElementById("drop3-title").textContent === "Syntakt_OS1.41.syx" && /OS officiel Syntakt 1.41 reconnu/.test(text(doc, "file3-status")),
      "FR: loaded Syntakt file name kept, status translated");
    doc.querySelector('.lang button[data-lang="en"]').click();
    await wait(20);
    doc.querySelector('input[name="var-sdvintage"][value="sdvintage-7th"]').click();
    await settle(w);
    const f7 = app.state.fw;
    check(f7 && f7.ref && f7.sdv === "sdvintage-7th" && /sdvintage-7th/.test(f7.name), "7th machine variant -> reference build " + (f7 ? f7.name : ""));
    check(new RegExp("MAIN OS " + app.REF_MAINOS["sdvintage-7th"].slice(0, 8)).test(text(doc, "file-status")),
      "status line shows the MAIN OS hash prefix: " + text(doc, "file-status").slice(-20));
    const n1 = sent.length;
    doc.getElementById("flash").click();
    for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
    check(sent.length - n1 === w.MCFlasher.splitMessages(f7.raw).length && /pick SDVtg, the 7th machine/.test(text(doc, "result")),
      "full transfer + SDVtg message");
    check(errors.length === 0, "no JS error in the SD VINTAGE flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  console.log(fail ? `\nFAILED (${fail})` : "\nALL OK");
  process.exit(fail ? 1 : 0);
}
main();
