# 155 - Ping Pong et deux Shimmer

Demande AveyCole du23/10/2026 dans Codex : alternatives au delay standard, Ping Pong stereo, octave integrale propre et conservation du v62 comme Shimmer2. Retour : "64 seemed to work for me, push that to main with updated feature shortcuts and stuff". Publication exacte v64 avec filtre partage, principal2.27. Adresses : VA OS1.13.

## Reponse courte

[FAIT] IDs delay0..4 conserves ;5 Ping Pong,6 Shimmer1,7 Shimmer2. Ordre affiche haut/bas : Shimmer2,Shimmer1,Ping Pong,Crush2,Crush1,Delay,CRU1+DEL,CRU2+DEL. TRACK+DELAY TIME parcourt sans changement sonore ; relachement TRACK applique ; BACK annule. Time/Send natifs ; FUNC+TIME ou SETTINGS+TIME : Feedback. Pas de variante combinee pour les nouveaux delays.

## Diagnostic et conception

[FAIT] Les premiers tests forcaient le pointeur SRAM0x8000a560, masquant le rejet du vrai tampon initialise0x8000b590 par la garde. v61 accepte la vraie adresse ; AveyCole confirme Ping Pong fonctionnel. Entree mono vers gauche ; retour stereo natif inverse avant feedback.

[FAIT] Hook0x40057638 apres interpolation/filtrage du retour natif, avant wet et feedback. Rejoue le chargement du pointeur puis reprend0x4005763e. Le ring/DMA et Time/Feedback restent natifs. Shimmer1 : deux tetes octavees, Hann4096,ring8192 stereo Q20. Alignement original par erreur quadratique, recherche97decalages sur16blocs (7candidats/bloc), decalage commun stereo. Retard minimum32trames meme avec offset negatif. Aucun echo non transpose melange dans Shimmer1.

[FAIT] v64 conserve le FIR binomial7 et ajoute un FIR demi-bande31 original (sinc fc=1/4,fenetre Hamming,Q15,somme32768),8paires symetriques et centre ; multiplication signee sans perte de la precision Q20. Gain octave3/4 pour marge. Aucun remappage/reduction de la plage Feedback. Shimmer2 garde les tetes v62 non alignees,FIR initial,allpass et melange propre/octave v62. Les deux algorithmes partagent le ring ; changement de mode fondu et reset borne.

## Preuves

Sources privees : tools/machines/fx_menu/{delays.c,control.c,popup.c,fx.h},tools/fx_menu_assets.py,tools/gen_governor_recovery_test.py --octave-polish. Construction depuis OS officiel, jamais depuis un candidat. --check reproduit le SysEx approuve.

[FAIT en emulation] test_new_delays.py : Ping Pong alterne reellement gauche/droite ; rendu complet avec feedback Shimmer2 bit exact v62 ; ABI/registres/EMAC preserves ; les5routes legacy restent PCM exactes face au v57 dans le vrai mixeur ; Vinyl source muette,mute,volume0 respectes. test_shimmer_polish.py :1280sorties FIR exactes face a reference independante ; attenuation supplementaire59,5dB a15kHz ; transitions6/7/6/5/7/0 avec Feedback50. Comptage C shifter22 061instructions ordinaire,26 978max aux phases de recherche mesurees ; ce ne sont pas des pourcentages CPU materiels. test_shimmer_quality.py :4notes hors grille,puissance autour de l octave >99,98% hors fuite de fenetre ; pas de composante echo non transposee.

[FAIT en emulation] Menus30positions,differes/cancel,modificateurs ordonnes,retrig/temp/DX physique,SETTINGS,affichage natif opaque verifies. Bootstrap natif :2 551 005octets exacts,garde minimale733 538octets avant donnees compressees non lues ; sections hors MAIN identiques a OS officiel.

## Publication et resultat materiel

[FAIT,retour utilisateur] AveyCole signale le v64 fonctionnel puis demande la publication. Ne pas transformer ce retour en promesse de charge CPU illimitee ou de qualite subjective pour toutes les sources. Binaire approuve inchange. Guide EN/FR et PDF imprimable4pages,59lignes de commandes,issus du meme contenu canonique. Ancien v62 conserve comme fichier prive et comme Shimmer2.

Module FX code `0x46800000`, BSS `0x46808000`, fin `0x4681eef4` ; pas de chevauchement.

SysEx : `77f533e3d6856ab204ff121ddd9c2562d90b378cfa59d24e7befa592ccf6357a`.
MAIN : `2192a9ab2deba19d3362622f1f9dca5b545dda4c690b394096e737c2bf55c2a6`.

Seul fichier firmware suivi modifie : `docs/flasher/all-features-usb-2ch-default.syx`, voie existante autorisee. Publication2.27,checksum navigateur et PDF verifies avant push.
