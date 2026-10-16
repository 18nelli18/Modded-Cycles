# 105 — Filtre en forte charge : moins de checks, meme signal

Demande AveyCole du 16/10/2026 : continuer le correctif filtre apres publication de la capacite sans MIDI. Distorsion et ticks a coupure baissee, lecture chargee ordinaire ; amplification avec Banque MIDI, legerement aussi sans. Adresses : VA de l'OS 1.13.

## Reponse courte

[FAIT] Le gain natif 0x40056f58..0x4005725c vide acc0/acc1 par movclr avant retour ; aucune preuve de corruption d'accumulateur trouvee. [HYP] L'ajout du filtre et de la Banque augmente la charge de calcul et pourrait contribuer aux artefacts. Pas de preuve de la duree CPU physique ni de reproduction acoustique des ticks dans l'emulateur.

[FAIT en emulation] Une optimisation limitee retire des tests de saturation mathematiquement redondants, sans changer les produits EMAC, arrondis, cutoff, feedback, makeup, etats Q27 ou limites de sortie. Le noyau passe de 520 a 430 octets au meme emplacement 0x401badda..0x401bb080 ; aucune allocation ni modification de callback.

## 1. Invariant de bornes

Le coefficient de chaque pole est entre 0 et 1. Son etat et son entree bornes donnent une interpolation convexe bornee, arrondie au meme entier que precedemment. Avec resonance, le premier pole peut recevoir une entree plus large et conserve donc ses deux clamps. Les poles 2/3/4 recoivent l'etat deja borne du precedent ; leurs clamps ne changent jamais le resultat. Sans feedback, le premier pole recoit aussi une entree bornee, issue du sample int32 >>4 : ses clamps peuvent etre sautes. Tous les etats initiaux du noyau 1.77 respectent deja ces bornes. Les clamps feedback et sortie restent inchanges.

`tools/emu/test_filter_load_equivalence.py` execute les deux vrais corps assembles. 256 blocs : samples int32 extremes/aleatoires, etats aux bornes, coefficients extremes/aleatoires, six pistes, avec/sans resonance. Tous les samples et etats finaux sont bit-identiques. Registres MACSR/accumulateurs preserves selon le contrat precedent. Nombre d'instructions observees : -28,2 % sans resonance et -15,6 % avec resonance. Ce ne sont pas des cycles materiels ni une garantie de correction des ticks.

## 2. Integration experimentale

`tools/gen_filter_load.py` compile `tools/machines/track_filter/load.s`. `load.js` exige le SHA exact du noyau principal 1.77, puis le remplace avant la composition des payloads. La page `flasher-filter-load-test` garde les builds avec/sans Banque, toute la selection et le packing de note 104. Banque MIDI et filtre candidat experimentaux. Principal 1.77 inchange.

```
python3 tools/gen_filter_load.py --check
python3 tools/gen_filter_load_flasher.py --check
python3 tools/emu/test_filter_load_equivalence.py
node tools/test_filter_load_flasher.js
python3 tools/emu/test_filter_current.py --case build/filter-load/all-midi --precision-data build/filter-load-data.js
python3 tools/emu/test_filter_current.py --case build/filter-load/all-no-midi --precision-data build/filter-load-data.js
```

Six builds signes : filtre seul, filtre+MIDI, selection complete avec/sans MIDI, animation alternative sans MIDI, filtre decoche. Boot natif/cache et noyau exact verifies. Preuves filtre six pistes/resonance/bypass, voix RETROSYN, MIDI/LED/Genie, sauvegarde, beat repeat et parite Python relancees.

## 3. Verification machine attendue

Utiliser le meme pattern charge, memes niveaux et resonances que le rapport. Baisser la coupure, relever ticks/distorsion avec Banque MIDI puis sans. Verifier aussi bypass ouvert/resonance nulle et beat repeat. Si le resultat ne change pas, l'hypothese charge reste non confirmee ; poursuivre la vraie chaine de mixage/LFO et les transitions de parametres. Aucun resultat materiel affirme.

## 4. Retour test 1 et candidat 2 — 16/10/2026

AveyCole confirme disparition de la distorsion mais conserve des clicks legers, meme a coupure fixe. Ils semblent partiellement rythmiques sans suivre exactement les triggers. Seuil observe : six machines actives en lecture ordinaire, cinq ou plus avec beat repeat, avec ou sans Banque. Le comportement avec beat repeat est inclus dans la verification suivante.

La trace de la vraie boucle des voix ajoutees ne montre pas de passage du filtre partage avant le post-gain ; le second emplacement historique dans amp_hook ne demontre donc pas un double filtrage du chemin observe. Aucune correction speculative de ces appels appliquee.

Test 2 choisit le chemin sans resonance une fois par bloc plutot que deux tests par sample. Les memes bornes et calculs restent en place. Noyau 522 octets dans la meme region de 678 octets. Sur les 256 blocs comparatifs : -36,2 % d instructions sans resonance, -21,7 % avec resonance face au principal 1.77 ; samples et etats restent bit exacts. Pas de modification beat repeat. Huit profils navigateur, incluant les selections completes avec beat repeat decoche pour isoler la charge. Resultat physique clicks encore attendu.

Validation candidat 2 elargie a 2 048 blocs comparatifs, identite samples/etats conservee. Preuve combinee `tools/emu/test_filter_repeat_load.py` : vraies voix RETROSYN, cinq/six actives, beat repeat et filtre, notes retriggees ; comparaison au noyau principal. Les autres objets/peripheriques et historique sont fixtures, aucune deadline physique simulee.

Le seuil cinq/six voies indique par AveyCole est ajoute aux fixtures combinees. Elles couvrent un cycle beat repeat complet a 480 BPM/1-64 (375 samples) sur 16 blocs, avec retriggers, cinq/six vraies voix et comparaison de tous les samples. Mesure limitee aux modules compares pour eviter de ralentir artificiellement les autres boucles de synthese. Aucun tempo utilisateur modifie.

Les quatre fixtures combinees passent : cinq et six voix, avec et sans repeat, 16 blocs/cycle complet identiques au noyau principal. Instructions filtre+repeat observees pour six voix : 144 808 vers 93 148 sans repeat, 453 696 vers 402 036 avec repeat. Les huit builds et preuves Python/native passent. La reduction physique des clicks reste a verifier.

## Retour materiel et candidat 3 (16/10/2026)

AveyCole : test 2 clique encore en tenant TRACK + RETRIG seul, sans pad de division. Six machines filtrees avec Control All cliquent aussi. Configuration indiquee : Kick, quatre SY SWARM, Kick. Aucun resultat physique positif revendique pour ces clicks.

[FAIT] Avec le combo seul et apres allocation, render parcourait chaque sample avec calculs phase/enveloppe et recherche des voies, meme sans repetition active. Candidat 3 : chemin historique seul, pistes contigues, memes conversions signees/clamps et memes samples enregistres ; chemin wet/fondu conserve si un etat de voie reste actif. Aucun buffer supplementaire, meme taille historique, aucun changement filtre face au candidat 2.

[FAIT en emulation] `test_beat_repeat_idle.py` compare principal/candidat sur huit blocs, frontiere circulaire, extremes int32 et voies stereo partiellement actives. Audio, historique integral et etats identiques ; 242 376 vers 55 304 instructions pour ces fixtures, soit -77,2 %. Ce ne sont pas des cycles materiels. La preuve beat repeat existante passe (16 divisions, masques, release, stereo, ABI).

[HYP] Le cout de capture contribue aux clicks du combo seul ; reduction physique a verifier. Le cas six filtres sans combo reste ouvert et ce changement ne pretend pas le corriger. Page test 3 seulement, principal 1.77 inchange.

Reproduction candidat 3 : retirer uniquement le tweak `control-all-beat-repeat` du catalogue de reservation courant, puis `python3 tools/gen_beat_repeat.py --catalog build/beat-idle-catalog.json --output build/beat-idle-data.json`, `python3 tools/gen_filter_load_flasher.py` et leurs `--check`. `test_filter_repeat_load.py --case build/filter-load/all-midi --kick-swarms` couvre Kick / SYSwm x4 / Kick, combo arme sans division et repetition active. Les fixtures ne simulent toujours pas les deadlines/peripheriques physiques.

Les six fixtures Kick / SYSwm x4 / Kick passent (cinq/six voies, off/arme/repeat). Identite samples entre filtre principal et candidat maintenue. Huit parites navigateur/Python et regressions filtre A/B, Banque, sauvegarde et repeat passent ; vrai boot/cache sans Banque egalement. Publication 3 limitee aux quatre fichiers du dossier test (PR 15), principal inchange.
