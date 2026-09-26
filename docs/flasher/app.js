/* Model:Cycles web flasher — user interface.
 *
 * Four steps: 1) choose (mods or official firmware), 2) load the official OS file,
 * 3) connect the device and pick a MIDI port, 4) flash.
 * The firmware is built automatically as soon as the OS file and the mods are known.
 *
 * Uses window.MCBuilder (builder.js, JS port of tools/build.py), window.MC_TWEAKS
 * (tweaks.js, generated) and window.MCFlasher (flasher.js: verify + send).
 */
(function () {
"use strict";

const $ = (id) => document.getElementById(id);
const REPO = "https://github.com/18nelli18/Modded-Cycles";
const ELEKTRON_DL = "https://www.elektron.se/support-downloads/modelcycles";

// Patched MAIN OS reference hashes (BUILD.md): 6ch-multiout = known-good result of
// ms-multi-output; the others = tools/build.py on the official OS 1.13. A build whose
// bytes don't match is refused. Key = tweak ids joined with "+", in feature order.
const REF_MAINOS = {
  "6ch-multiout": "65e24b50dd457444e87daea79dd41b82f61098cb8ae5cd27cbe0d91742f29555",
  "6ch-usbup": "db3d26cc3a48d1155933240c7d1d5476c8f56d2b6a54be1ffe7f5327e54c0521",
  "sdvintage-snare": "80b7b2bd003f2695488d629c0fab56c84e10213898c9820c321efa711f6957c7",
  "6ch-multiout+sdvintage-snare": "4494fb764c7643b2a9acea8b4fa2cafe10ee7d9644e56d08e333ee019f4cbe72",
  "6ch-usbup+sdvintage-snare": "38754937b06e3815ee1da9c93137d46283b612e1881772f4d034fb9f998b3335",
};

// ---------------------------------------------------------------------------
// Texts
// ---------------------------------------------------------------------------
const T = {
  en: {
    title: "Model:Cycles Flasher",
    tagline: "Install mods on your Elektron Model:Cycles, right from your browser.",
    s1: "What do you want to install?",
    tab_mods: "Mods",
    tab_restore: "Official firmware",
    mods_note: "None of these mods has been flashed on a real Model:Cycles yet. The MIDI IN route (step 3) always lets you go back to the official firmware.",
    restore_text: "Sends your official OS file <b>unchanged</b>, to go back to the stock firmware. It is also the best first rehearsal: it checks your cable and your setup without changing anything.",
    experimental: "Experimental",
    s2: "Load your official OS file",
    drop_title: "Drop model-cycles_OS1.13.syx here",
    drop_sub: "or click to choose it",
    drop_again: "Checked. Click or drop to use another file.",
    get_os: `Don't have it? <a href="${ELEKTRON_DL}" target="_blank" rel="noopener">Download OS 1.13 from elektron.se</a>, then unzip it.`,
    s3: "Connect your Model:Cycles",
    method_legend: "Connection",
    m_midi: "MIDI interface → MIDI IN",
    m_midi_sub: "Recommended. Always works, and it is also how you recover.",
    m_usb: "USB cable only",
    m_usb_sub: "No interface needed, but only from the official OS or a USB-friendly mod.",
    hm1: "Connect your MIDI interface's <b>MIDI OUT</b> to the Model:Cycles <b>MIDI IN</b> (3.5 mm jack): use the DIN adapter supplied with the Model:Cycles, or a stereo jack cable if your interface has a TRS MIDI out.",
    hm2: "Turn the Model:Cycles off. Hold <kbd>FUNC</kbd>, turn it on, then press <kbd>TRIG 4</kbd> (OS UPGRADE).",
    hm3: "The screen shows <code>READY TO RECEIVE</code>. Leave it like that.",
    hu1: "Connect the Model:Cycles to the computer with its USB cable and turn it on normally.",
    hu2: "On the Model:Cycles, open <b>CONFIG › UPGRADE</b> and confirm with <b>YES</b>.",
    hu3: "If this transfer fails, you will need a MIDI interface on the MIDI IN to recover.",
    allow: "Allow MIDI access",
    refresh: "Refresh",
    s4: "Flash",
    ack: "I've backed up my projects (Elektron Transfer) and I understand that flashing is at my own risk.",
    flash_btn: "Flash the Model:Cycles",
    flashing: "Flashing…",
    stop: "Stop",
    trouble: "Something went wrong?",
    t1q: "The screen stays on READY TO RECEIVE",
    t1a: "The data doesn't reach the MIDI IN. Pick your <b>MIDI interface</b> in step 3 (not “Model:Cycles”), and check that the cable goes from the interface's <b>OUT</b> to the Model:Cycles <b>IN</b>.",
    t2q: "It stays on RECEIVING… forever",
    t2a: "A packet was lost. It's harmless: turn the Model:Cycles off and on, enter OS UPGRADE again, set <b>Advanced › Send speed margin</b> to 2.0 and flash again.",
    t3q: "No MIDI port in the list",
    t3a: "Plug in your MIDI interface (or the Model:Cycles over USB), then click <b>Refresh</b>. Some interfaces only appear after the browser is restarted.",
    t4q: "The Model:Cycles doesn't start any more",
    t4a: "Hold <kbd>FUNC</kbd> while turning it on, press <kbd>TRIG 4</kbd>, then choose <b>Official firmware</b> in step 1 and flash through the MIDI IN. This always works: the startup menu is never overwritten.",
    advanced: "Advanced",
    pace: "Send speed margin",
    pace_hint: "1.4 by default. Raise it to 2.0 if the transfer stalls.",
    download: "Download the prepared .syx",
    download_hint: `To flash with <code>flash.sh</code> / <code>flash.bat</code> instead (<a href="${REPO}/blob/main/FLASH.md" target="_blank" rel="noopener">guide</a>).`,
    privacy: "Your firmware file never leaves your computer. Nothing is uploaded, no firmware is provided.",
    links: `<a href="${REPO}" target="_blank" rel="noopener">Source code</a> · <a href="${REPO}/blob/main/FLASH.md" target="_blank" rel="noopener">Full guide (French)</a> · Not affiliated with Elektron.`,
    // dynamic
    no_webmidi: "This browser can't talk to MIDI devices. Open this page in <b>Chrome, Edge or Opera</b> on a computer (Firefox and Safari don't support Web MIDI). You can still prepare and download the firmware here.",
    insecure: "Web MIDI needs a secure page. Open the online version, or serve this folder with <code>python3 -m http.server</code> — not by double-clicking the file.",
    reading: "Reading {name}…",
    os_ok: "Official Model:Cycles OS 1.13 recognised.",
    os_custom: "{name}: {device} firmware, but not the official OS 1.13 file. It will be sent <b>exactly as it is</b>.",
    os_custom_mods: "Your mod selection is ignored for this file.",
    os_restore_needs: "To restore the official firmware, load the official <code>model-cycles_OS1.13.syx</code>.",
    os_bad: "This file can't be used: {err}",
    building: "Preparing the firmware…",
    built: "Firmware ready: {mods}.",
    built_ref: "Checked against the reference build.",
    build_failed: "The firmware couldn't be prepared: {err}",
    stock_ready: "Ready to send the official firmware, unchanged.",
    pick_one: "Select at least one mod, or switch to “Official firmware”.",
    midi_asking: "Asking for MIDI access…",
    midi_wait: "Waiting for your permission: Chrome shows a prompt near the address bar. Click “Allow”. If you blocked it before, click the icon left of the address and allow MIDI.",
    midi_denied: "MIDI access was refused. Click the icon left of the address, allow MIDI, reload the page and try again.",
    midi_none: "No MIDI output found. Plug in your MIDI interface, then click Refresh.",
    midi_found: "{n} MIDI output(s) found.",
    midi_pick_iface: "Pick your MIDI interface — the one connected to the Model:Cycles MIDI IN.",
    midi_no_iface: "Only the Model:Cycles USB port is visible. For the MIDI IN route, plug in your MIDI interface and click Refresh.",
    midi_pick_dev: "The Model:Cycles USB port is selected.",
    midi_no_dev: "The Model:Cycles doesn't appear over USB. Connect it, turn it on and click Refresh.",
    warn_dev_on_midi: "This is the Model:Cycles' own USB port: the startup menu (OS UPGRADE) ignores USB. Pick your MIDI interface instead.",
    warn_iface_on_usb: "For the USB route, pick the port named “Model:Cycles”.",
    choose_port: "— choose a MIDI output —",
    via: "via",
    minutes: "about {m} min",
    mods_list_restore: "Official firmware (unchanged)",
    mods_list_custom: "Custom file {name} (sent as is)",
    miss_file: "Load your official OS file (step 2).",
    miss_mod: "Select a mod (step 1), or switch to “Official firmware”.",
    miss_build: "Preparing the firmware…",
    miss_fw: "The firmware isn't ready (step 2).",
    miss_midi: "Allow MIDI access (step 3).",
    miss_port: "Choose a MIDI output (step 3).",
    miss_ack: "Tick the box above to confirm.",
    miss_ready: "Put the Model:Cycles in receive mode (step 3), then flash.",
    watch_midi: "Watch the Model:Cycles screen: <code>READY TO RECEIVE</code> should turn into <code>RECEIVING…</code> within a few seconds. If it doesn't, press <b>Stop</b>: wrong port or cable.",
    watch_usb: "Watch the Model:Cycles screen: it should show that it is receiving. If nothing happens within a few seconds, press <b>Stop</b>.",
    keep_visible: "Keep this tab in the foreground: browsers slow down background tabs.",
    remaining: "{t} left",
    done_title: "Transfer complete.",
    done_body: "The Model:Cycles now writes the firmware (<code>UPDATING FLASH</code>) and restarts by itself. <b>Don't turn it off</b> until it has restarted.",
    done_6ch: "With the 6-channel mod, your computer should then show a Model:Cycles audio device with <b>6 input channels</b>.",
    stopped: "Stopped. The Model:Cycles is still waiting: turn it off and on, enter receive mode again, then flash again.",
    send_error: "The transfer failed: {err}. Turn the Model:Cycles off and on, enter receive mode again and retry.",
    port_gone: "The MIDI output has disappeared. Check the connection and pick it again.",
    leave: "A firmware transfer is in progress. Leaving now will interrupt it.",
    log_start: "Sending {n} packets to “{port}”, margin {pace}.",
  },
  fr: {
    title: "Flasher Model:Cycles",
    tagline: "Installe des mods sur ton Elektron Model:Cycles, directement depuis ton navigateur.",
    s1: "Qu'est-ce que tu veux installer ?",
    tab_mods: "Mods",
    tab_restore: "Firmware officiel",
    mods_note: "Aucun de ces mods n'a encore été flashé sur un vrai Model:Cycles. Le MIDI IN (étape 3) permet toujours de revenir au firmware officiel.",
    restore_text: "Envoie ton fichier d'OS officiel <b>sans le modifier</b>, pour revenir au firmware d'origine. C'est aussi la meilleure répétition avant un mod : elle vérifie ton câble et ton installation sans rien changer.",
    experimental: "Expérimental",
    s2: "Dépose ton fichier d'OS officiel",
    drop_title: "Dépose model-cycles_OS1.13.syx ici",
    drop_sub: "ou clique pour le choisir",
    drop_again: "Vérifié. Clique ou dépose pour changer de fichier.",
    get_os: `Tu ne l'as pas ? <a href="${ELEKTRON_DL}" target="_blank" rel="noopener">Télécharge l'OS 1.13 sur elektron.se</a>, puis dézippe-le.`,
    s3: "Branche ton Model:Cycles",
    method_legend: "Branchement",
    m_midi: "Interface MIDI → MIDI IN",
    m_midi_sub: "Recommandé. Marche toujours, et c'est aussi la voie de secours.",
    m_usb: "Câble USB seul",
    m_usb_sub: "Sans interface, mais seulement depuis l'OS officiel ou un mod qui garde l'USB.",
    hm1: "Relie la <b>sortie MIDI</b> de ton interface au <b>MIDI IN</b> du Model:Cycles (jack 3,5 mm) : avec l'adaptateur DIN fourni avec le Model:Cycles, ou un câble jack stéréo si ton interface a une sortie MIDI en TRS.",
    hm2: "Éteins le Model:Cycles. Maintiens <kbd>FUNC</kbd>, allume-le, puis appuie sur <kbd>TRIG 4</kbd> (OS UPGRADE).",
    hm3: "L'écran affiche <code>READY TO RECEIVE</code>. Laisse-le ainsi.",
    hu1: "Relie le Model:Cycles à l'ordinateur avec son câble USB et allume-le normalement.",
    hu2: "Sur le Model:Cycles, ouvre <b>CONFIG › UPGRADE</b> et confirme avec <b>YES</b>.",
    hu3: "Si ce transfert échoue, il faudra une interface MIDI sur le MIDI IN pour revenir en arrière.",
    allow: "Autoriser le MIDI",
    refresh: "Rafraîchir",
    s4: "Flasher",
    ack: "J'ai sauvegardé mes projets (Elektron Transfer) et je comprends que je flashe à mes risques.",
    flash_btn: "Flasher le Model:Cycles",
    flashing: "Flash en cours…",
    stop: "Arrêter",
    trouble: "Un problème ?",
    t1q: "L'écran reste sur READY TO RECEIVE",
    t1a: "Les données n'arrivent pas au MIDI IN. Choisis ton <b>interface MIDI</b> à l'étape 3 (pas « Model:Cycles »), et vérifie que le câble va de la <b>sortie</b> de l'interface à l'<b>entrée</b> du Model:Cycles.",
    t2q: "Il reste bloqué sur RECEIVING…",
    t2a: "Un paquet a été perdu, sans danger : éteins et rallume le Model:Cycles, repasse en OS UPGRADE, règle <b>Options avancées › Marge de vitesse</b> sur 2.0 et relance.",
    t3q: "Aucun port MIDI dans la liste",
    t3a: "Branche ton interface MIDI (ou le Model:Cycles en USB), puis clique <b>Rafraîchir</b>. Certaines interfaces n'apparaissent qu'après un redémarrage du navigateur.",
    t4q: "Le Model:Cycles ne démarre plus",
    t4a: "Maintiens <kbd>FUNC</kbd> en l'allumant, appuie sur <kbd>TRIG 4</kbd>, choisis <b>Firmware officiel</b> à l'étape 1 et flashe par le MIDI IN. Ça marche toujours : le menu de démarrage n'est jamais effacé.",
    advanced: "Options avancées",
    pace: "Marge de vitesse d'envoi",
    pace_hint: "1.4 par défaut. Monte à 2.0 si le transfert se bloque.",
    download: "Télécharger le .syx préparé",
    download_hint: `Pour flasher plutôt avec <code>flash.sh</code> / <code>flash.bat</code> (<a href="${REPO}/blob/main/FLASH.md" target="_blank" rel="noopener">guide</a>).`,
    privacy: "Ton fichier firmware ne quitte jamais ton ordinateur. Rien n'est envoyé en ligne, aucun firmware n'est fourni.",
    links: `<a href="${REPO}" target="_blank" rel="noopener">Code source</a> · <a href="${REPO}/blob/main/FLASH.md" target="_blank" rel="noopener">Guide complet</a> · Projet non affilié à Elektron.`,
    no_webmidi: "Ce navigateur ne sait pas parler aux appareils MIDI. Ouvre cette page dans <b>Chrome, Edge ou Opera</b> sur ordinateur (Firefox et Safari ne gèrent pas le Web MIDI). Tu peux quand même préparer et télécharger le firmware ici.",
    insecure: "Le Web MIDI exige une page sécurisée. Ouvre la version en ligne, ou sers ce dossier avec <code>python3 -m http.server</code> — pas par double-clic sur le fichier.",
    reading: "Lecture de {name}…",
    os_ok: "OS officiel Model:Cycles 1.13 reconnu.",
    os_custom: "{name} : firmware {device}, mais pas le fichier d'OS 1.13 officiel. Il sera envoyé <b>tel quel</b>.",
    os_custom_mods: "Ta sélection de mods est ignorée pour ce fichier.",
    os_restore_needs: "Pour restaurer le firmware officiel, dépose le fichier officiel <code>model-cycles_OS1.13.syx</code>.",
    os_bad: "Fichier inutilisable : {err}",
    building: "Préparation du firmware…",
    built: "Firmware prêt : {mods}.",
    built_ref: "Conforme au build de référence.",
    build_failed: "Impossible de préparer le firmware : {err}",
    stock_ready: "Prêt à envoyer le firmware officiel, sans modification.",
    pick_one: "Coche au moins un mod, ou passe sur « Firmware officiel ».",
    midi_asking: "Demande d'accès MIDI…",
    midi_wait: "En attente de ton autorisation : Chrome affiche une demande près de la barre d'adresse. Clique « Autoriser ». Si tu l'as bloquée, clique l'icône à gauche de l'adresse et autorise le MIDI.",
    midi_denied: "Accès MIDI refusé. Clique l'icône à gauche de l'adresse, autorise le MIDI, recharge la page et réessaie.",
    midi_none: "Aucune sortie MIDI. Branche ton interface MIDI, puis clique Rafraîchir.",
    midi_found: "{n} sortie(s) MIDI trouvée(s).",
    midi_pick_iface: "Choisis ton interface MIDI — celle reliée au MIDI IN du Model:Cycles.",
    midi_no_iface: "Seul le port USB du Model:Cycles est visible. Pour passer par le MIDI IN, branche ton interface MIDI et clique Rafraîchir.",
    midi_pick_dev: "Le port USB du Model:Cycles est sélectionné.",
    midi_no_dev: "Le Model:Cycles n'apparaît pas en USB. Branche-le, allume-le et clique Rafraîchir.",
    warn_dev_on_midi: "C'est le port USB du Model:Cycles lui-même : le menu de démarrage (OS UPGRADE) ignore l'USB. Choisis plutôt ton interface MIDI.",
    warn_iface_on_usb: "Pour passer par l'USB, choisis le port nommé « Model:Cycles ».",
    choose_port: "— choisis une sortie MIDI —",
    via: "via",
    minutes: "environ {m} min",
    mods_list_restore: "Firmware officiel (sans modification)",
    mods_list_custom: "Fichier {name} (envoyé tel quel)",
    miss_file: "Dépose ton fichier d'OS officiel (étape 2).",
    miss_mod: "Coche un mod (étape 1), ou passe sur « Firmware officiel ».",
    miss_build: "Préparation du firmware…",
    miss_fw: "Le firmware n'est pas prêt (étape 2).",
    miss_midi: "Autorise le MIDI (étape 3).",
    miss_port: "Choisis une sortie MIDI (étape 3).",
    miss_ack: "Coche la case ci-dessus pour confirmer.",
    miss_ready: "Mets le Model:Cycles en réception (étape 3), puis flashe.",
    watch_midi: "Regarde l'écran du Model:Cycles : <code>READY TO RECEIVE</code> doit passer à <code>RECEIVING…</code> en quelques secondes. Sinon, clique <b>Arrêter</b> : mauvais port ou mauvais câble.",
    watch_usb: "Regarde l'écran du Model:Cycles : il doit indiquer qu'il reçoit. S'il ne se passe rien en quelques secondes, clique <b>Arrêter</b>.",
    keep_visible: "Garde cet onglet au premier plan : les navigateurs ralentissent les onglets en arrière-plan.",
    remaining: "encore {t}",
    done_title: "Transfert terminé.",
    done_body: "Le Model:Cycles écrit maintenant le firmware (<code>UPDATING FLASH</code>) puis redémarre tout seul. <b>Ne l'éteins pas</b> avant qu'il ait redémarré.",
    done_6ch: "Avec le mod 6 canaux, ton ordinateur doit ensuite voir un périphérique audio Model:Cycles avec <b>6 canaux d'entrée</b>.",
    stopped: "Arrêté. Le Model:Cycles attend toujours : éteins-le et rallume-le, repasse en réception, puis relance.",
    send_error: "Le transfert a échoué : {err}. Éteins et rallume le Model:Cycles, repasse en réception et réessaie.",
    port_gone: "La sortie MIDI a disparu. Vérifie le branchement et choisis-la de nouveau.",
    leave: "Un flash est en cours. Quitter maintenant l'interromprait.",
    log_start: "Envoi de {n} paquets vers « {port} », marge {pace}.",
  },
};

// Feature texts shown in the UI (fallback: labels from tweaks.js).
const FEAT = {
  en: {
    usb6: { label: "6-channel USB audio",
      desc: "Each track gets its own USB channel (48 kHz / 32-bit): record the 6 tracks separately in your DAW. The stereo mix is no longer sent over USB." },
    "6ch-usbup": { label: "Keep OS updates over USB", note: "Recommended. Never flashed yet." },
    "6ch-multiout": { label: "Reference version", note: "Code verified on a Model:Samples running the Cycles OS. OS updates over USB stop working." },
    sdvintage: { label: "SD VINTAGE machine",
      desc: "A vintage snare engine inspired by the Syntakt, in place of the SNARE machine. PITCH tunes it, DECAY sets the length, COLOR the snap, SHAPE the brightness, SWEEP the pitch sweep, CONTOUR the body." },
  },
  fr: {
    usb6: { label: "Audio USB 6 canaux",
      desc: "Chaque piste a son propre canal USB (48 kHz / 32 bits) : enregistre les 6 pistes séparément dans ton logiciel. Le mix stéréo n'est plus envoyé en USB." },
    "6ch-usbup": { label: "Garder les mises à jour de l'OS par USB", note: "Recommandé. Jamais encore flashé." },
    "6ch-multiout": { label: "Version de référence", note: "Code vérifié sur un Model:Samples sous OS Cycles. La mise à jour de l'OS par USB ne marche plus." },
    sdvintage: { label: "Machine SD VINTAGE",
      desc: "Une caisse claire vintage inspirée du Syntakt, à la place de la machine SNARE. PITCH l'accorde, DECAY règle la longueur, COLOR le claquant, SHAPE la brillance, SWEEP le balayage, CONTOUR le corps." },
  },
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const st = {
  lang: "en",
  mode: "mods",            // "mods" | "restore"
  os: null,                // { raw, name, info, sha, stock }
  osError: null,
  fw: null,                // { raw, name, kind: "built"|"stock"|"custom", mods:[labels], ref:bool, sixch:bool }
  fwError: null,
  building: false,
  buildKey: null,
  cache: {},               // build results per selection key, for the current OS file
  midi: null,
  midiState: "idle",       // idle | asking | ready | denied | unsupported
  method: "midi",          // "midi" | "usb"
  portManual: false,
  sending: false,
  cancel: false,
  finished: null,          // "ok" | "stopped" | "error"
  url: null,
  wakeLock: null,
};

function t(key, vars) {
  let s = (T[st.lang] && T[st.lang][key]) || T.en[key] || key;
  if (vars) for (const k in vars) s = s.split("{" + k + "}").join(vars[k]);
  return s;
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function featText(id, key, fallback) {
  const f = (FEAT[st.lang] && FEAT[st.lang][id]) || FEAT.en[id];
  return (f && f[key]) || fallback || "";
}

function log(msg, cls) {
  const el = $("log");
  if (!el) return;
  const d = document.createElement("div");
  if (cls) d.className = cls;
  d.textContent = new Date().toLocaleTimeString() + "  " + msg;
  el.appendChild(d);
  el.scrollTop = el.scrollHeight;
}

// status block: list of [cls, html]
function setStatus(id, rows) {
  const el = $(id);
  el.innerHTML = (rows || []).filter(Boolean)
    .map(([cls, html]) => `<div class="row ${cls || ""}"><span class="dot"></span><span>${html}</span></div>`).join("");
}

const isDevicePort = (name) => /model\s*[:_-]?\s*(cycles|samples)/i.test(name || "");

// ---------------------------------------------------------------------------
// Language
// ---------------------------------------------------------------------------
function applyLang(lang) {
  st.lang = T[lang] ? lang : "en";
  document.documentElement.lang = st.lang;
  try { localStorage.setItem("mc-lang", st.lang); } catch (e) { /* private mode */ }
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach((el) => { el.innerHTML = t(el.dataset.i18nHtml); });
  document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === st.lang)));
  document.title = t("title");
  renderFeatures();
  if (st.os) describeOs();
  fillPorts();
  checkCompat();
  render();
}

// ---------------------------------------------------------------------------
// Step 1 — features
// ---------------------------------------------------------------------------
const selection = {};      // feature id -> { on: bool, variant: id }

function renderFeatures() {
  const box = $("features");
  const tw = window.MC_TWEAKS;
  if (!box || !tw || !tw.features) return;
  box.innerHTML = "";
  for (const f of tw.features) {
    const sel = selection[f.id] || (selection[f.id] = { on: false, variant: f.variants[0].id });
    const card = document.createElement("label");
    card.className = "feat" + (sel.on ? " on" : "");
    card.htmlFor = "feat-" + f.id;

    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.id = "feat-" + f.id;
    cb.checked = sel.on;
    cb.addEventListener("change", () => { sel.on = cb.checked; renderFeatures(); update(); });

    const ttl = document.createElement("div");
    ttl.className = "ttl";
    ttl.innerHTML = `<span>${esc(featText(f.id, "label", f.label))}</span><span class="tag">${esc(t("experimental"))}</span>`;
    const desc = document.createElement("div");
    desc.className = "desc";
    desc.textContent = featText(f.id, "desc", f.desc);
    card.append(cb, ttl, desc);

    if (f.variants.length > 1 && sel.on) {
      const vs = document.createElement("div");
      vs.className = "variants";
      for (const v of f.variants) {
        const l = document.createElement("label");
        const r = document.createElement("input");
        r.type = "radio";
        r.name = "var-" + f.id;
        r.value = v.id;
        r.checked = sel.variant === v.id;
        r.addEventListener("change", () => { sel.variant = v.id; update(); });
        const s = document.createElement("span");
        s.innerHTML = `${esc(featText(v.id, "label", v.label || v.id))}<small>${esc(featText(v.id, "note", ""))}</small>`;
        l.append(r, s);
        l.addEventListener("click", (e) => e.stopPropagation());   // don't toggle the card
        vs.appendChild(l);
      }
      card.appendChild(vs);
    }
    box.appendChild(card);
  }
}

function chosenTweaks() {
  const tw = window.MC_TWEAKS;
  if (!tw || !tw.features) return [];
  const out = [];
  for (const f of tw.features) {
    const sel = selection[f.id];
    if (!sel || !sel.on) continue;
    const tk = tw.tweaks.find((x) => x.id === (f.variants.length > 1 ? sel.variant : f.variants[0].id));
    if (tk) out.push(tk);
  }
  return out;
}
function chosenLabels() {
  const tw = window.MC_TWEAKS, out = [];
  for (const f of (tw && tw.features) || []) {
    const sel = selection[f.id];
    if (!sel || !sel.on) continue;
    let l = featText(f.id, "label", f.label);
    if (f.variants.length > 1) l += ` — ${featText(sel.variant, "label", sel.variant)}`;
    out.push(l);
  }
  return out;
}

function setMode(mode) {
  st.mode = mode;
  $("tab-mods").setAttribute("aria-selected", String(mode === "mods"));
  $("tab-restore").setAttribute("aria-selected", String(mode === "restore"));
  $("panel-mods").hidden = mode !== "mods";
  $("panel-restore").hidden = mode !== "restore";
  if (st.os) describeOs();
  update();
}

// ---------------------------------------------------------------------------
// Step 2 — OS file and automatic build
// ---------------------------------------------------------------------------
function readFile(file) {
  setStatus("file-status", [["is-busy", esc(t("reading", { name: file.name }))]]);
  const r = new FileReader();
  r.onload = () => loadOs(new Uint8Array(r.result), file.name);
  r.onerror = () => setStatus("file-status", [["is-bad", esc(t("os_bad", { err: String(r.error) }))]]);
  r.readAsArrayBuffer(file);
}

function loadOs(raw, name) {
  st.fw = null; st.fwError = null; st.buildKey = null; st.cache = {}; st.finished = null;
  $("result").innerHTML = ""; $("result").className = "result";
  try {
    const info = window.MCFlasher.verify(raw);
    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(raw));
    const stock = !!(window.MC_TWEAKS && sha === window.MC_TWEAKS.device.stock_syx_sha256);
    st.os = { raw, name, info, sha, stock };
    st.osError = null;
    log(`${name}: ${info.name}, ${info.count} packets, checksums OK${stock ? ", official OS 1.13" : ""}.`, "is-ok");
  } catch (e) {
    st.os = null;
    st.osError = e.message;
    log(`${name}: refused — ${e.message}`, "is-bad");
  }
  const d = $("drop");
  d.classList.toggle("loaded", !!st.os);
  $("drop-title").textContent = st.os ? name : t("drop_title");
  $("drop-sub").textContent = st.os ? t("drop_again") : t("drop_sub");
  describeOs();
  update();
}

function describeOs() {
  if (!st.os) {
    if (st.osError) setStatus("file-status", [["is-bad", esc(t("os_bad", { err: st.osError }))]]);
    else setStatus("file-status", []);
  }
}

function update() {
  prepareFirmware();
  render();
}

// Decide what will be sent, building it when needed.
function prepareFirmware() {
  const os = st.os;
  st.building = false;
  if (!os) { st.fw = null; st.fwError = null; return; }
  if (!os.stock) {
    if (st.mode === "restore") { st.fw = null; st.fwError = "restore_needs"; return; }
    st.fw = { raw: os.raw, name: os.name, kind: "custom", mods: [], ref: false, sixch: false };
    st.fwError = null;
    return;
  }
  if (st.mode === "restore") {
    st.fw = { raw: os.raw, name: os.name, kind: "stock", mods: [], ref: true, sixch: false };
    st.fwError = null;
    return;
  }
  const tweaks = chosenTweaks();
  if (!tweaks.length) { st.fw = null; st.fwError = "pick_one"; st.building = false; return; }
  const key = tweaks.map((x) => x.id).join("+");
  st.buildKey = key;
  // results are cached per selection, for this OS file
  const cached = st.cache[key];
  if (cached) {
    st.building = false;
    st.fw = cached.fw || null;
    st.fwError = cached.error || null;
    return;
  }
  st.fw = null; st.fwError = null; st.building = true;
  const labels = chosenLabels();
  const osRef = os;
  setTimeout(() => {                           // let the browser paint "Preparing…" first
    if (st.os !== osRef || st.cache[key]) return;
    let entry;
    try {
      const opts = {};
      if (REF_MAINOS[key]) opts.expectMainOsSha = REF_MAINOS[key];
      const r = window.MCBuilder.build(osRef.raw, window.MC_TWEAKS.device, tweaks, opts);
      entry = { fw: { raw: r.raw, name: `model-cycles_OS1.13_${key}.syx`, kind: "built", mods: labels,
        ref: !!REF_MAINOS[key], sixch: tweaks.some((x) => x.id.startsWith("6ch")) } };
      log(`Built ${key}: MAIN OS ${r.mainOsSha.slice(0, 12)}…, ${r.patchedBytes} bytes patched, ${r.raw.length} bytes.`, "is-ok");
    } catch (e) {
      entry = { error: e.message };
      log(`Build ${key} refused: ${e.message}`, "is-bad");
    }
    if (st.os !== osRef) return;              // another file was loaded meanwhile
    st.cache[key] = entry;
    if (st.mode === "mods" && st.buildKey === key) {   // still the current selection
      st.building = false;
      st.fw = entry.fw || null;
      st.fwError = entry.error || null;
    }
    render();
  }, 40);
}

// ---------------------------------------------------------------------------
// Step 3 — MIDI
// ---------------------------------------------------------------------------
function checkCompat() {
  const box = $("compat");
  let msg = "";
  if (typeof window.isSecureContext !== "undefined" && !window.isSecureContext) msg = t("insecure");
  else if (!navigator.requestMIDIAccess) msg = t("no_webmidi");
  box.innerHTML = msg;
  box.hidden = !msg;
  if (msg) st.midiState = st.midiState === "ready" ? "ready" : "unsupported";
  return !msg;
}

async function initMidi(silent) {
  if (!checkCompat()) { render(); return; }
  if (st.midiState === "asking") return;
  st.midiState = "asking";
  if (!silent) log("Requesting MIDI access (with SysEx)…");
  renderMidi();
  let done = false;
  const hint = setTimeout(() => { if (!done) { st.midiHint = true; renderMidi(); } }, 2500);
  try {
    st.midi = await navigator.requestMIDIAccess({ sysex: true });
  } catch (e) {
    done = true; clearTimeout(hint); st.midiHint = false;
    st.midiState = "denied";
    log("MIDI access failed: " + (e && e.message ? e.message : e), "is-bad");
    render();
    return;
  }
  done = true; clearTimeout(hint); st.midiHint = false;
  st.midiState = "ready";
  st.midi.onstatechange = () => { fillPorts(); render(); };
  log("MIDI access granted.", "is-ok");
  fillPorts();
  render();
}

function outputs() {
  return st.midi ? [...st.midi.outputs.values()] : [];
}

function fillPorts() {
  const sel = $("port");
  if (!sel) return;
  const outs = outputs();
  const prev = sel.value;
  sel.innerHTML = "";
  const ph = document.createElement("option");
  ph.value = "";
  ph.textContent = t("choose_port");
  sel.appendChild(ph);
  for (const o of outs) {
    const opt = document.createElement("option");
    opt.value = o.id;
    opt.textContent = o.name + (o.manufacturer && !(o.name || "").includes(o.manufacturer) ? ` (${o.manufacturer})` : "");
    sel.appendChild(opt);
  }
  if (st.portManual && outs.some((o) => o.id === prev)) sel.value = prev;
  else {
    st.portManual = false;
    const want = outs.find((o) => (st.method === "usb" ? isDevicePort(o.name) : !isDevicePort(o.name)));
    sel.value = want ? want.id : "";
  }
}

function currentPort() {
  const id = $("port").value;
  return id && st.midi ? st.midi.outputs.get(id) : null;
}

function renderMidi() {
  const ready = st.midiState === "ready";
  $("allow").hidden = ready;
  $("allow").disabled = st.midiState === "unsupported";
  $("port").hidden = !ready;
  $("refresh").hidden = !ready;
  const rows = [];
  if (st.midiState === "asking") rows.push(["is-busy", esc(t(st.midiHint ? "midi_wait" : "midi_asking"))]);
  if (st.midiState === "denied") rows.push(["is-bad", esc(t("midi_denied"))]);
  if (ready) {
    const outs = outputs();
    const port = currentPort();
    if (!outs.length) rows.push(["is-warn", esc(t("midi_none"))]);
    else {
      const ifaces = outs.filter((o) => !isDevicePort(o.name));
      const devs = outs.filter((o) => isDevicePort(o.name));
      if (st.method === "midi") {
        if (port && isDevicePort(port.name)) rows.push(["is-warn", esc(t("warn_dev_on_midi"))]);
        else if (port) rows.push(["is-ok", esc(t("midi_found", { n: outs.length })) + " " + esc(t("midi_pick_iface"))]);
        else if (!ifaces.length) rows.push(["is-warn", esc(t("midi_no_iface"))]);
        else rows.push(["", esc(t("midi_pick_iface"))]);
      } else {
        if (port && !isDevicePort(port.name)) rows.push(["is-warn", esc(t("warn_iface_on_usb"))]);
        else if (port) rows.push(["is-ok", esc(t("midi_pick_dev"))]);
        else if (!devs.length) rows.push(["is-warn", esc(t("midi_no_dev"))]);
      }
    }
  }
  setStatus("midi-status", rows);
}

function setMethod(m) {
  st.method = m;
  $("m-midi").classList.toggle("on", m === "midi");
  $("m-usb").classList.toggle("on", m === "usb");
  $("howto-midi").hidden = m !== "midi";
  $("howto-usb").hidden = m !== "usb";
  st.portManual = false;
  fillPorts();
  render();
}

// ---------------------------------------------------------------------------
// Rendering (status, step badges, flash button)
// ---------------------------------------------------------------------------
function missingReason() {
  if (!st.os) return st.osError ? "miss_fw" : "miss_file";
  if (st.fwError === "pick_one") return "miss_mod";
  if (st.building) return "miss_build";
  if (!st.fw) return "miss_fw";
  if (st.midiState !== "ready") return "miss_midi";
  if (!currentPort()) return "miss_port";
  if (!$("ack").checked) return "miss_ack";
  return null;
}

function render() {
  // step 2 status
  if (st.os) {
    const rows = [];
    if (st.os.stock) rows.push(["is-ok", esc(t("os_ok"))]);
    else {
      rows.push(["is-warn", t("os_custom", { name: esc(st.os.name), device: esc(st.os.info.name) })]);
      if (st.mode === "mods" && chosenTweaks().length) rows.push(["", esc(t("os_custom_mods"))]);
    }
    if (st.fwError === "restore_needs") rows.push(["is-bad", t("os_restore_needs")]);
    else if (st.fwError === "pick_one") rows.push(["", esc(t("pick_one"))]);
    else if (st.building) rows.push(["is-busy", esc(t("building"))]);
    else if (st.fwError) rows.push(["is-bad", esc(t("build_failed", { err: st.fwError }))]);
    else if (st.fw && st.fw.kind === "built")
      rows.push(["is-ok", esc(t("built", { mods: st.fw.mods.join(" + ") })) + (st.fw.ref ? " " + esc(t("built_ref")) : "")]);
    else if (st.fw && st.fw.kind === "stock") rows.push(["is-ok", esc(t("stock_ready"))]);
    setStatus("file-status", rows);
  }

  renderMidi();

  // download link
  const dl = $("download");
  if (st.fw) {
    if (st.urlFor !== st.fw.raw) {
      if (st.url) URL.revokeObjectURL(st.url);
      st.url = URL.createObjectURL(new Blob([st.fw.raw], { type: "application/octet-stream" }));
      st.urlFor = st.fw.raw;
    }
    dl.href = st.url;
    dl.download = st.fw.name;
    dl.hidden = false;
  } else dl.hidden = true;

  // step badges
  const choseOk = st.mode === "restore" || chosenTweaks().length > 0;
  $("step-choose").classList.toggle("done", choseOk);
  $("step-file").classList.toggle("done", !!st.fw && !st.building);
  $("step-connect").classList.toggle("done", st.midiState === "ready" && !!currentPort());
  $("step-flash").classList.toggle("done", st.finished === "ok");

  // summary
  const sum = $("summary");
  if (st.fw) {
    const what = st.fw.kind === "built" ? st.fw.mods.join(" + ")
      : st.fw.kind === "stock" ? t("mods_list_restore") : t("mods_list_custom", { name: st.fw.name });
    const port = currentPort();
    const mins = Math.max(1, Math.round(window.MCFlasher.transferSeconds(st.fw.raw, pace()) / 60));
    sum.innerHTML = `<b>${esc(what)}</b>` + (port ? ` ${esc(t("via"))} <b>${esc(port.name)}</b>` : "") +
      ` · ${esc(t("minutes", { m: mins }))}`;
    sum.hidden = false;
  } else sum.hidden = true;

  // flash button
  const miss = st.sending ? null : missingReason();
  $("flash").disabled = st.sending || !!miss;
  $("flash").textContent = st.sending ? t("flashing") : t("flash_btn");
  $("missing").textContent = st.sending ? "" : miss ? t(miss) : st.finished === "ok" ? "" : t("miss_ready");
  $("stop").hidden = !st.sending;
}

function pace() {
  const v = parseFloat($("pace").value);
  return Number.isFinite(v) && v >= 0 ? v : window.MCFlasher.DEFAULT_PACE;
}

// ---------------------------------------------------------------------------
// Step 4 — flash
// ---------------------------------------------------------------------------
function fmtTime(s) {
  s = Math.max(0, Math.round(s));
  const m = Math.floor(s / 60), r = s % 60;
  return m ? `${m} min ${String(r).padStart(2, "0")} s` : `${r} s`;
}

async function flash() {
  if (missingReason() || st.sending) return;
  const out = currentPort();
  const fw = st.fw;
  const p = pace();
  st.sending = true; st.cancel = false; st.finished = null;
  $("result").innerHTML = ""; $("result").className = "result";
  $("progress").hidden = false;
  $("bar").style.width = "0%";
  $("pct").textContent = "0 %";
  $("eta").textContent = "";
  $("watch").className = "callout";
  $("watch").hidden = false;
  $("watch").innerHTML = t(st.method === "usb" ? "watch_usb" : "watch_midi") + "<br>" + esc(t("keep_visible"));
  render();
  try { if (navigator.wakeLock) st.wakeLock = await navigator.wakeLock.request("screen"); } catch (e) { /* optional */ }
  const total = window.MCFlasher.transferSeconds(fw.raw, p);
  const t0 = Date.now();
  log(t("log_start", { n: window.MCFlasher.splitMessages(fw.raw).length, port: out.name, pace: p }));
  let res = null, err = null;
  try {
    res = await window.MCFlasher.sendSysex(out, fw.raw, {
      pace: p,
      isCancelled: () => st.cancel || !st.midi || !st.midi.outputs.get(out.id),
      onProgress: (n, tot) => {
        const pct = (100 * n) / tot;
        $("bar").style.width = pct.toFixed(1) + "%";
        $("barwrap").setAttribute("aria-valuenow", pct.toFixed(0));
        $("pct").textContent = `${pct.toFixed(0)} %`;
        const el = (Date.now() - t0) / 1000;
        const left = n > 0 ? Math.max(total - el, (el / n) * (tot - n)) : total;
        $("eta").textContent = t("remaining", { t: fmtTime(left) });
      },
    });
  } catch (e) {
    err = e;
  }
  try { if (st.wakeLock) await st.wakeLock.release(); } catch (e) { /* ignore */ }
  st.wakeLock = null;
  st.sending = false;
  const r = $("result");
  if (err) {
    st.finished = "error";
    r.className = "result bad";
    r.innerHTML = `<p>${esc(t("send_error", { err: err.message || err }))}</p>`;
    log("Transfer error: " + (err.message || err), "is-bad");
  } else if (res.cancelled) {
    st.finished = "stopped";
    r.className = "result warn";
    const gone = !st.cancel;
    r.innerHTML = `<p>${esc(t(gone ? "port_gone" : "stopped"))}</p>` + (gone ? `<p>${esc(t("stopped"))}</p>` : "");
    log(`Stopped after ${res.sent}/${res.total} packets.`, "is-warn");
  } else {
    st.finished = "ok";
    $("watch").hidden = true;
    $("bar").style.width = "100%";
    $("pct").textContent = "100 %";
    $("eta").textContent = fmtTime(res.seconds);
    r.className = "result ok";
    r.innerHTML = `<p><b>${esc(t("done_title"))}</b></p><p>${t("done_body")}</p>` +
      (fw.sixch ? `<p>${t("done_6ch")}</p>` : "");
    log(`Transfer complete in ${Math.round(res.seconds)} s.`, "is-ok");
  }
  $("progress").hidden = st.finished !== "ok";
  render();
}

// ---------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------
function init() {
  let lang = "en";
  try { lang = localStorage.getItem("mc-lang") || ""; } catch (e) { lang = ""; }
  if (!lang) lang = /^fr\b/i.test(navigator.language || "") ? "fr" : "en";
  st.lang = lang;

  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => applyLang(b.dataset.lang)));
  $("tab-mods").addEventListener("click", () => setMode("mods"));
  $("tab-restore").addEventListener("click", () => setMode("restore"));

  const drop = $("drop"), file = $("file");
  file.addEventListener("change", (e) => { if (e.target.files[0]) readFile(e.target.files[0]); e.target.value = ""; });
  drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); file.click(); } });
  ["dragover", "dragenter"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0]); });

  document.querySelectorAll('input[name="method"]').forEach((r) => r.addEventListener("change", () => setMethod(r.value)));
  $("allow").addEventListener("click", () => initMidi(false));
  $("refresh").addEventListener("click", () => { fillPorts(); render(); });
  $("port").addEventListener("change", () => { st.portManual = true; render(); });
  $("ack").addEventListener("change", render);
  $("pace").addEventListener("input", render);
  $("flash").addEventListener("click", flash);
  $("stop").addEventListener("click", () => { st.cancel = true; });

  document.addEventListener("visibilitychange", () => {
    if (st.sending && document.hidden) {
      log(t("keep_visible"), "is-warn");
      $("watch").classList.add("warn");
    }
  });
  window.addEventListener("beforeunload", (e) => {
    if (!st.sending) return;
    e.preventDefault();
    e.returnValue = t("leave");
  });

  $("build-stamp").textContent = "· build " + (window.MC_BUILD || "?");
  applyLang(st.lang);
  update();

  // Returning visitor who already allowed MIDI: connect without a click.
  if (checkCompat() && navigator.permissions && navigator.permissions.query) {
    navigator.permissions.query({ name: "midi", sysex: true })
      .then((p) => { if (p.state === "granted") initMidi(true); })
      .catch(() => { /* not supported */ });
  }
}

// test hooks (tools/webflash_smoke.js)
window.MCFlasherApp = { state: st, REF_MAINOS, loadOs, setMode, setMethod, applyLang, render };

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
})();
