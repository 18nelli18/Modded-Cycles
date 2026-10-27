#!/usr/bin/env python3
"""Preuve de la fenêtre de valeur d'Attack, du Filtre et de la Résonance (popup_view, notes/82), sur l'OS 1.13 avec
Model-TG ; au départ un diagnostic du rapport popup-envelope-re.md.

Le vrai 0x4001d818 (slot 144 de ParameterPageView, que Model-TG détourne par wf_popup 0x401ba49c puis saute
directement au code stock pour les identifiants testés) est appelé dans un vrai Bitmap 128 x 64, avec les polices et
les vecteurs de sprites construits au démarrage (0x400e7ccc, 0x400ab7b8). Pour chaque identifiant et chaque valeur
(0, 0x2000, 0x4000, 0x7f00), le banc note :

  (a) chaque DRAW_SPRITE 0x40071da4 : pointeur du sprite, x, y, mode, largeur x hauteur ;
  (b) chaque DRAW_TEXT 0x40071a04 et la chaîne effectivement dessinée ;
  (c) les appels aux points 0x40070c4e (creux) et 0x40070efc (plein) ;
  (d) le retour de vtable[64] 0x4000a66a (octet bas : 1 = grand nombre supprimé, 0 = texte dessiné) ;
  (e) les pixels finaux (nombre allumé, boîte englobante, CRC) et, avec --png, une image côte à côte.

Il imprime aussi, par identifiant, UI_REC[id] (+0x2c, +0x30, +0x5c, +0x60) et param_table (0x4010dce0 + id*56)
min (+8) / max (+12), puis confronte les affirmations du rapport aux mesures.

Puis la retouche (tools/popup_view.py) : Filtre (0x0c) dessiné comme celui du Sampler (0x49), Résonance (0x0b) comme
0x4a, pixel pour pixel ; Attack (0x0d) comme Amp Decay (0x18) dont la courbe (x 7..56, y 8..29) est retournée de
gauche à droite, le reste identique ; grand nombre et points pour les trois. Sort 1 si une vérification échoue ; les
affirmations du rapport (TIENT / FAUX) ne comptent pas.

    python3 tools/emu/test_popup_view.py --cycles firmware/model-cycles_OS1.13.syx \
        [--with model-tg-st,autre-tweak] [--syntakt firmware/Syntakt_OS1.42.syx] [--png build/popup-png]
"""
import argparse
import json
import pathlib
import struct
import sys
import zlib

from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import lofi_ui as L                 # noqa: E402
import test_sdvintage as T          # noqa: E402

STOCK_POPUP = 0x4001d818           # le code stock appelé par le slot 144 (Model-TG y saute pour ces ids)
PARAM_TABLE = 0x4010dce0           # descripteurs de paramètres, 56 o chacun
VT64 = 0x4000a66a                  # vtable[64] de l'objet des paramètres : 0 = chiffres, 1 = dessin spécial
DOT_OUTLINE, DOT_FILLED = 0x40070c4e, 0x40070efc
IDS = [
    (0x18, "Amp Decay",          0x40fe401c),
    (0x49, "Sampler Filter",     0x40fe3ce0),
    (0x4a, "Sampler Resonance",  0x40fe3364),
    (0x0d, "Attack",             None),
    (0x0c, "track Filter",       None),
    (0x0b, "track Resonance",    None),
]
VALUES = (0, 0x2000, 0x4000, 0x7f00)
FAIL = []
FACTS = []
CLAIMS = []


def check(ok, msg):
    """Un fait d'exécution : il doit être vrai (sinon pas de « TOUT OK »)."""
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    FACTS.append(bool(ok))
    if not ok:
        FAIL.append(msg)


def claim(ok, msg):
    """Une affirmation du rapport : fausse n'est pas une erreur du banc."""
    print(("  TIENT " if ok else "  FAUX  ") + msg, flush=True)
    CLAIMS.append(bool(ok))


class KeepSprites(dict):
    """Le dict des interceptions de UI.popup, sauf DRAW_SPRITE : on veut voir le vrai dessin pour les pixels."""

    def __setitem__(self, key, value):
        if key == L.DRAW_SPRITE:
            return
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if key == L.DRAW_SPRITE:
            return
        super().__delitem__(key)


class PopupView(L.UI):
    """UI de l'OS, plus les polices/vecteurs de sprites du démarrage et la trace des appels de dessin."""

    WATCH = {STOCK_POPUP: "popup", L.DRAW_TEXT: "texte", L.DRAW_SPRITE: "sprite",
             DOT_OUTLINE: "point", DOT_FILLED: "point_plein", VT64: "vt64"}

    def __init__(self, img, payload=None, end=None):
        self.trace, self.vt64, self._vt64_ret, self.popup_hits = [], [], [], 0
        super().__init__(img, payload, end=end)
        self.fonts_ok = self._call_ok(0x400e7ccc)             # polices/objets statiques du dessin
        self.sprites_ok = self._call_ok(0x400ab7b8, 1, 0xffff)  # vecteurs de sprites (decay, filtre, résonance...)
        self.vectors = self._vectors()

    def _call_ok(self, fn, *args):
        self.call(fn, *args, count=50_000_000)
        return not self.bad and self.sp_ok

    def _vectors(self):
        """{adresse de vecteur: (begin, count)} pour les trois vecteurs du rapport."""
        out = {}
        for vec in (0x40fe401c, 0x40fe3ce0, 0x40fe3364):
            b, e, _ = struct.unpack(">III", self.uc.mem_read(vec, 12))
            out[vec] = (b, (e - b) // 28 if e >= b else 0)
        return out

    def _hook(self, uc, addr, size, ud):
        if addr == STOCK_POPUP:
            self.popup_hits += 1
        if addr in self.WATCH:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))     # 8 : texte a son 7e argument
            ret = self.u32(sp)
            if self.WATCH[addr] == "vt64":
                self._vt64_ret.append(ret)
            self.trace.append({"kind": self.WATCH[addr], "args": args, "ret": ret})
        if self._vt64_ret and addr == self._vt64_ret[-1]:
            self._vt64_ret.pop()
            d0 = uc.reg_read(mk.UC_M68K_REG_D0)
            self.vt64.append((addr, d0 & 0xff, d0))
        super()._hook(uc, addr, size, ud)

    def popup_probe(self, desc, val):
        """Appelle le vrai slot 144 dans un écran neuf ; les sprites sont dessinés, pas remplacés par un relevé."""
        self.trace.clear()
        self.vt64.clear()
        self._vt64_ret.clear()
        self.popup_hits = 0
        real_hooks = self.hooks
        self.hooks = KeepSprites(real_hooks)
        err, out = None, None
        try:
            out = L.UI.popup(self, desc, val)
        except Exception as exc:                 # diagnostic : une erreur se lit dans le tableau, sans arrêter
            err = str(exc)
        finally:
            self.hooks = real_hooks
        return out, err

    def origin(self, sprite):
        """(vecteur, index) statique du sprite copié, d'après ses plans image/masque."""
        if not sprite:
            return None
        image, mask = self.u32(sprite + 0x10), self.u32(sprite + 0x14)
        for vec, (b, n) in self.vectors.items():
            for i in range(n):
                elem = b + 28 * i
                if self.u32(elem + 0x10) == image and self.u32(elem + 0x14) == mask:
                    return vec, i
        return None


def pixels(fb):
    """[y][x], y = 0 en bas, depuis le tampon 1 bit par pixel de Bitmap."""
    return [[(struct.unpack(">I", fb[8 * x + 4 * (y // 32):8 * x + 4 * (y // 32) + 4])[0] >> (31 - y % 32)) & 1
             for x in range(128)] for y in range(64)]


def png(path, screens, scale=4):
    """Les écrans côte à côte (y vers le haut), en PNG, sans dépendance (style test_multiline_browser.py)."""
    gap = 8
    w = len(screens) * 128 * scale + (len(screens) - 1) * gap
    h = 64 * scale
    rows = []
    for yy in range(h):
        y = 63 - yy // scale
        line = bytearray()
        for k, px in enumerate(screens):
            if k:
                line += bytes([0x40]) * gap
            for x in range(128):
                line += bytes([0xf0 if px[y][x] else 0x10]) * scale
        rows.append(b"\0" + bytes(line))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
    pathlib.Path(path).write_bytes(data)


def px_summary(fb):
    if fb is None:
        return "ECHEC"
    px = pixels(fb)
    pts = [(x, y) for y in range(64) for x in range(128) if px[y][x]]
    if not pts:
        return "0 px"
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (f"{len(pts):4d} px bbox x{min(xs)}..{max(xs)} y{min(ys)}..{max(ys)} "
            f"crc=0x{zlib.crc32(fb) & 0xffffffff:08x}")


def sprite_line(view, sprites):
    if not sprites:
        return "-"
    out = []
    for rec in sprites:
        _, sprite, x, y, mode = rec["args"][:5]
        if not sprite:
            out.append("null")
            continue
        w, h = struct.unpack(">II", view.uc.mem_read(sprite + 4, 8))
        org = view.origin(sprite)
        where = f"0x{org[0]:08x}#{org[1]}" if org else "-"
        out.append(f"0x{sprite:08x} {w}x{h} @({x},{y}) m{mode} {where}")
    return " ; ".join(out)


def text_line(view, texts):
    if not texts:
        return "-"
    out = []
    for rec in texts:
        ptr = rec["args"][6]
        s = view.cstr(ptr) if ptr else ""
        out.append('"' + s + '"')
    return " ; ".join(out)


def points_line(dots):
    if not dots:
        return "0"
    top = [d for d in dots if d["ret"] != 0x40070f40]      # le plein appelle le creux : ne pas le compter deux fois
    outline = sum(d["kind"] == "point" for d in top)
    filled = sum(d["kind"] == "point_plein" for d in top)
    centers = sorted({(d["args"][1] + d["args"][3]) // 2 for d in top})
    internal = len(dots) - len(top)
    s = f"{len(top)} ({outline}/{filled}) @{','.join(map(str, centers))}"
    return s + (f" +{internal} int" if internal else "")


def vec_count(view, vec):
    return view.vectors.get(vec, (0, 0))[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="model-tg-st",
                    help="tweaks appliqués, ids séparés par des virgules (model-tg-st toujours inclus)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx, si un tweak --with en extrait un moteur")
    ap.add_argument("--png", help="dossier des images côte à côte (un PNG par identifiant)")
    args = ap.parse_args()

    stock = T.main_os_from_syx(args.cycles)
    by_id = {}
    for f in (HERE.parent.parent / "tweaks" / "model-cycles_OS1.13").glob("*.json"):
        if f.name != "device.json":
            t = json.loads(f.read_text(encoding="utf-8"))
            by_id[t["id"]] = t
    ids = [i for i in args.others.split(",") if i]
    if "model-tg-st" not in ids:                    # le banc est défini sur l'image avec Model-TG
        ids.insert(0, "model-tg-st")
    ids = list(dict.fromkeys(ids))
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise SystemExit(f"!! tweak(s) inconnu(s) : {', '.join(missing)}")
    tweaks = [by_id[i] for i in ids]
    pl, _ = build.build_payload(tweaks, stock, args.syntakt)
    img = build.apply_writes(stock, sorted(tweaks, key=lambda t: t["order"]))[0] + pl
    payload = None                              # moteurs du Syntakt : leur charge utile, copiée au démarrage
    ours = [t for t in tweaks if t.get("append") and not t["id"].startswith("model-tg")]
    if ours:
        import syntakt                          # noqa: E402 (seulement avec les moteurs)
        payload = (int(ours[0]["append"]["dest"], 16),
                   build.payload_runtime(ours[0], stock, syntakt.dsp_image(args.syntakt)))

    print(f"firmware : {', '.join(ids)}")
    print(f"image    : 0x{build.BASE + len(img):08x} ({len(img)} o, charge utile {len(pl)} o)")
    view = PopupView(img, payload, end=build.BASE + len(img))
    slot = view.u32(L.POPUP_SLOT)
    print(f"popup    : slot 144 de 0x{L.PAGE_VT:08x} -> 0x{slot:08x} ; stock 0x{STOCK_POPUP:08x} "
          f"(Model-TG y saute pour ces identifiants)")
    print(f"objets   : UI_REC=0x{L.UI_REC:08x}, vtable objet=0x{L.VTABLE:08x}, vt[64]=0x{view.u32(L.VTABLE + 64):08x}")
    print("légende  : vt64 = octet bas du retour de 0x4000a66a ; points = 0x40070c4e (creux) / "
          "0x40070efc (plein), « +N int » = appels internes du plein au creux ; "
          "sprite = pointeur, largeur x hauteur, @(x,y), mode, vecteur#index")
    check(view.init_ok and view.fonts_ok and view.sprites_ok,
          "objets d'interface (0x400de244), polices (0x400e7ccc) et sprites (0x400ab7b8) construits")
    check(vec_count(view, 0x40fe401c) == 15 and vec_count(view, 0x40fe3ce0) == 7
          and vec_count(view, 0x40fe3364) == 11,
          f"vecteurs : decay 15, filtre 7, résonance 11 sprites "
          f"({vec_count(view, 0x40fe401c)}/{vec_count(view, 0x40fe3ce0)}/{vec_count(view, 0x40fe3364)})")

    results = {}
    shots = {}
    for pid, label, vec in IDS:
        rec = L.UI_REC + 100 * pid
        fields = [view.u32(rec + off) for off in (0x2c, 0x30, 0x5c, 0x60)]
        ptab = PARAM_TABLE + pid * 56
        mn, mx = struct.unpack(">ii", view.uc.mem_read(ptab + 8, 8))
        print(f"\n0x{pid:02x} {label}")
        print(f"  UI_REC +0x2c=0x{fields[0]:08x} +0x30=0x{fields[1]:08x} "
              f"+0x5c=0x{fields[2]:08x} +0x60=0x{fields[3]:08x} ; "
              f"param_table 0x{ptab:08x} min={mn} (0x{mn & 0xffffffff:08x}) max={mx} (0x{mx & 0xffffffff:08x})")
        print(f"  {'val':>8}  {'vt64':>4}  {'texte':<7}  {'sprite(s)':<54}  {'points (creux/plein)':<30}  pixels")
        rows = []
        for val in VALUES:
            out, err = view.popup_probe(pid, val)
            sprites = [t for t in view.trace if t["kind"] == "sprite"]
            texts = [t for t in view.trace if t["kind"] == "texte"]
            dots = [t for t in view.trace if t["kind"] in ("point", "point_plein")]
            vt = view.vt64[-1][1] if view.vt64 else None
            row = {"val": val, "vt": vt, "texts": texts, "sprites": sprites, "dots": dots,
                   "out": out, "err": err, "hits": view.popup_hits,
                   "sprites_txt": sprite_line(view, sprites), "texts_txt": text_line(view, texts),
                   "points_txt": points_line(dots), "pixels_txt": px_summary(out[0] if out else None)}
            rows.append(row)
            print(f"  0x{val:04x}     {str(vt) if vt is not None else '?':>4}  {row['texts_txt']:<7}  "
                  f"{row['sprites_txt']:<54}  {row['points_txt']:<30}  {row['pixels_txt']}")
            if out:
                shots.setdefault(pid, []).append(pixels(out[0]))
            check(out is not None and err is None and row["hits"] == 1,
                  f"0x{pid:02x} valeur 0x{val:04x} : fenêtre dessinée par 0x{STOCK_POPUP:08x} "
                  f"({row['hits']} entrée), sans accès hors mémoire")
        results[pid] = (rows, mn, mx)

    # --- confrontation au rapport ---------------------------------------------------------------------------------
    print("\nBilan des affirmations du rapport popup-envelope-re.md")
    r18 = results[0x18][0]
    decay_ok = all(r["vt"] == 0 and len(r["sprites"]) == 1 and r["texts"] for r in r18)
    decay_ok = decay_ok and all("50x22 @(32,19) m1 0x40fe401c#" in r["sprites_txt"] for r in r18)
    idx18 = [r["sprites_txt"].split("#")[1].split()[0] if "#" in r["sprites_txt"] else "?" for r in r18]
    claim(decay_ok,
          f"Amp Decay 0x18 : 4/4 valeurs -> un sprite 50x22 centré (32,19) mode 1, du vecteur 0x40fe401c, "
          f"indices {','.join(idx18)} (choisi par la valeur)")
    for pid, vec in ((0x49, "0x40fe3ce0"), (0x4a, "0x40fe3364")):
        rows = results[pid][0]
        ok = all(r["vt"] == 0 and len(r["sprites"]) == 1 and r["texts"] for r in rows)
        ok = ok and all(f"48x22 @(32,19) m1 {vec}#" in r["sprites_txt"] for r in rows)
        idx = [r["sprites_txt"].split("#")[1].split()[0] if "#" in r["sprites_txt"] else "?" for r in rows]
        claim(ok, f"0x{pid:02x} : 4/4 valeurs -> un sprite 48x22 centré (32,19) mode 1, du vecteur {vec}, "
                  f"indices {','.join(idx)}")
    bcd = [results[i][0] for i in (0x0b, 0x0c, 0x0d)]
    no_env = all(not any(("50x22" in r["sprites_txt"] or "48x22" in r["sprites_txt"]) for r in rows) for rows in bcd)
    vt1 = all(all(r["vt"] == 1 for r in rows) for rows in bcd)
    no_text = all(all(not r["texts"] for r in rows) for rows in bcd)
    knob = all(all(r["sprites"] and "19x17 @(96,34) m1" in r["sprites_txt"] for r in rows) for rows in bcd)
    claim(no_env and vt1 and no_text and knob,
          "0x0b/0x0c/0x0d : aucun sprite d'enveloppe 50x22 ou 48x22, grand nombre supprimé (vt[64]=1, 0 DRAW_TEXT), "
          "à la place un bouton 19x17 @(96,34) mode 1 (4/4 valeurs, 0x0b/0x0c/0x0d)")
    zero = all(results[i][1] == 0 and results[i][2] == 0 for i in (0x0b, 0x0c, 0x0d))
    vals = ", ".join(f"0x{i:02x}: min={results[i][1]} max={results[i][2]}" for i in (0x0b, 0x0c, 0x0d))
    claim(zero, f"0x0b/0x0c/0x0d : min=max=0 ; mesuré {vals} (les 5 points se dessinent normalement)")
    print(f"  affirmations : {sum(CLAIMS)}/{len(CLAIMS)} tiennent (avant la retouche popup_view)")

    # --- la retouche popup_view (notes/82) ---------------------------------------------------------------------------
    print("\nRetouche popup_view (tools/popup_view.py, notes/82)")
    for pid, ref, label in ((0x0c, 0x49, "Filtre comme celui du Sampler"), (0x0b, 0x4a, "Résonance comme celle du "
                                                                                       "Sampler")):
        same = all(a == b for a, b in zip(shots[pid], shots[ref])) and len(shots[pid]) == len(VALUES)
        txt = [r["texts_txt"] for r in results[pid][0]] == [r["texts_txt"] for r in results[ref][0]]
        check(same and txt and all(r["vt"] == 0 for r in results[pid][0]),
              f"0x{pid:02x} : {label} (0x{ref:02x}), pixel pour pixel, même nombre ({', '.join(r['texts_txt'] for r in results[pid][0])}), 4/4 valeurs")
    flip_ok, rest_ok = True, True
    for a, d in zip(shots[0x0d], shots[0x18]):
        for y in range(64):
            for x in range(128):
                if 8 <= y <= 29 and 7 <= x <= 56:
                    flip_ok &= a[y][x] == d[y][7 + 56 - x]
                else:
                    rest_ok &= a[y][x] == d[y][x]
    txt = [r["texts_txt"] for r in results[0x0d][0]] == [r["texts_txt"] for r in results[0x18][0]]
    check(flip_ok and len(shots[0x0d]) == len(VALUES),
          "0x0d Attack : la courbe d'Amp Decay retournée de gauche à droite (x 7..56, y 8..29), 4/4 valeurs")
    check(rest_ok and txt and all(r["vt"] == 0 for r in results[0x0d][0]),
          f"0x0d Attack : hors de la courbe, la fenêtre d'Amp Decay telle quelle : grand nombre "
          f"({', '.join(r['texts_txt'] for r in results[0x0d][0])}) et points")
    changes = len({tuple(map(tuple, s_)) for s_ in shots[0x0d]})
    check(changes == len(VALUES), f"0x0d Attack : la courbe suit la valeur ({changes} images différentes sur {len(VALUES)})")

    if args.png:
        out = pathlib.Path(args.png)
        out.mkdir(parents=True, exist_ok=True)
        print("\nPNG (une image par identifiant, valeurs 0, 0x2000, 0x4000, 0x7f00 de gauche à droite)")
        for pid, label, _ in IDS:
            path = out / f"popup-{pid:02x}.png"
            png(path, shots[pid])
            print(f"  0x{pid:02x} {label:<20} {path}")

    print("\nTOUT OK" if all(FACTS) else f"\n{len(FAIL)} ÉCHEC(S)")
    return 0 if all(FACTS) else 1              # les affirmations du rapport ne comptent pas


if __name__ == "__main__":
    sys.exit(main())
