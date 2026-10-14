# 91 — Référence ChordKeys sans Banque MIDI

A.V. signale le 14 octobre 2026 : « chord-keys-supermodel : écritures différentes de la référence »
lors d’une construction main sans banque MIDI. Adresses : VA de l’OS 1.13.

## Réponse courte

La vérification refusait correctement une référence erronée du frontend. Le profil ChordKeys seul,
avec tous les moteurs additionnels sélectionnés, modifie le hook de démarrage du moteur avant que
le correctif ACID décale sa source flash. Le SHA stocké décrivait le prototype sans ce hook moteur.
Aucune vérification n’est supprimée ; aucun changement de code firmware n’est introduit.

## Correction

`gen_kevin_acid_test.py` construit explicitement `prototype-full-engine` depuis le prototype ChordKeys :
retirer le hook direct offset 306, ajouter le hook documenté du bundle moteur complet, puis déplacer
la source `0x401f8f76` vers `0x401f8f8a`. Le frontend utilise la référence de cette variante lorsque
ChordKeys fonctionne sans banque avec ce bundle. Les références Banque plain/chord restent identiques.

Ancienne référence inadéquate : `099a2dc3549b229f0c1ab452401de7e234e132b7e0927f9119fd0cae36d4f61e`.
Référence exacte : `31165988f3ca17a8d2579c0c6e06cd3ab47779df43525e83bb06eb2422921609`.

## Validation

`test_main_chord_optional_machines.js` reproduit l’erreur sur le main précédent et réussit après
correction. ChordKeys+TG seul, MACRO, ACID, Syntakt, performance et Select All restent inchangés.
Select All sans Banque réussit, MAIN OS `7b5fb4c9890ad6943e162718d5621e71efccd0ffdc34d80ca903693fd28dc9f5`.
Réactiver la banque rend exactement le hash Select All précédent. Références strictes vérifiées,
conteneurs SysEx signés valides. Les fichiers de firmware générés restent privés et ignorés.
