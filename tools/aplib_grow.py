"""Recompression aPLib (variante Elektron, tools/mtlib/aplib.py) d'une section AGRANDIE (notes/17).

mtlib.aplib.repack ré-émet le flux d'origine et passe en littéraux les octets modifiés ; il ne sait pas
ajouter d'octets après la fin. repack_grow fait la même chose pour la partie d'origine, puis compresse la
partie ajoutée avec un compresseur glouton simple (correspondances de 4 octets et plus, dans la partie
ajoutée seulement). Mêmes règles d'encodage que _Writer.match : décalage >= 1, longueur >= 2
(>= 3 au-delà de FAR_THRESHOLD), réutilisation du dernier décalage quand il est égal.

pack compresse une charge utile rangée compressée dans l'image (notes/50 §10) : il cherche mieux (chaînes de
hachage, correspondances courtes, dernier décalage, un pas d'attente), car chaque octet y compte sous 0x40200000.
"""
from mtlib import aplib

MIN_MATCH = 4
MAX_MATCH = 0xFFFF
WINDOW = 1 << 20


def _tail(w, data, start, last_off):
    n = len(data)
    table = {}
    i = start
    while i < n:
        best_len = best_off = 0
        if i + MIN_MATCH <= n:
            key = data[i:i + MIN_MATCH]
            cand = table.get(key)
            if cand is not None and i - cand <= WINDOW:
                length = MIN_MATCH
                limit = min(n - i, MAX_MATCH)
                while length < limit and data[cand + length] == data[i + length]:
                    length += 1
                best_len, best_off = length, i - cand
            table[key] = i
        if best_len >= MIN_MATCH:
            w.match(best_off, best_len, last_off)
            last_off = best_off
            for k in range(i + 1, min(i + best_len, n - MIN_MATCH + 1)):
                table[data[k:k + MIN_MATCH]] = k
            i += best_len
        else:
            w.literal(data[i])
            i += 1
    return last_off


def repack_grow(data, ops, dirty, orig_len):
    """Comme aplib.repack pour data[:orig_len] (dirty couvre tout data), puis la partie ajoutée."""
    w = aplib._Writer()
    last_off = 1
    lo = dirty.find(b"\x01", 0, orig_len)
    hi = dirty.rfind(b"\x01", 0, orig_len)
    if lo < 0:
        lo = hi = -1
    for kind, pos, off, n in ops:
        if kind == aplib.LITERAL:
            w.literal(data[pos])
            continue
        end = pos + n
        src = pos - off
        touched = False
        if lo >= 0 and src <= hi and end > lo:
            touched = (dirty.find(b"\x01", pos, end) >= 0 or dirty.find(b"\x01", src, src + n) >= 0)
        if touched:
            for k in range(pos, end):
                w.literal(data[k])
        else:
            w.match(off, n, last_off)
            last_off = off
    _tail(w, data, orig_len, last_off)
    w.end()
    body = w.o
    stream_len = len(body) - aplib.SECT_HDR
    body[0:4] = stream_len.to_bytes(4, "big")
    body[4:8] = (sum(body[aplib.SECT_HDR:]) & 0xFFFFFFFF).to_bytes(4, "big")
    return bytes(body)


# Compresseur de la charge utile (notes/50 §10) : chaînes de hachage sur 3 octets (PACK_DEPTH candidats, du plus
# proche au plus lointain), réutilisation du dernier décalage, correspondances de 2 octets proches, coût exact en bits
# de chaque correspondance, et un pas d'attente (« lazy ») : si la position suivante gagne plus d'un littéral de plus,
# on y va. Même format, même décompresseur (stub.S) ; 230 000 o au lieu de 247 441 pour la charge utile de l'OS 2.0.
PACK_DEPTH = 48
PACK_NEAR2 = 128


def _gbits(v):
    return 2 * (v.bit_length() - 1)


def _mbits(off, n, last):
    """Bits d'une correspondance, comme _Writer.match les écrit."""
    b = 3 if off == last else 9 + _gbits((off + aplib.OFFSET_BIAS) >> 8)
    base = n - 1 - (1 if off > aplib.FAR_THRESHOLD else 0)
    return b + (2 if base <= 3 else 2 + _gbits(base - 2))


def pack(data):
    """Flux aPLib (même variante), SANS l'en-tête de 8 o : charge utile rangée compressée dans l'image
    (append.compress = "aplib", notes/50), décompressée au démarrage par tools/machines/syntakt_bridge/stub.S (APLIB).
    Même algorithme octet pour octet que aplibPack de docs/flasher/builder.js."""
    n = len(data)
    far = aplib.FAR_THRESHOLD
    head = {}
    prev = [-1] * n
    ins = 0

    def mlen(c, i, limit):
        L = 0
        while L + 64 <= limit and data[c + L:c + L + 64] == data[i + L:i + L + 64]:
            L += 64
        while L < limit and data[c + L] == data[i + L]:
            L += 1
        return L

    def best(i, last):
        """(gain en bits, décalage, longueur) de la meilleure correspondance en i ; gain 0 : aucune."""
        nonlocal ins
        limit = min(n - i, MAX_MATCH)
        bg = bo = bl = 0
        if limit < 2:
            return 0, 0, 0
        if last <= i:
            L = mlen(i - last, i, limit)
            if L >= (3 if last > far else 2):
                g = 9 * L - _mbits(last, L, last)
                if g > bg:
                    bg, bo, bl = g, last, L
        if limit >= 3:
            while ins < i:
                if ins + 3 <= n:
                    k = data[ins:ins + 3]
                    prev[ins] = head.get(k, -1)
                    head[k] = ins
                ins += 1
            c = head.get(data[i:i + 3], -1)
            d = 0
            while c >= 0 and d < PACK_DEPTH:
                off = i - c
                if bl < limit and data[c + bl] == data[i + bl]:
                    L = mlen(c, i, limit)
                    if L >= (3 if off > far else 2):
                        g = 9 * L - _mbits(off, L, last)
                        if g > bg:
                            bg, bo, bl = g, off, L
                c = prev[c]
                d += 1
        if bl < 2:
            for off in range(1, min(i, PACK_NEAR2) + 1):
                if data[i - off] == data[i] and data[i - off + 1] == data[i + 1]:
                    g = 18 - _mbits(off, 2, last)
                    if g > bg:
                        bg, bo, bl = g, off, 2
                    break
        return bg, bo, bl

    w = aplib._Writer()
    last = 1
    i = 0
    while i < n:
        g, off, L = best(i, last)
        if g > 0 and i + 1 < n and best(i + 1, last)[0] > g + 9:
            g = 0
        if g > 0:
            w.match(off, L, last)
            last = off
            i += L
        else:
            w.literal(data[i])
            i += 1
    w.end()
    return bytes(w.o[aplib.SECT_HDR:])
