/* Model:Cycles web flasher — user interface.
 *
 * Four steps: 1) choose (mods or official firmware), 2) load the official OS file,
 * 3) connect the device over USB (CONFIG > UPGRADE) and pick its MIDI port, 4) flash.
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
const ELEKTRON_SMP_DL = "https://www.elektron.se/support-downloads/modelsamples";
const ELEKTRON_ST_DL = "https://www.elektron.se/support-downloads/syntakt";

// Patched MAIN OS reference hashes, from tools/build.py on the official OS 1.13 (the drumkilla
// tweaks alone also match drumkilla's own tweak.py byte for byte). A build whose bytes don't
// match is refused. Key = tweak ids joined with "+", in feature order. Every combination the
// page offers must be listed here (tools/webflash_smoke.js checks it).
const REF_MAINOS = {
  "6ch-usbup": "db3d26cc3a48d1155933240c7d1d5476c8f56d2b6a54be1ffe7f5327e54c0521",
  "latching-mute": "6903892ba3119ed161190dee315e41101634d588ce5aff47e4fa99a92b16c078",
  "trig-preview": "87608a429e540b17d92f105135d29777817da92187bf5dfb6a714d8da0094107",
  "browser-scroll": "4d7caf0d48b0deae53872400ffa98e3acf588f88b2b7684cf4971ead5f834d05",
  "6ch-usbup+latching-mute": "641c2f9e43d38b0f73401c05e3bbee5a4454187e0d251982a1567671bc59dd6a",
  "6ch-usbup+trig-preview": "03e2896b3685f113fa434de20dc73f3ded70266cf26bc1034d097f722cd05e08",
  "6ch-usbup+browser-scroll": "c75c9fef8924b8f235adbcd621f37c976156f46d09a8451a28718dc40095d237",
  "latching-mute+trig-preview": "694e7d8cbb6fc17c04cc8e0037013c2d1e5a46e415acc5a6c50a185281bd0fe1",
  "latching-mute+browser-scroll": "2b52fec33202d5ba41ae50e1453efbb73f5de06b573de2d3ca8fce0b479aea60",
  "trig-preview+browser-scroll": "777d6613c07d2e5b6dfe701c99f5f1c3b2cd3a8932a52185987f9125842e0794",
  "6ch-usbup+latching-mute+trig-preview": "868bc96cfb7c9621533bd8c119fbdcccd7c55e560f5ec7808a0f2531f7c47d52",
  "6ch-usbup+latching-mute+browser-scroll": "65d3aaffc219bd2b837ebde53d6b69e388a4b44f30391bafe23c0f8787f38960",
  "6ch-usbup+trig-preview+browser-scroll": "74d1f467974c019a7120e8dce7c4c45a773d5d2854a2832eea64e34d327dc5ce",
  "latching-mute+trig-preview+browser-scroll": "71fef138b1ae16f3ad440ecaa6a6327c1a987ce2c8a86b74329f68159981a15c",
  "6ch-usbup+latching-mute+trig-preview+browser-scroll": "fd57831c61926fb3b1902cadcb0f95e68db3bb637b4cd20860a0efc46db82cfa",
  // + the real Syntakt SD VINTAGE engine, built with the official Syntakt_OS1.41.syx (build.py --syntakt)
  "sdvintage-exact": "8e2290a79fb1406ce65b3af3c5d3d95faade666e98eb8ecce0c0fa25fe87b15d",
  "6ch-usbup+sdvintage-exact": "ea57b3c52b77d4de3df073ee605f2fecde59878d06e3141c927ed3bd7f489904",
  "latching-mute+sdvintage-exact": "8995df8f3f3781e73b86bedc2447a65ccbe718c14dad7e0e8bfd8dc6e905b39b",
  "trig-preview+sdvintage-exact": "5b90c5f7a681914238a17aab7d1e0236a1ec132297c9f4eaaa47ee127daf0618",
  "browser-scroll+sdvintage-exact": "b51e82a934787e128eb452da36b6f4f3355040b8bf9a5dbcc8f8e84dc4fee5cb",
  "6ch-usbup+latching-mute+sdvintage-exact": "9843c5424b067ec21322ce3fcbd4468d73813ac03f5e5b5282747f1e4511ae4e",
  "6ch-usbup+trig-preview+sdvintage-exact": "df09c1f9458dad0a0022ce234ed73d45952a0adad4b2df8779c285dffb787945",
  "6ch-usbup+browser-scroll+sdvintage-exact": "6433f71e1d66dbdeb23c61814072892c33a301b5cf0d518a9cc9ad4bd04e2924",
  "latching-mute+trig-preview+sdvintage-exact": "f92c11bdc3beba6ca859ac5b1bb3f731f9c40ecf06a96a7b69b5585d971aa5c0",
  "latching-mute+browser-scroll+sdvintage-exact": "a087f95d842c7fef6c8aad690a53d27cd2aca20c992718744a95bdaf9bd5c001",
  "trig-preview+browser-scroll+sdvintage-exact": "a08580c9929d1cc981f27adc6ae2cfb17dde4416a536a0246d5cdf227a7898f3",
  "6ch-usbup+latching-mute+trig-preview+sdvintage-exact": "575990496b3f11cd44e19f5b129602ea9789624d848b161a0ac0e84da05982c7",
  "6ch-usbup+latching-mute+browser-scroll+sdvintage-exact": "509552fbb9a7d6d948755b56ed69b851b508fb787f1571e886d899c9e23978c5",
  "6ch-usbup+trig-preview+browser-scroll+sdvintage-exact": "04c924d6e289ea672a3df22dadd60eb52575ac34c52f1210f4580bbde31513be",
  "latching-mute+trig-preview+browser-scroll+sdvintage-exact": "5f6505f757183bc5601d4f041dc4fda689e3e23b33c75ca62d4db12fdb30f48e",
  "6ch-usbup+latching-mute+trig-preview+browser-scroll+sdvintage-exact": "20d5c2d861796a849a45dfe5b5f11d6254dddc0037ff5594ff75d359a93d86a2",
  // + SD VINTAGE as a 7th machine "SDVtg" next to SNARE (tweak sdvintage-7th, notes/18)
  "sdvintage-7th": "badc7748a986c0b101b17a3405e6d05e9e9cdd718258ba9436ea0dcd832e91c6",
  "6ch-usbup+sdvintage-7th": "4c93c7c2212d75c5d54e63969d88cbd5886b1a4424256e26ea9dc72cb1eb0d21",
  "latching-mute+sdvintage-7th": "602718d9a0f0acee6cdcf4c90455d9b830463a30d2ec9de3d82fc0acd0dc4a1f",
  "trig-preview+sdvintage-7th": "632862776713cf969a8970b1409df015ce2632ef51a9f6bf3dc1ab318cbd6206",
  "browser-scroll+sdvintage-7th": "c034dc1c663db5ad8039b9661cdde8df2087ba661a3bde749104c99c3d3e8cd6",
  "6ch-usbup+latching-mute+sdvintage-7th": "9fa943d7c398d3d7f901d47b0d71876babb406736363dc82f0616066f91c3fcc",
  "6ch-usbup+trig-preview+sdvintage-7th": "9a23578dc5ba03585f85a2154490deb237296cc370e8b4f7c92b7e71f821bca5",
  "6ch-usbup+browser-scroll+sdvintage-7th": "3f5aef098421270ee7d5c8526724e4c09ad15f35bccd7fc91b8032d11fcf7af2",
  "latching-mute+trig-preview+sdvintage-7th": "357495c3a067a7c370256b3330174dee398b105b43bc4b5b9025eae264d770cb",
  "latching-mute+browser-scroll+sdvintage-7th": "501d829ece5a6d581b361746a7e7e785612ec3a880c61ede12c7a1cfa3a5b6a6",
  "trig-preview+browser-scroll+sdvintage-7th": "1a76e301e5a37ae952e7ba53b0243d9169552754105400cdf4cc6999113bf403",
  "6ch-usbup+latching-mute+trig-preview+sdvintage-7th": "8b4f3d9b06211427d96cb43b1eeb30962df8ede91353ee6e53e1007b0735a09e",
  "6ch-usbup+latching-mute+browser-scroll+sdvintage-7th": "3ef61003c2df9efe268a3f8cc571693cc2128432ef02b089b31cfc116a45ccb4",
  "6ch-usbup+trig-preview+browser-scroll+sdvintage-7th": "9f7e7d4417b30b31952e939ad3cc026c1829ec6e256b702f5348f4a9a3f05758",
  "latching-mute+trig-preview+browser-scroll+sdvintage-7th": "2d42894ce3688cc2ff2db6471d20e722701be276e436281223fe06694ab4b011",
  "6ch-usbup+latching-mute+trig-preview+browser-scroll+sdvintage-7th": "ed3fd6ed901076f3c66dba8df1b8133686182be4af1db1b5c3d851a7ef4de47d",
};

// "Samples OS" tab: official Model:Samples OS 1.13 inside the official Model:Cycles container
// (tools/crossflash.py --to cycles). SHA-256 of the resulting .syx; tested on a real Model:Cycles.
const REF_SAMPLES_ON_CYCLES = "614d28cfe1100856aef7a67aa49003726e27e0e6eb3b6b05ecba6dc177e83911";

// Open-source work this flasher builds on (shown in the Credits section).
const CREDITS = [
  { who: "scottmetoyer", repo: "scottmetoyer/ms-multi-output",
    en: "the 6-channel USB audio mod", fr: "le mod audio USB 6 canaux" },
  { who: "drumkilla", repo: "drumkilla/elektron-model-tweaks",
    en: "latching mute, trig preview and name scrolling, and the firmware toolkit (mtlib) this page's builder is ported from",
    fr: "le mute verrouillé, l'écoute d'un pas et le défilement des noms, et la boîte à outils firmware (mtlib) dont le builder de cette page est un portage" },
  { who: "mischa85", repo: "mischa85/elektron-firmware-tool",
    en: "the Elektron firmware container format and its re-signing", fr: "le format du conteneur firmware Elektron et sa re-signature" },
  { who: "mxldyn", repo: "mxldyn/octamax",
    en: "the reverse-engineering method for Elektron firmware", fr: "la méthode de rétro-ingénierie des firmwares Elektron" },
];

const FLASH_GUIDE = `${REPO}/blob/main/FLASH.md`;

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
    mods_note: "All these mods have been tested on a real Model:Cycles, except the options marked “New”. Tick several to combine them.",
    restore_text: "Sends your official OS file <b>unchanged</b>, to go back to the stock firmware. It is also a good first rehearsal: it checks your cable and your setup without changing anything.",
    tab_samples: "Samples OS",
    samples_title: "Turn your Model:Cycles into a Model:Samples",
    samples_text: "Load and play your own samples, managed with Elektron Transfer. The page puts the official Model:Samples OS inside your Model:Cycles firmware: the startup menu, the updater and the signature of the Model:Cycles stay in place.",
    samples_w1: "Back up your projects with Transfer first: the Model:Samples OS uses the same storage.",
    samples_w2: `Coming back to the Model:Cycles OS goes through the startup menu, which only listens to the MIDI IN: it needs a MIDI interface (<a href="${FLASH_GUIDE}" target="_blank" rel="noopener">full guide</a>).`,
    samples_w3: "From the Samples OS, never run CONFIG › UPGRADE with a Model:Samples file: it would also replace the startup menu of your Model:Cycles.",
    samples_ack: "I have a MIDI interface for the way back (to the Model:Cycles MIDI IN).",
    restore_from_samples: `Coming back from the Samples OS? Its way back is the startup menu through the MIDI IN: see the <a href="${FLASH_GUIDE}" target="_blank" rel="noopener">full guide</a>.`,
    tested: "Tested",
    experimental: "Experimental",
    credit_by: "by {who}",
    credit_based: "based on {repo} by {who}",
    s2: "Load your official OS file",
    drop_title: "Drop model-cycles_OS1.13.syx here",
    drop_sub: "or click to choose it",
    drop_again: "Checked. Click or drop to use another file.",
    get_os: `Don't have it? <a href="${ELEKTRON_DL}" target="_blank" rel="noopener">Download Model:Cycles OS 1.13 from elektron.se</a>, then unzip it.`,
    s2_samples: "Load both official OS files",
    drop2_title: "Drop model-samples_OS1.13.syx here",
    drop2_sub: "the official Model:Samples OS — or click to choose it",
    get_os_samples: `Don't have it? <a href="${ELEKTRON_SMP_DL}" target="_blank" rel="noopener">Download Model:Samples OS 1.13 from elektron.se</a>, then unzip it.`,
    drop3_title: "Drop Syntakt_OS1.41.syx here",
    drop3_sub: "the official Syntakt OS, for the SD VINTAGE engine — or click to choose it",
    get_os_syntakt: `Don't have it? <a href="${ELEKTRON_ST_DL}" target="_blank" rel="noopener">Download Syntakt OS 1.41 from elektron.se</a>, then unzip it. The page reads the SD VINTAGE engine from it, on your computer: no Syntakt needed.`,
    s3: "Connect your Model:Cycles over USB",
    hu1: "Connect the Model:Cycles to the computer with a USB cable and turn it on normally.",
    hu2: "On the Model:Cycles, open <b>CONFIG › UPGRADE</b> and confirm with <b>YES</b>. It now waits for the firmware.",
    hu3: "Allow MIDI access below: the port named “Model:Cycles” is selected automatically.",
    allow: "Allow MIDI access",
    refresh: "Refresh",
    s4: "Flash",
    ack: "I've backed up my projects (Elektron Transfer) and I understand that flashing is at my own risk.",
    flash_btn: "Flash the Model:Cycles",
    flashing: "Flashing…",
    stop: "Stop",
    trouble: "Something went wrong?",
    t1q: "Nothing happens on the Model:Cycles screen",
    t1a: "Check that <b>CONFIG › UPGRADE</b> is open and waiting, and that the port named “Model:Cycles” is selected in step 3. Close Elektron Transfer, Overbridge and your music software (on Windows they lock the port), then try again.",
    t2q: "The transfer stops, or the Model:Cycles shows an error",
    t2a: "Turn the Model:Cycles off and on, open <b>CONFIG › UPGRADE</b> again, set <b>Advanced › Send speed margin</b> to 2.0 and flash again.",
    t3q: "No MIDI port in the list",
    t3a: "Connect the Model:Cycles with a USB cable that carries data (some cables only charge), turn it on, then click <b>Refresh</b>. Some systems only show a new device after the browser is restarted.",
    t4q: "The update over USB is refused, or the Model:Cycles doesn't start any more",
    t4a: `Recovery goes through the startup menu, which only listens to the MIDI IN: follow the <a href="${FLASH_GUIDE}" target="_blank" rel="noopener">full guide</a> (it needs a MIDI interface). The same goes if you installed the old “6-channel reference version”, which disables updates over USB.`,
    advanced: "Advanced",
    pace: "Send speed margin",
    pace_hint: "1.4 by default. Raise it to 2.0 if the transfer stalls.",
    download: "Download the prepared .syx",
    download_hint: `To flash with <code>flash.sh</code> / <code>flash.bat</code> instead (<a href="${FLASH_GUIDE}" target="_blank" rel="noopener">guide</a>).`,
    credits: "Credits",
    credits_intro: "This flasher stands on the shoulders of these open-source projects (MIT licence), none of which includes firmware:",
    privacy: "Your firmware file never leaves your computer. Nothing is uploaded, no firmware is provided.",
    links: `<a href="${REPO}" target="_blank" rel="noopener">Source code</a> · <a href="${FLASH_GUIDE}" target="_blank" rel="noopener">Full guide (French)</a> · Not affiliated with Elektron.`,
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
    smp_ok: "Official Model:Samples OS 1.13 recognised.",
    smp_bad: "This is not the official Model:Samples OS 1.13 file: {err}",
    smp_not_official: "its SHA-256 differs from the official file",
    st_ok: "Official Syntakt OS 1.41 recognised.",
    st_bad: "This is not the official Syntakt OS 1.41 file: {err}",
    needs_syntakt: "The SD VINTAGE engine is read from the official Syntakt OS file: drop it below.",
    miss_syntakt: "Load the official Syntakt OS file (step 2).",
    done_sdv: "Then pick the SNARE machine on a track and play it: it is the Syntakt's SD VINTAGE. PITCH, COLOR, SHAPE, SWEEP and CONTOUR act as its TUNE, INHM, FCMP, SWEP and MENV.",
    done_sdv7: "Then press MACHINES on a track and pick <b>SDVtg</b>, the 7th machine: the Syntakt's SD VINTAGE. Its knobs show the Syntakt names (Inharmonicity, Freq Complex, Pitch Sweep, Mod Envelope). SNARE is unchanged. If something goes wrong, flash the official firmware back from CONFIG › UPGRADE.",
    warn_samples_port: "This port is a Model:Samples (a Model:Cycles running the Samples OS): it refuses a Model:Cycles firmware over USB. The way back goes through the startup menu and the MIDI IN (see the full guide).",
    samples_needs_cycles: "For the Samples OS, the first file must be the official <code>model-cycles_OS1.13.syx</code>: it provides the startup menu, updater and signature that stay on your Model:Cycles.",
    samples_ready: "Firmware ready: the Model:Samples OS for your Model:Cycles.",
    mods_list_samples: "Model:Samples OS (for Model:Cycles)",
    miss_samples_cycles: "The first file must be the official Model:Cycles OS (step 2).",
    miss_samples_file: "Load the official Model:Samples OS file (step 2).",
    miss_samples_ack: "Confirm you have a MIDI interface for the way back (step 1).",
    done_samples: "It restarts as a <b>Model:Samples</b>: Elektron Transfer and your computer see a “Model:Samples”. Load your samples with Transfer.",
    pick_one: "Select at least one mod, or switch to “Official firmware”.",
    midi_asking: "Asking for MIDI access…",
    midi_wait: "Waiting for your permission: Chrome shows a prompt near the address bar. Click “Allow”. If you blocked it before, click the icon left of the address and allow MIDI.",
    midi_denied: "MIDI access was refused. Click the icon left of the address, allow MIDI, reload the page and try again.",
    midi_none: "No MIDI output found. Connect the Model:Cycles over USB, turn it on, then click Refresh.",
    midi_pick_dev: "The Model:Cycles USB port is selected.",
    midi_no_dev: "The Model:Cycles doesn't appear over USB. Connect it, turn it on and click Refresh.",
    warn_not_dev: "This doesn't look like the Model:Cycles: pick the port named “Model:Cycles”.",
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
    miss_ready: "Open CONFIG › UPGRADE on the Model:Cycles (step 3), then flash.",
    watch: "Watch the Model:Cycles screen: it should show that it is receiving. If nothing happens within a few seconds, press <b>Stop</b>.",
    keep_visible: "Keep this tab in the foreground: browsers slow down background tabs.",
    remaining: "{t} left",
    done_title: "Transfer complete.",
    done_body: "The Model:Cycles now writes the firmware (<code>UPDATING FLASH</code>) and restarts by itself. <b>Don't turn it off</b> until it has restarted.",
    done_6ch: "With the 6-channel mod, your computer should then show a Model:Cycles audio device with <b>6 input channels</b>.",
    stopped: "Stopped. Turn the Model:Cycles off and on, open CONFIG › UPGRADE again, then flash again.",
    send_error: "The transfer failed: {err}. Turn the Model:Cycles off and on, open CONFIG › UPGRADE again and retry.",
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
    mods_note: "Tous ces mods ont été testés sur un vrai Model:Cycles, sauf les options marquées « Nouveau ». Coche-en plusieurs pour les combiner.",
    restore_text: "Envoie ton fichier d'OS officiel <b>sans le modifier</b>, pour revenir au firmware d'origine. C'est aussi une bonne répétition avant un mod : elle vérifie ton câble et ton installation sans rien changer.",
    tab_samples: "OS Samples",
    samples_title: "Transforme ton Model:Cycles en Model:Samples",
    samples_text: "Charge et joue tes propres samples, gérés avec Elektron Transfer. La page place l'OS officiel du Model:Samples dans le firmware de ton Model:Cycles : le menu de démarrage, l'updater et la signature du Model:Cycles restent en place.",
    samples_w1: "Sauvegarde d'abord tes projets avec Transfer : l'OS du Model:Samples utilise le même stockage.",
    samples_w2: `Le retour à l'OS du Model:Cycles passe par le menu de démarrage, qui n'écoute que le MIDI IN : il faut une interface MIDI (<a href="${FLASH_GUIDE}" target="_blank" rel="noopener">guide complet</a>).`,
    samples_w3: "Depuis l'OS Samples, ne lance jamais CONFIG › UPGRADE avec un fichier Model:Samples : il remplacerait aussi le menu de démarrage de ton Model:Cycles.",
    samples_ack: "J'ai une interface MIDI pour le retour (vers le MIDI IN du Model:Cycles).",
    restore_from_samples: `Tu reviens de l'OS Samples ? Le retour passe par le menu de démarrage et le MIDI IN : voir le <a href="${FLASH_GUIDE}" target="_blank" rel="noopener">guide complet</a>.`,
    tested: "Testé",
    experimental: "Expérimental",
    credit_by: "par {who}",
    credit_based: "d'après {repo} de {who}",
    s2: "Dépose ton fichier d'OS officiel",
    drop_title: "Dépose model-cycles_OS1.13.syx ici",
    drop_sub: "ou clique pour le choisir",
    drop_again: "Vérifié. Clique ou dépose pour changer de fichier.",
    get_os: `Tu ne l'as pas ? <a href="${ELEKTRON_DL}" target="_blank" rel="noopener">Télécharge l'OS Model:Cycles 1.13 sur elektron.se</a>, puis dézippe-le.`,
    s2_samples: "Dépose les deux fichiers d'OS officiels",
    drop2_title: "Dépose model-samples_OS1.13.syx ici",
    drop2_sub: "l'OS officiel du Model:Samples — ou clique pour le choisir",
    get_os_samples: `Tu ne l'as pas ? <a href="${ELEKTRON_SMP_DL}" target="_blank" rel="noopener">Télécharge l'OS Model:Samples 1.13 sur elektron.se</a>, puis dézippe-le.`,
    drop3_title: "Dépose Syntakt_OS1.41.syx ici",
    drop3_sub: "l'OS officiel du Syntakt, pour le moteur SD VINTAGE — ou clique pour le choisir",
    get_os_syntakt: `Tu ne l'as pas ? <a href="${ELEKTRON_ST_DL}" target="_blank" rel="noopener">Télécharge l'OS Syntakt 1.41 sur elektron.se</a>, puis dézippe-le. La page y lit le moteur SD VINTAGE, sur ton ordinateur : pas besoin d'avoir un Syntakt.`,
    s3: "Branche ton Model:Cycles en USB",
    hu1: "Relie le Model:Cycles à l'ordinateur avec un câble USB et allume-le normalement.",
    hu2: "Sur le Model:Cycles, ouvre <b>CONFIG › UPGRADE</b> et confirme avec <b>YES</b>. Il attend alors le firmware.",
    hu3: "Autorise le MIDI ci-dessous : le port nommé « Model:Cycles » est choisi automatiquement.",
    allow: "Autoriser le MIDI",
    refresh: "Rafraîchir",
    s4: "Flasher",
    ack: "J'ai sauvegardé mes projets (Elektron Transfer) et je comprends que je flashe à mes risques.",
    flash_btn: "Flasher le Model:Cycles",
    flashing: "Flash en cours…",
    stop: "Arrêter",
    trouble: "Un problème ?",
    t1q: "Rien ne se passe sur l'écran du Model:Cycles",
    t1a: "Vérifie que <b>CONFIG › UPGRADE</b> est ouvert et en attente, et que le port nommé « Model:Cycles » est choisi à l'étape 3. Ferme Elektron Transfer, Overbridge et ton logiciel de musique (sous Windows, ils bloquent le port), puis réessaie.",
    t2q: "Le transfert s'arrête, ou le Model:Cycles affiche une erreur",
    t2a: "Éteins et rallume le Model:Cycles, rouvre <b>CONFIG › UPGRADE</b>, règle <b>Options avancées › Marge de vitesse</b> sur 2.0 et relance.",
    t3q: "Aucun port MIDI dans la liste",
    t3a: "Branche le Model:Cycles avec un câble USB qui transporte les données (certains câbles ne font que charger), allume-le, puis clique <b>Rafraîchir</b>. Certains systèmes n'affichent un nouvel appareil qu'après un redémarrage du navigateur.",
    t4q: "La mise à jour par USB est refusée, ou le Model:Cycles ne démarre plus",
    t4a: `La récupération passe par le menu de démarrage, qui n'écoute que le MIDI IN : suis le <a href="${FLASH_GUIDE}" target="_blank" rel="noopener">guide complet</a> (il faut une interface MIDI). C'est aussi le cas si tu avais installé l'ancienne « version de référence » du 6 canaux, qui désactive la mise à jour par USB.`,
    advanced: "Options avancées",
    pace: "Marge de vitesse d'envoi",
    pace_hint: "1.4 par défaut. Monte à 2.0 si le transfert se bloque.",
    download: "Télécharger le .syx préparé",
    download_hint: `Pour flasher plutôt avec <code>flash.sh</code> / <code>flash.bat</code> (<a href="${FLASH_GUIDE}" target="_blank" rel="noopener">guide</a>).`,
    credits: "Crédits",
    credits_intro: "Ce flasher s'appuie sur ces projets open source (licence MIT), dont aucun ne contient de firmware :",
    privacy: "Ton fichier firmware ne quitte jamais ton ordinateur. Rien n'est envoyé en ligne, aucun firmware n'est fourni.",
    links: `<a href="${REPO}" target="_blank" rel="noopener">Code source</a> · <a href="${FLASH_GUIDE}" target="_blank" rel="noopener">Guide complet</a> · Projet non affilié à Elektron.`,
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
    smp_ok: "OS officiel Model:Samples 1.13 reconnu.",
    smp_bad: "Ce n'est pas le fichier officiel de l'OS Model:Samples 1.13 : {err}",
    smp_not_official: "son SHA-256 diffère du fichier officiel",
    st_ok: "OS officiel Syntakt 1.41 reconnu.",
    st_bad: "Ce n'est pas le fichier officiel de l'OS Syntakt 1.41 : {err}",
    needs_syntakt: "Le moteur SD VINTAGE se lit dans le fichier officiel de l'OS Syntakt : dépose-le ci-dessous.",
    miss_syntakt: "Dépose le fichier officiel de l'OS Syntakt (étape 2).",
    done_sdv: "Choisis ensuite la machine SNARE sur une piste et joue-la : c'est le SD VINTAGE du Syntakt. PITCH, COLOR, SHAPE, SWEEP et CONTOUR agissent comme ses TUNE, INHM, FCMP, SWEP et MENV.",
    done_sdv7: "Appuie ensuite sur MACHINES sur une piste et choisis <b>SDVtg</b>, la 7ᵉ machine : c'est le SD VINTAGE du Syntakt. Ses potards affichent les noms du Syntakt (Inharmonicity, Freq Complex, Pitch Sweep, Mod Envelope). SNARE ne change pas. Si quelque chose cloche, reflashe le firmware officiel depuis CONFIG › UPGRADE.",
    warn_samples_port: "Ce port est un Model:Samples (un Model:Cycles sous l'OS Samples) : il refuse un firmware Model:Cycles par USB. Le retour passe par le menu de démarrage et le MIDI IN (voir le guide complet).",
    samples_needs_cycles: "Pour l'OS Samples, le premier fichier doit être le <code>model-cycles_OS1.13.syx</code> officiel : il fournit le menu de démarrage, l'updater et la signature qui restent sur ton Model:Cycles.",
    samples_ready: "Firmware prêt : l'OS Model:Samples pour ton Model:Cycles.",
    mods_list_samples: "OS Model:Samples (pour Model:Cycles)",
    miss_samples_cycles: "Le premier fichier doit être l'OS officiel du Model:Cycles (étape 2).",
    miss_samples_file: "Dépose le fichier officiel de l'OS Model:Samples (étape 2).",
    miss_samples_ack: "Confirme que tu as une interface MIDI pour le retour (étape 1).",
    done_samples: "Il redémarre en <b>Model:Samples</b> : Elektron Transfer et ton ordinateur voient un « Model:Samples ». Charge tes samples avec Transfer.",
    pick_one: "Coche au moins un mod, ou passe sur « Firmware officiel ».",
    midi_asking: "Demande d'accès MIDI…",
    midi_wait: "En attente de ton autorisation : Chrome affiche une demande près de la barre d'adresse. Clique « Autoriser ». Si tu l'as bloquée, clique l'icône à gauche de l'adresse et autorise le MIDI.",
    midi_denied: "Accès MIDI refusé. Clique l'icône à gauche de l'adresse, autorise le MIDI, recharge la page et réessaie.",
    midi_none: "Aucune sortie MIDI. Branche le Model:Cycles en USB, allume-le, puis clique Rafraîchir.",
    midi_pick_dev: "Le port USB du Model:Cycles est sélectionné.",
    midi_no_dev: "Le Model:Cycles n'apparaît pas en USB. Branche-le, allume-le et clique Rafraîchir.",
    warn_not_dev: "Ce port ne semble pas être le Model:Cycles : choisis le port nommé « Model:Cycles ».",
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
    miss_ready: "Ouvre CONFIG › UPGRADE sur le Model:Cycles (étape 3), puis flashe.",
    watch: "Regarde l'écran du Model:Cycles : il doit indiquer qu'il reçoit. S'il ne se passe rien en quelques secondes, clique <b>Arrêter</b>.",
    keep_visible: "Garde cet onglet au premier plan : les navigateurs ralentissent les onglets en arrière-plan.",
    remaining: "encore {t}",
    done_title: "Transfert terminé.",
    done_body: "Le Model:Cycles écrit maintenant le firmware (<code>UPDATING FLASH</code>) puis redémarre tout seul. <b>Ne l'éteins pas</b> avant qu'il ait redémarré.",
    done_6ch: "Avec le mod 6 canaux, ton ordinateur doit ensuite voir un périphérique audio Model:Cycles avec <b>6 canaux d'entrée</b>.",
    stopped: "Arrêté. Éteins et rallume le Model:Cycles, rouvre CONFIG › UPGRADE, puis relance.",
    send_error: "Le transfert a échoué : {err}. Éteins et rallume le Model:Cycles, rouvre CONFIG › UPGRADE et réessaie.",
    port_gone: "La sortie MIDI a disparu. Vérifie le branchement et choisis-la de nouveau.",
    leave: "Un flash est en cours. Quitter maintenant l'interromprait.",
    log_start: "Envoi de {n} paquets vers « {port} », marge {pace}.",
  },
};

// Feature texts shown in the UI (fallback: labels from tweaks.js).
const FEAT = {
  en: {
    usb6: { label: "6-channel USB audio",
      desc: "Each track gets its own USB channel (48 kHz / 32-bit): record the 6 tracks separately in your DAW. The stereo mix is no longer sent over USB. OS updates over USB keep working." },
    "latching-mute": { label: "Latching mute mode",
      desc: "Hold TRK and tap FUNC: mute mode stays on, so you mute tracks without holding FUNC. A short tap on FUNC leaves it." },
    "trig-preview": { label: "Trig preview",
      desc: "With the sequencer stopped, hold a step and press PAGE: the step plays with its own note, length and p-locks." },
    "browser-scroll": { label: "Scroll long names",
      desc: "In the sound browser, a name too long for the screen scrolls so you can read it." },
    sdvintage: { label: "SD VINTAGE, the real Syntakt engine",
      desc: "The Syntakt's own SD VINTAGE engine, copied from your Syntakt OS 1.41 file (step 2): in place of SNARE, or as a 7th machine “SDVtg” next to it, with the Syntakt's knob names and defaults. In the emulator it is identical to the Syntakt, sample for sample." },
    "sdvintage-exact": { label: "In place of SNARE", note: "Tested on a real Model:Cycles." },
    "sdvintage-7th": { label: "As a 7th machine, SDVtg", note: "SNARE stays. New: not tested on a Model:Cycles yet." },
  },
  fr: {
    usb6: { label: "Audio USB 6 canaux",
      desc: "Chaque piste a son propre canal USB (48 kHz / 32 bits) : enregistre les 6 pistes séparément dans ton logiciel. Le mix stéréo n'est plus envoyé en USB. La mise à jour de l'OS par USB continue de marcher." },
    "latching-mute": { label: "Mode mute verrouillé",
      desc: "Maintiens TRK et tape FUNC : le mode mute reste actif, tu mutes les pistes sans tenir FUNC. Un appui court sur FUNC en sort." },
    "trig-preview": { label: "Écoute d'un pas",
      desc: "Séquenceur à l'arrêt, maintiens un pas et appuie sur PAGE : le pas joue avec sa note, sa longueur et ses p-locks." },
    "browser-scroll": { label: "Défilement des noms longs",
      desc: "Dans le navigateur de sons, un nom trop long pour l'écran défile pour que tu puisses le lire." },
    sdvintage: { label: "SD VINTAGE, le vrai moteur du Syntakt",
      desc: "Le propre moteur SD VINTAGE du Syntakt, copié depuis ton fichier d'OS Syntakt 1.41 (étape 2) : à la place de SNARE, ou en 7ᵉ machine « SDVtg » à côté, avec les noms et défauts des potards du Syntakt. En émulation, identique au Syntakt échantillon par échantillon." },
    "sdvintage-exact": { label: "À la place de SNARE", note: "Testé sur un vrai Model:Cycles." },
    "sdvintage-7th": { label: "En 7ᵉ machine, SDVtg", note: "SNARE reste. Nouveau : pas encore testé sur un Model:Cycles." },
  },
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const st = {
  lang: "en",
  mode: "mods",            // "mods" | "restore" | "samples"
  samplesOs: null,         // official Model:Samples OS { raw, name, sha } ("samples" mode)
  samplesError: null,
  syntakt: null,           // official Syntakt OS { raw, name, sha } (SD VINTAGE engine source)
  syntaktError: null,
  os: null,                // { raw, name, info, sha, stock }
  osError: null,
  fw: null,                // { raw, name, kind: "built"|"stock"|"custom", mods:[labels], ref:bool, sixch:bool }
  fwError: null,
  building: false,
  buildKey: null,
  cache: {},               // build results per selection key, for the current OS file
  midi: null,
  midiState: "idle",       // idle | asking | ready | denied | unsupported
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
  // a loaded file keeps its name in its drop zone
  if (st.os) { $("drop-title").textContent = st.os.name; $("drop-sub").textContent = t("drop_again"); }
  if (st.samplesOs) { $("drop2-title").textContent = st.samplesOs.name; $("drop2-sub").textContent = t("drop_again"); }
  if (st.syntakt) { $("drop3-title").textContent = st.syntakt.name; $("drop3-sub").textContent = t("drop_again"); }
  document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === st.lang)));
  document.title = t("title");
  renderFeatures();
  renderCredits();
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
    const tested = f.status === "tested";
    ttl.innerHTML = `<span>${esc(featText(f.id, "label", f.label))}</span>` +
      `<span class="tag${tested ? " ok" : ""}">${esc(t(tested ? "tested" : "experimental"))}</span>`;
    const desc = document.createElement("div");
    desc.className = "desc";
    desc.textContent = featText(f.id, "desc", f.desc);
    card.append(cb, ttl, desc);
    if (f.credit) {
      const cr = document.createElement("div");
      cr.className = "credit";
      cr.innerHTML = creditHtml(f.credit);
      card.appendChild(cr);
    }

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

// "by drumkilla" / "based on ms-multi-output by scottmetoyer", linked to the repository.
// A link inside the card's <label> doesn't toggle the checkbox (interactive content).
function creditHtml(c) {
  const url = "https://github.com/" + c.repo;
  const link = (txt) => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(txt)}</a>`;
  return c.kind === "based"
    ? t("credit_based", { repo: link(c.repo.split("/")[1]), who: esc(c.who) })
    : t("credit_by", { who: link(c.who) });
}

function renderCredits() {
  const box = $("credits-list");
  if (!box) return;
  box.innerHTML = CREDITS.map((c) =>
    `<li><a href="https://github.com/${esc(c.repo)}" target="_blank" rel="noopener">${esc(c.repo)}</a> — ` +
    `${esc(c[st.lang] || c.en)}</li>`).join("");
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

// A mod whose engine is copied from the Syntakt OS (tweak "append", notes/17).
function needsSyntakt() {
  return st.mode === "mods" && chosenTweaks().some((x) => x.append && x.append.syntakt);
}

function setMode(mode) {
  st.mode = mode;
  for (const m of ["mods", "restore", "samples"]) {
    $("tab-" + m).setAttribute("aria-selected", String(mode === m));
    $("panel-" + m).hidden = mode !== m;
  }
  $("drop2-wrap").hidden = mode !== "samples";
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

// "Samples OS" tab: the second file, the official Model:Samples OS (recognised by its SHA-256).
function readSamplesFile(file) {
  const r = new FileReader();
  r.onload = () => loadSamples(new Uint8Array(r.result), file.name);
  r.onerror = () => { st.samplesOs = null; st.samplesError = String(r.error); update(); };
  r.readAsArrayBuffer(file);
}

function loadSamples(raw, name) {
  st.finished = null;
  try {
    const info = window.MCFlasher.verify(raw);
    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(raw));
    if (sha !== window.MC_TWEAKS.samples.syx_sha256) throw new Error(t("smp_not_official") + ` (${info.name})`);
    st.samplesOs = { raw, name, sha };
    st.samplesError = null;
    log(`${name}: official Model:Samples OS 1.13, ${info.count} packets, checksums OK.`, "is-ok");
  } catch (e) {
    st.samplesOs = null;
    st.samplesError = e.message;
    log(`${name}: refused — ${e.message}`, "is-bad");
  }
  $("drop2").classList.toggle("loaded", !!st.samplesOs);
  $("drop2-title").textContent = st.samplesOs ? name : t("drop2_title");
  $("drop2-sub").textContent = st.samplesOs ? t("drop_again") : t("drop2_sub");
  update();
}

// Mods tab, SD VINTAGE: the official Syntakt OS (recognised by its SHA-256). Only read here, in the browser.
function readSyntaktFile(file) {
  const r = new FileReader();
  r.onload = () => loadSyntakt(new Uint8Array(r.result), file.name);
  r.onerror = () => { st.syntakt = null; st.syntaktError = String(r.error); update(); };
  r.readAsArrayBuffer(file);
}

function loadSyntakt(raw, name) {
  st.finished = null;
  try {
    const tk = window.MC_TWEAKS.tweaks.find((x) => x.append && x.append.syntakt);
    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(raw));
    if (!tk || sha !== tk.append.syntakt.syx_sha256) throw new Error(t("smp_not_official"));
    st.syntakt = { raw, name, sha };
    st.syntaktError = null;
    log(`${name}: official Syntakt OS 1.41.`, "is-ok");
  } catch (e) {
    st.syntakt = null;
    st.syntaktError = e.message;
    log(`${name}: refused — ${e.message}`, "is-bad");
  }
  $("drop3").classList.toggle("loaded", !!st.syntakt);
  $("drop3-title").textContent = st.syntakt ? name : t("drop3_title");
  $("drop3-sub").textContent = st.syntakt ? t("drop_again") : t("drop3_sub");
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
  st.buildKey = null;
  if (!os) { st.fw = null; st.fwError = null; return; }
  if (st.mode === "samples") { prepareSamples(os); return; }
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
  if (!tweaks.length) { st.fw = null; st.fwError = "pick_one"; return; }
  const sdv = needsSyntakt();
  if (sdv && !st.syntakt) { st.fw = null; st.fwError = "needs_syntakt"; return; }
  const key = tweaks.map((x) => x.id).join("+");
  const labels = chosenLabels();
  const syntakt = sdv ? st.syntakt.raw : null;     // only the official file is accepted: same bytes for every key
  buildCached(key, (raw) => {
    const opts = {};
    if (REF_MAINOS[key]) opts.expectMainOsSha = REF_MAINOS[key];
    if (syntakt) opts.syntakt = syntakt;
    const r = window.MCBuilder.build(raw, window.MC_TWEAKS.device, tweaks, opts);
    log(`Built ${key}: MAIN OS ${r.mainOsSha.slice(0, 12)}…, ${r.patchedBytes} bytes patched, ${r.raw.length} bytes.`, "is-ok");
    return { raw: r.raw, name: `model-cycles_OS1.13_${key}.syx`, kind: "built", mods: labels, sha: r.mainOsSha,
      ref: !!REF_MAINOS[key], sixch: tweaks.some((x) => x.id.startsWith("6ch")),
      sdv: sdv && (tweaks.find((x) => x.append) || {}).id };
  });
}

// Model:Samples OS in the Model:Cycles container (MCBuilder.crossflash = tools/crossflash.py).
function prepareSamples(os) {
  if (!os.stock) { st.fw = null; st.fwError = "samples_needs_cycles"; return; }
  const smp = st.samplesOs;
  if (!smp) { st.fw = null; st.fwError = null; return; }
  buildCached("samples-os:" + smp.sha, (raw) => {
    const r = window.MCBuilder.crossflash(raw, smp.raw);
    const sha = window.MCBuilder.hex(window.MCBuilder.sha256(r.raw));
    if (sha !== REF_SAMPLES_ON_CYCLES) throw new Error(`result ${sha.slice(0, 16)}… is not the reference build`);
    log(`Built the Model:Samples OS for Model:Cycles: MAIN OS ${r.mainOsSha.slice(0, 12)}…, ${r.raw.length} bytes.`, "is-ok");
    return { raw: r.raw, name: "model-samples_OS1.13_for-model-cycles.syx", kind: "samples", mods: [], ref: true, sixch: false };
  });
}

// Builds once per key and OS file (st.cache is reset when the Model:Cycles file changes), after
// letting the browser paint "Preparing…". The result is applied only if it is still the current choice.
function buildCached(key, make) {
  st.buildKey = key;
  const cached = st.cache[key];
  if (cached) { st.fw = cached.fw || null; st.fwError = cached.error || null; return; }
  st.fw = null; st.fwError = null; st.building = true;
  const osRef = st.os;
  setTimeout(() => {
    if (st.os !== osRef || st.cache[key]) return;
    let entry;
    try {
      entry = { fw: make(osRef.raw) };
    } catch (e) {
      entry = { error: e.message };
      log(`Build ${key} refused: ${e.message}`, "is-bad");
    }
    if (st.os !== osRef) return;              // another file was loaded meanwhile
    st.cache[key] = entry;
    if (st.buildKey === key) {                 // still the current choice
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
    const want = outs.find((o) => isDevicePort(o.name));
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
    else if (port && !isDevicePort(port.name)) rows.push(["is-warn", esc(t("warn_not_dev"))]);
    else if (port && /samples/i.test(port.name)) rows.push(["is-warn", esc(t("warn_samples_port"))]);
    else if (port) rows.push(["is-ok", esc(t("midi_pick_dev"))]);
    else if (!outs.some((o) => isDevicePort(o.name))) rows.push(["is-warn", esc(t("midi_no_dev"))]);
  }
  setStatus("midi-status", rows);
}

// ---------------------------------------------------------------------------
// Rendering (status, step badges, flash button)
// ---------------------------------------------------------------------------
function missingReason() {
  if (!st.os) return st.osError ? "miss_fw" : "miss_file";
  if (st.mode === "samples") {
    if (st.fwError === "samples_needs_cycles") return "miss_samples_cycles";
    if (!st.samplesOs) return "miss_samples_file";
    if (!$("samples-ack").checked) return "miss_samples_ack";
  }
  if (st.fwError === "pick_one") return "miss_mod";
  if (needsSyntakt() && !st.syntakt) return "miss_syntakt";
  if (st.building) return "miss_build";
  if (!st.fw) return "miss_fw";
  if (st.midiState !== "ready") return "miss_midi";
  if (!currentPort()) return "miss_port";
  if (!$("ack").checked) return "miss_ack";
  return null;
}

function render() {
  // step 2 status
  $("h2s").textContent = t(st.mode === "samples" ? "s2_samples" : "s2");
  if (st.os && st.mode === "samples" && !st.os.stock) setStatus("file-status", [["is-bad", t("samples_needs_cycles")]]);
  else if (st.os) {
    const rows = [];
    if (st.os.stock) rows.push(["is-ok", esc(t("os_ok"))]);
    else {
      rows.push(["is-warn", t("os_custom", { name: esc(st.os.name), device: esc(st.os.info.name) })]);
      if (st.mode === "mods" && chosenTweaks().length) rows.push(["", esc(t("os_custom_mods"))]);
    }
    if (st.fwError === "restore_needs") rows.push(["is-bad", t("os_restore_needs")]);
    else if (st.fwError === "pick_one") rows.push(["", esc(t("pick_one"))]);
    else if (st.fwError === "needs_syntakt") rows.push(["", esc(t("needs_syntakt"))]);
    else if (st.building) rows.push(["is-busy", esc(t("building"))]);
    else if (st.fwError) rows.push(["is-bad", esc(t("build_failed", { err: st.fwError }))]);
    else if (st.fw && st.fw.kind === "built")
      rows.push(["is-ok", esc(t("built", { mods: st.fw.mods.join(" + ") })) + (st.fw.ref ? " " + esc(t("built_ref")) : "") +
        ` <span class="hash">MAIN OS ${esc(st.fw.sha.slice(0, 8))}</span>`]);
    else if (st.fw && st.fw.kind === "stock") rows.push(["is-ok", esc(t("stock_ready"))]);
    else if (st.fw && st.fw.kind === "samples") rows.push(["is-ok", esc(t("samples_ready")) + " " + esc(t("built_ref"))]);
    setStatus("file-status", rows);
  }
  setStatus("file2-status", st.samplesOs ? [["is-ok", esc(t("smp_ok"))]]
    : st.samplesError ? [["is-bad", esc(t("smp_bad", { err: st.samplesError }))]] : []);
  const sdv = needsSyntakt();
  $("drop3-wrap").hidden = !sdv;
  setStatus("file3-status", st.syntakt ? [["is-ok", esc(t("st_ok"))]]
    : st.syntaktError ? [["is-bad", esc(t("st_bad", { err: st.syntaktError }))]] : []);

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
  const choseOk = st.mode === "restore" || (st.mode === "samples" ? $("samples-ack").checked : chosenTweaks().length > 0);
  $("step-choose").classList.toggle("done", choseOk);
  $("step-file").classList.toggle("done", !!st.fw && !st.building);
  $("step-connect").classList.toggle("done", st.midiState === "ready" && !!currentPort());
  $("step-flash").classList.toggle("done", st.finished === "ok");

  // summary
  const sum = $("summary");
  if (st.fw) {
    const what = st.fw.kind === "built" ? st.fw.mods.join(" + ")
      : st.fw.kind === "stock" ? t("mods_list_restore")
      : st.fw.kind === "samples" ? t("mods_list_samples") : t("mods_list_custom", { name: st.fw.name });
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
  $("watch").innerHTML = t("watch") + "<br>" + esc(t("keep_visible"));
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
      (fw.sixch ? `<p>${t("done_6ch")}</p>` : "") +
      (fw.sdv ? `<p>${t(fw.sdv === "sdvintage-7th" ? "done_sdv7" : "done_sdv")}</p>` : "") +
      (fw.kind === "samples" ? `<p>${t("done_samples")}</p>` : "");
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
  $("tab-samples").addEventListener("click", () => setMode("samples"));
  $("samples-ack").addEventListener("change", render);

  const drop = $("drop"), file = $("file");
  file.addEventListener("change", (e) => { if (e.target.files[0]) readFile(e.target.files[0]); e.target.value = ""; });
  drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); file.click(); } });
  ["dragover", "dragenter"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) readFile(e.dataTransfer.files[0]); });

  const drop2 = $("drop2"), file2 = $("file2");
  file2.addEventListener("change", (e) => { if (e.target.files[0]) readSamplesFile(e.target.files[0]); e.target.value = ""; });
  drop2.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); file2.click(); } });
  ["dragover", "dragenter"].forEach((ev) => drop2.addEventListener(ev, (e) => { e.preventDefault(); drop2.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => drop2.addEventListener(ev, (e) => { e.preventDefault(); drop2.classList.remove("over"); }));
  drop2.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) readSamplesFile(e.dataTransfer.files[0]); });

  const drop3 = $("drop3"), file3 = $("file3");
  file3.addEventListener("change", (e) => { if (e.target.files[0]) readSyntaktFile(e.target.files[0]); e.target.value = ""; });
  drop3.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); file3.click(); } });
  ["dragover", "dragenter"].forEach((ev) => drop3.addEventListener(ev, (e) => { e.preventDefault(); drop3.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => drop3.addEventListener(ev, (e) => { e.preventDefault(); drop3.classList.remove("over"); }));
  drop3.addEventListener("drop", (e) => { if (e.dataTransfer.files[0]) readSyntaktFile(e.dataTransfer.files[0]); });

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
window.MCFlasherApp = { state: st, REF_MAINOS, REF_SAMPLES_ON_CYCLES, loadOs, loadSamples, loadSyntakt, setMode, applyLang, render };

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
})();
