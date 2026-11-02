"""Recompression aPLib (variante Elektron, tools/mtlib/aplib.py) d'une section AGRANDIE (notes/17).

mtlib.aplib.repack ré-émet le flux d'origine et passe en littéraux les octets modifiés ; il ne sait pas
ajouter d'octets après la fin. repack_grow fait la même chose pour la partie d'origine, puis compresse la
partie ajoutée avec un compresseur glouton simple (correspondances de 4 octets et plus, dans la partie
ajoutée seulement). Mêmes règles d'encodage que _Writer.match : décalage >= 1, longueur >= 2
(>= 3 au-delà de FAR_THRESHOLD), réutilisation du dernier décalage quand il est égal.
"""
from mtlib import aplib

MIN_MATCH = 4
MAX_MATCH = 0xFFFF
WINDOW = 1 << 20


def _tail(w, data, start, last_off, candidates=1, history=False, window=WINDOW, minimum=MIN_MATCH):
    n = len(data)
    table = {}
    def remember(at):
        key=data[at:at+minimum]
        if candidates==1:table[key]=at;return
        chain=table.setdefault(key,[]);chain.append(at)
        if len(chain)>candidates:del chain[0]
    if history:
        for at in range(max(0,start-window),start):
            if at+minimum<=n:remember(at)
    i = start
    while i < n:
        best_len = best_off = best_score = 0
        if i + minimum <= n:
            key = data[i:i + minimum]
            found=table.get(key)
            chain=(() if found is None else (found,)) if candidates==1 else reversed(found or [])
            for cand in chain:
                if i-cand>window:continue
                length = minimum
                limit = min(n - i, MAX_MATCH)
                if minimum==MIN_MATCH and best_len and data[cand+best_len-1]!=data[i+best_len-1]:continue
                while length < limit and data[cand + length] == data[i + length]:
                    length += 1
                offset=i-cand
                base=length-1-int(offset>aplib.FAR_THRESHOLD)
                if base<1:continue
                offset_bits=2*(aplib.REUSE_GAMMA.bit_length()-1) if offset==last_off else 8+2*(((offset+aplib.OFFSET_BIAS)>>8).bit_length()-1)
                bits=1+offset_bits+2+(0 if base<=3 else 2*((base-2).bit_length()-1))
                score=9*length-bits
                if (length>best_len if minimum==MIN_MATCH else score>best_score):best_len,best_off,best_score=length,offset,score
                if length==limit:break
            remember(i)
        if best_len >= minimum:
            w.match(best_off, best_len, last_off)
            last_off = best_off
            for k in range(i + 1, min(i + best_len, n - minimum + 1)):
                remember(k)
            i += best_len
        else:
            w.literal(data[i])
            i += 1
    return last_off


def repack_grow(data, ops, dirty, orig_len, *, tail_candidates=1, tail_history=False, tail_window=WINDOW, tail_minimum=MIN_MATCH):
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
    _tail(w, data, orig_len, last_off, tail_candidates, tail_history, tail_window, tail_minimum)
    w.end()
    body = w.o
    stream_len = len(body) - aplib.SECT_HDR
    body[0:4] = stream_len.to_bytes(4, "big")
    body[4:8] = (sum(body[aplib.SECT_HDR:]) & 0xFFFFFFFF).to_bytes(4, "big")
    return bytes(body)


def pack(data):
    """Flux aPLib (même variante, même compresseur glouton que la partie ajoutée), SANS l'en-tête de 8 o : charge
    utile rangée compressée dans l'image (append.compress = "aplib", notes/50), décompressée au démarrage par
    tools/machines/syntakt_bridge/stub.S (APLIB). Même algorithme octet pour octet que aplibPack de
    docs/flasher/builder.js."""
    w = aplib._Writer()
    _tail(w, data, 0, 1)
    w.end()
    return bytes(w.o[aplib.SECT_HDR:])
