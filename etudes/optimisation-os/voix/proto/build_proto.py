"""Construit le prototype « arrêt des voix muettes, OS d'origine » (tweak JSON de travail, non versionné)."""
import sys, json, struct, subprocess, tempfile, pathlib
sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import build, sprites

HERE = pathlib.Path(__file__).resolve().parent
SEC3 = HERE.parent.parent.parent / "os" / "sec3.bin"
BASE = 0x40000400
MASK = 0x40185f48          # sprite 34x34 libre (REGISTRY.md)
HOOK1, OLD1 = 0x400a7dfe, "b08465222046"
HOOK2, OLD2 = 0x400a7e24, "269522434280"


def assemble(n=64, t=4096):
    with tempfile.TemporaryDirectory() as d:
        o, b = pathlib.Path(d) / "a.o", pathlib.Path(d) / "a.bin"
        subprocess.run(["m68k-linux-gnu-as", "-mcpu=54418", f"--defsym", f"IDLE_N={n}", "--defsym", f"IDLE_T={t}",
                        "-o", str(o), str(HERE / "idle_stock.S")], check=True)
        rel = subprocess.run(["m68k-linux-gnu-objdump", "-r", str(o)], capture_output=True, text=True).stdout
        assert "R_68K" not in rel, rel
        syms = subprocess.run(["m68k-linux-gnu-nm", str(o)], capture_output=True, text=True).stdout
        subprocess.run(["m68k-linux-gnu-objcopy", "-O", "binary", "-j", ".text", str(o), str(b)], check=True)
        code = b.read_bytes()
    sym = {l.split()[2]: int(l.split()[0], 16) for l in syms.splitlines() if len(l.split()) == 3}
    return code, sym


def tweak(stock, n=64, t=4096):
    code, sym = assemble(n, t)
    size = sprites.MASKS[MASK][0]
    assert len(code) <= size, (len(code), size)
    w = []
    for va, old, tgt in ((HOOK1, OLD1, MASK + sym["gate"]), (HOOK2, OLD2, MASK + sym["after"])):
        assert stock[va - BASE:va - BASE + 6].hex() == old
        w.append({"off": va - BASE, "old": old, "new": "4ef9" + f"{tgt:08x}"})
    w.append({"off": MASK - BASE, "old": stock[MASK - BASE:MASK - BASE + len(code)].hex(), "new": code.hex()})
    w.append(sprites.redirect_write(MASK))
    tw = {"id": "idle-stock-proto", "name": "Arrêt des voix muettes (prototype)", "writes": sorted(w, key=lambda x: x["off"])}
    return tw, sym, len(code)


def image(n=64, t=4096):
    stock = SEC3.read_bytes()
    tw, sym, ln = tweak(stock, n, t)
    img, _ = build.apply_writes(stock, [tw])
    return bytes(img), tw, sym, ln


if __name__ == "__main__":
    img, tw, sym, ln = image()
    (HERE / "idle-stock-proto.json").write_text(json.dumps(tw, indent=1, ensure_ascii=False) + "\n")
    print(f"code {ln} o dans le masque {MASK:#x} ({sprites.MASKS[MASK][0]} o) ; gate {MASK + sym['gate']:#x}, "
          f"after {MASK + sym['after']:#x}, QUIET {MASK + sym['QUIET']:#x}")
