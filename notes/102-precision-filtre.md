# 102 — Precision du filtre continu

Demande AveyCole, conversation du 16/10/2026 : le test feedback sonne normal au neutre mais quantifie quand la coupure baisse, avec symptome signale sur piste 6 ; le meme son sur piste 5 parait propre. ChpHzrd est suspendu pour traiter ce probleme. Adresses : VA OS 1.13.

## En bref

[FAIT] Le ladder partage supprime 14 bits a l'entree et a la sortie et tronque chaque etage avant multiplication. Les signaux faibles peuvent alors ne garder que quelques niveaux. Cette quantification est reproduite avec le vrai firmware feedback ; elle disparait du candidat haute precision. [HYP] Elle explique le symptome physique de piste 6 : les tests directs et les six voix RETROSYN n'ont pas reproduit une difference d'index entre pistes 5 et 6. Validation materielle de ce symptome encore necessaire.

## 1. Modification minimale

Le corps de `gflt_run` (0x401badda..0x401bb080, 678 octets) est remplace en place apres toutes les adaptations du filtre continu. Les 520 octets propres de `precision.s` utilisent l'EMAC fractionnaire pour les quatre poles, avec etats Q27 : entree >>4 et sortie <<4 au lieu de >>14/<<14, sans nouvelle troncature de 12 bits entre poles. Arrondi EMAC au plus proche et retour au zero/fast path quand le signal est silencieux et les etats stabilises sous le seuil inaudible d origine. Meme coefficient, feedback, makeup, limites de saturation et stockage par piste. La voie sans resonance evite les produits de feedback/makeup. Pas de nouvelle allocation, cave, chargeur ou schema de sauvegarde. Les etats DSP ne sont pas persistants.

Le SHA du corps initial apres patch continu est exige. Les octets de l'OS sont uniquement lus depuis les fichiers officiels locaux ; le catalogue ne contient que le nouveau code propre et une empreinte. Le resolver modifie le payload Wizard avant la composition MIDI, recalcule ses references et laisse les autres machines et le filtre propre des samples Wizard intacts.

## 2. ABI

D2–D7/A2–A6 et pile preserves. MACSR restaure. Acc1–3 intacts ; acc0 utilise comme scratch et rendu vide. L'appel depuis Volume+Dist/Attack a deja acc0 vide, comme le contrat natif de cette chaine. Bypass complet sans calcul quand gflt_f=0. Les sept slots d'origine sont gardes ; seules les six pistes audio sont traitees par l'adaptateur partage.

## 3. Preuves

`tools/emu/test_filter_current.py` execute le vrai boot SYX et le constructeur cache, puis exige que le code charge soit celui du candidat, sans le reinjecter. Signaux sinus 220 Hz a trois niveaux, six positions de coupure et six pistes ; bypass bit exact. Reference flottante aux memes coefficients : a coupure 96, SNR 95,17 dB au niveau 2^20 et 64,77 dB au niveau 2^15 (ancien noyau : 37,12 dB et 7,76 dB). Balayage resonance 32/96/127, coupure 0/32/64/96/126, six pistes, entree alternee forte ; registres, MACSR, accumulateurs et bornes verifies. Vraies six voix RETROSYN comparees. Ce ne sont pas des mesures CPU ou de bruit physiques.

```
python3 tools/gen_filter_precision.py --output build/filter-precision-data.js --check
python3 tools/gen_filter_precision_flasher.py --data build/filter-precision-data.js --check
node tools/test_filter_precision_flasher.js
python3 tools/emu/test_filter_current.py --case build/filter-precision/all --precision-data build/filter-precision-data.js
```

Le profil toutes machines + Wizard + beat repeat sans MIDI depasse deja la capacite du principal : reproduction independante sur le principal 1.74. Le profil de preuve sans MIDI desactive donc aussi beat repeat ; aucune nouvelle restriction introduite par cette correction. Les autres profils couvrent filtre seul, supports, ChordKeys, MIDI, RETROSYN, selection complete et animation alternative.

## 4. Essai materiel attendu

Comparer exactement le meme son sur pistes 5 et 6, a meme niveau/volume, en baissant la coupure depuis 127, resonance nulle puis croissante. Verifier les fins de notes et les sons faibles. Revenir a cutoff 127/resonance 0 : bypass exact attendu. Si le probleme reste propre a la piste 6, ne pas conclure a sa correction sur la seule base de cette amelioration numerique. Principal inchange jusqu'a confirmation utilisateur.
