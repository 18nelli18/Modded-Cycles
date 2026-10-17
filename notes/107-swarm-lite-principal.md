# 107 — Swarm LITE dans le principal

Le 16/10/2026, AveyCole rapporte que le Swarm trois oscillateurs du test SY reduit nettement charge et clicks. Il demande de remplacer la version sept oscillateurs, de nommer la case `Swarm LITE` et d expliquer le compromis. Les clicks ne sont pas declares totalement corriges.

## Implementation

Le fondamental et les deux oscillateurs desaccordes d indices 0, 3, 6 restent ; quatre appels de rendu sont retires. La somme propre ne lit que ces trois buffers. Gain non compense : timbre plus fin, niveau parfois reduit. PUNCH reste relie a sa commande existante. Un helper commun de recurrence garde le calcul exact tout en retirant des instructions redondantes.

Adresses DSP Syntakt 1.42 : helper 0x40006074 ; appels retires 0x40009758, 0x40009760, 0x40009774, 0x4000977c ; somme 0x40009790. Six SHA verifient les regions natives. `gen_swarm_lite.py` extrait uniquement du fichier officiel local et exporte code propre/hashes. Aucun octet OS ajoute au depot.

`main.js` reconnait les recettes contenant le rendu Swarm, verifie leurs references avant modification, remplace les six regions par du code propre avant compression/composition, recalcule les references. Tailles/adresses/relocations conservees. Les recettes sans Swarm restent identiques. Le nom de la case et son detail EN/FR expliquent trois au lieu de sept ; aucune case permettant de remettre sept oscillateurs dans le principal. L identifiant interne reste swarm pour les combinaisons existantes.

Seuls ces calculs Swarm sont promus. Filtre, repeat et regulateur conservent les assets principaux 1.78. Diagnostics CPU/CUT, voie rapide repeat experimentale et comparaisons du regulateur restent hors de cette promotion. Banque MIDI reste experimentale ; MODEL TG bloque, TINY et Wizard facultatif conserves.

## Preuves et limites

`test_sy_load.py` execute le vrai DSP Syntakt, six voix audibles : Toy/Bits bit-identiques ; Swarm sept vers trois, audio modifie comme prevu, 402 968 vers 252 416 instructions pour la fixture huit blocs (-37,36 %). Ceci mesure des instructions DSP, pas le CPU physique total.

`test_swarm_lite_main.js` construit les profils avec/sans Banque et Wizard ainsi que Swarm seul et Toy/Bits sans Swarm. Comparaison avec le builder Python, signature/refus MODEL TG et nom de la case. `test_sy_load_boot.py` exige les six regions attendues dans le payload ET la SRAM apres vrai boot/cache navigateur avec/sans Banque, sans les reinjecter. Les anciennes preuves natives du test couvrent les memes corps Swarm. Retour hardware : baisse significative de charge/clicks, sans garantie d absence totale de clicks sous forte charge.

Statut du changement : choisi pour promotion par AveyCole sur ce retour machine. La correction globale de surcharge n est pas revendiquee.

Controle catalogue historique : gen_flasher_tweaks.py --check signale un ecart deja present entre les JSON sources et docs/flasher/tweaks.js (adresses de detours existantes). Le generateur, les JSON et tweaks.js sont tous identiques a origin/main pour cette promotion ; licences concordantes. Catalogue laisse intact pour ne pas introduire de regenerations etrangeres. check_overlaps et registry --check passent.

Validation finale : huit profils navigateur/Python identiques ; vrais boots/cache six regions et SRAM avec/sans Banque passes. Principal complet MIDI SHA-256 c51ce21b961a312c12fea73fbbafcb56b5e435caa4cb2cf36cf2414286d4e887 ; sans Banque 577b288b2da086676d4b690ca7fc0b9f51a03f47e21b5e18911fb11bd987bdfc. Filtre/repeat principaux compares a origin/main : aucun changement. La garde refuse aussi une selection Swarm qui n aurait pas recu exactement six edits.
