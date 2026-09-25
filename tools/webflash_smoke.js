/* Smoke test navigateur (jsdom) du flasher : charge la vraie page + ses scripts,
 * simule Web MIDI, clique "Activer le MIDI", teste build + envoi. */
const fs = require("fs");
const path = require("path");
const { pathToFileURL } = require("url");
const { JSDOM, VirtualConsole } = require("jsdom");

const FLASH = require("path").join(__dirname, "..", "docs", "flasher");
const SYNTH = process.argv[2];
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function load({ midi = true, ports = true, secure = true } = {}) {
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
      window.addEventListener("error", (e) => errors.push("window.onerror: " + ((e.error && e.error.message) || e.message)));
      window.addEventListener("unhandledrejection", (e) => errors.push("unhandled: " + ((e.reason && e.reason.message) || e.reason)));
      if (midi) {
        const outputs = new Map();
        if (ports) {
          outputs.set("iface", { id: "iface", name: "USB MIDI Interface", manufacturer: "Acme", send: (d) => sent.push(d.length) });
          outputs.set("dev", { id: "dev", name: "Elektron Model:Cycles", manufacturer: "Elektron", send: (d) => sent.push(d.length) });
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

async function main() {
  let fail = 0;
  const check = (cond, msg) => { console.log((cond ? "  ok  " : "  FAIL ") + msg); if (!cond) fail++; };

  // 1. Aucune erreur JS au chargement + wiring present (la regression ELEKTRON)
  {
    const { w, doc, errors } = await load();
    check(errors.length === 0, "chargement sans erreur JS " + (errors.length ? JSON.stringify(errors) : ""));
    check(typeof w.MCBuilder === "object", "window.MCBuilder present");
    check(!!w.MC_TWEAKS && w.MC_TWEAKS.tweaks.length === 3, "MC_TWEAKS charge (3 tweaks)");
    check(typeof w.loadFlasherBytes === "function", "loadFlasherBytes expose");
    check([...doc.getElementById("variant").options].length === 3, "menu Sortie USB peuple (origine + 2 variantes)");
    check(doc.getElementById("build").textContent === "Construire", "bouton Construire intact (estampille a part)");
    check(/build \d{4}-/.test(doc.getElementById("build-stamp").textContent), "estampille de version affichee");
    const extras = [...doc.querySelectorAll("#extras input[type=checkbox]")].map((c) => c.value);
    check(extras.length === 1 && extras[0] === "sdvintage-snare", "case « machine ajoutee » : " + JSON.stringify(extras));
    doc.getElementById("enable").click();
    await wait(60);
    const st = doc.getElementById("midi-status").textContent;
    check(/detectee/i.test(st), 'clic "Activer le MIDI" -> "' + st.slice(0, 50) + '"');
    const opts = [...doc.getElementById("port").options].map((o) => o.textContent);
    check(opts.length === 2, "ports listes : " + JSON.stringify(opts));
  }

  // 2. Web MIDI absent (Firefox/Safari) -> message clair, pas de silence
  {
    const { doc } = await load({ midi: false });
    doc.getElementById("enable").click();
    await wait(30);
    const st = doc.getElementById("midi-status").textContent;
    check(/indisponible|Chrome/i.test(st), 'sans Web MIDI -> "' + st.slice(0, 40) + '"');
  }

  // 3. Contexte non securise (file://) -> message clair
  {
    const { doc } = await load({ secure: false });
    doc.getElementById("enable").click();
    await wait(30);
    const st = doc.getElementById("midi-status").textContent;
    check(/securise|localhost|https/i.test(st), 'file:// -> "' + st.slice(0, 45) + '"');
  }

  // 4. Build depuis un OS synthetique, puis envoi
  if (SYNTH) {
    const { w, doc, errors, sent } = await load();
    const raw = new Uint8Array(fs.readFileSync(path.join(SYNTH, "synth.syx")));
    const meta = JSON.parse(fs.readFileSync(path.join(SYNTH, "meta.json")));
    w.MC_TWEAKS.device.section_sha256 = meta.section_sha256;   // l'OS reel differe
    const tw = w.MC_TWEAKS.tweaks.find((t) => t.id === "6ch-usbup");
    const built = w.MCBuilder.build(raw, w.MC_TWEAKS.device, [tw], {});
    w.loadFlasherBytes(built.raw, "test.syx");
    await wait(30);
    check(/checksums OK/i.test(doc.getElementById("file-info").textContent), "image construite chargee et verifiee");
    doc.getElementById("enable").click();
    await wait(60);
    doc.getElementById("port").value = "iface";
    doc.getElementById("port").dispatchEvent(new w.Event("change"));
    doc.getElementById("ack").checked = true;
    doc.getElementById("ack").dispatchEvent(new w.Event("change"));
    doc.getElementById("pace").value = "0";
    check(!doc.getElementById("send").disabled, "bouton Flasher active apres port+case cochee");
    doc.getElementById("send").click();
    await wait(500);
    check(sent.length === built.raw.length ? false : sent.length >= 3, "messages envoyes : " + sent.length);
    check(errors.length === 0, "envoi sans erreur JS " + (errors.length ? JSON.stringify(errors) : ""));
  }

  console.log(fail ? `\nECHEC (${fail})` : "\nTOUT OK");
  process.exit(fail ? 1 : 0);
}
main();
