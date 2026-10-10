"""Génère le prototype PAN/niveau (notes/50), depuis le fichier officiel fourni.
Usage : python3 tools/gen_pan_level.py --cycles model-cycles_OS1.13.syx [--check].
Le prototype n’est pas inscrit au flasher avant preuve complète en émulation.
"""
from pathlib import Path
import argparse, hashlib, json, re, shutil, struct, subprocess, tempfile
import build as builder
from mtlib import aplib, container
from mtlib.syx import unwrap

ROOT = Path(__file__).resolve().parents[1]
CROSS = next((p for p in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(p+"as")), "m68k-elf-")
OUT = ROOT/"tweaks/model-cycles_OS1.13/44-pan-level-display.json"
BASE = 0x40000400
RUNTIME = 0x42339000
STOCK_SHA = 'cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98'
HOOKS = [
    (0x4001aa4e,'4fefffe048d70cfc','pan_encoder','pan_encoder_stock'),
    (0x4001b22a,'4e56ffc048d73cfc','pan_draw','pan_draw_stock'),
]

def run(*args):
    subprocess.run([CROSS + a[9:] if a.startswith("m68k-elf-") else a for a in args], cwd=ROOT, check=True, capture_output=True)

def compile_patch(stock, out):
    assert hashlib.sha256(stock).hexdigest() == STOCK_SHA
    out.mkdir(parents=True, exist_ok=True)
    replay = ['.text']
    for address,raw,hook,original in HOOKS:
        assert stock[address-BASE:address-BASE+8] == bytes.fromhex(raw)
        replay.extend([f'.globl {original}',f'{original}:',
            '.byte '+','.join('0x'+raw[i:i+2] for i in range(0,len(raw),2)),
            f'jmp 0x{address+8:08x}'])
    (out/'stock-replay.s').write_text('\n'.join(replay)+'\n')
    (out/'payload.ld').write_text(f'SECTIONS {{ . = 0x{RUNTIME:x}; .text : {{ *(.text) }} .rodata : {{ *(.rodata) }} .data : {{ *(.data) }} }}')
    run('m68k-elf-as','-mcpu=5475','tools/machines/pan_level/pan_level.S','-o',str(out/'payload.o'))
    run('m68k-elf-as','-mcpu=5475',str(out/'stock-replay.s'),'-o',str(out/'stock-replay.o'))
    run('m68k-elf-ld','-T',str(out/'payload.ld'),'-o',str(out/'payload.elf'),str(out/'payload.o'),str(out/'stock-replay.o'))
    run('m68k-elf-objcopy','-O','binary',str(out/'payload.elf'),str(out/'payload.bin'))
    nm = subprocess.check_output([CROSS+'nm','-n',str(out/'payload.elf')],text=True)
    symbols = {m[2]:int(m[1],16) for line in nm.splitlines() if (m:=re.match(r'([0-9a-f]+)\s+\w\s+(\S+)',line))}
    payload = (out/'payload.bin').read_bytes()
    b = bytearray(stock)
    changes = []
    def patch(address, before, after, label):
        offset = address-BASE
        assert b[offset:offset+len(before)] == before
        assert len(before) == len(after)
        b[offset:offset+len(before)] = after
        changes.append(dict(address=hex(address),before=before.hex(),after=after.hex(),label=label))
    for address,raw,hook,original in HOOKS:
        patch(address,bytes.fromhex(raw),b'\x4e\xf9'+struct.pack('>I',symbols[hook])+b'\x4e\x71',
            'entrée écran principal : '+hook)
    patch(0x4001aac2,bytes.fromhex('4eb94006f73a'),b'\x4e\xb9'+struct.pack('>I',symbols['level_pan_delta']),'pas PAN/niveau un ; maintien seize')
    patch(0x400081f2,bytes.fromhex('4eb940090f48'),b'\x4e\xb9'+struct.pack('>I',symbols['pan_ui_tick']),'horloge UI 30 Hz')
    loader_address = BASE+len(stock)
    (out/'loader.s').write_text(f'''.text
.globl boot_loader
boot_loader:
 move.l %d0,-(%sp)
 move.l %a2,-(%sp)
 pea .Lafter_stock
 move.l %a2,-(%sp)
 lea 0x4019b590,%a2
 jmp 0x40000464
.Lafter_stock:
 lea payload_source,%a2
 lea 0x{RUNTIME:x},%a0
 move.l #{(len(payload)+3)//4},%d0
.Lcopy:
 move.l (%a2)+,(%a0)+
 subq.l #1,%d0
 bne.s .Lcopy
 move.l (%sp)+,%a2
 move.l (%sp)+,%d0
 rts
.balign 4
payload_source:
.incbin "{out / 'payload.bin'}"
.balign 4
''')
    (out/'loader.ld').write_text(f'SECTIONS {{ . = 0x{loader_address:x}; .text : {{ *(.text) }} }}')
    run('m68k-elf-as','-mcpu=5475',str(out/'loader.s'),'-o',str(out/'loader.o'))
    run('m68k-elf-ld','-T',str(out/'loader.ld'),'-o',str(out/'loader.elf'),str(out/'loader.o'))
    run('m68k-elf-objcopy','-O','binary',str(out/'loader.elf'),str(out/'loader.bin'))
    patch(0x4000045c,bytes.fromhex('2f0a45f94019b590'),b'\x4e\xf9'+struct.pack('>I',loader_address)+b'\x4e\x71','copie avant effacement BSS')
    b.extend((out/'loader.bin').read_bytes())
    assert len(b) < 2*1024*1024
    (out/'mainos-level-pan.bin').write_bytes(b)
    manifest = dict(changes=changes, symbols={k:hex(v) for k,v in symbols.items()})
    return bytes(b), manifest, payload


def main_os(path):
    stream, _ = unwrap(Path(path).read_bytes())
    c = container.parse(stream)
    s = next(s for s in c["sections"] if s["id"] == 3)
    stock = aplib.depack(c["blob"][s["off"]:s["off"]+s["size"]])[0]
    if hashlib.sha256(stock).hexdigest() != STOCK_SHA:
        raise SystemExit("MAIN OS officiel 1.13 requis")
    return stock


def build_tweak(stock):
    with tempfile.TemporaryDirectory() as d:
        binary, manifest, payload = compile_patch(stock, Path(d))
    at = BASE+len(stock)
    tail = binary[len(stock):]
    parts = []
    start = 0
    # Les huit octets des prologues viennent du fichier de l'utilisateur, pas du dépôt.
    for address, raw, hook, original in HOOKS:
        code = bytes.fromhex(raw)
        offset = tail.index(code, 48)
        if offset > start:
            parts.append({"dest": hex(at+start), "hex": tail[start:offset].hex()})
        parts.append({"dest": hex(at+offset), "cycles": [hex(address),hex(address+8)]})
        start = offset+8
    if start < len(tail):
        parts.append({"dest": hex(at+start), "hex": tail[start:].hex()})
    conflicts = []
    for file in OUT.parent.glob("*.json"):
        t = json.loads(file.read_text())
        if t.get("append") and t.get("id") != "pan-level-display":
            conflicts.append(t["id"])
    tweak = dict(id="pan-level-display", order=44, name="Valeurs PAN et niveau temporaires",
        description=["Tourner LEVEL/DATA affiche le niveau ; FUNC + LEVEL/DATA affiche PAN pendant trois secondes.",
            "Pas normal de un ; clics inchangés. Prototype expérimental, non proposé au flasher.",
            "Généré par tools/gen_pan_level.py ; notes/50-valeurs-pan-niveau.md."],
        device="Model:Cycles", os="1.13", section=3, conflicts=sorted(conflicts),
        symbols=manifest["symbols"],
        writes=[dict(off=int(c["address"],16)-BASE,old=c["before"],new=c["after"])
            for c in manifest["changes"]],
        append=dict(at=hex(at),dest=hex(at),size=len(tail),parts=parts,reloc=[]))
    patched, _ = builder.apply_writes(stock,[tweak])
    assert patched+builder.payload_runtime(tweak,stock,None)==binary
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles",required=True)
    ap.add_argument("--check",action="store_true")
    args = ap.parse_args()
    text = json.dumps(build_tweak(main_os(args.cycles)),indent=1,ensure_ascii=False)+"\n"
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:
            raise SystemExit("JSON différent")
        print("ok : JSON à jour")
    else:
        OUT.write_text(text)
        print("ok : recette écrite")

if __name__ == "__main__":
    main()
