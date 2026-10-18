// Catalogue du preset MIDI seulement ; les pages publiees restent inchangees.
(()=>{const d=window.MCMachineCombinationData,b=window.MCBuilder,x=window.MCMidiMachineAll.entry,old=d.wizard[1023];x.engine.id=old.engine.id;x.engine_sha256=b.hex(b.sha256(Uint8Array.from(unescape(encodeURIComponent(JSON.stringify(x.engine))),c=>c.charCodeAt(0))));d.wizard[1023]=x;})();
