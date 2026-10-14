# 75 — ChordKeys et Model-TG dans Supermodel

Demande d’AveyCole, le 13/10/2026 : intégrer le ChordKeys récent compatible
Model-TG et les ajouts de roterodamus, en conservant les commandes MIDI B déjà
validées. Générateur de récupération : `tools/gen_midi_bank_reclaim.py` ; preuve :
`tools/emu/test_midi_bank_reclaim.py`. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT en émulation] Le retrait du code disque B devenu inaccessible libère de
la place sans déplacer les données ni les fonctions musicales de la banque.
Vingt fragments sont déplacés dans ces corps inertes : 3 900 octets de masques
redeviennent disponibles. La sauvegarde MIDI reste désactivée.

[FAIT en émulation] La recette intégrée passe ses preuves ciblées. La combinaison
ChordKeys/TG/Supermodel reste **expérimentale** jusqu’à son essai matériel. Les résultats matériels
des anciennes versions ne valident pas automatiquement ce nouvel assemblage.

## 1. Sources et licences

| Origine | Révision épinglée | Portée |
|---|---|---|
| [18nelli18, PR 87](https://github.com/18nelli18/Modded-Cycles/pull/87) | `770369210cab889fd8642184632d7b9853afd33e` | Intégration MIT de ChordKeys, fondée sur Nico Heuser `c34e7973139ed8f27c46b57666b66ec84c15f8e1` ; HARMONY déplacé en slot 32, identifiant disque 33. |
| [roterodamus/Model-TG](https://github.com/roterodamus/Model-TG) | `0c567d8c9e3d0c61837e1d91ac2f5c747ea9763f` | Ajout Slice/varispeed au Model-TG de TinyGregAudio, MIT. |
| TinyGregAudio/Model-TG de la combinaison existante | `70b39dd6787770ebefc7a2d78dea1678ec012679` | Base dont les adresses exportées sont conservées. |
| 18nelli18, main | `d89267af1e3ae9b54f54572a8401c4f8c2fe3e78` | Audit du catalogue 1.54 : ses 21 fonctionnalités sont déjà représentées avant le retrait volontaire de MIDI OUT while THRU. |

Les fichiers de PR 87 portent la licence MIT du projet et de ses contributeurs.
Le crédit Nico Heuser doit rester visible. Le texte MIT de Model-TG conserve le
copyright TinyGregAudio. Les recettes ne distribuent pas d’image Elektron ; les
octets `old` restent de courts contrats de vérification sur l’OS de l’utilisateur.

## 2. Pourquoi le placement amont ne suffit pas

[FAIT] Le ChordKeys de PR 87 contient environ 13,3 Ko de code propre. La sélection
Supermodel complète laisse 4 864 octets de masques libres : plusieurs masques du
placement amont accueillent déjà Sequence Genie, LFO 2 ou SCRAMBLE.

[FAIT] Le préfixe apparemment nul `0x401aa140..0x401ab750` de l’append TG **n’est
pas une réserve disponible**. Il appartient au tampon de remplissage nul du
filesystem, et les boucles de remise à zéro TG/MIDI l’effacent au démarrage.
Déplacer uniquement la borne de clear ne supprimerait pas son usage filesystem.
Aucun nouveau code ne doit y être placé.

L’approche retenue utilise les masques réellement libérés et, si nécessaire, des
corps disque morts à l’intérieur de l’image RAM MIDI déjà chargée. Une variante
ChordKeys utilisant cette dernière réserve doit déclarer la dépendance à son
chargeur MIDI ; une recette autonome doit fournir un chargement indépendant.

## 3. Récupération de la banque RAM

| Plage disque devenue inerte | Traitement |
|---|---|
| `0x401c34b4..0x401c4818` | Reçoit les 20 fragments MIDI entiers, soit 3 706 octets. |
| `0x401c4984..0x401c5624` | Effacée ; entrée de chaque ancienne fonction conservée en RTS. |
| `0x401c56b0..0x401c5ce8` | Même traitement ; données musicales hors plage inchangées. |

Le menu TEMPO `0x401c481c..0x401c4984`, `ml_store_bank_init`, les adaptateurs LFO
audio, le live-rec et tous les états RAM restent à leurs adresses précédentes.
Le chargeur `ml_boot_copy` et le décompresseur `ml_depack` restent dans leurs
masques natifs : ils doivent fonctionner avant la copie de la banque.

[FAIT] 131 opérandes absolus sont corrigés : JMP, JSR, un callback MOVE immédiat
et une adresse de table LEA. Tout autre opcode rencontré fait échouer le
générateur. Les 198 références PC locales restent dans leur fragment entier.
Une recherche des entrées absolues et relatives refuse tout appel musical vers
les corps disque récupérés, sauf le service public déjà remplacé par RTS.
Les anciens redirects de sprites sont vérifiés avant leur retrait.

[FAIT] La taille RAM reste 58 336 octets. Le payload compressé passe de
25 567 à 23 449 octets avant l’ajout ChordKeys : 2 118 octets flash récupérés.
Le champ `midi_reclaim.free_spans` décrit les espaces restants après exclusion
des fragments et des entrées RTS. Le placement final doit vérifier sa propre
limite flash ; ce gain ne constitue pas une preuve qu’il tient automatiquement.

## 4. Vérification et limites

[FAIT en émulation] Le décompresseur ColdFire produit exactement toute l’image
RAM récupérée. Les 500 comparaisons chance/conditions avant/après donnent les
mêmes résultats. Le relais déplacé conserve les types et canaux MIDI, le running
status, le CC fragmenté intercalé avec Note Off et les SysEx de 1 024 octets.

Passent également les preuves placées des slides CC, des confirmations des
12 LFO MIDI, des locks/potards/SCRAMBLE et du menu TEMPO natif revenant à B.
Les writers physiques, certains callbacks de vues et les frontières d’allocation
restent simulés dans ces tests.

Le compilateur C m68k-elf-gcc étant absent de cette session, une relocalisation
du code **MIT propre** déjà compilé de PR 87 est étudiée. Elle ne vaut pas
recompilation vérifiée : il faut auditer les opérandes, les références PC, les
sections et les contrats des hooks, puis exécuter la vraie recette combinée.

## 5. Essais matériels à demander

- Démarrage, upgrade et récupération avec la sélection complète, USB six pistes
  activé puis désactivé.
- ChordKeys : maintien/release, harmonies, SHAPE/COLOR, notes MIDI et retour au
  mode normal ; aucun accrochage de notes ni modification des pistes B.
- Slice varispeed : note de slice fixée au trig ; PITCH change la vitesse sans
  sélectionner une autre slice ; comparaison avec les autres modes sampler.
- Banque B : notes/Note Off, CC simultanés au THRU, locks/slides, deux LFO,
  live-rec, menus et retour à B.
- Save/Load : seulement le comportement A natif ; aucune réintroduction de
  sauvegarde automatique ou de hooks disque MIDI B.

## 6. Source flash après recompression des moteurs

La recompression amont change l’adresse flash du payload MIDI sans changer son
adresse RAM. `tools/gen_midi_bank_rebase.py` modifie seulement le LEA initial de
`ml_boot_copy`, `append.at` et le symbole `ML_PAYLOAD_SRC`. Un scan à l’octet
refuse toute seconde référence à l’ancienne source, tout alias supplémentaire
ou tout contrat chargeur différent. Aucun flux compressé n’est réécrit ici.

[FAIT en émulation] Pour les candidats banque seule et banque avec ChordKeys,
la source passe de `0x401f9bce` à `0x401f8f76`. Le vrai chargeur et son
décompresseur lisent ce nouveau départ et produisent exactement 58 336 octets.
Le tampon nul filesystem `0x401a7750..0x401ab750` reste nul, avec interception
de toute tentative d’écriture. La preuve s’arrête avant le MOVEC CACR matériel ;
le clear de boot et toutes les adresses musicales sont identiques.

Preuve : `tools/emu/test_midi_bank_rebase.py`. La recette complète doit aussi
vérifier son chaînage réel d’append et l’équivalence des builders Python/JS ;
l’adresse ne doit jamais être choisie indépendamment des payloads précédents.

## 7. Intégration finale et isolation de LFO2

[FAIT en émulation] Le slot32 de PR87 remplaçait la profondeur LFO2, malgré le
son de base intact. `tools/chord_keys_slot26.py` adapte neuf instructions propres
vérifiées pour HARMONY RAM26, en conservant l’identifiant disque33 et les 33 mots
du frame audio. Model-TG réserve 26/27 à son état dans le son, sans les utiliser
comme locks ni comme paramètres DSP. Aucun champ du codec LFO2 n’est déplacé.

La preuve `test_chord_keys_lfo_isolation.py` conserve la régression slot32,
exécute 42 locks sur six LFO2 actifs, puis les codecs du son TG/LFO2 et les
rangées de locks natives. HARMONY26 et les cinq réglages LFO2 se relisent sans
modifier l’autre état. Les variantes TG normale et ST passent.

[FAIT] Les 147 unités de code MIT PR87 sont relogées sans couper leurs branches
relatives. L’audit refuse toute version autre que le digest propre épinglé,
classe 284 opérandes d’instruction et 62 pointeurs de données, et vérifie toutes
les références. 9 709 comparaisons ColdFire couvrent accords, harmonies, voicings,
gains et noms avant/après relocation. Aucun compilateur C de remplacement n’est
utilisé : ce résultat est une relocation vérifiée, pas une recompilation C.

[FAIT] Le placement ChordKeys utilise la banque MIDI RAM : la carte de ce test
demande donc ce bundle. Les autres sélections de la page principale ne changent
pas. La compression coût512 des moteurs donne 235 190 octets ; le build complet
avec ChordKeys conserve 2 504 octets avant END_LIMIT. Le compresseur navigateur
et Python donnent le même hash. Les décodeurs ColdFire relisent moteurs et banque.

[FAIT en émulation] Menus natifs, touches/pads, accords MIDI, HARMONY live-rec,
save/load A, six pistes et locks Attack/Filter/Resonance sont couverts. Le
transfert navigateur simulé envoie 689 blocs avec CRC/positions/conteneur exacts,
USB six pistes activé ou désactivé. Ce n’est pas un essai matériel.

Le banc DSP rejoue aussi la vraie boucle de copie CHORD du bootstrap MACRO :
les tables sont volontairement nulles dans le flux compressé, puis reprises
depuis la SRAM initialisée par l’OS. Omettre cette étape rendait les deux images
muettes sur CHORD, sans démontrer une différence de firmware.

Les deux demandes suivantes restent séparées de ce candidat : clear de piste
avec reset LFO/Undo commun, et suppression de trig effaçant tous les locks
(dont SCRAMBLE) sur A et B. Aucun de ces ajouts n’est revendiqué comme terminé.

[FAIT en émulation] Après reprise de la copie native des tables, la matrice finale
passe : PCM identique des six machines Keys OFF, CHORD diatonique audible Keys ON,
sept HARMONY exacts, machines ajoutées intactes, régulateur 50 % identique et
surcharge suivie d’un nouveau trig audible. Douze instances DSP, aucun accès hors
du banc. La suite ne simule pas un démarrage matériel complet ni les périphériques.
