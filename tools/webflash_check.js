/* Verifie que docs/flasher/flasher.js valide les .syx exactement comme
 * tools/mtlib/syx.py. Lance-le via tools/webflash_check.sh (qui fabrique les
 * fichiers de test avec le Python), ou :
 *   node tools/webflash_check.js <bon.syx> <mauvais.syx> <NOM> <NB_PAQUETS>
 */
"use strict";
const fs = require("fs");
const { verify, splitMessages } = require("../docs/flasher/flasher.js");

const [good, bad, wantName, wantCount] = process.argv.slice(2);
let ok = true;

const g = new Uint8Array(fs.readFileSync(good));
const info = verify(g); // doit reussir
if (info.name !== wantName || info.count !== Number(wantCount)) {
  console.log(`ECHEC: attendu ${wantName}/${wantCount}, obtenu ${info.name}/${info.count}`);
  ok = false;
} else {
  console.log(`bon fichier accepte: ${info.name}, ${info.count} paquets, ${info.bytes} o`);
}

const b = new Uint8Array(fs.readFileSync(bad));
try {
  verify(b);
  console.log("ECHEC: le fichier corrompu a ete accepte");
  ok = false;
} catch (e) {
  console.log("fichier corrompu rejete: " + e.message);
}

// le nombre de messages doit correspondre a ce que compte le Python
console.log("messages F0..F7:", splitMessages(g).length);
process.exit(ok ? 0 : 1);
