# 116 — Arpege Oct0 sur A et B

Demande AveyCole du17/10/2026 : une option0 parcourt uniquement les notes tenues, sur les deux arpegiateurs. Test `flasher-arp-zero-test`, diagnostics conserves, principal inchange. Adresses : VA OS1.13.

## En bref

[FAIT] Le reglage historique1 jouait deja uniquement les notes tenues. Le menu compte desormais les octaves ajoutees :0 = notes tenues,1 = une octave ajoutee,2 = deux,3 = trois. Aucun changement du son des anciens projets ni du format sauvegarde.

## Implementation

`gen_arp_zero_test.py` : adapte seulement le rendu A a0x4016cc6a (`pea1(a0)` devient `move.l a0,-(sp); nop`). Les octaves audio restent stockees en bits3..4 a l'octet512 du pattern.

Sur B, un wrapper20octets intercepte la comparaison de ligne apres `mlp_retrigger_value`. Pour la ligne5 seulement, soustrait1 a la valeur affichee puis rejoue `cmpi.l #2,d2` ; les autres lignes gardent valeur et flags. Stockage MIDI toujours1..4, verrous et persistence inchanges. Le wrapper se place apres le payload de beat repeat, avec gardes d'opcodes et recalcul des hashes/tailles/source du loader. Le test exige beat repeat si Banque MIDI selectionnee.

## Validation

[FAIT en emulation] `test_arp_zero.py` execute le constructeur et callbacks de menu A, changements bornes et suites UP/DOWN/UPDN/PLAY/RAND/OFF ; callback B reel et suites MIDI pour les quatre extensions. Oct0 ne sort jamais des notes tenues. Les projets ne sont pas reecrits. Builds navigateur all-midi, bank-alone, no-midi verifies.

Inclut le test curseur/phase B de la note115, encore en attente de verification physique. [A FAIRE] Jouer plusieurs notes tenues sur A puis B, tourner Oct0..3 et verifier les extensions. Les diagnostics restent reserves au test.
