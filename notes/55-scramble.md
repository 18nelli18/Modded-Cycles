# 55 — SCRAMBLE indépendant

Demande d’AveyCole, conversation des 10–11/10/2026 : SETTINGS + TRACK,
un seul tirage des quatre contrôles machine et cartouche SCRAMBLE, sans menu.
Adresses : VA de l’OS 1.13. Générateur `tools/gen_scramble.py`, preuve
`tools/emu/test_scramble.py`. Proposé seulement dans le flasher de test 2.

## 1. Comportement

Code indépendant du générateur de séquence, sans allocation ni menu sonore.
Quatre contrôles machine seulement ; decay, pan et séquence ne sont pas touchés.
Sampler exclu. Pas de Undo sonore. Le crash de l’ancien Random sound a été
signalé lors d’une sélection dans son menu, tous mods activés ; sa cause
reste inconnue. Ce nouveau chemin ne démontre pas la cause de cet incident.

## 2. Route OS vérifiée

`[FAIT en émulation]` `0x4000f2a2` reçoit un CC MIDI et une valeur entière,
pas un descripteur et une valeur 8.8. Les slots 11–14 sont résolus par
`0x4005a692`, leurs bornes par `0x4005a65a`, le CC par `0x4005a7f8` et
la correspondance inverse contrôlée par `0x4005a8ce`. Les quatre résultats
sont préparés avant les écritures. `SoundParameterContext` utilise sa vraie
vtable `0x400fd134`, son setter natif et ses notifications typées.

Le hook touche chaîne Model-TG → générateur éventuel → SCRAMBLE ; les variantes
`-gen` et `-gen-queued` visent le symbole exact de chaque générateur.
La répétition du même événement ne retire pas un deuxième son ; le release
reste consommé après relâchement de SETTINGS. Contexte UI seulement.

## 3. Espace, provenance, preuves

785 octets dans sept masques, références uniques redirigées et contenu stock
vérifié. Le générateur exclut les masques de tous tweaks canoniques, du
générateur séquence seul et de sa variante différée. Source originale ;
Model-TG de TinyGregAudio, MIT, commit `70b39dd6787770ebefc7a2d78dea1678ec012679`.

Preuves : six pistes × six machines stock sur les deux bases ; combinaison
maximale et douze machines de synthèse. Quatre paramètres seuls modifiés,
bornes natives, quatre notifications, un popup ; Sampler refusé.
La sélection du contexte sans verrous, les observateurs externes et le popup
restent simulés dans cette preuve. Démarrage complet et comportement matériel
à confirmer. Aucun résultat matériel revendiqué pour SCRAMBLE.

## 4. Incident matériel et correction (11/10/2026)

AveyCole signale `EXCEPTION v03-M0-P4018B1C6`. `[FAIT]` Dans le build
publié, cette adresse est exactement `move.l d0,(0,a4,d2.l*8)` du premier
stockage de descripteur. Le facteur huit est interdit sur ColdFire et provoque
le vecteur 03 : voir [manuel NXP MCF54455, Address Error Exception](https://www.nxp.com/docs/en/reference-manual/MCF54455RM.pdf).
Unicorn accepte ce mode 68000, donc la preuve précédente ne détectait pas
cette incompatibilité ISA. Les mêmes modes existaient dans le prototype
sonore retiré ; cela constitue une cause possible de son incident, sans
rapport d’adresse permettant de le confirmer.

Correction : parcours des quatre paires par pointeur `a4`, incrément de huit
octets et réinitialisation avant application. Aucune adresse indexée facteur
huit ne subsiste dans SCRAMBLE. Taille : 783 octets, sept masques. Le générateur
contrôle le désassemblage compilé et refuse les index mots ou facteur huit ;
la preuve conserve l’instruction fautive comme cas de régression refusé.
Le correctif reste expérimental, à retester sur matériel.

## 5. Testé sur la machine (11/10/2026)

AveyCole : « Scramble is now functional », avec demande explicite de publication
au flasher principal. Promotion de SCRAMBLE seul ; génération différée toujours
expérimentale, nouveau refus « Check range/stop » signalé. Les variantes
principales chaînent le générateur principal, pas celui du test 2.
