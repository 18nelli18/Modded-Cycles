// Existing hardware status only; this test filter remains experimental.
(()=>{const t=window.MC_TWEAKS;function approved(v){if(!v||typeof v!=='object')return;for(const child of Object.values(v))approved(child);if('tested' in v||'tg_tested' in v||typeof v.id==='string'){v.tested=true;v.tg_tested=true;}}
const testOnly=new Set(['scale-gen','sample-wizard','tiny','track-filter']);
for(const f of t.features){if(testOnly.has(f.id)){f.status='experimental';f.hardwareTestedByOwner=false;continue;}approved(f);f.status='tested';f.hardwareTestedByOwner=true;}window.MCFlasherApp.applyLang(document.documentElement.lang||'en');})();
