/* Browser smoke test (jsdom) of the web flasher: loads the real page and its scripts,
 * fakes Web MIDI, and walks through the 4 steps (choose, OS file, connect over USB, flash).
 * Run through tools/webflash_smoke.sh (installs jsdom in a temp folder).
 *   node tools/webflash_smoke.js <synth_dir> [model-cycles_OS1.13.syx] [model-samples_OS1.13.syx] [Syntakt_OS1.42.syx or 1.41]
 * The optional official files are told apart by their names. The Model:Cycles OS checks every
 * combination the page offers against its reference hash (REF_MAINOS in app.js; the real Syntakt
 * engines need the Syntakt OS too); with the Model:Samples OS, the "Samples OS" tab is checked end
 * to end (REF_SAMPLES_ON_CYCLES); with the Syntakt OS, the Syntakt engines flow is. */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { JSDOM, VirtualConsole } = require("jsdom");

const FLASH = path.join(__dirname, "..", "docs", "flasher");
const SYNTH = process.argv[2];
const REAL = process.argv.slice(3);
const REAL_ST = REAL.find((f) => /syntakt/i.test(path.basename(f)));
const ST_NAME = REAL_ST ? path.basename(REAL_ST) : "Syntakt_OS1.42.syx";
const ST_VERSION = (/OS(\d+\.\d+)/.exec(ST_NAME) || [])[1];   // "1.42" or "1.41": both official, same engines
const REAL_SMP = REAL.find((f) => /samples/i.test(path.basename(f)));
const REAL_OS = REAL.find((f) => f !== REAL_ST && f !== REAL_SMP);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
// Syntakt engine combinations offered by the page: tweak id -> engine codes (tweaks.js)
const engineCombos = (w) => Object.fromEntries(w.MC_TWEAKS.features.find((f) => f.engines).combos.map((c) => [c.id, c.engines]));

// Tick exactly the given Syntakt engines (the card is turned on first; ticking before unticking
// never empties the list, which would turn the card off).
async function pickEngines(doc, codes) {
  if (!doc.getElementById("feat-syntakt").checked) { doc.getElementById("feat-syntakt").click(); await wait(5); }
  for (const want of [true, false]) {
    for (const cb of [...doc.querySelectorAll('input[name="eng-syntakt"]')].map((x) => x.value)) {
      const box = doc.getElementById("eng-" + cb);                 // re-query: the cards are re-rendered
      if (codes.includes(cb) === want && box.checked !== want) { box.click(); await wait(5); }
    }
  }
}

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
  // tweaks.js fait plus d'1 Mo : sur une machine occupée, les scripts peuvent mettre plus de 300 ms à se charger
  for (let i = 0; i < 200 && !(dom.window.MCFlasherApp && dom.window.MC_TWEAKS && dom.window.MCBuilder); i++) await wait(50);
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
    const nEng = w.MC_TWEAKS.features.find((f) => f.engines).engines.length;
    check(ids.slice(0, 9).join() === "6ch-usbup,model-tg,model-tg-st,latching-mute,trig-preview,browser-scroll,syntakt-sd,syntakt-tg-sd,syntakt-cp"
      && ids.length === 6 + 2 * ((1 << nEng) - 1) && ids.includes("syntakt-sd-cp") && ids.includes("syntakt-tg-sd-cp-toy-bits")
      && !ids.some((x) => /exact|snare|multiout/.test(x)) && w.MC_TWEAKS.features.length === 6,
      `MC_TWEAKS: only USB-friendly tweaks, one tweak per choice of the ${nEng} Syntakt engines (no SNARE replacement), alone and with Model-TG: ${ids.length} tweaks`);
    check(/build \d{4}-/.test(text(doc, "build-stamp")), "version stamp shown");
    const srcs = [...doc.querySelectorAll("script[src]")].map((x) => x.getAttribute("src"));
    check(["builder.js", "tweaks.js", "flasher.js", "app.js"].every((f) => srcs.some((x) => x.startsWith(f + "?")))
      && srcs.every((x) => x.endsWith("?v=" + w.MC_BUILD)), "scripts loaded with ?v=<build> (no stale cache): " + srcs.join());
    check(doc.getElementById("compat").hidden, "no compatibility banner in a good browser");
    const feats = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    check(feats.join() === "feat-usb6,feat-model-tg,feat-latching-mute,feat-trig-preview,feat-browser-scroll,feat-syntakt", "6 feature cards: " + JSON.stringify(feats));
    const tags = [...doc.querySelectorAll("#features .tag")].map((x) => x.textContent);
    const synTag = w.MC_TWEAKS.features.find((f) => f.engines).status === "tested" ? "Tested" : "Experimental";
    check(tags.join() === "Tested,Experimental,Tested,Tested,Tested," + synTag,
      "cards tagged as tested or not (Model-TG experimental until tested here): " + tags.join());
    check(doc.getElementById("drop3-wrap").hidden, "Syntakt drop zone hidden until the Syntakt engines are ticked");
    doc.getElementById("feat-syntakt").click();
    await wait(30);
    check(!doc.getElementById("drop3-wrap").hidden && /Drop Syntakt_OS1.42.syx/.test(text(doc, "drop3"))
      && /elektron\.se\/support-downloads\/syntakt/.test(doc.getElementById("step-file").innerHTML),
      "Syntakt engines ticked -> Syntakt drop zone and download link");
    const engs = [...doc.querySelectorAll('input[name="eng-syntakt"]')];
    check(engs.map((r) => r.value + ":" + r.checked).join() === "sd:true,cp:false,toy:false,bits:false,swarm:false" && engs.every((r) => r.type === "checkbox")
      && /SDVtg — SD VINTAGE/.test(text(doc, "features")) && /CPVtg — CP VINTAGE/.test(text(doc, "features"))
      && /SYToy — SY TOY/.test(text(doc, "features")) && /SYBit — SY BITS/.test(text(doc, "features"))
      && /SYSwm — SY SWARM/.test(text(doc, "features"))
      && !/in place of SNARE/.test(text(doc, "features")) && doc.querySelectorAll('input[name="var-syntakt"]').length === 0
      && (engineCombos(w) && w.MC_TWEAKS.features.find((f) => f.engines).combos[0].tested
        ? /tested on a real Model:Cycles/ : /not tested on a Model:Cycles yet/).test(text(doc, "features")),
      "Syntakt engines: one checkbox per engine (SDVtg ticked by default, CPVtg, SYToy, SYBit, SYSwm), no SNARE replacement");
    await pickEngines(doc, ["cp"]);
    check(/not tested on a Model:Cycles yet/.test(text(doc, "features")) && /Experimental/.test(doc.querySelector("label[for=feat-syntakt] .tag").textContent),
      "CPVtg alone: a new choice, tagged Experimental");
    doc.getElementById("eng-cp").click();
    await wait(30);
    check(!doc.getElementById("feat-syntakt").checked && doc.querySelectorAll('input[name="eng-syntakt"]').length === 0
      && doc.getElementById("drop3-wrap").hidden, "last engine unticked -> the card turns off");
    const credits = [...doc.querySelectorAll("#features .credit a")].map((a) => a.href);
    check(credits.length === 6 && credits[0] === "https://github.com/scottmetoyer/ms-multi-output"
      && credits[1] === "https://github.com/TinyGregAudio/Model-TG" && /\/LICENSE-Model-TG\.txt$/.test(credits[2])
      && credits.slice(3).every((h) => h === "https://github.com/drumkilla/elektron-model-tweaks"),
      "each card credits its author, Model-TG with its MIT license: " + JSON.stringify(credits));
    const list = [...doc.querySelectorAll("#credits-list a")].map((a) => a.textContent);
    check(list.join() === "scottmetoyer/ms-multi-output,drumkilla/elektron-model-tweaks,TinyGregAudio/Model-TG,mischa85/elektron-firmware-tool,mxldyn/octamax",
      "credits section lists the 5 upstream repositories");
    // Model-TG holds drumkilla's tweaks: ticking one unticks the other. With the Syntakt engines it makes the
    // combined version (notes/31): its base, then the engines' tweak built on top of it
    doc.getElementById("feat-latching-mute").click(); await wait(5);
    doc.getElementById("feat-syntakt").click(); await wait(5);
    doc.getElementById("feat-model-tg").click(); await wait(5);
    const off = !doc.getElementById("feat-latching-mute").checked && doc.getElementById("feat-syntakt").checked;
    const noteOn = /set to CYC/.test(text(doc, "features")) && /its Sampler is the 7th machine/.test(text(doc, "features"));
    const both = w.MCFlasherApp.chosenTweaks().map((x) => x.id).join();
    doc.getElementById("feat-trig-preview").click(); await wait(5);
    check(off && noteOn && both === "model-tg-st,syntakt-tg-sd" && !doc.getElementById("feat-model-tg").checked
      && doc.getElementById("feat-trig-preview").checked && w.MCFlasherApp.chosenTweaks().map((x) => x.id).join() === "trig-preview,syntakt-sd",
      "Model-TG unticks drumkilla's tweaks (and the other way round), shows its install note; with the Syntakt engines: " + both);
    doc.getElementById("feat-trig-preview").click(); await wait(5);
    // the combined version's badges follow its tests on the hardware (gen_syntakt_engines.HW_TESTED_TG, the
    // combos' tg_tested in tweaks.js): Model-TG + the 5 engines, then Model-TG + SDVtg alone
    doc.getElementById("feat-model-tg").click(); await wait(5);
    const tgCombos = w.MC_TWEAKS.features.find((f) => f.id === "syntakt").combos;
    const tgTested = (codes) => !!tgCombos.find((c) => c.engines.join() === codes.join()).tg_tested;
    const tagOf = (id) => doc.querySelector(`label[for=${id}] .tag`).textContent;
    const badges = async (codes) => {
      await pickEngines(doc, codes);
      const want = tgTested(codes) ? "Tested" : "Experimental";
      const note = tgTested(codes) ? /tested on a real Model:Cycles/ : /not tested on a Model:Cycles yet/;
      return note.test(text(doc, "features")) && tagOf("feat-syntakt") === want && tagOf("feat-model-tg") === want;
    };
    const all5 = ["sd", "cp", "toy", "bits", "swarm"];
    const badgesOk = await badges(all5) && await badges(["sd"]);
    const word = (codes) => (tgTested(codes) ? "tested" : "experimental");
    check(badgesOk, `Model-TG + the 5 engines: ${word(all5)} (both cards); Model-TG + SDVtg alone: ${word(["sd"])}`);
    doc.getElementById("feat-model-tg").click(); await wait(5);
    doc.getElementById("feat-syntakt").click(); await wait(5);
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
    check(/Que voulez-vous installer/.test(text(doc, "h1s")) && doc.documentElement.lang === "fr", "FR switch translates the page");
    check(/Audio USB 6 canaux/.test(text(doc, "features")) && /Mode mute verrouillé/.test(text(doc, "features"))
      && /par drumkilla/.test(text(doc, "features")) && /Vrais moteurs du Syntakt/.test(text(doc, "features"))
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
    doc.getElementById("feat-syntakt").click();
    await settle(w);
    check(!app.state.fw && app.state.fwError === "needs_syntakt" && /read from the official Syntakt OS/.test(text(doc, "file-status"))
      && /Load the official Syntakt OS file/.test(text(doc, "missing")), "Syntakt engines without the Syntakt file -> asks for it");
    app.loadSyntakt(raw, "Syntakt_OS1.42.syx");
    await settle(w);
    check(!app.state.syntakt && /not the official Syntakt OS 1.42/.test(text(doc, "file3-status")), "a wrong file in the Syntakt zone is refused");
    doc.getElementById("feat-syntakt").click();
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "built" && doc.getElementById("drop3-wrap").hidden, "Syntakt engines unticked -> back to the 6-channel build");

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
    if (REAL_ST) app.loadSyntakt(new Uint8Array(fs.readFileSync(REAL_ST)), ST_NAME);
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
      if (!REAL_ST && doc.getElementById("feat-syntakt").checked) {
        check(!f && app.state.fwError === "needs_syntakt", `real OS without the Syntakt OS: Syntakt engines combination waits for it`);
        continue;
      }
      seen.add(app.state.buildKey);
      check(f && f.kind === "built" && f.ref, `real OS: ${app.state.buildKey} matches its reference hash`);
    }
    const combos = engineCombos(w);
    const plain = boxes.filter((b) => b !== "feat-syntakt" && b !== "feat-model-tg");   // what goes with the engines
    const sets = [];                                  // with the engines: any of these, or Model-TG (with or without USB)
    for (let mask = 0; mask < 1 << plain.length; mask++) sets.push(plain.filter((b, k) => mask & (1 << k)));
    sets.push(["feat-model-tg"], ["feat-model-tg", "feat-usb6"]);
    const tgOf = Object.fromEntries(w.MC_TWEAKS.features.find((f) => f.engines).combos.map((c) => [c.id, c.tg]));
    for (const variant of REAL_ST ? Object.keys(combos).slice(1) : []) {   // the other engine combinations
      for (const on of sets) {
        for (const b of boxes) {
          const cb = doc.getElementById(b);
          const want = b === "feat-syntakt" || on.includes(b);
          if (cb.checked !== want) { cb.click(); await wait(5); }
        }
        await pickEngines(doc, combos[variant]);
        await settle(w);
        const f = app.state.fw;
        seen.add(app.state.buildKey);
        check(f && f.kind === "built" && f.ref && app.state.buildKey.endsWith(on.includes("feat-model-tg") ? tgOf[variant] : variant),
          `real OS: ${app.state.buildKey} matches its reference hash`);
      }
    }
    const offered = Object.keys(app.REF_MAINOS).filter((k) => REAL_ST || !/sdvintage|syntakt/.test(k));
    check(seen.size === offered.length && offered.every((k) => seen.has(k)),
      `REF_MAINOS lists exactly the ${seen.size} combinations offered` + (REAL_ST ? "" : " (without the Syntakt engines: no Syntakt OS given)"));
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

  // 8. Syntakt engines with the official Model:Cycles and Syntakt files, up to the transfer
  if (REAL_OS && REAL_ST) {
    const { w, doc, errors, sent } = await load();
    const app = w.MCFlasherApp;
    const cyc = new Uint8Array(fs.readFileSync(REAL_OS)), syn = new Uint8Array(fs.readFileSync(REAL_ST));
    app.loadOs(cyc, "model-cycles_OS1.13.syx");
    doc.getElementById("feat-syntakt").click();
    await settle(w);
    app.loadSyntakt(cyc, "model-cycles_OS1.13.syx");               // wrong file in the Syntakt zone
    await settle(w);
    check(!app.state.syntakt && /not the official Syntakt/.test(text(doc, "file3-status")) && !app.state.fw, "a Cycles file in the Syntakt zone is refused");
    app.loadSyntakt(syn, ST_NAME);
    await settle(w);
    const f = app.state.fw;
    check(f && f.kind === "built" && f.ref && f.sdv === "syntakt-sd"
      && text(doc, "file3-status").includes(`Official Syntakt OS ${ST_VERSION} recognised`)
      && /Real Syntakt engines — SDVtg/.test(text(doc, "file-status")), "Syntakt file -> reference build of SDVtg (default) " + (f ? f.name : ""));
    check(new RegExp("MAIN OS " + app.REF_MAINOS["syntakt-sd"].slice(0, 8)).test(text(doc, "file-status")),
      "status line shows the MAIN OS hash prefix: " + text(doc, "file-status").slice(-20));
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
    check(sent.length - n0 === w.MCFlasher.splitMessages(app.state.fw.raw).length
      && /after Chord come SDVtg \(SD VINTAGE\)\./.test(text(doc, "result")), "full transfer + SDVtg message: " + text(doc, "result").slice(0, 90));
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(doc.getElementById("drop3-title").textContent === ST_NAME && text(doc, "file3-status").includes(`OS officiel Syntakt ${ST_VERSION} reconnu`),
      "FR: loaded Syntakt file name kept, status translated");
    doc.querySelector('.lang button[data-lang="en"]').click();
    await wait(20);
    const combos = engineCombos(w);
    for (const [variant, msg] of [["syntakt-sd-cp", /after Chord come SDVtg \(SD VINTAGE\), CPVtg \(CP VINTAGE\)\./],
                                  ["syntakt-sd-cp-toy-bits-swarm", /after Chord come SDVtg \(SD VINTAGE\), CPVtg \(CP VINTAGE\), SYToy \(SY TOY\), SYBit \(SY BITS\), SYSwm \(SY SWARM\)\./],
                                  ["syntakt-cp", /after Chord come CPVtg \(CP VINTAGE\)\./]]) {
      await pickEngines(doc, combos[variant]);
      await settle(w);
      const fv = app.state.fw;
      check(fv && fv.ref && fv.sdv === variant && fv.name.endsWith(variant + ".syx"),
        `engines ${combos[variant].join(" + ")} -> reference build ${fv ? fv.name : ""}`);
      const n1 = sent.length;
      doc.getElementById("flash").click();
      for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
      check(sent.length - n1 === w.MCFlasher.splitMessages(fv.raw).length && msg.test(text(doc, "result")),
        `full transfer + message for ${combos[variant].join(" + ")}`);
    }
    doc.getElementById("eng-cp").click();
    await settle(w);
    check(!app.state.fw && app.state.fwError === "pick_one" && !doc.getElementById("feat-syntakt").checked,
      "every engine unticked -> no mod left to build");
    check(errors.length === 0, "no JS error in the Syntakt engines flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  console.log(fail ? `\nFAILED (${fail})` : "\nALL OK");
  process.exit(fail ? 1 : 0);
}
main();
