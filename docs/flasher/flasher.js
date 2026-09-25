/* Flasher Web MIDI pour Model:Cycles / Model:Samples.
 *
 * Envoie un firmware .syx par SysEx, via l'API Web MIDI de Chrome. C'est le
 * pendant navigateur de tools/flash.py : meme verification (identifiant
 * fabricant/produit, chaque checksum de paquet), meme cadence d'envoi.
 *
 * AUCUNE image firmware n'est incluse : l'utilisateur depose SON .syx.
 *
 * La logique SysEx (split, unwrap, checksum) reproduit tools/mtlib/syx.py a
 * l'octet pres ; tools/webflash_check.js le verifie contre le Python.
 *
 * Enveloppe dans une IIFE : en <script> classique, les declarations de premier
 * niveau sont globales et entreraient en collision avec builder.js.
 */
(function () {
"use strict";

const ELEKTRON = [0x00, 0x20, 0x3c];
const MSG_LEN = 128;
const CS_OFF = 126;
// product id -> [nom, device byte, graine de masque V, base de checksum C0]
const PRODUCTS = {
  0x11: ["Model:Cycles", 0x0c, 0x3a, 0x22],
  0x0f: ["Model:Samples", 0x0a, 0x3c, 0x1e],
};
const DIN_BYTES_PER_SEC = 31250 / 10; // 8N1 sur le fil MIDI
const DEFAULT_PACE = 1.4;

/* Decoupe un .syx en messages F0..F7 (chacun inclut F0 et F7). */
function splitMessages(raw) {
  const msgs = [];
  let i = 0;
  while (true) {
    const a = raw.indexOf(0xf0, i);
    if (a < 0) break;
    const b = raw.indexOf(0xf7, a);
    if (b < 0) throw new Error(`SysEx non termine a l'offset ${a}`);
    msgs.push(raw.subarray(a, b + 1));
    i = b + 1;
  }
  return msgs;
}

function maskByte(V, i) {
  return (V - i) & 0x3f;
}

/* checksum d'un message (mtlib.syx.checksum) : sur les octets 8..125. */
function packetChecksum(msg, V, C0) {
  let acc = 0;
  for (let i = 8; i < 126; i++) acc += msg[i] ^ maskByte(V, i);
  return (C0 - acc) & 0x7f;
}

function u21(b, o) {
  return (b[o] << 14) | (b[o + 1] << 7) | b[o + 2];
}

/* Verifie le fichier comme mtlib.syx.unwrap : structure + chaque checksum.
 * Renvoie { product, name, count, bytes, messages, wireMinutes }.
 * Leve une Error avec un message clair au premier probleme. */
function verify(raw) {
  const msgs = splitMessages(raw);
  if (msgs.length < 3) throw new Error("pas un .syx Elektron (trop peu de messages)");
  const head = msgs[0];
  const tail = msgs[msgs.length - 1];
  const data = msgs.slice(1, -1);

  for (let k = 0; k < 3; k++) {
    if (head[1 + k] !== ELEKTRON[k] || tail[1 + k] !== ELEKTRON[k])
      throw new Error("en-tete non Elektron (attendu 00 20 3C)");
  }
  const prod = head[4];
  if (!(prod in PRODUCTS)) throw new Error(`identifiant produit inconnu : 0x${prod.toString(16)}`);
  const [name, , V, C0] = PRODUCTS[prod];
  if (head[6] !== 0x7f || head[7] !== 0x01 || tail[6] !== 0x7f || tail[7] !== 0x02)
    throw new Error("marqueurs de debut/fin absents");

  const count = u21(head, 12);
  if (count !== data.length)
    throw new Error(`le marqueur annonce ${count} messages, ${data.length} trouves`);

  for (let n = 0; n < data.length; n++) {
    const m = data[n];
    if (m.length !== MSG_LEN)
      throw new Error(`message ${n} : longueur ${m.length} (attendu ${MSG_LEN})`);
    if (m[CS_OFF] !== packetChecksum(m, V, C0))
      throw new Error(`message ${n} : checksum invalide — fichier corrompu, ne pas flasher`);
  }

  const bytes = raw.length;
  const wireMinutes = bytes / DIN_BYTES_PER_SEC / 60;
  return { product: prod, name, count, bytes, messages: msgs.length, wireMinutes };
}

// ---- Export pour le test node ; ignore dans le navigateur ------------------
if (typeof module !== "undefined" && module.exports) {
  module.exports = { splitMessages, verify, packetChecksum, PRODUCTS, DEFAULT_PACE, DIN_BYTES_PER_SEC };
}

// ---------------------------------------------------------------------------
// Interface (navigateur seulement)
// ---------------------------------------------------------------------------
if (typeof window !== "undefined") {
  const $ = (id) => document.getElementById(id);
  const state = { midi: null, raw: null, info: null, filename: null, sending: false };

  const log = (msg, cls = "") => {
    const el = $("log");
    const line = document.createElement("div");
    if (cls) line.className = cls;
    line.textContent = msg;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
  };

  function refreshReady() {
    const port = $("port").value;
    const acked = $("ack").checked;
    $("send").disabled = !(state.info && port && acked && !state.sending);
  }

  // ---- MIDI ---------------------------------------------------------------
  function setStatus(msg, cls) {
    $("midi-status").textContent = msg;
    $("midi-status").className = "msg tiny " + (cls || "");
  }

  async function initMidi() {
    setStatus("Demande d'autorisation MIDI…", "");     // retour immediat au clic
    log("Activation du MIDI…");
    if (typeof window.isSecureContext !== "undefined" && !window.isSecureContext) {
      setStatus("Contexte non securise : Web MIDI exige https:// ou localhost. "
        + "Ouvre la page en ligne (GitHub Pages) ou via « python3 -m http.server » — pas par double-clic (file://).", "bad");
      log("Contexte non securise (file:// ?) : Web MIDI desactive par le navigateur.", "bad");
      return;
    }
    if (!navigator.requestMIDIAccess) {
      setStatus("Web MIDI indisponible dans ce navigateur. Utilise Chrome, Edge ou Opera sur ordinateur "
        + "(Firefox et Safari ne gerent pas Web MIDI).", "bad");
      log("navigator.requestMIDIAccess absent.", "bad");
      return;
    }
    try {
      state.midi = await navigator.requestMIDIAccess({ sysex: true });
    } catch (e) {
      setStatus("Acces MIDI refuse (" + (e && e.name ? e.name : e) + "). Recharge la page et accepte "
        + "la demande d'autorisation MIDI, SysEx compris.", "bad");
      log("requestMIDIAccess a echoue : " + (e && e.message ? e.message : e), "bad");
      return;
    }
    state.midi.onstatechange = fillPorts;
    fillPorts();
  }

  function fillPorts() {
    const sel = $("port");
    const prev = sel.value;
    sel.innerHTML = "";
    const outs = state.midi ? [...state.midi.outputs.values()] : [];
    if (!outs.length) {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "— aucune sortie MIDI detectee —";
      sel.appendChild(o);
      setStatus("Aucune sortie MIDI. Branche ton interface (ou le Model:Cycles en USB) puis clique Rafraichir.", "warn");
    } else {
      for (const out of outs) {
        const o = document.createElement("option");
        o.value = out.id;
        o.textContent = out.name + (out.manufacturer ? ` (${out.manufacturer})` : "");
        sel.appendChild(o);
      }
      if ([...sel.options].some((o) => o.value === prev)) sel.value = prev;
      setStatus(`${outs.length} sortie(s) MIDI detectee(s). Choisis le bon port ci-dessous.`, "ok");
    }
    refreshReady();
  }

  // ---- Fichier ------------------------------------------------------------
  function loadBytes(u8, name) {
    state.filename = name;
    state.raw = u8;
    try {
      state.info = verify(state.raw);
      const i = state.info;
      $("file-info").innerHTML =
        `<b>${name}</b> — ${i.name} (0x${i.product.toString(16)}), ` +
        `${i.bytes.toLocaleString("fr-FR")} o, ${i.count.toLocaleString("fr-FR")} paquets. ` +
        `Tous les checksums OK. Duree minimale ~${i.wireMinutes.toFixed(1)} min.`;
      $("file-info").className = "ok";
      log(`Fichier verifie : ${name} — ${i.name}, ${i.count} paquets, checksums OK.`, "ok");
    } catch (e) {
      state.info = null;
      $("file-info").textContent = "Fichier refuse : " + e.message;
      $("file-info").className = "bad";
      log("Fichier refuse : " + e.message, "bad");
    }
    refreshReady();
  }
  window.loadFlasherBytes = loadBytes; // utilise par le panneau de construction

  function loadFile(file) {
    const reader = new FileReader();
    reader.onload = () => loadBytes(new Uint8Array(reader.result), file.name);
    reader.readAsArrayBuffer(file);
  }

  // ---- Envoi --------------------------------------------------------------
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function send() {
    if (!state.info || state.sending) return;
    const out = state.midi.outputs.get($("port").value);
    if (!out) {
      log("Sortie MIDI introuvable — rafraichis la liste.", "bad");
      return;
    }
    const low = (out.name || "").toLowerCase();
    if (low.includes("model:cycles") || low.includes("model:samples") || low.includes("model cycles")) {
      log(
        "Note : ce port est le Model:Cycles lui-meme. Il ne recoit un OS que depuis " +
          "CONFIG > UPGRADE (OS en marche), PAS depuis le STARTUP MENU (la, il faut le MIDI IN).",
        "warn"
      );
    }
    const pv = parseFloat($("pace").value);           // 0 explicite honore (Number.isFinite, pas ||)
    const pace = Number.isFinite(pv) && pv >= 0 ? pv : DEFAULT_PACE;
    const msgs = splitMessages(state.raw);

    state.sending = true;
    refreshReady();
    $("send").textContent = "Envoi en cours…";
    $("bar").style.width = "0%";
    log(`Envoi de ${msgs.length} messages, cadence ${pace}. Ne debranche rien.`, "");
    log("Surveille l'ecran : READY TO RECEIVE doit passer a RECEIVING… en quelques secondes.", "");

    const t0 = performance.now();
    try {
      for (let n = 0; n < msgs.length; n++) {
        out.send(msgs[n]); // message complet, F0..F7 inclus
        const delayMs = (pace * msgs[n].length) / DIN_BYTES_PER_SEC * 1000;
        if (delayMs > 0) await sleep(delayMs);
        if (n % 200 === 0 || n === msgs.length - 1) {
          const pct = (100 * (n + 1)) / msgs.length;
          $("bar").style.width = pct.toFixed(1) + "%";
          $("count").textContent = `${n + 1} / ${msgs.length} (${pct.toFixed(1)} %)`;
        }
      }
      const secs = (performance.now() - t0) / 1000;
      log(`Termine en ${secs.toFixed(0)} s. Laisse finir UPDATING FLASH, l'appareil redemarre seul.`, "ok");
      log("Si l'ecran reste sur RECEIVING… : un paquet a ete perdu (sans danger). Eteins/rallume, " +
          "re-entre en OS UPGRADE et relance avec une cadence plus haute (2.0).", "");
    } catch (e) {
      log("Erreur pendant l'envoi : " + e.message, "bad");
    } finally {
      state.sending = false;
      $("send").textContent = "Flasher";
      refreshReady();
    }
  }

  // ---- Cablage ------------------------------------------------------------
  window.addEventListener("DOMContentLoaded", () => {
    $("enable").addEventListener("click", initMidi);
    $("refresh").addEventListener("click", fillPorts);
    $("port").addEventListener("change", refreshReady);
    $("ack").addEventListener("change", refreshReady);
    $("send").addEventListener("click", send);

    const drop = $("drop");
    const file = $("file");
    drop.addEventListener("click", () => file.click());
    file.addEventListener("change", (e) => e.target.files[0] && loadFile(e.target.files[0]));
    ["dragover", "dragenter"].forEach((ev) =>
      drop.addEventListener(ev, (e) => {
        e.preventDefault();
        drop.classList.add("over");
      })
    );
    ["dragleave", "drop"].forEach((ev) =>
      drop.addEventListener(ev, (e) => {
        e.preventDefault();
        drop.classList.remove("over");
      })
    );
    drop.addEventListener("drop", (e) => e.dataTransfer.files[0] && loadFile(e.dataTransfer.files[0]));
  });
}
})();
