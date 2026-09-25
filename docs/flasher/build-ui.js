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

  // tweaks choisis : pour chaque fonctionnalite cochee, la variante selectionnee (ordre stable
  // = ordre des fonctionnalites, pour que la cle REF_MAINOS tombe juste)
  function chosen() {
    const tw = window.MC_TWEAKS;
    if (!tw || !tw.features) return [];
    const out = [];
    for (const f of tw.features) {
      const cb = $("feat-" + f.id);
      if (!cb || !cb.checked) continue;
      let id = f.variants[0].id;
      if (f.variants.length > 1) {
        const sel = document.querySelector('input[name="var-' + f.id + '"]:checked');
        if (sel) id = sel.value;
      }
      const t = tw.tweaks.find((x) => x.id === id);
      if (t) out.push(t);
    }
    return out;
  }

  // une fonctionnalite = une case a cocher ; si elle a plusieurs variantes, des boutons radio
  // apparaissent en sous-choix, actifs seulement quand la case est cochee.
  function renderFeature(box, f) {
    const wrap = document.createElement("div");
    wrap.style.margin = "8px 0";
    const lab = document.createElement("label");
    lab.className = "ack";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.id = "feat-" + f.id;
    const sp = document.createElement("span");
    const strong = document.createElement("b");
    strong.textContent = f.label;
    sp.appendChild(strong);
    if (f.desc) {
      sp.appendChild(document.createElement("br"));
      const d = document.createElement("span");
      d.className = "tiny";
      d.style.color = "var(--muted)";
      d.textContent = f.desc;
      sp.appendChild(d);
    }
    lab.append(cb, sp);
    wrap.appendChild(lab);

    const radios = [];
    if (f.variants.length > 1) {
      const sub = document.createElement("div");
      sub.style.margin = "4px 0 0 1.9em";
      f.variants.forEach((v, i) => {
        const r = document.createElement("label");
        r.className = "tiny";
        r.style.display = "block";
        const radio = document.createElement("input");
        radio.type = "radio";
        radio.name = "var-" + f.id;
        radio.value = v.id;
        radio.checked = i === 0;
        radio.disabled = true;
        radio.style.marginRight = ".45em";
        radios.push(radio);
        const t = document.createElement("span");
        t.textContent = v.label || v.id;
        r.append(radio, t);
        sub.appendChild(r);
      });
      wrap.appendChild(sub);
    }
    cb.addEventListener("change", () => {
      radios.forEach((r) => { r.disabled = !cb.checked; });
      ready();
    });
    box.appendChild(wrap);
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
    const box = $("features");
    if (tw && tw.features && box) {
      for (const f of tw.features) renderFeature(box, f);
    }
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
