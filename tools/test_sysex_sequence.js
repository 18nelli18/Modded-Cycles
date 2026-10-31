/* Numero de sequence SysEx sur 21 bits (notes/212).
 *
 *   node tools/test_sysex_sequence.js [model-cycles_OS1.13.syx model-samples_OS1.13.syx]
 *
 * Sans firmware : un flux de 17 000 paquets (au-dela de la sequence 16 383) s'emballe sans octet >= 0x80 et se
 * relit ; chaque image publiee de docs/flasher/ est saine ou se reemballe (meme flux, meme depart, meme
 * nombre de paquets) ; l'envoi classique refuse l'image d'origine avant le premier message ; mtlib (Python) et
 * builder.js produisent les memes octets ; le recepteur du bootstrap, transcrit, accepte chaque fichier reemballe
 * et refuse l'original. Avec les OS officiels : wrap(unwrap(x)) === x, octet pour octet, et accepte. */
const fs = require("node:fs"), path = require("node:path"), cp = require("node:child_process");
const assert = require("node:assert/strict"), crypto = require("node:crypto"), os = require("node:os");
const root = path.resolve(__dirname, ".."), site = path.join(root, "docs/flasher");
const B = require(path.join(site, "builder.js")), F = require(path.join(site, "flasher.js"));
const hash = (x) => crypto.createHash("sha256").update(x).digest("hex");
const u21 = (m, o) => (m[o] << 14) | (m[o + 1] << 7) | m[o + 2];

/* Recepteur du bootstrap Model:Samples (0x800035ca), transcrit tel quel, sur le flux d'octets MIDI : un octet
 * >= 0x80 autre que F7 coupe le message en cours (comme le recepteur UART). Renvoie le nombre de paquets acceptes
 * et si le marqueur de fin a ete accepte (etat 2 puis 3 : la verification du conteneur peut commencer). */
function bootstrapReceive(raw, dev) {
  let state = 0, seq = 0, count = 0, got = 0, startSeq = 0, done = false, cur = null;
  const handle = (m) => {                      // m = F0 .. F7 ; a2 = m + 6 dans le code d'origine
    const a2 = m.subarray(6);
    if (a2[0] === 0x7e) {
      if (a2.length !== 122 || a2[121] !== 0xf7 || state !== 1) return;
      if (u21(a2, 1) !== seq) { state = 0; return; }
      let acc = 0;
      for (let k = 0; k < 119; k++) acc += ((k + dev) & 0xff) ^ a2[1 + k];
      if (((acc + dev) & 0x7f) !== a2[120]) { state = 0; return; }
      seq++; got++; if (got === count) state = 2;
    } else if (a2[9] === 0xf7 && a2[1] === 1 && a2[2] === dev) {
      startSeq = seq = u21(a2, 3); count = u21(a2, 6); got = 0; state = 1;
    } else if (a2[9] === 0xf7 && a2[1] === 2 && state === 2 && a2[2] === dev
               && u21(a2, 3) === startSeq && u21(a2, 6) === count) done = true;
  };
  for (const b of raw) {
    if (b === 0xf0) cur = [b];
    else if (cur && b === 0xf7) { cur.push(b); handle(Uint8Array.from(cur)); cur = null; }
    else if (cur && b & 0x80) cur = null;      // octet d'etat : message abandonne
    else if (cur) cur.push(b);
  }
  return { got, count, done };
}
const accepted = (raw) => { const r = bootstrapReceive(raw, raw[8]); return r.done && r.got === r.count; };

// 1. Au-dela de 16 383 : aucun octet >= 0x80, sequence lue comme le bootstrap (0x8000355c sur paquet+1)
const body = new Uint8Array(17000 * 101).map((_, i) => (i * 37) & 0xff);
const big = B.wrap(body, 0x11, 242);
assert.deepEqual(B.invalidMessages(big), []);
const msgs = F.splitMessages(big);
msgs.slice(1, -1).forEach((m, n) => assert.equal(u21(m, 7), 242 + n));
assert.deepEqual(B.unwrap(big).stream, body);
assert.equal(F.verify(big).count, 17000);
assert(accepted(big), "the bootstrap receiver must accept 17 000 packets");
assert(accepted(B.wrap(body, 0x0f, 242)), "same on the Model:Samples transport");
console.log("PASS 17 000 packets: valid SysEx, 21-bit sequence 242..17241, round trip");

// 2. Images publiees : saines, ou reemballees a l'identique du flux
(async () => {
  const sent = { send() { sent.n++; }, n: 0 };
  for (const name of fs.readdirSync(site).filter((f) => f.endsWith(".syx")).sort()) {
    const raw = fs.readFileSync(path.join(site, name)), bad = B.invalidMessages(raw);
    if (!bad.length) { assert.equal(B.rewrap(raw), raw); assert(accepted(raw), name); continue; }
    const fixed = B.rewrap(raw), a = B.unwrap(raw), b = B.unwrap(fixed);
    assert.deepEqual(B.invalidMessages(fixed), []);
    assert.deepEqual(b.stream, a.stream);
    assert.equal(b.start_seq, a.start_seq); assert.equal(b.count, a.count); assert.equal(fixed.length, raw.length);
    assert.equal(F.verify(fixed).count, a.count);
    assert(!accepted(raw) && accepted(fixed), `${name}: bootstrap receiver refuses the original, accepts the re-wrap`);
    sent.n = 0;
    await assert.rejects(F.sendSysex(sent, raw, { pace: 0 }), /invalid SysEx/);
    assert.equal(sent.n, 0);
    // meme reparation en Python (mtlib.syx.rewrap)
    const tmp = path.join(os.tmpdir(), `rewrap-${process.pid}.syx`);
    cp.execFileSync("python3", [path.join(root, "tools/rewrap_syx.py"), path.join(site, name), "-o", tmp], { stdio: "pipe" });
    assert.equal(hash(fs.readFileSync(tmp)), hash(fixed)); fs.unlinkSync(tmp);
    console.log(`PASS ${name}: ${bad.length} invalid packets from #${bad[0]}, re-wrapped (stream ${hash(a.stream).slice(0, 12)}…, JS = Python)`);
  }
  // 3. OS officiels : emballage inchange, octet pour octet
  for (const file of process.argv.slice(2)) {
    const raw = fs.readFileSync(file), u = B.unwrap(raw);
    assert.equal(hash(B.wrap(u.stream, u.product, u.start_seq)), hash(raw));
    assert(accepted(raw), path.basename(file));
    console.log(`PASS ${path.basename(file)}: wrap(unwrap()) is byte-identical`);
  }
})().catch((e) => { console.error(e); process.exit(1); });
