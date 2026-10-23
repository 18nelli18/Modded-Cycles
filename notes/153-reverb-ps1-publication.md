# 153 - Reverb PS1 et publication 2.29

Demande AveyCole le23/10/2026 : ajouter une reverb inspiree PS1 apres le test CLOUD. Adresses : VA de OS1.13.

## En bref

[FAIT, retour utilisateur] « Okay, love PS1 reverb but cloud is still present in v69 », puis « push v70 ». v69 etait le prototype avec les deux effets. v70 repart de v66, ajoute PS1 et exclut CLOUD. Publier exactement v70, sans recompilation. Aucun test exhaustif de la composition v70 sur materiel n est revendique.

## DSP et commandes

[FAIT] Implementation originale, sans donnees Sony/de jeu : quatre combs stereo avec reflexions croisees, amortissement IIR, deux allpass, memoires16bits. Traitement24kHz et interpolation vers le bus48kHz des Cycles. Inspiration SPU, pas emulation exacte22,05kHz. Reference : https://psx-spx.consoledev.net/soundprocessingunitspu/#spu-reverb-formula .

TRACK+REVERB SIZE gauche/haut apres VINYL+REV : PS1. Parcours sans audition ; release TRACK applique, BACK annule. REVERB SEND : PS1 Send par piste ; SIZE : Decay ; FUNC+SIZE ou SETTINGS+SIZE : Tone. Mode PS1 sauvegarde, anciens IDs inchanges. Un ancien mode CLOUD sauvegarde revient a Delay sans perdre les autres preferences.

[FAIT en emulation] Code FX0x46800000, BSS0x46808000, fin0x46827f6c. Origine2Mo copiee et remise a zero par le bootstrap natif. Sources privees tools/machines/fx_menu/ps1.c, outils gen_governor_recovery_test.py --ps1-only et fx_menu_assets.py. Code PS1 identique v69/v70. Le renderer PS1 execute15575instructions dans le cas mesure : ce n est pas un pourcentage CPU materiel.

## Preuves

[FAIT en emulation] test_ps1_reverb.py : queues stereo bornees, Decay/Tone distincts, reset sans anciens buffers, vrai mixeur/send0 sec et send actif, anciens effets PCM exacts v66, ABI, mode/persistance. test_ps1_popup.py : trois controles et16positions de menu, CLOUD absent du code/menu. Matrice gestes, overlays opaques, sauvegarde et touches retrig/diagnostic passes. Objets Delay/Shimmer, voix, filtres et SCRAMBLE exacts v66. Chargeur natif :2587989octets exacts, aucun ecrasement des donnees compressees ; autres sections inchangees. Reconstruction --check exacte.

[FAIT] CLOUD v67/v68 conserves prives : le raccord de pitch hors grille est ameliore en emulation mais AveyCole rapporte Density qui continue a changer apres arret du potard, FUNC tenu. Le garde de release v68 ne resout pas ce cas. La cause CPU reste une hypothese non etablie ; aucune affirmation de correction complete.

## Publication

Fichier approuve v70 :21d21e29611a02f426c7e6f61066c771d8ed6e6c43b2695994f9b8961ed9d8b0.
MAIN :65d75a6fb846519ff3a01f9abd8c39a1a6145a14f9d88497684744467ed2c04c.
Principal2.29 : image fixe existante, guide EN/FR60lignes, PDF4pages, notes bilingues. Pas de variante compagnon.
