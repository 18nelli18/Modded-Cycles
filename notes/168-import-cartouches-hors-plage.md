# 168 — Import de cartouches DX7 avec valeurs hors plage

Demande AveyCole du24/10/2026 : l importateur refuse certaines cartouches avec «Invalid voice parameters in slot…». Exemple fourni : `rom3a.syx`, fichier prive4104octets. Aucun octet de cartouche Yamaha ajoute au depot. Cette correction concerne la page seulement ; firmware principal2.38/v121 inchange.

## 1. Cause verifiee

[FAIT] Le fichier fourni a une entete et un checksum Yamaha valides. TIMPANI, slot20 en numerotation1–32, contient127 au niveau EG3 de l operateur2, limite99. L ancien validateur web refusait toute la banque, avec un index0–31. Le firmware LEGACY refuse aussi cette valeur : retirer simplement la garde web ne suffit pas.

## 2. Copie compatible

Le parseur verifie d abord format, taille, donnees7bits et checksum original. Une copie du payload borne les valeurs depassant les limites du validateur LEGACY : donnees EG/scaling/niveau/frequence fine99, detune14, algorithme31, onde LFO5 et transposition48. Les autres bits et champs valides restent identiques. Seul le checksum Yamaha est recalcule apres ajustement. Les noms gardent leur ordre. Aucun changement du fichier utilisateur.

La page indique le nombre de corrections et les slots1–32 concernes avant envoi. Les donnees converties utilisent le paquet SML existant, avec son propre checksum. Aucune validation firmware retiree et aucun nouveau SysEx hors protocole.

## 3. Preuves

`tools/test_legacy_import_compat.js` : les128positions du format packed, isolation de la voix cible, preservation du fichier, idempotence, checksums et refus des paquets corrompus. Avec MC_TEST_DX7_COMPAT_BANK pointant sur le fichier prive : exactement un ajustement127→99 de TIMPANI, plus checksum ;32voix conservees.

`tools/emu/test_legacy_import_compat.py` : le vrai chemin USB et parseur du121 approuve recoivent le paquet genere par le navigateur. Validation des32voix, sauvegarde dans /Legacy01.cfg puis rechargement natif, sans popup bloquant. Seules les API disque et destination MIDI precedente sont simulees. Aucun envoi MIDI physique ni nouvel essai appareil affirme.
