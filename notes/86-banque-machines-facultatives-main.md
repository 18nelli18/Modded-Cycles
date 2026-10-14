# 86 — Banque main sans imposer Syntakt/MACRO/ACID

Demande d’AveyCole du 14/10/2026 : reprendre la possibilité de note78 sur le
main actuel, contenant le correctif ACID Kevin. Publication sur une page de test
avant main, selon sa demande explicite. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT] Les deux RAW Banque main de 62 016 octets restent byte-identiques,
clear/Undo LFO et clavier/LED inclus. Model-TG reste requis : aucun noyau
indépendant des tests à écran blanc ni code de sauvegarde ajouté.

Sélection Banque : Model-TG, générateur, Second LFO, SCRAMBLE, MIDI Live.
Syntakt, MACRO, ACID, ChordKeys et USB6 sont facultatifs. Ne pas sélectionner
un moteur Syntakt n’impose pas d’OS Syntakt au build.

## Démarrage

Sans moteur ajouté, l’immédiat du crochet boot en +306 passe de 0x401bf3d8
(TG) à 0x401907a4 (loader Banque). Avec les moteurs, seule sa chaîne boot
0x4016cb1a / 0x4016cb44 / 0x4016cb96 est détournée, comme note78.
La réserve flash remplie de zéros va jusqu’à la source Banque existante :
0x401f8f76 normalement ; 0x401f8f8a avec le moteur complet et ACID corrigée.
Écritures et références propres aux deux RAW, quatre boot et deux sources.
Les plafonds, tables et réservations SRAM/cache de main ne changent pas.

## Vérification

Navigateur : huit builds — Banque seule, MACRO, MACRO+ACID, ACID, Syntakt,
Select All avec/sans ChordKeys, puis extras stock avec ChordKeys.
Références strictes et conteneurs vérifiés ; les deux full restent identiques
au main ACID matériellement testé. Le navigateur n’impose ni ChordKeys ni USB6.

Émulation : tools/emu/test_optional_midi_boot.py, hash Python exact puis vraie
chaîne TG/moteurs/loader ; RAW copié intégralement. MOVEC observé sans simuler
la cohérence physique du cache. Nouveau port sur main à vérifier sur matériel.

Générateur : tools/gen_main_bank_optional_machines.py. Le builder Python
versionné sur main possède déjà les mêmes réserves bornées de note78.
Le retrait des dépendances TG et l’intégration Model909/WAVE restent distincts.
