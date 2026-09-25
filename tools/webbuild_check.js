const fs = require("fs"), path = require("path");
const B = require("../docs/flasher/builder.js");
const dir = process.argv[2];
const meta = JSON.parse(fs.readFileSync(path.join(dir, "meta.json")));
const raw = new Uint8Array(fs.readFileSync(path.join(dir, "synth.syx")));
const tweaks = {
  "6ch-multiout": JSON.parse(fs.readFileSync("tweaks/model-cycles_OS1.13/10-6ch-multiout.json")),
  "6ch-usbup": JSON.parse(fs.readFileSync("tweaks/model-cycles_OS1.13/11-6ch-usbup.json")),
};
const device = { device: meta.device, os: meta.os, section_sha256: meta.section_sha256 };
let ok = true;
for (const id of Object.keys(meta.expect)) {
  const exp = new Uint8Array(fs.readFileSync(path.join(dir, `expect_${id}.syx`)));
  const r = B.build(raw, device, [tweaks[id]], { expectMainOsSha: meta.expect[id].sha_mainos });
  const same = r.raw.length === exp.length && r.raw.every((b, i) => b === exp[i]);
  console.log(`${id}: JS ${r.raw.length} o, MAIN OS ${r.mainOsSha.slice(0,16)}, ` +
    `${r.patchedBytes} octets patches, caves ${r.caves.zones.length} zone(s) ` +
    `(${r.caves.sure.length} sures/${r.caves.doubt.length} douteuses) -> ${same ? "IDENTIQUE au Python" : "DIFFERENT !!"}`);
  ok = ok && same;
}
process.exit(ok ? 0 : 1);
