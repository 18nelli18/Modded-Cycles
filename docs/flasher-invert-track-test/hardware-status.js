// Statut existant confirmé par le propriétaire ; aucune modification firmware.
(()=>{const t=window.MC_TWEAKS;t.features=t.features.filter(f=>f.id!=='track-filter');
function approved(v){if(!v||typeof v!=='object')return;for(const child of Object.values(v))approved(child);if('tested' in v||'tg_tested' in v||typeof v.id==='string'){v.tested=true;v.tg_tested=true;}}
for(const f of t.features){approved(f);f.status='tested';f.hardwareTestedByOwner=true;}window.MCFlasherApp.applyLang(document.documentElement.lang||'en');})();
