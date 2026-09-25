/* Panneau « Construire le .syx dans le navigateur ».
 * Utilise docs/flasher/builder.js (window.MCBuilder) et tweaks.js (window.MC_TWEAKS),
 * puis charge le resultat dans le flasher (window.loadFlasherBytes de flasher.js). */
"use strict";
(function () {
  const $ = (id) => document.getElementById(id);
  // MAIN OS patche connu-bon (reproductibilite verifiee, cf. BUILD.md). Sert de
  // garde-fou : la construction est refusee si l'octet ne tombe pas juste.
  const REF_MAINOS = {
    "6ch-multiout": "65e24b50dd457444e87daea79dd41b82f61098cb8ae5cd27cbe0d91742f29555",
  };
  const st = { os: null, built: null, url: null };

  function log(msg, cls) {
    const el = $("log");
    if (!el) return;
    const d = document.createElement("div");
    if (cls) d.className = cls;
    d.textContent = msg;
    el.appendChild(d);
    el.scrollTop = el.scrollHeight;
  }

  function ready() {
    $("build").disabled = !(st.os && $("variant").value && window.MCBuilder);
  }

  function loadOs(file) {
    const r = new FileReader();
    r.onload = () => {
      st.os = new Uint8Array(r.result);
      $("os-info").textContent = `${file.name} — ${st.os.length.toLocaleString("fr-FR")} o, prêt à construire.`;
      $("os-info").className = "msg tiny ok";
      ready();
    };
    r.readAsArrayBuffer(file);
  }

  function build() {
    const tw = window.MC_TWEAKS;
    const id = $("variant").value;
    const tweak = tw.tweaks.find((t) => t.id === id);
    const opts = { force: $("force-cave").checked };
    if (REF_MAINOS[id]) opts.expectMainOsSha = REF_MAINOS[id];
    $("build-info").className = "msg tiny";
    $("build-info").textContent = "Construction…";
    // laisse le navigateur peindre avant le calcul (aPLib ~1-2 s)
    setTimeout(() => {
      try {
        const r = window.MCBuilder.build(st.os, tw.device, [tweak], opts);
        st.built = r.raw;
        const name = `model-cycles_OS1.13_${id}.syx`;
        // rapport caves
        let cave = "";
        if (r.caves.zones.length) {
          const [lo, hi] = r.caves.zones[0];
          cave = ` Cave 0x${(lo + window.MCBuilder.BASE).toString(16)}..0x${(hi + window.MCBuilder.BASE - 1).toString(16)} ` +
            `(${r.caves.sure.length} référence(s) sûre(s), ${r.caves.doubt.length} à vérifier).`;
        }
        const okref = REF_MAINOS[id] ? " Conforme au MAIN OS de référence." : " (variante sans hash de référence.)";
        $("build-info").innerHTML =
          `Construit : <b>${name}</b> — MAIN OS ${r.mainOsSha.slice(0, 16)}…, ${r.patchedBytes} octets patchés.${okref}${cave}`;
        $("build-info").className = "msg tiny ok";
        log(`Construction OK : ${id}, MAIN OS ${r.mainOsSha.slice(0, 12)}…, ${r.raw.length} o.`, "ok");

        // lien de telechargement
        if (st.url) URL.revokeObjectURL(st.url);
        st.url = URL.createObjectURL(new Blob([r.raw], { type: "application/octet-stream" }));
        const dl = $("download");
        dl.href = st.url;
        dl.download = name;
        dl.style.display = "inline-block";

        // charge directement dans le flasher (verifie de nouveau tout, checksums compris)
        if (window.loadFlasherBytes) window.loadFlasherBytes(r.raw, name);
      } catch (e) {
        st.built = null;
        $("download").style.display = "none";
        $("build-info").textContent = "Construction refusée : " + e.message;
        $("build-info").className = "msg tiny bad";
        log("Construction refusée : " + e.message, "bad");
      }
    }, 30);
  }

  window.addEventListener("DOMContentLoaded", () => {
    const tw = window.MC_TWEAKS;
    const sel = $("variant");
    if (tw && tw.tweaks) {
      for (const t of tw.tweaks) {
        const o = document.createElement("option");
        o.value = t.id;
        o.textContent = `${t.id} — ${t.name}`;
        sel.appendChild(o);
      }
    }
    sel.addEventListener("change", ready);
    $("build").addEventListener("click", build);

    const drop = $("os-drop");
    const file = $("os-file");
    drop.addEventListener("click", () => file.click());
    file.addEventListener("change", (e) => e.target.files[0] && loadOs(e.target.files[0]));
    ["dragover", "dragenter"].forEach((ev) =>
      drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
    ["dragleave", "drop"].forEach((ev) =>
      drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
    drop.addEventListener("drop", (e) => e.dataTransfer.files[0] && loadOs(e.dataTransfer.files[0]));
    ready();
  });
})();
