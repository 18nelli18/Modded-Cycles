# 182 — Banques LEGACY en petits messages verifies

> CORRECTION25/10/2026 : test150 retire apres erreurs appareil. La reservation0x46880000 chevauche factoryWAVE ; les gardes locales182 sont insuffisantes. Voir183 pour la file de reception et la reservation151 corrigees. Les conclusions de non-chevauchement et de fiabilite de150 ci-dessous sont historiques et invalidees.

Demande AveyCole25/10/2026, suite180 : le navigateur dit envoye, sans LEGACY BANK SAVED sur l'appareil. Generateur prive --bank-chunks, bank_chunks150.c, test_bank_chunks150.py et importateur prive v150. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] Test150 sur base148, sans optimisation149/147 :34messages SML2, maximum139octets, checksum individuel, ordre et transaction verifies. Sauvegarde seulement apres COMMIT complet et validation originale des32voix. Ancien protocoleSML1 et Yamaha conserves. Confirmation5s, erreurs BANK RX ERROR / INCOMPLETE BANK / BANK SAVE ERROR. La page dit explicitement qu'elle ne peut confirmer la sauvegarde. Cause physique encore inconnue.

## 1. Protocole et cadence

F0 7D S M L 02 tx cmd donnees checksum F7. Somme depuisS jusqu'au checksum incluse =0 modulo128. BEGIN0 : slot0..15,nomASCII16 ; DATA1 : index0..31,128octets ; COMMIT2 : checksum du payload4096. Nouveau BEGIN abandonne le precedent. Duplicata deja recu accepte seulement si identique ; ordre/manque/corruption interdit la sauvegarde. Etat separe DIN/USB. Aucun fichier ni reconstruction en IRQ ; service UI seulement. Navigateur attend75ms entre messages, puis2,5s avant nouvel envoi. Aucun accuseMIDI, retransmission automatique ou changementCYC/SMP. Arreter la lecture reste obligatoire. Une cadence nominale ne garantit pas l'USB reel ; essai appareil requis.

## 2. Memoire

Premiere allocation des8276octets dans BSS rejetee par le garde de chevauchement de mod_overlay_assets.py. Garde conserve. Allocation NOLOAD dediee a0x46880000, fin0x46882054, dans padding DX7 prouve libre : code termine0x4685d2f0, art commence0x46888000. Le generateur exige code_end<=46880000 et chunks_end<ART, puis BSS usuel finit0x46898630 avant overlay0x46899000. Payload zero initialise ces octets. Aucun emprunt aux buffers audio. Seuls bank.c/library.c changent d'objets ; FX/fundamentals ne changent que leurs adresses de relais DX7, verifies symbole par symbole. Bootloader/updater et autres sections exacts.

## 3. Preuves et limites

32transferts sur16slots, fichiers strictement identiques aSML1, aucune ecriture avantCOMMIT ; paquets manquants/desordonnes/checksum/transaction rejects ; doublon, abandon/retry, ancien protocole et MIDI ordinaire/realtime passes. Echec d'ecriture detecte sans succes. Confirmation5s verifiee avec bouclage compteur. Popup, QntM et retention parametres MIDI24machines/sixpistes passes. Navigateur Edge via file:// : deux transferts espaces, exclusion, deconnexion et fichier invalide, affichage mobile passes avec MIDI simule uniquement. Builds standard/adulte --check passes. [A FAIRE appareil] Meme banque vers deux slots puis retransfert ; lire confirmation ou erreur. Le principal2.47 et son importateur restent inchanges.
