/* Browser smoke test (jsdom) of the web flasher: loads the real page and its scripts,
 * fakes Web MIDI, and walks through the 4 steps (choose, OS file, connect over USB, flash).
 * Run through tools/webflash_smoke.sh (installs jsdom in a temp folder).
 *   node tools/webflash_smoke.js <synth_dir> [official_os.syx [official_samples_os.syx]]
 * The optional official OS also checks every combination the page offers against its
 * reference hash (REF_MAINOS in app.js); with the official Model:Samples OS too, the
 * "Samples OS" tab is checked end to end (REF_SAMPLES_ON_CYCLES). */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { JSDOM, VirtualConsole } = require("jsdom");

const FLASH = path.join(__dirname, "..", "docs", "flasher");
const SYNTH = process.argv[2];
const REAL_OS = process.argv[3];
const REAL_SMP = process.argv[4];
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function load({ midi = true, ports = true, secure = true, lang = "en" } = {}) {
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
          outputs.set("dev", { id: "dev", name: "Elektron Model:Cycles", manufacturer: "Elektron", send: (d) => sent.push(d.length) });
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
    check(ids.join() === "6ch-usbup,latching-mute,trig-preview,browser-scroll" && w.MC_TWEAKS.features.length === 4,
      "MC_TWEAKS: only USB-friendly tweaks (no 6ch-multiout, no sdvintage): " + ids.join());
    check(/build \d{4}-/.test(text(doc, "build-stamp")), "version stamp shown");
    check(doc.getElementById("compat").hidden, "no compatibility banner in a good browser");
    const feats = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    check(feats.join() === "feat-usb6,feat-latching-mute,feat-trig-preview,feat-browser-scroll", "4 feature cards: " + JSON.stringify(feats));
    check(doc.querySelectorAll("#features .tag.ok").length === 4 && /Tested/.test(text(doc, "features")), "every card is tagged Tested");
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
      && /par drumkilla/.test(text(doc, "features")), "FR switch translates the feature cards and credits");
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
    const boxes = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    const seen = new Set();
    for (let mask = 1; mask < 1 << boxes.length; mask++) {
      for (let k = 0; k < boxes.length; k++) {
        const cb = doc.getElementById(boxes[k]);           // re-query: the cards are re-rendered
        if (cb.checked !== !!(mask & (1 << k))) { cb.click(); await wait(5); }
      }
      await settle(w);
      const f = app.state.fw;
      seen.add(app.state.buildKey);
      check(f && f.kind === "built" && f.ref, `real OS: ${app.state.buildKey} matches its reference hash`);
    }
    check(seen.size === Object.keys(app.REF_MAINOS).length, `REF_MAINOS lists exactly the ${seen.size} combinations offered`);
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

  console.log(fail ? `\nFAILED (${fail})` : "\nALL OK");
  process.exit(fail ? 1 : 0);
}
main();
