/* Construction d'un firmware .syx modifie, dans le navigateur.
 *
 * Port JavaScript de tools/build.py + tools/mtlib/ (SysEx, codec aPLib,
 * conteneur ELE3, derivation de cle HMAC). Part de TON OS officiel et applique
 * une table de patchs (tweak). Rien n'est envoye a un serveur ; aucune image
 * firmware n'est incluse.
 *
 * Fidelite : chaque couche reproduit le Python a l'octet pres.
 * tools/webbuild_check.sh le verifie contre tools/build.py sur des images
 * synthetiques (pipeline complet, HMAC compris).
 *
 * Enveloppe dans une IIFE : en <script> classique, les declarations de premier
 * niveau sont globales et entreraient en collision avec flasher.js.
 */
(function () {
"use strict";

// ===========================================================================
// SHA-256 + HMAC-SHA256 (synchrones, sur Uint8Array)
// ===========================================================================
const _K = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]);

function sha256(msg) {
  const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                             0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const l = msg.length;
  const withPad = ((l + 8) >> 6) + 1;         // blocs de 64 o
  const buf = new Uint8Array(withPad * 64);
  buf.set(msg);
  buf[l] = 0x80;
  const bits = l * 8;
  const dv = new DataView(buf.buffer);
  dv.setUint32(buf.length - 4, bits >>> 0, false);
  dv.setUint32(buf.length - 8, Math.floor(bits / 0x100000000), false);
  const w = new Uint32Array(64);
  for (let off = 0; off < buf.length; off += 64) {
    for (let i = 0; i < 16; i++) w[i] = dv.getUint32(off + i * 4, false);
    for (let i = 16; i < 64; i++) {
      const a = w[i - 15], b = w[i - 2];
      const s0 = ((a >>> 7) | (a << 25)) ^ ((a >>> 18) | (a << 14)) ^ (a >>> 3);
      const s1 = ((b >>> 17) | (b << 15)) ^ ((b >>> 19) | (b << 13)) ^ (b >>> 10);
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, hh] = h;
    for (let i = 0; i < 64; i++) {
      const S1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
      const ch = (e & f) ^ (~e & g);
      const t1 = (hh + S1 + ch + _K[i] + w[i]) >>> 0;
      const S0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const t2 = (S0 + maj) >>> 0;
      hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
    }
    h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0; h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
    h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0; h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
  }
  const out = new Uint8Array(32);
  new DataView(out.buffer).setUint32(0, h[0], false);
  for (let i = 0; i < 8; i++) new DataView(out.buffer).setUint32(i * 4, h[i], false);
  return out;
}

function hmacSha256(key, msg) {
  if (key.length > 64) key = sha256(key);
  const pad = new Uint8Array(64);
  pad.set(key);
  const ip = new Uint8Array(64), op = new Uint8Array(64);
  for (let i = 0; i < 64; i++) { ip[i] = pad[i] ^ 0x36; op[i] = pad[i] ^ 0x5c; }
  const inner = sha256(concat(ip, msg));
  return sha256(concat(op, inner));
}

// ===========================================================================
// Utilitaires
// ===========================================================================
function concat(...arrs) {
  let n = 0;
  for (const a of arrs) n += a.length;
  const out = new Uint8Array(n);
  let o = 0;
  for (const a of arrs) { out.set(a, o); o += a.length; }
  return out;
}
function hex(bytes) {
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
}
function fromHex(s) {
  const out = new Uint8Array(s.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(s.substr(i * 2, 2), 16);
  return out;
}
function be32(b, o) { return ((b[o] << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3]) >>> 0; }
function eq(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

// ===========================================================================
// SysEx (mtlib/syx.py)
// ===========================================================================
const ELEKTRON = [0x00, 0x20, 0x3c];
const MSG_LEN = 128, PAYLOAD_OFF = 10, PAYLOAD_END = 126, CS_OFF = 126, BYTES_PER_MSG = 101, START_SEQ = 114;
// product id -> [name, device byte, V, C0]
const PRODUCTS = { 0x11: ["Model:Cycles", 0x0c, 0x3a, 0x22], 0x0f: ["Model:Samples", 0x0a, 0x3c, 0x1e] };

function unpack7(p) {
  const out = [];
  for (let i = 0; i < p.length; i += 8) {
    const hi = p[i];
    for (let k = 0; k < 7; k++) {
      if (i + 1 + k >= p.length) break;
      out.push(((hi << (k + 1)) & 0x80) | p[i + 1 + k]);
    }
  }
  return Uint8Array.from(out);
}
function pack7(b) {
  const out = [];
  for (let i = 0; i < b.length; i += 7) {
    const chunk = b.subarray(i, i + 7);
    let hi = 0;
    for (let k = 0; k < chunk.length; k++) hi |= (chunk[k] >> 7) << (6 - k);
    out.push(hi);
    for (const v of chunk) out.push(v & 0x7f);
  }
  return Uint8Array.from(out);
}
function maskArr(V) {
  const m = new Uint8Array(MSG_LEN);
  for (let i = 0; i < MSG_LEN; i++) m[i] = (V - i) & 0x3f;
  return m;
}
function msgChecksum(msg, V, C0) {
  let acc = 0;
  for (let i = 8; i < 126; i++) acc += msg[i] ^ ((V - i) & 0x3f);
  return (C0 - acc) & 0x7f;
}
function splitRaw(raw) {
  const msgs = [];
  let i = 0;
  while (true) {
    const a = raw.indexOf(0xf0, i);
    if (a < 0) break;
    const b = raw.indexOf(0xf7, a);
    if (b < 0) break;
    msgs.push(raw.subarray(a, b + 1));
    i = b + 1;
  }
  return msgs;
}
function u21(b, o) { return (b[o] << 14) | (b[o + 1] << 7) | b[o + 2]; }
function p21(v) { return Uint8Array.of((v >> 14) & 0x7f, (v >> 7) & 0x7f, v & 0x7f); }

function unwrap(raw) {
  const msgs = splitRaw(raw);
  if (msgs.length < 3) throw new Error("pas un .syx Elektron (trop peu de messages)");
  const head = msgs[0], tail = msgs[msgs.length - 1], data = msgs.slice(1, -1);
  for (let k = 0; k < 3; k++)
    if (head[1 + k] !== ELEKTRON[k] || tail[1 + k] !== ELEKTRON[k]) throw new Error("pas un .syx Elektron");
  const prod = head[4];
  if (!(prod in PRODUCTS)) throw new Error("identifiant produit inconnu 0x" + prod.toString(16));
  const [name, dev, V, C0] = PRODUCTS[prod];
  if (head[6] !== 0x7f || head[7] !== 0x01 || tail[6] !== 0x7f || tail[7] !== 0x02)
    throw new Error("marqueurs de debut/fin absents");
  const start = u21(head, 9), count = u21(head, 12);
  if (count !== data.length) throw new Error(`le marqueur annonce ${count} messages, ${data.length} trouves`);
  const body = [];
  for (let n = 0; n < data.length; n++) {
    const m = data[n];
    if (m.length !== MSG_LEN) throw new Error(`message ${n} : longueur ${m.length}`);
    if (m[CS_OFF] !== msgChecksum(m, V, C0)) throw new Error(`message ${n} : checksum invalide`);
    const dec = unpack7(m.subarray(PAYLOAD_OFF, PAYLOAD_END));
    for (const x of dec) body.push(x);
  }
  return { stream: Uint8Array.from(body), product: prod, name, start_seq: start, count };
}

function wrap(body, product, startSeq = START_SEQ) {
  const [name, dev, V, C0] = PRODUCTS[product];
  if (body.length % BYTES_PER_MSG) throw new Error("longueur de corps non multiple de " + BYTES_PER_MSG);
  const count = body.length / BYTES_PER_MSG;
  const pre = Uint8Array.of(0xf0, ...ELEKTRON, product, 0x00);
  const chunks = [];
  chunks.push(concat(pre, Uint8Array.of(0x7f, 0x01, dev), p21(startSeq), p21(count), Uint8Array.of(0xf7)));
  for (let n = 0; n < count; n++) {
    const seq = startSeq + n;
    const m = new Uint8Array(MSG_LEN);
    m.set(concat(pre, Uint8Array.of(0x7e, 0x00, seq >> 7, seq & 0x7f)), 0); // seq>>7 non masque (comme mtlib)
    m.set(pack7(body.subarray(n * BYTES_PER_MSG, (n + 1) * BYTES_PER_MSG)), PAYLOAD_OFF);
    m[MSG_LEN - 1] = 0xf7;
    m[CS_OFF] = msgChecksum(m, V, C0);
    chunks.push(m);
  }
  chunks.push(concat(pre, Uint8Array.of(0x7f, 0x02, dev), p21(startSeq), p21(count), Uint8Array.of(0xf7)));
  return concat(...chunks);
}

// ===========================================================================
// Codec aPLib (mtlib/aplib.py)
// ===========================================================================
const SECT_HDR = 8, OFFSET_BIAS = 767, REUSE_GAMMA = 2, FAR_THRESHOLD = 3328, END_GAMMA = 0x1000002;
const LITERAL = 1, MATCH = 0;

function aplibDepack(stream) {
  if (stream.length < SECT_HDR) throw new Error("section plus courte que son en-tete");
  let ip = SECT_HDR, tag = 0;
  const bit = () => {
    tag <<= 1;
    if ((tag & 0xff) === 0) {
      const by = stream[ip++];
      tag = (by << 1) | 1;
      return (by >> 7) & 1;
    }
    return (tag >> 8) & 1;
  };
  const gamma = () => {
    let v = 1;
    while (true) {
      v = (v << 1) + bit();
      if (bit()) return v;
      if (v > 0x02000000) throw new Error("flux corrompu : gamma deborde");
    }
  };
  const out = [];
  const ops = [];
  let lastOff = 1;
  while (true) {
    if (bit()) { ops.push([LITERAL, out.length, 0, 1]); out.push(stream[ip++]); continue; }
    const g = gamma();
    let off;
    if (g === REUSE_GAMMA) {
      off = lastOff;
    } else {
      off = (((g << 8) >>> 0) + stream[ip++]) >>> 0;
      if (off === OFFSET_BIAS) break;
      off -= OFFSET_BIAS;
      lastOff = off;
    }
    const sl = 2 * bit() + bit();
    let L = sl ? sl : gamma() + 2;
    if (off > FAR_THRESHOLD) L += 1;
    const n = L + 1;
    if (off === 0 || off > out.length) throw new Error("flux corrompu : offset hors sortie");
    ops.push([MATCH, out.length, off, n]);
    const src = out.length - off;
    for (let k = 0; k < n; k++) out.push(out[src + k]);
  }
  return { data: Uint8Array.from(out), ops };
}

class _Writer {
  constructor() { this.o = []; for (let i = 0; i < SECT_HDR; i++) this.o.push(0); this.tagpos = -1; this.tagbits = 0; }
  bit(v) {
    if (this.tagbits === 0) { this.tagpos = this.o.length; this.o.push(0); this.tagbits = 8; }
    if (v) this.o[this.tagpos] |= 1 << (this.tagbits - 1);
    this.tagbits -= 1;
  }
  gamma(v) {
    for (let i = (31 - Math.clz32(v)) - 1; i >= 0; i--) { this.bit((v >> i) & 1); this.bit(i === 0 ? 1 : 0); }
  }
  literal(b) { this.bit(1); this.o.push(b); }
  match(off, n, lastOff) {
    this.bit(0);
    if (off === lastOff) { this.gamma(REUSE_GAMMA); }
    else { const raw = off + OFFSET_BIAS; this.gamma(raw >> 8); this.o.push(raw & 0xff); }
    const base = n - 1 - (off > FAR_THRESHOLD ? 1 : 0);
    if (base <= 3) { this.bit(base >> 1); this.bit(base & 1); }
    else { this.bit(0); this.bit(0); this.gamma(base - 2); }
  }
  end() { this.bit(0); this.gamma(END_GAMMA); this.o.push(0xff); }
}

function indexOfDirty(dirty, start, end) {         // premier 1 dans [start, end)
  for (let i = start; i < end; i++) if (dirty[i]) return i;
  return -1;
}

function aplibRepack(data, ops, dirty) {
  const w = new _Writer();
  let lastOff = 1;
  let lo = -1, hi = -1;
  for (let i = 0; i < dirty.length; i++) if (dirty[i]) { if (lo < 0) lo = i; hi = i; }
  for (const [kind, pos, off, n] of ops) {
    if (kind === LITERAL) { w.literal(data[pos]); continue; }
    const end = pos + n, src = pos - off;
    let touched = false;
    if (lo >= 0 && src <= hi && end > lo)
      touched = indexOfDirty(dirty, pos, end) >= 0 || indexOfDirty(dirty, src, src + n) >= 0;
    if (touched) { for (let k = pos; k < end; k++) w.literal(data[k]); }
    else { w.match(off, n, lastOff); lastOff = off; }
  }
  w.end();
  const body = w.o;
  const streamLen = body.length - SECT_HDR;
  body[0] = (streamLen >>> 24) & 0xff; body[1] = (streamLen >>> 16) & 0xff;
  body[2] = (streamLen >>> 8) & 0xff; body[3] = streamLen & 0xff;
  let s = 0;
  for (let i = SECT_HDR; i < body.length; i++) s = (s + body[i]) >>> 0;
  body[4] = (s >>> 24) & 0xff; body[5] = (s >>> 16) & 0xff; body[6] = (s >>> 8) & 0xff; body[7] = s & 0xff;
  return Uint8Array.from(body);
}

// ===========================================================================
// Conteneur ELE3 (mtlib/container.py)
// ===========================================================================
const PREAMBLE = 8, COUNT_OFF = 0x1c, TABLE_OFF = 0x20, ENTRY_SZ = 16, ALIGN = 16, DIGEST_LEN = 32;
const KEY_ANCHOR = Uint8Array.of(0xbe, 0xf9, 0xa3, 0xf7, 0xc6, 0x71, 0x78, 0xf2), KEY_STR_MAX = 64;

function contentChecksum(container) {
  let acc = 0;
  for (let k = 0; k < (container.length >> 2); k++) acc = (acc + (((k + 1) ^ be32(container, 4 * k)) >>> 0)) >>> 0;
  return acc >>> 0;
}
function parseContainer(stream) {
  if (stream.length < PREAMBLE + TABLE_OFF) throw new Error("flux trop court");
  const declared = be32(stream, 0);
  const blob = stream.subarray(PREAMBLE, PREAMBLE + declared);
  if (!(blob[0] === 0x45 && blob[1] === 0x4c && blob[2] === 0x45 && blob[3] === 0x33))
    throw new Error("pas de magie ELE3 — mauvais format de firmware");
  const n = be32(blob, COUNT_OFF);
  if (n < 1 || n > 16) throw new Error("nombre de sections invraisemblable : " + n);
  const secs = [];
  for (let s = 0; s < n; s++) {
    const e = TABLE_OFF + s * ENTRY_SZ;
    secs.push({ index: s, id: be32(blob, e), off: be32(blob, e + 4), size: be32(blob, e + 8), attr: be32(blob, e + 12) });
  }
  let ver = "";
  for (let i = 8; i < 16; i++) if (blob[i]) ver += String.fromCharCode(blob[i]);
  return { declared, blob: Uint8Array.from(blob), sections: secs, version: ver.replace(/\0+$/, "") };
}
function indexOfSub(hay, needle, start) {
  outer: for (let i = start; i + needle.length <= hay.length; i++) {
    for (let j = 0; j < needle.length; j++) if (hay[i + j] !== needle[j]) continue outer;
    return i;
  }
  return -1;
}
function findKey(buffers, message, expect) {
  for (const buf of buffers) {
    let i = indexOfSub(buf, KEY_ANCHOR, 0);
    while (i >= 0) {
      const s = i + KEY_ANCHOR.length;
      let p = s;
      while (p < buf.length && buf[p] >= 0x20 && buf[p] < 0x7f && p - s < KEY_STR_MAX) p++;
      if (p > s && p < buf.length && buf[p] === 0 && p + 1 + 32 <= buf.length) {
        const text = buf.subarray(s, p);
        const konst = buf.subarray(p + 1, p + 33);
        const h = sha256(text), hr = sha256(Uint8Array.from([...text].reverse()));
        const key = new Uint8Array(32);
        for (let k = 0; k < 32; k++) key[k] = h[k] ^ hr[k] ^ konst[k];
        if (eq(hmacSha256(key, message), expect)) return key;
      }
      i = indexOfSub(buf, KEY_ANCHOR, i + 1);
    }
  }
  return null;
}
function rebuildContainer(info, replacements, key) {
  const blob = info.blob, secs = info.sections;
  let first = Infinity;
  for (const s of secs) first = Math.min(first, s.off);
  const out = [...blob.subarray(0, first)];
  const order = [...secs.keys()].sort((a, b) => secs[a].off - secs[b].off);
  let pos = first;
  for (const i of order) {
    const sec = secs[i];
    const data = replacements[sec.id] || blob.subarray(sec.off, sec.off + sec.size);
    pos = (pos + ALIGN - 1) & ~(ALIGN - 1);
    while (out.length < pos) out.push(0);
    for (let k = 0; k < data.length; k++) out[pos + k] = data[k];
    const e = TABLE_OFF + sec.index * ENTRY_SZ;
    out[e + 4] = (pos >>> 24) & 0xff; out[e + 5] = (pos >>> 16) & 0xff; out[e + 6] = (pos >>> 8) & 0xff; out[e + 7] = pos & 0xff;
    const ln = data.length;
    out[e + 8] = (ln >>> 24) & 0xff; out[e + 9] = (ln >>> 16) & 0xff; out[e + 10] = (ln >>> 8) & 0xff; out[e + 11] = ln & 0xff;
    pos += data.length;
  }
  const end = pos;
  const hmacOff = (end + 4 + ALIGN - 1) & ~(ALIGN - 1);
  while (out.length < hmacOff) out.push(0);
  const digest = hmacSha256(key, Uint8Array.from(out.slice(0, hmacOff)));
  for (let k = 0; k < DIGEST_LEN; k++) out[hmacOff + k] = digest[k];
  return Uint8Array.from(out.slice(0, hmacOff + DIGEST_LEN));
}
function buildStream(blob, padTo) {
  const head = new Uint8Array(PREAMBLE);
  const dv = new DataView(head.buffer);
  dv.setUint32(0, blob.length, false);
  dv.setUint32(4, contentChecksum(blob), false);
  let stream = concat(head, blob);
  if (stream.length % padTo) stream = concat(stream, new Uint8Array(padTo - (stream.length % padTo)));
  return stream;
}

// ===========================================================================
// Orchestration (tools/build.py)
// ===========================================================================
const BASE = 0x40000400;

function applyWrites(mainOs, tweaks) {
  const data = Uint8Array.from(mainOs);
  const dirty = new Uint8Array(mainOs.length);
  for (const t of tweaks) {
    for (const w of t.writes) {
      const off = w.off, old = fromHex(w.old), nw = fromHex(w.new);
      for (let k = 0; k < old.length; k++)
        if (data[off + k] !== old[k])
          throw new Error(`${t.id} @ 0x${(off + BASE).toString(16)} : octet 'old' ${hex(old)} attendu, trouve `
            + hex(data.subarray(off, off + old.length)));
      data.set(nw, off);
      for (let k = off; k < off + nw.length; k++) dirty[k] = 1;
    }
  }
  return { data, dirty };
}

function checkConflicts(chosen) {
  const ids = new Set(chosen.map((t) => t.id));
  for (const t of chosen)
    for (const other of t.conflicts || [])
      if (ids.has(other)) throw new Error(`${t.id} et ${other} sont incompatibles`);
}

// Verifie que les zones 0xFF ou un tweak ecrit sont libres dans l'image d'origine.
// Zone = [debut du bloc 0xFF, fin des octets ecrits). Une reference dont les octets sont
// reecrits par les tweaks (dirty) n'existe plus : listee dans « gone », elle ne bloque pas,
// sauf une constante qui, dans l'image patchee (patched), pointe encore dans la zone.
// Renvoie { zones, sure, doubt, gone } ; leve une Error si une constante 32 bits pointe dedans (sauf force).
function checkCaves(mainOs, chosen, force, dirty, patched) {
  const top = new Map();                        // debut du bloc -> fin ecrite la plus haute
  for (const t of chosen) for (const w of t.writes) {
    const old = fromHex(w.old);
    if (old.length < 2 || !old.every((b) => b === 0xff)) continue;
    let lo = w.off;
    const hi = w.off + old.length;
    while (lo > 0 && mainOs[lo - 1] === 0xff) lo--;
    top.set(lo, Math.max(hi, top.get(lo) || hi));
  }
  const zones = [...top.entries()].sort((a, b) => a[0] - b[0]);
  if (!zones.length) return { zones: [], sure: [], doubt: [], gone: [] };
  const vz = zones.map(([lo, hi]) => [lo + BASE, hi + BASE]);
  const loAll = Math.min(...vz.map((z) => z[0])), hiAll = Math.max(...vz.map((z) => z[1]));
  const inside = (t) => t >= loAll && t < hiAll && vz.some(([a, b]) => t >= a && t < b);
  const s16 = (x) => (x & 0x8000 ? x - 0x10000 : x);
  const sure = [], doubt = [];
  const n = mainOs.length;
  const rd16 = (i) => (mainOs[i] << 8) | mainOs[i + 1];
  for (let i = 0; i + 3 < n; i += 2) {
    const x = rd16(i), va = BASE + i;
    const v = ((x << 16) >>> 0) + rd16(i + 2);
    if (inside(v)) sure.push([va, v, "constante 32 bits"]);
    let t = null, kind = "";
    if ((x & 0x3f) === 0x3a && ((x & 0xf1ff) === 0x41fa || x === 0x487a || x === 0x4efa || x === 0x4eba
        || ((x & 0xc000) === 0 && (x & 0x3000)))) { t = va + 2 + s16(rd16(i + 2)); kind = "adressage (d16,PC)"; }
    else if ((x & 0xf000) === 0x6000) {
      const d8 = x & 0xff;
      if (d8 === 0) t = va + 2 + s16(rd16(i + 2));
      else if (d8 === 0xff) t = va + 2 + ((((rd16(i + 2) << 16) | (i + 4 < n ? rd16(i + 4) : 0)) ^ 0x80000000) - 0x80000000);
      else t = va + 2 + (d8 & 0x80 ? d8 - 0x100 : d8);
      kind = "branchement";
    }
    if (t !== null && inside(t)) doubt.push([va, t, kind]);
  }
  const gone = [];
  if (dirty) {
    const rewritten = ([va, , kind]) => {
      const o = va - BASE;
      if (!(dirty[o] || dirty[o + 1] || dirty[o + 2] || dirty[o + 3])) return false;
      if (patched && kind.startsWith("constante")) {
        const v = ((patched[o] << 24) >>> 0) + (patched[o + 1] << 16) + (patched[o + 2] << 8) + patched[o + 3];
        if (inside(v)) return false;                // toujours une reference vers la zone
      }
      return true;
    };
    for (const list of [sure, doubt])
      for (let k = list.length - 1; k >= 0; k--)
        if (rewritten(list[k])) gone.unshift(...list.splice(k, 1));
  }
  if (sure.length && !force) {
    const lines = sure.map(([va, t]) => `  0x${va.toString(16)} -> 0x${t.toString(16)}`).join("\n");
    throw new Error("l'image d'origine pointe dans une zone 0xFF ou un tweak ecrit :\n" + lines
      + "\nZone peut-etre non libre : construction refusee.");
  }
  return { zones, sure, doubt, gone };
}

/* Construit le .syx modifie.
 * raw = Uint8Array du .syx officiel ; device = device.json ; chosen = [tweak] ;
 * opts = { expectMainOsSha, force }.
 * Renvoie { raw, mainOsSha, patchedBytes, caves, product, name }. */
function build(raw, device, chosen, opts = {}) {
  const { stream, product, name, start_seq } = unwrap(raw);
  const c = parseContainer(stream);
  const s3 = c.sections.find((s) => s.id === 3);
  if (!s3) throw new Error("section 3 (MAIN OS) absente");
  const { data: mainOs, ops } = aplibDepack(c.blob.subarray(s3.off, s3.off + s3.size));
  const mainSha = hex(sha256(mainOs));
  if (device.section_sha256 && mainSha !== device.section_sha256)
    throw new Error("la section 3 ne correspond pas a l'image de reference (OS 1.13 attendu)");

  checkConflicts(chosen);
  const { data: patched, dirty } = applyWrites(mainOs, chosen);
  const caves = checkCaves(mainOs, chosen, opts.force, dirty, patched);
  const patchedSha = hex(sha256(patched));
  if (opts.expectMainOsSha && patchedSha !== opts.expectMainOsSha)
    throw new Error(`MAIN OS patche ${patchedSha}, attendu ${opts.expectMainOsSha}`);

  const newS3 = aplibRepack(patched, ops, dirty);
  const blobNoDigest = c.blob.subarray(0, c.blob.length - DIGEST_LEN);
  const expect = c.blob.subarray(c.blob.length - DIGEST_LEN);
  const plain = [];
  for (const s of c.sections) {
    try { plain.push(aplibDepack(c.blob.subarray(s.off, s.off + s.size)).data); } catch (e) { /* raw */ }
  }
  const key = findKey(plain, blobNoDigest, expect);
  if (!key) throw new Error("cle HMAC introuvable — image inattendue");
  const blob = rebuildContainer(c, { 3: newS3 }, key);
  const outStream = buildStream(blob, BYTES_PER_MSG);
  const outRaw = wrap(outStream, product, start_seq);
  return { raw: outRaw, mainOsSha: patchedSha, patchedBytes: dirty.reduce((a, b) => a + b, 0),
           caves, product, name };
}

// ---- Export node / navigateur ---------------------------------------------
const API = { sha256, hmacSha256, unwrap, wrap, aplibDepack, aplibRepack, parseContainer, findKey,
              rebuildContainer, buildStream, contentChecksum, applyWrites, checkConflicts, checkCaves,
              build, hex, fromHex, PRODUCTS, BASE };
if (typeof module !== "undefined" && module.exports) module.exports = API;
if (typeof window !== "undefined") window.MCBuilder = API;
})();
