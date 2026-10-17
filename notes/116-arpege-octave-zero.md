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


## Retour materiel et collision (17/10/2026)

AveyCole confirme Oct0 fonctionnel sur la machine. Ne constitue pas une autorisation de promotion main. Signale V04-M0-PC40187548 a entree B, puis soupconne un lien avec arp.

[FAIT] Le placement quick-save main utilise40187528, mais ChordKeys y conserve `live[6]` (48octets), puis `prepared_modifiers` a40187558. Ce zero initial est un BSS vivant, pas de la place libre. L'ancien validateur avait accepte ces zeros a tort. `test_quick_save_room.py` execute `ck_midi_live_off` : note-off piste4 ecrase reellement le premier octet de l'instruction40187548. Ce chemin explique le lien possible avec les notes de l'arpege, sans reproduire toute la sequence UI physique.

Test2 deplace les92octets quick-save dans le payload reserve du beat repeat et retire les ecritures code/sprite du faux cave. Donnees et code ChordKeys retrouvent leur place. Le pointeur de vtable est redirige, taille loader et references recalcules. Le cas sans MIDI est aussi corrige si ChordKeys est installe. Les512combinaisons clavier quick-save et les suites arp/cursor restent verifiees. Main conserve son firmware : correction de placement a confirmer dans ce test avant promotion.


## Promotion demandee et confirmee (17/10/2026)

AveyCole : « BOTH FIXES WORKED IN TEST 2, PUSH TO MAIN ». Oct0 A/B, entree B/curseur et correction collision confirmes. Release1.83, sans diagnostics.

`gen_performance_release.py` reprend les modules confirmes de612et20octets. Si repeat est selectionne, il fournit le carrier ; sinon Banque MIDI fournit son payload compresse. Le code save92octets rejoint ce payload. Sans Banque ni repeat, un petit payload charge uniquement le wrapper save : bootstrap copie TinyGregAudio MIT deja utilise par le repeat, aucun hook audio/clavier repeat ni allocation de son buffer. La recette runtime quick-save-exit conserve le pointeur mute natif et les gardes. L'ancien tweak59dans le masque BSS est retire. Tous les placements sont demarres reellement dans Unicorn.

Le packing commun sans MIDI est aussi applicable sans repeat, uniquement en cas de capacite insuffisante, pour permettre les deux exclusions avec toutes les machines. Aucun nouveau comportement DSP. Verifications : huit compositions navigateur signees, sans diagnostic ; cursor/phase avec et sans repeat ; arpege A/B ;512cas clavier save ; ecrasement ChordKeys reproduit avant et code intact apres.

Controle generique `gen_flasher_tweaks.py --check` : catalogue historique deja divergent sur les recettes MACRO et les features ; aucune de ces recettes n est regeneree ici. Le tweak59retire ne faisait pas partie des cartes de ce generateur. Les huit compositions reelles du principal sont verifiees contre leurs empreintes de recettes et signees.
