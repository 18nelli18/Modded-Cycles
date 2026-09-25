const fs = require("fs"), path = require("path");
const B = require("../docs/flasher/builder.js");
const dir = process.argv[2];
const meta = JSON.parse(fs.readFileSync(path.join(dir, "meta.json")));
const raw = new Uint8Array(fs.readFileSync(path.join(dir, "synth.syx")));
const tweaks = {};
for (const f of ["10-6ch-multiout", "11-6ch-usbup", "20-sdvintage-snare"]) {
  const t = JSON.parse(fs.readFileSync(`tweaks/model-cycles_OS1.13/${f}.json`));
  tweaks[t.id] = t;
}
const device = { device: meta.device, os: meta.os, section_sha256: meta.section_sha256 };
let ok = true;
for (const [key, e] of Object.entries(meta.expect)) {
  const exp = new Uint8Array(fs.readFileSync(path.join(dir, `expect_${key}.syx`)));
  const r = B.build(raw, device, e.ids.map((id) => tweaks[id]), { expectMainOsSha: e.sha_mainos });
  const same = r.raw.length === exp.length && r.raw.every((b, i) => b === exp[i]);
  console.log(`${key}: JS ${r.raw.length} o, MAIN OS ${r.mainOsSha.slice(0,16)}, ` +
    `${r.patchedBytes} octets patches, caves ${r.caves.zones.length} zone(s) ` +
    `(${r.caves.sure.length} sures/${r.caves.doubt.length} douteuses/${r.caves.gone.length} neutralisees) ` +
    `-> ${same ? "IDENTIQUE au Python" : "DIFFERENT !!"}`);
  ok = ok && same;
}

// regle des caves : meme verdict que build.check_caves (cf. webbuild_synth.py §5)
const { stream } = B.unwrap(raw);
const c = B.parseContainer(stream);
const s3 = c.sections.find((s) => s.id === 3);
const mainOs = B.aplibDepack(c.blob.subarray(s3.off, s3.off + s3.size)).data;
const verdict = (t) => {
  const { data, dirty } = B.applyWrites(mainOs, [t]);
  try { B.checkCaves(mainOs, [t], false, dirty, data); return "accepte"; }
  catch (err) { return "refuse"; }
};
const vr = verdict(meta.cave_rule.refuse), vn = verdict(meta.cave_rule.noop), va = verdict(meta.cave_rule.accept);
console.log(`regle des caves : zone encore referencee -> ${vr} ; pointeur reecrit a l'identique -> ${vn} ; ` +
  `avec redirection du sprite -> ${va}`);
ok = ok && vr === "refuse" && vn === "refuse" && va === "accepte";
process.exit(ok ? 0 : 1);
