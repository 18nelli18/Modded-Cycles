// Statut demande par AveyCole pendant l'enquete filtre/charge, DSP inchange.
(()=>{
 const a=window.MCFlasherApp,f=window.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank'),previous=window.MCMidiBankCompose;
 f.status='experimental';f.hardwareTestedByOwner=false;
 a.registerFeatureTexts('midi-out-bank',{
  en:{label:'MIDI OUT Bank',short:'Experimental. Optional six-track MIDI bank with project saving.',desc:'Six parallel MIDI tracks, installable alone or with your chosen machines. This optional bank remains experimental. FUNC + SETTINGS + TRACK opens B-side. Stop playback before Save Project and wait for MIDI SAVED. Saved MIDI data loads only when you enter B-side and only while playback is stopped. CC assignments/locks, slides, retrigger, chance and two MIDI CC LFOs are retained. Sample Wizard is optional. MIDI files are outside Elektron project backups and SysEx exports.'},
  fr:{label:'Banque MIDI OUT',short:'Experimental. Six pistes MIDI facultatives avec sauvegarde projet.',desc:'Six pistes MIDI paralleles, seules ou avec les machines choisies. Cette banque facultative reste experimentale. FUNC + SETTINGS + TRACK ouvre B. Arreter avant Save Project et attendre MIDI SAVED. Les donnees MIDI sauvegardees se chargent uniquement en entrant cote B et uniquement lecture arretee. Assignations/locks CC, slides, retrigger, chance et deux LFO CC conserves. Wizard facultatif. Fichiers MIDI hors backups projet et exports SysEx Elektron.'}
 });
 window.MCMidiBankCompose=(...args)=>{const result=previous(...args);return {...result,tweaks:result.tweaks.map(t=>t.id==='midi-out-bank'?{...t,status:'experimental',hardwareTestedByOwner:false}:t)};};
 a.applyLang(document.documentElement.lang||'en');
})();
