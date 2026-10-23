# 143 — Publication Elder/effets, principal2.17

Demande explicite AveyCole,22/10/2026 : promouvoir la version avec filtre et
actualiser guides des raccourcis, liste des fonctions et flasheur. Retour antérieur :
« v40 worked ». Adresses : VA OS1.13.

## Réponse courte

Le principal2.17 distribue exactement le SysEx partagé v40 approuvé, sans
recompilation ni modification audio. Source :
`all-features-polivoks-cpu-trim-test-v40.syx`.
SHA256 SysEx : `8e11e8bed03666f4444f818f6a5d7dea67199f077eddf9d623de81584041e7cb`.
SHA256 MAIN : `077797c65adc12fbf133dac095fbc12e6a8b91852766ddfb7f65a9386618c2ee`.
Stamp : `2026-10-22-elder-fx-main-217`. Pages privées et comparaisons conservées.

## 1. Fonctions et documentation

Elder remplace l’emplacement ChpHzrd/Retrosyn : Wave/Warp/Noise/Motion,
interprétation originale inspirée de Junior de Fors, icône approuvée.
Feral de Glycinate et toutes les optimisations CPU2.16 sont conservés.
Reverb/ChorusI/II avec correctif du sifflement et labels natifs sur deux lignes.
Delay/Crush/Both : crusher sur envoi immédiat ou sur retour delay,
Rate/Bits globaux distincts de Time/Feedback, envois par piste avec locks.
Les guides précisent sauvegarde après arrêt, absence de destinations p-lock
Rate/Bits, coût supplémentaire Both et routage USB6ch sans retours d’effets.

`tools/shortcut_guide_content.json` est le contenu EN/FR commun de44lignes de
raccourcis. `gen_shortcut_guide.py` produit HTML et Markdown ;
`gen_print_shortcut_guide.py` produit le PDF anglais de4pages depuis le même HTML.
PDF rendu et inspecté sur toutes les pages, sans troncature ni chevauchement.
Index principal, liste flasheur, guide, notes de version et manifests actualisés.
Les anciens récits de versions restent consultables ; ils ne sont pas réécrits.

## 2. Vérifications

- Source v40 et copie main SHA identiques, preuves DSP/UI/integration épinglées.
- `test_fixed_main_delivery.js` : vraie page Chromium, OS officiels Cycles/Syntakt,
  SysEx/MAIN/checksums exacts, téléchargement exact, image corrompue refusée.
- PDF téléchargé identique, notes2.17 et lien retour main, crédit Glycinate.
- Guide :44lignes,EN/FR,1100px/390px sans débordement ; boutons de langue testés.
- Générateurs principal et guides `--check` concordants ; syntaxe Python et
  contrôle de diff limités à la publication.
- Bootloader/updater restent ceux du candidat v40 prouvé ; aucun test matériel
  supplémentaire revendiqué. Métadonnée globale hardware_verified non extrapolée.

## 3. Demandes suivantes

Après vérification publique de cette publication, AveyCole demande d’ajouter
PPPCCC et18nelli18 aux crédits, avec lien vers le projet18nelli18/Modded-Cycles.
Puis investigation privée : Bits4et moins peu audibles ; Bits5 commence à
s’entendre et effet perçu sous le son sec. Ne pas modifier les octets approuvés
sans une nouvelle validation. Le routage parallel via DelaySend explique le sec.
