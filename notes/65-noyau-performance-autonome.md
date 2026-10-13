# 65 — Extraire le noyau performance de Model-TG

Demande AveyCole, 12/10/2026 : séparer Model-TG tout en conservant les slides,
Scale Lock, mute verrouillé et écoute de trig, dans une nouvelle page indépendante.
Générateurs : `tools/gen_performance_core.py`, `tools/gen_performance_core_flasher.py`.
Preuves : `tools/emu/test_performance_core.py`, `tools/test_performance_core_flasher.js`.
Adresses : VA de l'OS 1.13.

## Réponse courte

[FAIT en émulation] Le noyau slide/Scale Lock se compile et démarre sans sampler.
Il occupe 5 862 octets à `0x401ab750`, contre environ 82 Ko pour Model-TG complet.
Un seul bloc cache FS de 16 384 octets est réservé : quinze restent natifs.
Le mute verrouillé et l'écoute de trig sont déjà deux tweaks autonomes.
La page `docs/flasher-core-test/` les propose avec LFO2 ; ni le flasher principal
ni Test3 ne sont écrits. Cette première page **ne contient pas encore** Sequence
Genie, SCRAMBLE, la banque MIDI, leur sauvegarde ni les moteurs supplémentaires.
Ce n'est donc pas encore le remplacement complet du pack existant.

## 1. Source et périmètre

Le générateur exige un clone propre du dépôt TinyGregAudio/Model-TG au commit
`70b39dd6787770ebefc7a2d78dea1678ec012679`. Il sélectionne ses seules routines MIT
slide/Scale Lock et leur popup ; la licence et l'attribution sont publiées avec
la page. Aucun extrait de code Elektron n'est distribué. Les anciens octets des
hooks restent des assertions de patch comme dans les autres tweaks du dépôt.

Le dispatch, le compteur audio et le clear de démarrage sont propres au noyau.
Le sampler, son mapping ACR, les effets master, le slice editor et ses menus
ne sont pas installés. Les pointeurs de menus supprimés restent nuls, conservés
comme ABI pour le futur raccordement des mods utilisateurs.

## 2. Hooks et mémoire

| Adresse | Rôle |
|---|---|
| `0x40000530` | Saut vers clear, préserve le noyau puis reprend à `0x4000053a` sans modifier la pile |
| `0x400792bc`, `0x400792f2` | Retire un bloc du cache FS natif |
| `0x4007240c` | SETTINGS et SETTINGS + trig ; autres touches inchangées |
| `0x400a7da8` | Applique la rampe avant les paramètres voix, rejoue le test/branche natif |
| `0x40059872` | Appel sortie natif puis compteur de blocs |
| `0x400169f0` | Réinitialisation des données slide |
| `0x40021f56` | Lumière double-clignotement du slide |
| `0x400551a6`, `0x40055bfa` | Préparation du slide depuis le séquenceur natif |
| `0x4002f7d8` | Scale Lock dans le menu clavier |
| `0x4008173c`, `0x40081474` | Même quantification de note pour note-on/off |

Les cinq callbacks LED sont raccordés au tick slide, sans service sampler.
Les 2 048 octets d'état slide sont dans le noyau, et non dans le buffer PCM.
Les exports incluent `blob_start` et `reserved_end` pour les futurs chargeurs.
Les frontières du clear et du cache sont vérifiées sur les instructions natives.

## 3. Vérification

[FAIT en émulation] Vrai clear complet, code préservé, pile inchangée,
initialisation native de quinze blocs cache ; 5 gammes × 12 tonalités × 128 notes.
Sans slide, les six machines d'origine donnent exactement les mêmes échantillons
que le firmware stock. Avec slide Pitch/Color/Decay, la sortie est identique à
la rampe de paramètres de référence et diffère de la sortie sans rampe.

La page utilise les mêmes builder et transfert que le principal, avec un catalogue
local limité. Seize sélections sont construites dans le navigateur, avec empreintes
par tweak et comparaison des références Python. Aucun firmware officiel ni `.syx`
produit n'est publié. Cette extraction reste expérimentale, sans validation matérielle.

## 4. Suite

[À FAIRE] Raccorder Sequence Genie, SCRAMBLE et banque MIDI aux exports du noyau,
puis leurs chargeurs/sauvegardes et les moteurs optionnels. Vérifier chaque sélection
et la coexistence avec LFO2 avant d'élargir le catalogue. Les assignations de knobs
CC et le nudge B-side natif restent à réaliser après cette séparation.
