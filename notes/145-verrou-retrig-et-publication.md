# 145 — Verrou retrig et publication2.18

Demande AveyCole, chat du22/10/2026 : apres les tests Tone/crusher, ajouter TRACK + double RETRIG pour verrouiller seulement le mode, pas la division. Precision : BACK doit quitter et copier/coller/effacer doivent etre impossibles dans ce mode. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] v42/v42nf ajoutent le verrou UI au v41 exact pour chorus/crusher/Tone. Aucun moteur retire, aucun calcul IRQ ajoute. Les pas gardent leur comportement momentane. AveyCole joint le fichier partage et demande « perfect, push this to be main » ; promotion de ses octets exacts en2.18.

## 1. Implantation

Code original `tools/machines/repeat_latch/latch.c`, construit par `tools/repeat_latch_assets.py` via `--repeat-latch`. Code0x467ff000, BSS0x467ffe00, fin inferieure0x46800000. Wrapper a l'entree `br_key`, prologue8octets verifie et rejoue par trampoline. Tous les appels globaux et Track utilisent le meme handler.

Etat physique TRACK/RETRIG distinct de `br_keys` logique. Deux pressions fraiches de RETRIG, TRACK maintenu, intervalle maximal350ms selon timer natif135168ticks/ms. Long/repeat/duplicate ne declenchent pas le verrou. Apres entree, releases des modificateurs consommees : br_keys reste3 et la vue Track reste ouverte. Chaque pas garde selection/release/ownership natifs, dernier pas tenu prioritaire.

BACK frais quitte : nettoyage natif des deux modificateurs, evenement transforme en vrai release TRACK pour fermer la TrackSelectionView. Release BACK possedee pour ne pas fermer une autre vue. Settings,LFO,Machines quittent aussi ; verrou non sauvegarde. Stop/projet conserve l'annulation audio native ; prochain pas intentionnel rearme le mode.

## 2. Protection d'edition

[FAIT] La TrackSelectionView0x40024078 traite REC9/PLAY10/STOP11 comme copier/effacer/coller, meme sans FUNC. Son relais `br_old_track_keys` pointe donc en verrou vers un wrapper qui laisse passer ces touches simples a la vue transport sous-jacente. FUNC ou TRACK physique + transport sont consommes, press/repeat/release possedes. Hors verrou, delegation exacte au handler ControlAll puis natif : edition initiale conservee. BACK logique vaut12.

## 3. Preuves

Les deux variantes passent le vrai handler et la vraie TrackSelectionView : seizepas momentanes, priorite/multi-held, ownership, doubles taps/lents/repeats/wraptimer, allocation refusee, rearmement apres Stop, fermeture native par BACK, aucune des trois fonctions d'edition atteinte en verrou, troisfonctions retrouvees horsverrou, transports simples propages.

Integration : seuls huitoctets d'entree `br_key` et quatreoctets du pointeur Track changent dans le tail anterieur ; chorus et crusher v41 entiers byte-exacts. Runtime/moteurs exacts.24blocs sixvoix/ChordKeys/Wizard stereo exacts. Bootstrap natif, aucun ecrasement source ; bootloader/updater exacts. Tests ne remplacent pas un resultat materiel.

## 4. Promotion approuvee

Partage v42 / principal2.18 :ea901ab5301763d0ebdd3e4656da57857c308f2a57a5ec841af6dff5d8718560.
MAIN :8b6a2786f1bd1dd54c050f2136db3b0bc007e0d744384117a026491704d19d59.
Sanspartage v42nf :a216702a998112e13dd081a215b0b9c6c8bc3efb04e44337cad8c5efd8abb275.

Notes EN/FR2.18, fonctionnalites, guide canonique46lignes et PDF4pages actualises. Credits Glycinate,PPPCCC,18nelli18 conserves. Fichiers de comparaison40/41 conserves. Verification navigateur : fichiers OS officiels -> image approuvee et telechargement byte-exacts ; corruption refusee. Quatrepages PDF rendues et inspectees, aucun chevauchement. Verification publique apres push consignée ci-dessous.
