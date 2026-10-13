# 73 — Démarrage SUPERMODEL by A.V.

Demande d’AveyCole, conversation du 13/10/2026 : titre SUPERMODEL et petite signature « by A.V. » sous le titre à droite. Animation exclusive de Modded Cycles, prioritaire dans Select All sur la page test. Adresses : VA de l’OS 1.13.

## En bref

[FAIT en émulation] Animation originale, même durée et contrat natif ; aucun besoin d’espace compressé supplémentaire. Flasher principal inchangé. Vérification matérielle encore attendue.

## 1. Implantation

Le générateur `tools/gen_boot_supermodel.py` assemble `tools/machines/boot_supermodel/boot_supermodel.S`. Les 696 octets remplacent le corps de tâche à `0x40053a6c`, dans son emplacement de 1 032 octets avant `0x40053e74`. Fonte 5 × 7 originale, titre doublé, signature petite alignée à droite. 80 images à 50 Hz puis dix ticks d’attente : même durée de 1,8 s. Timer, sémaphores et signal de fin natifs conservés. Aucun tas ni sortie LED.

## 2. Sélection

La recette `supermodel-startup` déclare un conflit avec `boot-anim`. Les deux cartes s’excluent aussi dans la page. Select All préfère SUPERMODEL. La dépendance du bundle MIDI à l’ancienne animation était seulement une sélection de catalogue ; elle est retirée dans cette page, sans changer ses écritures ni sa charge utile. Tous les autres mods sont conservés.

`tools/gen_supermodel_startup_test.py` reproduit la page depuis le candidat de sauvegarde et les deux OS officiels fournis par l’utilisateur. Il exporte les choix réels du navigateur avec `tools/export_supermodel_test_catalog.js`, puis calcule les références Python avec/sans USB6. Aucun firmware n’est distribué.

## 3. Preuves

`tools/emu/test_boot_supermodel.py` compare les 80 images natives pixel par pixel au rendu propre, vérifie le contrat stock, les écritures bornées et le refus des deux animations. La même tâche est vérifiée avec la banque MIDI et tous les mods sélectionnés. Le flasher vérifie les deux empreintes Python, le transfert intégral de 686 blocs, les exclusions visuelles, la priorité Select All et les textes EN/FR. Marge restante : 2 467 octets. La reprise de sauvegarde du candidat précédent reste incluse et n’est pas modifiée par l’animation.

[À FAIRE] Vérification matérielle de l’animation et de la persistance physique des fichiers CC après extinction.
