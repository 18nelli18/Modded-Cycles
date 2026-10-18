"""Les prototypes exacts (non versionnés) : mix2 sans boucle morte (en place), PUNCH éteint en chemin court (masque
0x40186238), et l'arrêt des voix muettes (build_proto). Rend des tweaks au format du dépôt."""
import sys, subprocess, tempfile, pathlib
sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import build, sprites

HERE = pathlib.Path(__file__).resolve().parent
SEC3 = HERE.parent.parent.parent / "os" / "sec3.bin"
BASE = 0x40000400


def asm(src, defs=()):
    with tempfile.TemporaryDirectory() as d:
        o, b = pathlib.Path(d) / "a.o", pathlib.Path(d) / "a.bin"
        cmd = ["m68k-linux-gnu-as", "-mcpu=54418", "-o", str(o), str(HERE / src)]
        for k, v in defs:
            cmd[2:2] = ["--defsym", f"{k}={v}"]
        subprocess.run(cmd, check=True)
        assert "R_68K" not in subprocess.run(["m68k-linux-gnu-objdump", "-r", str(o)], capture_output=True, text=True).stdout
        subprocess.run(["m68k-linux-gnu-objcopy", "-O", "binary", "-j", ".text", str(o), str(b)], check=True)
        return b.read_bytes()


def w(stock, va, new):
    return {"off": va - BASE, "old": stock[va - BASE:va - BASE + len(new)].hex(), "new": new.hex()}


def mix2(stock):
    code = asm("mix2.S")[:0x1c]
    code += bytes.fromhex("4e71") * ((0x40 - len(code)) // 2)
    return {"id": "mix2-proto", "writes": [w(stock, 0x400a98c4, code)]}, []


PUNCH_MASK = 0x40186238


def punch(stock):
    code = asm("punch.S")
    assert len(code) <= sprites.MASKS[PUNCH_MASK][0]
    hook = 0x400a9714
    assert stock[hook - BASE:hook - BASE + 6].hex() == "2e2802a42213"
    ws = [{"off": hook - BASE, "old": "2e2802a42213", "new": "4ef9" + f"{PUNCH_MASK:08x}"},
          w(stock, PUNCH_MASK, code), sprites.redirect_write(PUNCH_MASK)]
    return {"id": "punch-proto", "writes": sorted(ws, key=lambda x: x["off"])}, [(PUNCH_MASK, len(code))]


def idle(stock):
    import build_proto
    tw, sym, ln = build_proto.tweak(stock)
    return tw, []


def image(*names):
    stock = SEC3.read_bytes()
    tws, extra = [], []
    for n in names:
        tw, ex = globals()[n](stock)
        tws.append(tw); extra += ex
    img, _ = build.apply_writes(stock, tws)
    return bytes(img), tws, extra
