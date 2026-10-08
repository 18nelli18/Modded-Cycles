/* Constructions ciblées Chord Keys, Model-TG et Syntakt (notes/40 §22).
 * Référence Python : REF_MAINOS généré ; les autres sections restent intactes.
 * Aucun envoi MIDI ni fichier de firmware produit.
 * node tools/webchord_compat_check.js firmware/model-cycles_OS1.13.syx firmware/Syntakt_OS1.42.syx
 */
const fs = require("fs"), assert = require("assert"), vm = require("vm");
const B = require("../docs/flasher/builder.js");
const root = require("path").join(__dirname, "..");
const read = (file) => fs.readFileSync(require("path").join(root, file), "utf8");
const context = { window: {} };
vm.runInNewContext(read("docs/flasher/tweaks.js"), context);
const { device, tweaks } = context.window.MC_TWEAKS;
const match = read("docs/flasher/app.js").match(/const REF_MAINOS = (\{[\s\S]*?\n\});/);
assert(match, "REF_MAINOS absent");
const references = vm.runInNewContext(`(${match[1]})`);
const raw = new Uint8Array(fs.readFileSync(process.argv[2]));
const syntakt = new Uint8Array(fs.readFileSync(process.argv[3]));
const original = B.parseContainer(B.unwrap(raw).stream);
const cases = [
  ["chord-keys"],
  ["model-tg", "chord-keys"],
  ["6ch-usbup", "latching-mute", "trig-preview", "browser-scroll", "trig-hold", "arp", "tempo-max", "boot-anim", "chord-keys", "syntakt-sd-cp-toy-bits-swarm"],
  ["6ch-usbup", "model-tg-st", "trig-hold", "arp", "tempo-max", "boot-anim", "chord-keys", "syntakt-tg-sd-cp-toy-bits-swarm"],
];
for (const ids of cases) {
  const key = ids.join("+");
  assert(references[key], `Référence Python absente : ${key}`);
  const chosen = ids.map((id) => {
    const tweak = tweaks.find((item) => item.id === id);
    assert(tweak, `Tweak absent : ${id}`);
    return tweak;
  });
  const result = B.build(raw, device, chosen, { syntakt, expectMainOsSha: references[key] });
  const built = B.parseContainer(B.unwrap(result.raw).stream);
  for (const section of original.sections.filter((s) => s.id !== 3)) {
    const after = built.sections.find((s) => s.id === section.id);
    assert(after, `Section ${section.id} absente`);
    assert.deepStrictEqual(built.blob.subarray(after.off, after.off + after.size),
      original.blob.subarray(section.off, section.off + section.size));
  }
  console.log(`ok ${key} : MAIN OS identique au Python, autres sections intactes`);
}
