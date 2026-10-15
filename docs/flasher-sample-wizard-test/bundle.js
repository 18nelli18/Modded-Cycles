// Test Sample Wizard uniquement : conserver le transport main.
(function(){function ready(){const a=window.MCFlasherApp;a.setMachine('cyc');const e=document.getElementById('feat-sample-wizard');if(e&&!e.checked){e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else ready();})();
