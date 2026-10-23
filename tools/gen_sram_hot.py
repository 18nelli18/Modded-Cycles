#!/usr/bin/env python3
"""Code chaud en SRAM interne, chargé selon les machines du projet (notes/76) : analyse et tables du chargeur
(tools/machines/sram_hot/hot.c), pour le tweak de l'OS (tools/gen_modal.py, qui l'appelle).

Entrées : l'image de l'OS construit (os.json : MAIN OS avec les écritures, bloc de Model-TG, charge utile en
mémoire) et le profil d'émulation (tools/machines/sram_hot/profile.json, tools/emu/profile_hot.py).

  1. Entrées : les cibles des appels et des sauts du profil, dans le code qui peut être recopié (OS, bloc de
     Model-TG, charge utile ; pas la SRAM, pas le chargeur).
  2. Fonctions : instructions atteintes depuis chaque entrée sans suivre les appels (désassemblage, tables de sauts
     relatives au PC comprises).
  3. Unités : fonctions réunies tant qu'une référence relative au PC sort de l'une vers l'autre, ou que leurs
     étendues se chevauchent ; une unité qui lit ou écrit relativement au PC hors d'elle (variables de Model-TG)
     est refusée.
  4. Corrections : champs de 32 bits (jsr, jmp, lea… absolus) qui visent une instruction d'une unité.
  5. Détours : entrées dont les premières instructions (6 o au moins) se déplacent telles quelles.
  6. Valeur : lignes chaudes de l'unité (le profil, par machine) par octet ; masque des machines qui s'en servent.

Rien de l'OS d'Elektron dans les tables : des adresses, des tailles, une somme de contrôle des octets déplacés.

    python3 tools/gen_sram_hot.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx   # résumé
"""
import argparse
import collections
import json
import pathlib
import re
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen_sdvintage_exact as gx    # noqa: E402  (CROSS, run)

SRC = HERE / "machines" / "sram_hot"
PROFILE = SRC / "profile.json"
BASE = 0x40000400
NAMES = ["KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD", "Sampler", "SDVtg", "CPVtg", "SYToy", "SYBit", "SYSwm",
         "MACRO", "ACID", "MODAL"]
SYNTAKT = (7, 8, 9, 10, 11)                  # machines du Syntakt (index des machines, Model-TG : TG_FIRST = 7)
OS_CODE = (BASE, 0x4019b590)                 # code et données de l'OS (la remise à zéro du BSS commence après)
BUDGET = 2048                                # octets recopiés par bloc au plus (chargement)
AUDIO_CALL = 0x40059382                      # jsr de la fonction audio (la passerelle : audio_probe)
VOICE_MAP = 0x400a7dc2                       # lea table machine -> entrée (la passerelle), boucle des voix
MACHINE = 0x8000102c                         # octet fort du paramètre MACHINE de la piste 0 (valeurs lues, + 0x42 t)
VOICE0, VSTRIDE = 0x42308828, 0x31c          # voix des pistes : +0, la machine qu'elle joue (boucle des voix, 0x400a7d7c)
# place du chargeur dans la charge utile (gen_macro_syntakt.TG_ROOM : le dernier Mo de la zone d'échantillons de
# Model-TG) : code (points d'entrée fixes, voir hot_asm.S), tables, variables (à zéro au démarrage)
HOT_AT, HOT_TAB, HOT_RAM, HOT_END = 0x4678a000, 0x4678c000, 0x4678e000, 0x46792000
ENTRY = dict(hot_boot=HOT_AT, hot_probe=HOT_AT + 6, st_away=HOT_RAM)
BRANCH = re.compile(r"^b(ra|sr|cc|cs|eq|ne|ge|gt|le|lt|hi|ls|mi|pl|vc|vs)[swl]?$")


# --- désassemblage ------------------------------------------------------------------------------------------------
class Mem:
    """Lecture de l'image construite : [(début, octets)]."""

    def __init__(self, chunks):
        self.chunks = sorted(chunks)

    def read(self, a, n):
        for lo, data in self.chunks:
            if lo <= a and a + n <= lo + len(data):
                return data[a - lo:a - lo + n]
        raise KeyError(f"{a:#x}")

    def has(self, a):
        return any(lo <= a < lo + len(data) for lo, data in self.chunks)


class Dis:
    """Instructions décodées à la demande (objdump sur une fenêtre) : ins[a] = (taille, mnémonique, opérandes)."""

    def __init__(self, mem, tmp):
        self.mem, self.tmp, self.ins = mem, pathlib.Path(tmp), {}

    def window(self, a, n=512):
        while n > 16:
            try:
                data = self.mem.read(a, n)
                break
            except KeyError:
                n //= 2
        else:
            return
        path = self.tmp / "win.bin"
        path.write_bytes(data)
        out = gx.run([gx.CROSS + "objdump", "-D", "-b", "binary", "-m", "m68k:isa-c:emac", f"--adjust-vma={a:#x}",
                      str(path)])
        for line in out.splitlines():
            m = re.match(r"\s*([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s*(.*)$", line)
            if m:
                ad = int(m.group(1), 16)
                if ad + 10 > a + n:
                    break
                self.ins.setdefault(ad, (len(m.group(2).replace(" ", "")) // 2, m.group(3), m.group(4).strip()))

    def at(self, a):
        if a not in self.ins:
            self.window(a)
        return self.ins.get(a)


def pc_targets(mn, ops):
    """Adresses visées relativement au PC (branchements compris)."""
    if BRANCH.match(mn):
        return [int(x, 16) for x in re.findall(r"0x([0-9a-f]+)", ops)]
    return [int(x, 16) for x in re.findall(r"%pc@\(0x([0-9a-f]+)", ops)]


def abs_values(mn, ops):
    """Adresses absolues des opérandes (ni relatives au PC, ni immédiats)."""
    if BRANCH.match(mn):
        return []
    ops = re.sub(r"%pc@\([^)]*\)", "", ops)
    return [int(x, 16) for x in re.findall(r"0x([0-9a-f]+)", ops)]


def function(d, entry, limit=6000):
    """Instructions atteintes depuis entry sans suivre les appels ; tables de sauts relatives au PC (switch de GCC :
    « moveq #n ; cmp ; bcs » puis « jmp %pc@(T,%dN:l) », n + 1 décalages de 16 bits en T)."""
    seen, stack, tables = {}, [entry], []
    while stack:
        a = stack.pop()
        if a in seen:
            continue
        i = d.at(a)
        if i is None:
            raise ValueError(f"{entry:#x} : rien à décoder en {a:#x}")
        seen[a] = i
        sz, mn, ops = i
        if mn.startswith(".") or mn in ("illegal", "halt"):
            raise ValueError(f"{entry:#x} : {mn} en {a:#x}")
        if BRANCH.match(mn) and not mn.startswith("bsr"):
            stack += pc_targets(mn, ops)
        elif mn == "jmp":
            if "%pc@" in ops and ",%d" in ops:
                tab = pc_targets(mn, ops)[0]
                n = None
                for back in sorted((x for x in seen if a - 24 <= x < a), reverse=True):
                    m = re.match(r"#(\d+),%d\d$", seen[back][2])
                    if seen[back][1] in ("moveq", "cmpil") and m:
                        n = int(m.group(1)) + 1
                        break
                if n is None:
                    raise ValueError(f"{entry:#x} : table de sauts en {a:#x} sans borne")
                raw = d.mem.read(tab, 2 * n)
                stack += [tab + struct.unpack_from(">h", raw, 2 * k)[0] for k in range(n)]
                tables.append((tab, 2 * n))
            elif "%pc@" in ops:
                stack += pc_targets(mn, ops)
            continue
        if mn in ("rts", "rte") or mn in ("bra", "bras", "braw", "bral"):
            continue
        stack.append(a + sz)
        if len(seen) > limit:
            raise ValueError(f"{entry:#x} : trop grande")
    lo = min(seen)
    hi = max([a + seen[a][0] for a in seen] + [t + n for t, n in tables])
    return dict(entry=entry, lo=lo, hi=hi, insns=seen, tables=tables)


# --- unités -------------------------------------------------------------------------------------------------------
def clusters(d, entries):
    """Unités : [dict(lo, hi, funcs, insns, bad)], fonctions réunies par références relatives au PC sortantes ou
    étendues qui se chevauchent."""
    funcs, refused = {}, {}
    for f in sorted(entries):
        try:
            funcs[f] = function(d, f)
        except (ValueError, KeyError) as ex:
            refused[f] = str(ex)
    parent = {f: f for f in funcs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    owner = {}
    for f, r in funcs.items():
        for a in r["insns"]:
            owner.setdefault(a, f)
    bad = collections.defaultdict(list)
    todo = list(funcs)
    while todo:
        f = todo.pop()
        r = funcs[f]
        for a, (sz, mn, ops) in r["insns"].items():
            for t in pc_targets(mn, ops):
                if r["lo"] <= t < r["hi"]:
                    continue
                g = owner.get(t)
                if g is None:
                    if not (BRANCH.match(mn) or mn in ("jsr", "jmp")):
                        bad[f].append(f"{a:#x} {mn} {ops}")      # donnée relative au PC hors de la fonction
                        continue
                    try:
                        funcs[t] = function(d, t)
                    except (ValueError, KeyError) as ex:
                        bad[f].append(f"{a:#x} {mn} {ops} : {ex}")
                        continue
                    parent[t] = t
                    for b in funcs[t]["insns"]:
                        owner.setdefault(b, t)
                    todo.append(t)
                    g = t
                parent[find(g)] = find(f)
    # étendues qui se chevauchent : une seule unité
    spans = sorted((r["lo"], r["hi"], f) for f, r in funcs.items())
    for (lo0, hi0, f0), (lo1, hi1, f1) in zip(spans, spans[1:]):
        if lo1 < hi0:
            parent[find(f1)] = find(f0)
    groups = collections.defaultdict(list)
    for f in funcs:
        groups[find(f)].append(f)
    out = []
    for fs in groups.values():
        insns = {}
        for f in fs:
            insns.update(funcs[f]["insns"])
        lo = min(funcs[f]["lo"] for f in fs)
        hi = max(funcs[f]["hi"] for f in fs)
        out.append(dict(lo=lo, hi=hi, funcs=sorted(fs), insns=insns, bad=[x for f in fs for x in bad.get(f, [])]))
    out.sort(key=lambda c: c["lo"])
    # deux unités qui se chevauchent encore (fonctions ajoutées pendant la fermeture) : réunies
    merged = []
    for c in out:
        if merged and c["lo"] < merged[-1]["hi"]:
            m = merged[-1]
            m.update(lo=min(m["lo"], c["lo"]), hi=max(m["hi"], c["hi"]), funcs=sorted(m["funcs"] + c["funcs"]),
                     bad=m["bad"] + c["bad"])
            m["insns"].update(c["insns"])
        else:
            merged.append(c)
    return merged, refused


def fixups(d, units):
    """Pour chaque unité : [(décalage du champ, index de l'unité visée)] ; vérifie que les cibles relatives au PC
    restent dans l'unité."""
    where = {}
    for k, u in enumerate(units):
        for a in u["insns"]:
            where[a] = k
    for k, u in enumerate(units):
        fx = []
        for a, (sz, mn, ops) in sorted(u["insns"].items()):
            for t in pc_targets(mn, ops):
                if not u["lo"] <= t < u["hi"]:
                    raise SystemExit(f"!! unité {u['lo']:#x} : {a:#x} {mn} {ops} sort de l'unité")
            raw = d.mem.read(a, sz)
            for v in set(abs_values(mn, ops)):
                if v not in where:
                    continue
                at = raw.find(v.to_bytes(4, "big"), 2)
                if at < 0 or raw.find(v.to_bytes(4, "big"), at + 1) >= 0:
                    raise SystemExit(f"!! {a:#x} {mn} {ops} : champ de {v:#x} introuvable ou double")
                fx.append((a - u["lo"] + at, where[v]))
        u["fix"] = fx
    return units


def detours(d, units, entries, targets, avoid=()):
    """[(entrée, index de l'unité, k)] : entrées dont les premières instructions (k >= 6 o) se déplacent : ni
    relatives au PC, ni EMAC, ni branchement, sans cible de saut connue entre l'entrée et entrée + k. avoid : pas de
    détour qui touche ces plages (le bloc de Model-TG : son assembleur peut sauter n'importe où dans ses fonctions,
    ses unités ne servent qu'aux appels entre copies ; les octets que les tweaks de l'OS écrivent)."""
    where = {}
    for k, u in enumerate(units):
        for a in u["insns"]:
            where[a] = k
    out, taken, avoid = [], [], list(avoid)
    for e in sorted(entries):
        if e not in where:
            continue
        u = units[where[e]]
        k, a, ok = 0, e, True
        while k < 6:
            i = u["insns"].get(a)
            if i is None:
                ok = False
                break
            sz, mn, ops = i
            raw = d.mem.read(a, sz)
            if pc_targets(mn, ops) or "%pc@" in ops or raw[0] & 0xf0 == 0xa0 or mn in ("rts", "rte") or \
                    (mn in ("jmp", "jsr") and not abs_values(mn, ops)):
                ok = False
                break
            k += sz
            a += sz
        if not ok or any(e < t < e + k for t in targets) or any(lo < e + k and e < hi for lo, hi in taken + avoid):
            continue
        taken.append((e, e + k))
        out.append((e, where[e], k))
    return out


def value(units, profile):
    """Lignes chaudes par machine de chaque unité ; masque des machines ; priorité (lignes chaudes par octet)."""
    lines = {}
    for m, name in enumerate(NAMES):
        ls = set()
        for lo, hi in profile["machines"][name]["lines"]:
            ls.update(range(int(lo, 16) >> 4, int(hi, 16) >> 4))
        lines[m] = ls
    for u in units:
        span = set(range(u["lo"] >> 4, (u["hi"] + 15) >> 4))
        hot = {m: len(span & lines[m]) for m in lines}
        u["mask"] = sum(1 << m for m, n in hot.items() if n)
        u["hot"] = max(hot.values())
        u["prio"] = u["hot"] * 16 / (u["hi"] - u["lo"])
    return units


def analyse(mem, profile, regions, root, exclude=(), avoid=()):
    """Tables du chargeur pour cette image. regions : place [(début, fin)] de code qu'on peut recopier ; root :
    l'entrée de la passerelle (audio_probe). Rend dict(units, dets, root_unit, root_off, refused)."""
    entries, targets = set(), set()
    for name in NAMES:
        for key in profile["machines"][name]["calls"]:
            a = int(key.split(":")[1], 16)
            targets.add(a)
            if any(lo <= a < hi for lo, hi in regions) and not any(lo <= a < hi for lo, hi in exclude):
                entries.add(a)
    entries.add(root)
    with tempfile.TemporaryDirectory() as tmp:
        d = Dis(mem, tmp)
        units, refused = clusters(d, entries)
        units = [u for u in units if not u["bad"] and any(lo <= u["lo"] and u["hi"] <= hi for lo, hi in regions)]
        for u in units:
            for a, (sz, mn, ops) in u["insns"].items():
                targets.update(pc_targets(mn, ops))
        value(units, profile)
        units.sort(key=lambda u: (u["lo"] > root or u["hi"] <= root, -u["prio"], u["lo"]))   # la racine d'abord
        fixups(d, units)
        dets = detours(d, units, entries, targets, avoid)
        sums = {e: sum(mem.read(e, k)) & 0xffff for e, _, k in dets}
    ru = next(k for k, u in enumerate(units) if u["lo"] <= root < u["hi"])
    return dict(units=units, dets=dets, sums=sums, root_unit=ru, root_off=root - units[ru]["lo"], refused=refused)


# --- tables et code -----------------------------------------------------------------------------------------------
def tables_c(an, regs):
    """hot_tables.c : unités (par priorité), corrections, détours, régions."""
    units, dets = an["units"], an["dets"]
    by_unit = collections.defaultdict(list)
    for i, (e, k_unit, k) in enumerate(dets):
        by_unit[k_unit].append(i)
    # les détours d'une unité à la suite : on les range par unité
    order = [i for k in range(len(units)) for i in by_unit[k]]
    new_index = {old: new for new, old in enumerate(order)}
    lines = ["/* genere par tools/gen_sram_hot.py (notes/76) : ne pas modifier */",
             "typedef unsigned char u8;", "typedef unsigned short u16;", "typedef unsigned int u32;",
             "struct hunit { u32 src; u16 len, mask, fix, nfix, det, ndet; };", "struct hfix { u16 off, unit; };",
             "struct hdet { u32 at; u16 unit, off, sum; u8 k, pad; };", "struct hreg { u32 lo, hi, src; u16 need, pad; };"]
    fix_rows, unit_rows, det_rows = [], [], []
    for k, u in enumerate(units):
        f0 = len(fix_rows)
        fix_rows += [f"\t{{{off:#x}, {t}}}," for off, t in sorted(u["fix"])]
        ds = by_unit[k]
        d0 = new_index[ds[0]] if ds else 0
        unit_rows.append(f"\t{{{u['lo']:#x}, {u['hi'] - u['lo']}, {u['mask']:#x}, {f0}, {len(u['fix'])}, {d0}, "
                         f"{len(ds)}}},")
    for i in order:
        e, k_unit, k = dets[i]
        det_rows.append(f"\t{{{e:#x}, {k_unit}, {e - units[k_unit]['lo']:#x}, {an['sums'][e]:#x}, {k}, 0}},")
    lines += ["const struct hunit hot_units[] = {"] + unit_rows + ["};"]
    lines += ["const struct hfix hot_fixes[] = {"] + (fix_rows or ["\t{0, 0},"]) + ["};"]
    lines += ["const struct hdet hot_dets[] = {"] + det_rows + ["};"]
    lines += ["const struct hreg hot_regs[] = {"] + [f"\t{{{lo:#x}, {hi:#x}, {src:#x}, {need:#x}, 0}},"
                                                     for lo, hi, src, need in regs] + ["};"]
    return "\n".join(lines) + "\n", order


LINK = """SECTIONS
{{
  .text {code:#x} : {{ hot_code = .; *hot_asm.o(.text) *(.text*) hot_code_end = .; }}
  .rodata {tab:#x} : {{ *(.rodata*) }}
  .bss {ram:#x} (NOLOAD) : {{ *(.bss.away) *(.bss*) *(COMMON) *(.data*) *(.sbss*) hot_ram_end = .; }}
  /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }}
}}
"""


def compile_hot(tmp, an, regs, root_orig, voice_map):
    """Le chargeur lié à HOT_AT (code), HOT_TAB (tables), HOT_RAM (variables) : (octets de HOT_AT à la fin des
    tables, symboles)."""
    tmp = pathlib.Path(tmp)
    text, order = tables_c(an, regs)
    (tmp / "hot_tables.c").write_text(text)
    defs = [f"-DHOT_NU={len(an['units'])}", f"-DHOT_NDET={max(len(an['dets']), 1)}", f"-DHOT_NREG={len(regs)}",
            f"-DHOT_ROOT_UNIT={an['root_unit']}", f"-DHOT_ROOT_OFF={an['root_off']:#x}",
            f"-DHOT_ROOT_ORIG={root_orig:#x}", f"-DHOT_MAP={voice_map:#x}", f"-DHOT_MACHINE={MACHINE:#x}",
            f"-DHOT_VOICE={VOICE0:#x}", f"-DHOT_VSTRIDE={VSTRIDE:#x}", f"-DHOT_BUDGET={BUDGET}"]
    objs = []
    for src in ("hot_asm.S", "hot.c", "hot_tables.c"):
        path = (SRC / src) if src != "hot_tables.c" else tmp / src
        o = tmp / (pathlib.Path(src).stem + ".o")
        flags = ["-mcpu=54418"] if src.endswith(".S") else list(gx.CFLAGS)
        gx.run([gx.CROSS + "gcc", *flags, *defs, "-c", str(path), "-o", str(o)])
        objs.append(str(o))
    ld, elf = tmp / "hot.ld", tmp / "hot.elf"
    ld.write_text(LINK.format(code=HOT_AT, tab=HOT_TAB, ram=HOT_RAM))
    gx.run([gx.CROSS + "ld", "-T", str(ld), "-o", str(elf), *objs])
    syms = {p[-1]: int(p[0], 16) for p in (l.split() for l in gx.run([gx.CROSS + "nm", str(elf)]).splitlines())
            if len(p) == 3}
    blobs = {}
    for sec in (".text", ".rodata"):
        out = tmp / f"{sec[1:]}.bin"
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", sec, str(elf), str(out)])
        blobs[sec] = out.read_bytes()
    for k, v in ENTRY.items():
        if syms.get(k) != v:
            raise SystemExit(f"!! {k} en {syms.get(k, 0):#x}, attendu en {v:#x} (hot_asm.S, .bss.away)")
    if HOT_AT + len(blobs[".text"]) > HOT_TAB or HOT_TAB + len(blobs[".rodata"]) > HOT_RAM \
            or syms["hot_ram_end"] > HOT_END:
        raise SystemExit(f"!! chargeur trop grand : code {len(blobs['.text'])} o, tables {len(blobs['.rodata'])} o, "
                         f"variables jusqu'à {syms['hot_ram_end']:#x}")
    blob = blobs[".text"] + bytes(HOT_TAB - HOT_AT - len(blobs[".text"])) + blobs[".rodata"]
    return blob, syms


def regions(lay, transit):
    """Place du chargeur : [(début, fin, source pour la rendre, machines qui la veulent en place)]. Le code du
    Syntakt et ses tables lues à chaque bloc (layout() de gen_syntakt_engines.py : à rendre depuis la zone de transit
    de la charge utile), puis les deux fins de SRAM que l'OS remet à zéro au démarrage (0x4000047c, 0x400004a4) et ne
    désigne nulle part (notes/76 §3)."""
    import gen_syntakt_engines as gs
    (t0, r0, n0), _ = lay["banks"]
    run = lay["run"]
    code_end = run(lay["stage"][-1][2] + lay["stage"][-1][1] - lay["stage"][-1][0])
    tabs = [(run(dst) - gs.GUARD, run(dst) + hi - lo + gs.GUARD) for lo, hi, dst in
            ((lo, hi, dst) for lo, hi, dst in lay["move"] if (lo, hi) in [tuple(t) for t in gs.SRAM_TABLES])]
    if len(tabs) != 2 or tabs[0][0] < code_end - 16 or tabs[1][1] != lay["voices"][0]:
        raise SystemExit(f"!! disposition de la SRAM du Syntakt inattendue : {[(hex(a), hex(b)) for a, b in tabs]}")
    src = lambda a: transit + a - r0
    mask = lambda ms: sum(1 << m for m in ms)
    regs = [(r0, tabs[0][0], src(r0), mask(SYNTAKT)),
            (tabs[0][0], tabs[0][1], src(tabs[0][0]), mask((7,))),             # SD VINTAGE : ses 2 tables
            (tabs[0][1], tabs[1][1], src(tabs[0][1]), mask((10, 11))),         # SY SWARM (et l'une de SY BITS)
            (0x800074c0, 0x80008000, 0, 0), (0x8000f6f0, 0x80010000, 0, 0)]
    for (lo0, hi0, *_), (lo1, *_) in zip(regs, regs[1:]):
        if lo1 < hi0:
            raise SystemExit("!! régions de SRAM qui se chevauchent")
    return regs


def os_image(stock, tweak):
    """Mem de l'OS construit avec ce tweak des moteurs (à la place du versionné) : MAIN OS avec les écritures des
    tweaks de os.json, bloc de Model-TG à sa place, charge utile du tweak en mémoire (à zéro hors de ses morceaux) ;
    et les plages écrites par ces tweaks dans la section 3."""
    import build
    dev = HERE.parent / "tweaks" / "model-cycles_OS1.13"
    tweaks = {}
    for f in dev.glob("[0-9]*.json"):
        t = json.loads(f.read_text(encoding="utf-8"))
        tweaks[t["id"]] = t
    tweaks[tweak["id"]] = tweak
    ids = json.loads((HERE.parent / "os.json").read_text(encoding="utf-8"))["tweaks"]
    chosen = sorted((tweaks[i] for i in ids), key=lambda t: t["order"])
    img, _ = build.apply_writes(stock, chosen)
    tg = next(t for t in chosen if t["id"].startswith("model-tg"))
    blob = bytes.fromhex(tg["append"]["parts"][0]["hex"])
    at = int(tg["append"]["at"], 16)
    dest = int(tweak["append"]["dest"], 16)
    rt = _runtime(tweak)
    written = [(BASE + w["off"], BASE + w["off"] + len(w["old"]) // 2) for t in chosen for w in t["writes"]]
    return Mem([(BASE, bytes(img)), (at, blob), (dest, rt)]), (at, at + len(blob)), written


def _runtime(t):
    """La charge utile en mémoire, sans les morceaux copiés du Syntakt (zéros : tables et code du Syntakt, que
    l'analyse ne lit pas) ni ceux de l'OS d'origine."""
    ap_ = t["append"]
    dest = int(ap_["dest"], 16)
    out = bytearray(ap_["size"])
    for part in ap_["parts"]:
        if "hex" in part:
            at = int(part["dest"], 16) - dest
            chunk = bytes.fromhex(part["hex"])
            out[at:at + len(chunk)] = chunk
    for va, old, new in ap_["reloc"]:
        at = int(va, 16) - dest
        if out[at:at + 4] == bytes.fromhex(old):
            out[at:at + 4] = bytes.fromhex(new)
    return bytes(out)


def add_to(out, stock, info):
    """Ajoute au tweak des moteurs (gen_modal.py, construit avec les points d'entrée ENTRY) le chargeur et ses
    tables, d'après l'image de l'OS avec ce tweak et le profil versionné. Rend un résumé."""
    mem, tg, written = os_image(stock, out)
    lay = info["lay"]
    dest = int(out["append"]["dest"], 16)
    transit_end = dest + sum(n for _, _, n in lay["banks"])
    root = info["audio_probe"]
    prof = json.loads(PROFILE.read_text(encoding="utf-8"))
    code = [OS_CODE, tg, (transit_end, HOT_AT)]
    an = analyse(mem, prof, code, root, exclude=[(HOT_AT, HOT_END)], avoid=[tg] + written)
    regs = regions(lay, dest)
    lea = mem.read(VOICE_MAP, 6)
    if lea[:2] != bytes.fromhex("41f9") or mem.read(0x400a7d7c, 6) != bytes.fromhex("4df9") + VOICE0.to_bytes(4, "big"):
        raise SystemExit(f"!! {VOICE_MAP:#x}, 0x400a7d7c : lea de la table des machines et des voix attendus")
    voice_map = struct.unpack(">I", lea[2:])[0]
    with tempfile.TemporaryDirectory() as tmp:
        blob, syms = compile_hot(tmp, an, regs, root, voice_map)
    out["append"]["parts"].append({"dest": f"{HOT_AT:#x}", "hex": blob.hex()})
    # les entrées détournées au démarrage (hot_boot) : octets de l'OS réécrits pendant qu'il tourne
    out["runtime"] = [{"off": e - BASE, "len": k, "why": "hot code in SRAM: jmp to its stub (hot_boot, notes/76)"}
                      for e, _, k in an["dets"] if OS_CODE[0] <= e < OS_CODE[1]]
    out["symbols"].update({k: f"{syms[k]:#x}" for k in ("hot_probe", "hot_boot", "hot_note", "hot_step", "hot_after",
                                                         "hot_code", "hot_code_end", "hot_tab", "hot_state",
                                                         "hot_sig", "hot_booted", "st_away", "hot_units", "hot_dets",
                                                         "hot_regs", "hot_stubs", "hot_n", "hot_orig")})
    out["symbols"]["audio_probe"] = f"{root:#x}"
    us = an["units"]
    return dict(units=len(us), bytes=sum(u["hi"] - u["lo"] for u in us), dets=len(an["dets"]),
                fixes=sum(len(u["fix"]) for u in us), code=len(blob))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(HERE / "emu"))
    import gen_syntakt_engines as gs
    import syntakt
    import test_mesure as T
    stock = T.stock_of(args.cycles)
    dev = HERE.parent / "tweaks" / "model-cycles_OS1.13"
    tweak = json.loads(next(dev.glob("31-*-modal.json")).read_text(encoding="utf-8"))
    mem, tg, written = os_image(stock, tweak)
    gs.set_base(gs.PAY_TG)
    lay = gs.analyse(syntakt.dsp_image(args.syntakt), gs.generation(["sd", "cp", "toy", "bits", "swarm"]))["lay"]
    dest = int(tweak["append"]["dest"], 16)
    code = [OS_CODE, tg, (dest + sum(n for _, _, n in lay["banks"]), HOT_AT)]
    an = analyse(mem, json.loads(PROFILE.read_text(encoding="utf-8")), code, int(tweak["symbols"]["audio_probe"], 16),
                 exclude=[(HOT_AT, HOT_END)], avoid=[tg] + written)
    us = an["units"]
    print(f"{len(us)} unités, {sum(u['hi'] - u['lo'] for u in us)} o, {sum(len(u['fix']) for u in us)} corrections, "
          f"{len(an['dets'])} détours ; entrées refusées : {len(an['refused'])}")
    for u in us[:12]:
        print(f"  {u['lo']:#x} {u['hi'] - u['lo']:6d} o  {u['hot']:4d} lignes chaudes  masque {u['mask']:#06x}")
    for lo, hi, src, need in regions(lay, dest):
        print(f"  région {lo:#x}..{hi:#x} {hi - lo:6d} o, en place pour {need:#06x}")


if __name__ == "__main__":
    main()
