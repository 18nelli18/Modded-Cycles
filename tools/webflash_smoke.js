/* Browser smoke test (jsdom) of the web flasher: loads the real page and its scripts,
 * fakes Web MIDI, and walks through the 4 steps (choose, OS file, connect, flash).
 * Run through tools/webflash_smoke.sh (installs jsdom in a temp folder).
 *   node tools/webflash_smoke.js <synth_dir> [official_os.syx]
 * The optional official OS also checks the 5 real builds against their reference hashes. */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { JSDOM, VirtualConsole } = require("jsdom");

const FLASH = path.join(__dirname, "..", "docs", "flasher");
const SYNTH = process.argv[2];
const REAL_OS = process.argv[3];
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
    check(!!w.MC_TWEAKS && w.MC_TWEAKS.tweaks.length === 3 && w.MC_TWEAKS.features.length === 2, "MC_TWEAKS: 3 tweaks, 2 features");
    check(/build \d{4}-/.test(text(doc, "build-stamp")), "version stamp shown");
    check(doc.getElementById("compat").hidden, "no compatibility banner in a good browser");
    const feats = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    check(feats.length === 2 && feats.includes("feat-usb6") && feats.includes("feat-sdvintage"), "2 feature cards: " + JSON.stringify(feats));
    check(doc.querySelectorAll('input[name="var-usb6"]').length === 0, "usb6 variants hidden while unchecked");
    doc.getElementById("feat-usb6").click();
    await wait(30);
    const vars = [...doc.querySelectorAll('input[name="var-usb6"]')];
    check(vars.length === 2 && vars[0].checked && vars[0].value === "6ch-usbup", "checking usb6 shows 2 variants, recommended one selected");
    check(/Load your official OS file/.test(text(doc, "missing")), "flash button says what is missing: " + text(doc, "missing"));
    check(doc.getElementById("flash").disabled, "flash button disabled without a file");

    // language switch
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(/Qu'est-ce que tu veux installer/.test(text(doc, "h1s")) && doc.documentElement.lang === "fr", "FR switch translates the page");
    check(/Audio USB 6 canaux/.test(text(doc, "features")), "FR switch translates the feature cards");
    doc.querySelector('.lang button[data-lang="en"]').click();
    await wait(20);

    // MIDI: allow, port preselection per method
    doc.getElementById("allow").click();
    await wait(80);
    const sel = doc.getElementById("port");
    check(!sel.hidden && sel.value === "iface", "Allow MIDI -> MIDI interface preselected (" + sel.value + ")");
    check(/2 MIDI output/.test(text(doc, "midi-status")), "status: " + text(doc, "midi-status").slice(0, 50));
    doc.querySelector('input[name="method"][value="usb"]').click();
    await wait(30);
    check(sel.value === "dev" && !doc.getElementById("howto-usb").hidden, "USB method -> Model:Cycles port + USB steps");
    sel.value = "iface";
    sel.dispatchEvent(new w.Event("change"));
    await wait(20);
    check(/pick the port named/i.test(text(doc, "midi-status")), "USB method + interface port -> warning");
    doc.querySelector('input[name="method"][value="midi"]').click();
    await wait(30);
    sel.value = "dev";
    sel.dispatchEvent(new w.Event("change"));
    await wait(20);
    check(/startup menu \(OS UPGRADE\) ignores USB/i.test(text(doc, "midi-status")), "MIDI IN method + device port -> warning");
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
    check(/via USB MIDI Interface/.test(text(doc, "summary")), "summary: " + text(doc, "summary"));

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

  // 6. Real official OS: the 5 combinations must match their reference hashes
  if (REAL_OS) {
    const { w, doc, errors } = await load();
    const app = w.MCFlasherApp;
    app.loadOs(new Uint8Array(fs.readFileSync(REAL_OS)), "model-cycles_OS1.13.syx");
    await wait(20);
    const set = async (usb, variant, sd) => {
      const cu = doc.getElementById("feat-usb6");
      if (cu.checked !== usb) cu.click();
      await wait(10);
      if (usb) { const r = doc.querySelector(`input[name="var-usb6"][value="${variant}"]`); if (!r.checked) r.click(); }
      const cs = doc.getElementById("feat-sdvintage");
      if (cs.checked !== sd) cs.click();
      await settle(w);
    };
    for (const [usb, v, sd] of [[true, "6ch-multiout", false], [true, "6ch-usbup", false], [false, null, true],
                                 [true, "6ch-multiout", true], [true, "6ch-usbup", true]]) {
      await set(usb, v, sd);
      const f = app.state.fw;
      check(f && f.kind === "built" && f.ref, `real OS: ${app.state.buildKey} matches its reference hash`);
    }
    check(errors.length === 0, "no JS error with the real OS");
  }

  console.log(fail ? `\nFAILED (${fail})` : "\nALL OK");
  process.exit(fail ? 1 : 0);
}
main();
