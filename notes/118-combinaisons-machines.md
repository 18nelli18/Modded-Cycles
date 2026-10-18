# 118 — Choix independants TINY/RETROSYN

AveyCole signale le 17/10/2026 une exception navigateur « Cannot read properties of undefined (reading engine) ». Sa selection : SD, Clap, Swarm, MACRO, ACID, TINY, RETROSYN, Sample Wizard ; Trig Preview, Easy Trig Removal, Arp, Dimmed Trig, Second LFO, Synth Attack, filtre par piste, latch mute, ChordKeys, beat repeat collectif, preecoute, defilement et navigateur multiligne. Il demande explicitement que les combinaisons soient prises en charge, sans imposer la banque complete.

Adresses : VA de l’OS 1.13.

## Reponse courte

[FAIT] Le catalogue TINY ne contenait que trois ensembles (seule, WAVE, banque complete). Le resolveur lisait `variants[mask].engine` sans entree pour la selection demandee. RETROSYN refusait egalement les sous-ensembles. Une erreur lisible ne repondait pas a la demande : il fallait les construire.

Le catalogue etendu fournit les 768 ensembles contenant TINY ou RETROSYN, avec et sans Wizard, soit 1 536 recettes. Les machines non cochees ne figurent pas dans le selecteur. Sample Wizard reste facultatif. Sans voix Syntakt, aucun fichier Syntakt n’est requis. Les corps audio natifs restent identiques ; leurs tables et menus sont regeneres pour les indices compacts.

## 1. Generation et zones reservees

`tools/gen_machine_combinations.py` reprend les corps natifs des catalogues precedents, les recettes d’extraction Syntakt et les fonctions de la passerelle. Il assemble les detours et regenere noms, callbacks, descripteurs et bornes. WAVE garde le navigateur correspondant a son indice ; son routage Wizard est conserve. ChordKeys partage le flux de compression, dans la reservation deja utilisee en `PAY+0x2e900`.

Les nouvelles interfaces vivent a `PAY+0x88000`, tables a `+0x89000`, descripteurs a `+0x89400`; fin reservee `+0x8b000`, PAY = `0x46700000`. Rangees et fiches gardent les reservations `+0x84000`, `+0x84400`, `+0x84800`. Elles ne touchent ni le code/BSS des voix ni la memoire du regulateur.

[FAIT en emulation] Une premiere disposition en `+0x32a00` faisait tomber certaines tailles de detour sur les variables du regulateur, `+0x32f00`. L’audio sans Wizard a reproduit l’ecrasement. Les interfaces sont donc deplacees au-dela des voix avant publication.

`tools/pack_machine_combinations.py` partage objets, chaines et differences, avec restauration exacte verifiee. Aucun firmware officiel n’est exporte : seulement recettes, code natif existant et octets de modifications verifies. Les fichiers d’OS et SYX produits restent dans les dossiers ignores.

## 2. Composition navigateur

`machine-combinations.js` complete les catalogues utilises par les resolveurs existants, conserve les options UI et deplace ChordKeys dans la charge utile commune. `machine-combinations-build.js` prepare les references avant les transformations Swarm LITE et MIDI/audio existantes. La verification des ecritures et des charges utiles reste active dans le builder. Les anciennes recettes ne dependant pas de TINY/RETROSYN restent disponibles.

L’application capte egalement les erreurs de resolution et invalide le firmware precedent : une selection erronee ne peut pas laisser telecharger une ancienne composition. Cette protection ne remplace pas le support des combinaisons.

## 3. Reproduction

```
node tools/export_retrosyn_catalogues.js
python3 tools/gen_machine_combinations.py --masks all --wizard
python3 tools/gen_machine_combinations.py --masks all
python3 tools/pack_machine_combinations.py --check
python3 tools/emu/test_machine_catalogue.py
node tools/test_machine_combinations.js
node tools/test_machine_combinations_matrix.js
python3 tools/emu/test_machine_combinations.py
```

Le generateur accepte `--check`, ainsi que `--resume` explicite pour reprendre un lot interrompu. La preuve des menus execute le vrai constructeur OS et les recherches de descripteurs pour les 1 536 selections. Les preuves audio demarrent les SYX signes et comparent les memes voix sur les six pistes, avec changement d’indice. Les tests navigateur couvrent le choix signale et des sous-ensembles avec/sans Wizard, MIDI et beat repeat independants.

## 4. Portee

Les voix existantes conservent leurs statuts historiques ; les nouvelles combinaisons sont verifiees en emulation, sans inventer de validation materielle. Aucun diagnostic n’est ajoute au principal. Model-TG reste exclu. Le profil 909, qui a ses propres machines, n’est pas modifie par cette correction.

## 5. Publication test seulement

AveyCole demande explicitement le 17/10/2026 de publier en test avant le principal. PR59 ne publie que `docs/flasher-machine-combinations-test/`; la recette principale et son arbre Git restent identiques. URL : https://aveycole.github.io/Modded-Cycles/flasher-machine-combinations-test/?v=2026-10-17-machine-combinations-test-1 . PR58 reste en brouillon.

`tools/gen_machine_combinations_test.py --check` reproduit la copie. Diagnostic CPU/CUT facultatif conserve ; sa reference couvre toute la charge utile, dont le wrapper de sortie quick-save, au lieu du seul premier morceau. Le choix exact avec diagnostic, six variantes navigateur signees, le vrai boot/cache et les gestes/popup CPU/CUT passent en emulation. Validation materielle attendue.

## 6. Teste sur la machine (17/10/2026)

AveyCole confirme le test publie : « that worked push to main ». Cette confirmation concerne la combinaison signalee dans le test1 ; les autres selections du catalogue restent verifiees en emulation. Promotion de PR58 autorisee. Les scripts et payloads CPU/CUT restent uniquement dans la copie test ; ils ne sont pas charges par le principal.
