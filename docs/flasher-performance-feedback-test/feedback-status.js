// Note 100 : statut experimental pour ces deux changements seulement.
(()=>{for(const id of ['control-all-beat-repeat','midi-out-bank']){const f=window.MC_TWEAKS.features.find(f=>f.id===id);f.status='experimental';delete f.hardwareTestedByOwner;}})();
