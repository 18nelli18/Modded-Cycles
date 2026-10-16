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
