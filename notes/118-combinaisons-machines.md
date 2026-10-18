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


## 7. Retrait du principal et regression de demarrage (17/10/2026)

AveyCole signale ensuite Select All : `V04-M0-P401C4B44`. Le principal revient exactement a 1.83 via PR60 ; PR61 publie seulement la copie test2. La validation materielle precedente ne couvrait pas cette composition MIDI complete.

[FAIT en emulation] `0x401c4b44` est le hook de chargement ChordKeys. La composition generique partageait son flux mais omettait `engine.chord_source`. Le composeur MIDI ne copiait donc pas ce code vers `0x401c383c` et ne protegeait pas sa reservation lors du cache disque. Le test de regression execute le vrai bootstrap puis ce hook : ancien code absent et retour impossible, correction avec octet projet, pile et retour conserves. Le champ est restaure ; aucun changement du corps ChordKeys.

[FAIT] Le balayage elargi trouve aussi RETROSYN+WAVE sans Wizard (mask640) : le placeholder RETROSYN etait choisi comme ancien moteur a remplacer, laissant la recette WAVE autonome en plus du moteur combine. `compose-normal.js` choisit maintenant le vrai moteur ajoute avant le placeholder et retire les placeholders explicitement.

Les nouvelles preuves `test_startup_combinations.js` et `emu/test_startup_build_matrix.py` couvrent les selections machines avec/sans Wizard et ChordKeys, profils minimal/maximal ; puis images signees des familles de demarrage, variantes de backends MIDI et cas RETROSYN/WAVE. Elles executent les sites OS de chargement/init projet, le constructeur de cache et le constructeur de table machines. Une reprise exige les empreintes du site et de l'image signee identiques. Cela ne constitue pas une garantie materielle pour chaque sous-ensemble arbitraire de toutes les options.


[FAIT en emulation, test3] 8 192 compositions passent : 1 024 masques machines x Wizard oui/non x ChordKeys oui/non x profils minimal/maximal. 76 SYX signes passent le vrai bootstrap, init/chargement projet avant et apres cache, constructeur natif : 48 familles de demarrage, 12 variantes de backends MIDI et 16 cas RETROSYN/WAVE sans Wizard. La regression P401C4B44 reproduit le defaut test1 et passe sur la nouvelle image Select All. Le generateur de copie test passe `--check`.

PR62 publie seulement quatre fichiers dans la copie test3. L'arbre `docs/flasher` reste exactement `bda47b81f3a726393be0b0b8d37e5fd5857e5e7c`, principal1.83. Les preuves et reparations source sont conservees sur `fix-machine-combinations`, sans promotion du principal.


## 8. Promotion du test3 (17/10/2026)

AveyCole demande explicitement « push to main » depuis la copie test3 apres les resultats des 8 192 compositions et 76 demarrages signes. Publication principale1.85 autorisee. Les reparations de copie ChordKeys et remplacement WAVE sont incluses ; aucun outil diagnostic du test ne passe dans le principal. La confirmation utilisateur concerne le test3 essaye ; les autres compositions gardent leur preuve en emulation.
