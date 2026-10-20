#!/usr/bin/env python3
"""Génère les données du firmware principal fixe : enregistrement pas à pas et solo du mute verrouillé."""
import argparse
import json
import pathlib
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
STEP = ROOT / "tweaks/model-cycles_OS1.13/45-step-rec.json"
SOURCE = ROOT / "tools/machines/step_rec/latching_solo.S"
OUT = ROOT / "docs/flasher/step-rec-solo-data.js"
RUNTIME_END = 0x467b0000


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    step = json.loads(STEP.read_text(encoding="utf-8"))
    runtime = step.get("runtime_payload", {})
    if runtime.get("target_tweak") != "control-all-beat-repeat":
        raise SystemExit("!! Le Step Recorder ne cible pas le payload beat repeat du principal")
    start = int(runtime["dest"], 16) + len(bytes.fromhex(runtime["hex"]))
    prefix = next((p for p in ("m68k-elf-", "m68k-linux-gnu-")
                   if shutil.which(p + "as") and shutil.which(p + "ld") and shutil.which(p + "objcopy") and shutil.which(p + "nm")), None)
    if not prefix:
        raise SystemExit("!! binutils m68k requis pour compiler le solo")
    with tempfile.TemporaryDirectory(dir=ROOT / "build") as temporary:
        temp = pathlib.Path(temporary)
        obj, elf, raw, script = temp / "solo.o", temp / "solo.elf", temp / "solo.bin", temp / "solo.ld"
        script.write_text(f"SECTIONS {{ .solo {start:#x} : {{ *(.solo) }} }}\n", encoding="ascii")
        subprocess.run([prefix + "as", "-mcpu=54418", "-o", str(obj), str(SOURCE)], check=True)
        subprocess.run([prefix + "ld", "-T", str(script), "-o", str(elf), str(obj)], check=True)
        subprocess.run([prefix + "objcopy", "-O", "binary", "-j", ".solo", str(elf), str(raw)], check=True)
        symbols = {}
        for line in subprocess.check_output([prefix + "nm", str(elf)], text=True).splitlines():
            fields = line.split()
            if len(fields) == 3:
                symbols[fields[2]] = f"0x{int(fields[0], 16):08x}"
        solo = {"dest": f"0x{start:08x}", "hex": raw.read_bytes().hex()}
    if symbols.get("solo_pad") != solo["dest"] or int(solo["dest"], 16) + len(bytes.fromhex(solo["hex"])) > RUNTIME_END:
        raise SystemExit("!! Le code du solo sort de la plage libre verifiee")
    data = {"step": step, "solo": solo, "solo_symbols": symbols}
    text = "window.MCStepRecSoloData=" + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            raise SystemExit("!! step-rec-solo-data.js ne correspond pas aux sources")
        print("OK step-rec-solo-data.js")
    else:
        OUT.write_text(text, encoding="utf-8")
        print(f"Écrit {OUT.relative_to(ROOT)} ({len(bytes.fromhex(solo['hex']))} octets de solo)")


if __name__ == "__main__":
    main()
