// Sélection compatible : les deux préférences sont installées en premier.
Object.assign(T.en, { select_all: "Select all", select_all_note: "Selects compatible mods, keeping Model-TG and Live MIDI OUT + THRU. Included mods stay part of Model-TG." });
Object.assign(T.fr, { select_all: "Tout sélectionner", select_all_note: "Sélectionne les mods compatibles en conservant Model-TG et MIDI OUT + THRU en direct. Les mods inclus restent dans Model-TG." });
function selectAllCompatible() {
  for (const f of features()) selOf(f).on = false;
  const preferred = ["model-tg", "midi-live-both"].map(featById).filter(Boolean);
  for (const f of preferred) setOn(f, true);
  for (const f of features()) {
    if (preferred.includes(f) || includedBy(f)) continue;
    if (features().some(g => isOn(g.id) && (excludes(f, g) || clashVia(f, g)))) continue;
    setOn(f, true);
    if (f.engines) selOf(f).engines = f.engines.map(e => e.code);
  }
  const generator = featById("scale-gen");
  if (generator && generator.queued && isOn("scale-gen")) selOf(generator).queued = true;
  pick.swap = null;
  renderFeatures();
  update();
}
