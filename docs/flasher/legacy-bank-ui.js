/* Import DX7 original, protocole SML du firmware105 ; MIDI USB uniquement. */
(function(){'use strict';
const $=id=>document.getElementById(id);let midi=null,bank=null,busy=false;
const en=()=>document.documentElement.lang!=='fr';
const say=(a,b,error=false)=>{$('bank-status').textContent=en()?a:b;$('bank-status').classList.toggle('err',error);};
function refresh(){
 const ports=midi?Array.from(midi.outputs.values()).filter(p=>p.state!=='disconnected'&&!/through/i.test(p.name||'')):[];
 const old=$('bank-output').value;$('bank-output').replaceChildren(...ports.map(p=>new Option(p.name,p.id)));
 if(ports.some(p=>p.id===old))$('bank-output').value=old;
 else{const p=ports.find(p=>/model\s*[:_-]?\s*cycles/i.test(p.name||''));if(p)$('bank-output').value=p.id;}
 $('bank-output').disabled=busy||!!window.MCImportBusy||!ports.length;
 $('bank-send').disabled=busy||!!window.MCImportBusy||!bank||!ports.length;
 $('bank-connect').disabled=busy||!!window.MCImportBusy;
}
$('bank-connect').onclick=async()=>{try{
 if(!navigator.requestMIDIAccess)throw Error(en()?'Open this page in Chrome or Edge with Web MIDI.':'Ouvrez cette page dans Chrome ou Edge avec Web MIDI.');
 midi=await navigator.requestMIDIAccess({sysex:true});midi.onstatechange=refresh;refresh();
 say('Choose the Model:Cycles USB output. Stop playback before sending.','Choisissez la sortie USB Model:Cycles. Arretez la lecture avant l envoi.');
}catch(e){say(e.message,e.message,true);}};
$('bank-file').onchange=async()=>{bank=null;$('bank-voices').replaceChildren();try{
 const f=$('bank-file').files[0];if(!f){refresh();return;}
 const parsed=LegacyImport.parse(new Uint8Array(await f.arrayBuffer()));bank=parsed.raw;
 $('bank-label').value=f.name.replace(/\.syx$/i,'').slice(0,13);
 $('bank-voices').replaceChildren(...parsed.names.map((name,i)=>{const li=document.createElement('li');li.textContent=name||'—';li.value=i+1;return li;}));
 if(parsed.adjustments.length){
  const slots=Array.from(new Set(parsed.adjustments.map(a=>a.slot))).join(', '),count=parsed.adjustments.length;
  say('32 voices ready. Adjusted '+count+' out-of-range value(s) in slot(s) '+slots+' for LEGACY compatibility. Your original file is unchanged. Choose a library slot and send.',
      '32 voix pretes. '+count+' valeur(s) hors plage ajustee(s) dans les emplacements '+slots+' pour LEGACY. Votre fichier original reste intact. Choisissez un emplacement et envoyez.');
 }else say('32 voices validated. Choose a library slot and send.','32 voix validees. Choisissez un emplacement et envoyez.');
}catch(e){say(e.message,e.message,true);}refresh();};
$('bank-send').onclick=async()=>{if(busy||window.MCImportBusy)return;try{
 const out=midi?.outputs.get($('bank-output').value);if(!out||out.state==='disconnected')throw Error(en()?'Connect the Model:Cycles USB output.':'Connectez la sortie USB Model:Cycles.');
 const packet=LegacyImport.packet(bank,Number($('bank-slot').value),$('bank-label').value);
 busy=true;window.MCImportBusy=true;window.dispatchEvent(new Event('mc-import-busy'));refresh();
 await out.open();out.send(packet);
 say('Sent. Wait for LEGACY BANK SAVED on the device. Then select LEGACY, hold FUNC + MACHINES, turn DATA and press DATA to load. Sending again to this slot replaces its bank.','Envoye. Attendez LEGACY BANK SAVED sur l appareil. Choisissez LEGACY, maintenez FUNC + MACHINES, tournez DATA et appuyez pour charger. Un nouvel envoi au meme emplacement remplace sa banque.');
 /* L OS termine le petit fichier avant un nouvel envoi depuis cette page. */
 await new Promise(resolve=>setTimeout(resolve,2500));
}catch(e){say(e.message,e.message,true);}finally{busy=false;window.MCImportBusy=false;window.dispatchEvent(new Event('mc-import-busy'));refresh();}};
for(let i=0;i<16;i++)$('bank-slot').add(new Option(String(i+1).padStart(2,'0'),i));
window.addEventListener('mc-import-busy',refresh);refresh();
})();
