const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { open } = require("./test_retrosyn_flasher");

(async () => {
  const { w, errors } = open();
  try {
    await Promise.all([
      w.MCMidiMachineAllReady,
      w.MCMidiSafetyReady,
      w.MCPadModeReady,
    ]);
    const app = w.MCFlasherApp;
    assert(w.document.getElementById("mach-q"), "keep the Model:Cycles / Model:Samples selector");
    assert(w.document.getElementById("mach-cyc") && w.document.getElementById("mach-smp") && w.document.getElementById("mach-cos"));
    assert.equal(w.document.getElementById("fixed-six-usb"), null, "no flasher USB selector");
    assert.equal(app.isSelected("usb6"), true, "6ch is the fixed default");
    assert.equal(app.isSelected("track-filter"), true, "per-track filter stays in main");
    const selected = app.chosenTweaks();
    assert(selected.some((t) => t.id === "6ch-usbup"), "6ch build patch is included");
    assert(selected.some((t) => t.id === "wizard-continuous-filter"), "per-track filter patch is included");
    assert(!selected.some((t) => /diagnostic/i.test(t.id)), "diagnostics are excluded");

    const firmware = (name) => Uint8Array.from(fs.readFileSync(path.join(__dirname, "../firmware", name)));
    const raw = firmware("model-cycles_OS1.13.syx");
    const syntakt = firmware("Syntakt_OS1.42.syx");
    const composed = w.MCMidiBankCompose(selected, raw, syntakt);
    const pad = composed.tweaks.find((t) => t.id === "pad-selection");
    assert(pad?.symbols?.wf_usb_set, "Pad Setup USB switch is composed");
    assert(pad.symbols.wf_usb_two14 && pad.symbols.wf_usb_six14, "all USB ranges are included");
    assert(composed.tweaks.some((t) => t.id === "wizard-continuous-filter"), "filter survives composition");
    assert(!composed.tweaks.some((t) => /diagnostic/i.test(t.id)), "no diagnostic in composed firmware");
    const built = w.MCBuilder.build(raw, w.MC_TWEAKS.device, composed.tweaks, {
      syntakt,
      refMods: composed.refMods,
    });
    assert(built.modsChecked);
    assert(w.MCFlasher.verify(built.raw).count > 0);
    assert.equal(errors.length, 0, errors.join("\n"));
    const out = path.join(__dirname, "../build/usb-mode-main");
    fs.mkdirSync(out, { recursive: true });
    fs.writeFileSync(path.join(out, "main.syx"), built.raw);
    fs.writeFileSync(path.join(out, "main.json"), JSON.stringify({ tweaks: composed.tweaks }));
    console.log("PASS fixed 6ch default; no selector; filter included; USB Pad Setup switch composed; diagnostics absent; firmware checksums valid");
  } finally {
    w.close();
  }
})().catch((error) => {
  console.error(error.stack);
  process.exitCode = 1;
});
