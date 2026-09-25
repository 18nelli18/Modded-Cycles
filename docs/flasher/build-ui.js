/* Panneau « Construire le .syx dans le navigateur ».
 * Utilise docs/flasher/builder.js (window.MCBuilder) et tweaks.js (window.MC_TWEAKS),
 * puis charge le resultat dans le flasher (window.loadFlasherBytes de flasher.js). */
"use strict";
(function () {
  const $ = (id) => document.getElementById(id);
  // MAIN OS patche de reference (cf. BUILD.md) : 6ch-multiout = resultat connu-bon de
  // ms-multi-output ; les autres = builds de build.py sur l'OS 1.13 officiel. Garde-fou :
  // la construction est refusee si l'octet ne tombe pas juste.
  const REF_MAINOS = {
    "6ch-multiout": "65e24b50dd457444e87daea79dd41b82f61098cb8ae5cd27cbe0d91742f29555",
    "6ch-usbup": "db3d26cc3a48d1155933240c7d1d5476c8f56d2b6a54be1ffe7f5327e54c0521",
    "sdvintage-snare": "80b7b2bd003f2695488d629c0fab56c84e10213898c9820c321efa711f6957c7",
    "6ch-multiout+sdvintage-snare": "4494fb764c7643b2a9acea8b4fa2cafe10ee7d9644e56d08e333ee019f4cbe72",
    "6ch-usbup+sdvintage-snare": "38754937b06e3815ee1da9c93137d46283b612e1881772f4d034fb9f998b3335",
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

  // tweaks choisis : la variante « Sortie USB » (au plus une) + les machines cochees
  function chosen() {
    const tw = window.MC_TWEAKS;
    if (!tw) return [];
    const ids = [];
    if ($("variant").value) ids.push($("variant").value);
    for (const cb of document.querySelectorAll("#extras input[type=checkbox]"))
      if (cb.checked) ids.push(cb.value);
    return ids.map((id) => tw.tweaks.find((t) => t.id === id));
  }

  function ready() {
    $("build").disabled = !(st.os && chosen().length && window.MCBuilder);
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
    const tweaks = chosen();
    const id = tweaks.map((t) => t.id).join("+");
    const opts = { force: $("force-cave").checked };
    if (REF_MAINOS[id]) opts.expectMainOsSha = REF_MAINOS[id];
    $("build-info").className = "msg tiny";
    $("build-info").textContent = "Construction…";
    // laisse le navigateur peindre avant le calcul (aPLib ~1-2 s)
    setTimeout(() => {
      try {
        const r = window.MCBuilder.build(st.os, tw.device, tweaks, opts);
        st.built = r.raw;
        const name = `model-cycles_OS1.13_${id}.syx`;
        // rapport caves
        let cave = "";
        if (r.caves.zones.length) {
          const B = window.MCBuilder.BASE;
          const zs = r.caves.zones.map(([lo, hi]) => `0x${(lo + B).toString(16)}..0x${(hi + B - 1).toString(16)}`);
          cave = ` Caves ${zs.join(", ")} (${r.caves.sure.length} référence(s) sûre(s), ` +
            `${r.caves.doubt.length} à vérifier, ${r.caves.gone.length} redirigée(s) par le tweak).`;
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
    const extras = $("extras");
    if (tw && tw.tweaks) {
      for (const t of tw.tweaks) {
        if (t.web === "option") {
          const lab = document.createElement("label");
          lab.className = "ack tiny";
          lab.title = (t.description || []).join("\n");
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.value = t.id;
          cb.addEventListener("change", ready);
          const sp = document.createElement("span");
          sp.textContent = `${t.id} — ${t.name}`;
          lab.append(cb, sp);
          extras.appendChild(lab);
        } else {
          const o = document.createElement("option");
          o.value = t.id;
          o.textContent = `${t.id} — ${t.name}`;
          sel.appendChild(o);
        }
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
