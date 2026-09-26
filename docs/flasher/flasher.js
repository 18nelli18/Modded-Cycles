/* Web MIDI flasher core for the Model:Cycles / Model:Samples.
 *
 * Pure logic, no DOM: verify a .syx (same checks as tools/mtlib/syx.py, byte for
 * byte — tools/webflash_check.js compares it against the Python) and send it over
 * a Web MIDI output with the same pacing as tools/flash.py.
 * The user interface lives in app.js.
 *
 * NO firmware image is included: the user drops their own .syx.
 *
 * Wrapped in an IIFE: top-level declarations of classic <script>s are global and
 * would collide with builder.js.
 */
(function () {
"use strict";

const ELEKTRON = [0x00, 0x20, 0x3c];
const MSG_LEN = 128;
const CS_OFF = 126;
// product id -> [name, device byte, mask seed V, checksum base C0]
const PRODUCTS = {
  0x11: ["Model:Cycles", 0x0c, 0x3a, 0x22],
  0x0f: ["Model:Samples", 0x0a, 0x3c, 0x1e],
};
const DIN_BYTES_PER_SEC = 31250 / 10; // 8N1 on the MIDI wire
const DEFAULT_PACE = 1.4;

/* Split a .syx into F0..F7 messages (each one includes F0 and F7). */
function splitMessages(raw) {
  const msgs = [];
  let i = 0;
  while (true) {
    const a = raw.indexOf(0xf0, i);
    if (a < 0) break;
    const b = raw.indexOf(0xf7, a);
    if (b < 0) throw new Error(`unterminated SysEx at offset ${a}`);
    msgs.push(raw.subarray(a, b + 1));
    i = b + 1;
  }
  return msgs;
}

function maskByte(V, i) {
  return (V - i) & 0x3f;
}

/* Checksum of one message (mtlib.syx.checksum): over bytes 8..125. */
function packetChecksum(msg, V, C0) {
  let acc = 0;
  for (let i = 8; i < 126; i++) acc += msg[i] ^ maskByte(V, i);
  return (C0 - acc) & 0x7f;
}

function u21(b, o) {
  return (b[o] << 14) | (b[o + 1] << 7) | b[o + 2];
}

/* Verify the file like mtlib.syx.unwrap: structure and every checksum.
 * Returns { product, name, count, bytes, messages, wireMinutes }.
 * Throws an Error with a clear message at the first problem. */
function verify(raw) {
  const msgs = splitMessages(raw);
  if (msgs.length < 3) throw new Error("not an Elektron firmware file (too few SysEx messages)");
  const head = msgs[0];
  const tail = msgs[msgs.length - 1];
  const data = msgs.slice(1, -1);

  for (let k = 0; k < 3; k++) {
    if (head[1 + k] !== ELEKTRON[k] || tail[1 + k] !== ELEKTRON[k])
      throw new Error("not an Elektron file (header is not 00 20 3C)");
  }
  const prod = head[4];
  if (!(prod in PRODUCTS)) throw new Error(`unsupported product id 0x${prod.toString(16)}`);
  const [name, , V, C0] = PRODUCTS[prod];
  if (head[6] !== 0x7f || head[7] !== 0x01 || tail[6] !== 0x7f || tail[7] !== 0x02)
    throw new Error("start/end markers missing");

  const count = u21(head, 12);
  if (count !== data.length)
    throw new Error(`the header announces ${count} packets, ${data.length} found`);

  for (let n = 0; n < data.length; n++) {
    const m = data[n];
    if (m.length !== MSG_LEN)
      throw new Error(`packet ${n}: length ${m.length} (expected ${MSG_LEN})`);
    if (m[CS_OFF] !== packetChecksum(m, V, C0))
      throw new Error(`packet ${n}: bad checksum — the file is corrupted, do not flash it`);
  }

  const bytes = raw.length;
  const wireMinutes = bytes / DIN_BYTES_PER_SEC / 60;
  return { product: prod, name, count, bytes, messages: msgs.length, wireMinutes };
}

/* Expected transfer time in seconds for a given pace. */
function transferSeconds(raw, pace) {
  return (raw.length / DIN_BYTES_PER_SEC) * (Number.isFinite(pace) ? pace : DEFAULT_PACE);
}

/* Send every message of `raw` to a Web MIDI output, paced for a 31.25 kbaud wire.
 * opts = { pace, onProgress(done, total), isCancelled() }.
 * Resolves to { sent, total, cancelled, seconds }. */
async function sendSysex(output, raw, opts = {}) {
  const pv = opts.pace;
  const pace = Number.isFinite(pv) && pv >= 0 ? pv : DEFAULT_PACE;   // explicit 0 is honoured
  const msgs = splitMessages(raw);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const t0 = Date.now();
  let n = 0;
  for (; n < msgs.length; n++) {
    if (opts.isCancelled && opts.isCancelled()) break;
    output.send(msgs[n]); // full message, F0..F7 included
    const delayMs = (pace * msgs[n].length) / DIN_BYTES_PER_SEC * 1000;
    if (delayMs > 0) await sleep(delayMs);
    if (opts.onProgress && (n % 50 === 0 || n === msgs.length - 1)) opts.onProgress(n + 1, msgs.length);
  }
  return { sent: n, total: msgs.length, cancelled: n < msgs.length, seconds: (Date.now() - t0) / 1000 };
}

const API = { splitMessages, verify, packetChecksum, transferSeconds, sendSysex,
              PRODUCTS, DEFAULT_PACE, DIN_BYTES_PER_SEC };
if (typeof module !== "undefined" && module.exports) module.exports = API;
if (typeof window !== "undefined") window.MCFlasher = API;
})();
