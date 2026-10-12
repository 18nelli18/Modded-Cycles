# 62 — Sauvegarde des séquences B et des LFO A/B

Demande d’AveyCole dans cette conversation le 12/10/2026 : publier la sauvegarde sur Test3 puis sauvegarder également les réglages des LFO audio et MIDI. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT en émulation] Le candidat Test3 MBK3 ajoute les six configurations LFO2 audio aux données MIDI sauvegardées par pattern. Le LFO1 audio utilise toujours sa sauvegarde native. Il faut utiliser Save Project et obtenir MIDI SAVED : les éditions B et LFO2 audio ne sont pas sauvegardées automatiquement à l’extinction.

## 1. Format et compatibilité

MBK3 = en-tête32 + notes1584 + locks3120 + douze configurations LFO MIDI192 + six configurations LFO2 audio96, soit5024 octets. Le décodeur valide intégralement bornes, enums, identité et CRC avant copie. Les enregistrements MBK2 de4928 octets restent lisibles : leur LFO2 audio est initialisé OFF, profondeur neutre. La sauvegarde suivante écrit MBK3 dans la copie inactive ; l’ancienne copie reste disponible. Les anciens builds ne lisent pas MBK3.

## 2. Propriété et publication

`storage_audio_lfo.s` capture seulement `lf2_context+192..287`, jamais les phases ni les frames. Le service UI capture l’ancien pattern avant restauration du nouveau. Save capture aussi les dernières éditions du pattern actif. Le Load invalide le propriétaire avant de retirer ses banques, évitant tout accès à une banque libérée. La restauration des réglages et la remise à zéro des phases sont bornées sous IPL7 ; aucune allocation ou E/S en IRQ.

## 3. Disque et limites

Les hooks physiques read/write détectent les erreurs même lorsque la finalisation native retourne un faux succès. Une erreur persistante bloque les écritures suivantes jusqu’au redémarrage. Deux copies A/B, CRC et relecture protègent chaque pattern. Ce n’est pas une transaction atomique de tout le projet. Les fichiers annexes dans ModdedCycles restent hors du backup/export SysEx Elektron. Save As avec nouvelle identité demande de recharger le projet destination avant édition. Les modifications non enregistrées ne survivent pas au redémarrage.

## 4. Espace et preuves

La compression aPLib dense des moteurs est reconstruite depuis l’OS fourni par l’utilisateur ; aucun octet moteur n’est ajouté au dépôt. ACID et MACRO restent tous deux sélectionnables avec la sauvegarde ; la réserve disque reste de huit blocs. La compression spéciale ne s’applique que lorsque le bundle sauvegarde est sélectionné.

Preuves : `test_midi_storage_bank.py --audio-lfo` (patterns indépendants, capture Save, phases intactes, enums invalides, isolation Load et IRQ), `test_midi_storage_session.py --extended --audio-lfo --tweak …` (migration, CRC, récupération, Save natif, projets et annulation), `test_midi_bank_bundle.py --extended-storage --audio-storage` (boot TG/Syntakt et réserve), `test_midi_saving_flasher.js` (références Python/navigateur et transfert MIDI simulé). [À FAIRE] Sauvegarde, extinction, redémarrage et rechargement sur matériel. Le flasher principal reste inchangé.
