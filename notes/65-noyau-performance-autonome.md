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

## 5. Raccordement du pack MIDI (12/10/2026)

[FAIT en émulation] `tools/gen_core_midi_bundle.py` raccorde les sources actuelles
Sequence Genie, SCRAMBLE, LFO2 et banque MIDI au même noyau. Le générateur de banque
existant est réutilisé pour compiler, sans modifier ses sorties ni les anciennes
pages. Ses nouveaux bindings sont fournis seulement pendant cette compilation.
Les sources stock du firmware ne sont jamais embarquées dans la charge publiée.

La banque complète (conditions, retrigger/arp, clipboard, LFO CC, MBK4,
autosave working et live recording) occupe **44 048 octets**, à `0x401ace40`.
Avec le noyau, elle réserve **quatre blocs cache**, laissant **douze** blocs natifs,
contre sept dans le précédent candidat TG à neuf blocs réservés. La source
compressée se situe après ces quatre blocs, à `0x401bb750`, et ne chevauche pas
sa destination. Elle fait 21 561 octets ; la marge sous `0x40200000` est 259 191
octets. Le clear préserve le code noyau + banque et retire le mapping PCM ACR1
du boot hérité : aucun sampler n'est installé.

Le pack navigateur `performance-midi-core` aplatit les écritures successives et
les deux charges utiles en une recette unique. Le générateur vérifie que son
image est identique à la chaîne de composants, octet par octet. Cette recette
n'a **aucune dépendance Model-TG**, et n'embarque ni Syntakt, ni ACID/MACRO, ni
sampler/préécoute. Elle inclut aussi les tweaks autonomes mute verrouillé,
apercu de trig, arpégiateur et Live MIDI OUT + THRU. Le plus petit noyau seul
reste une autre sélection sur la nouvelle page ; `Select all` choisit le pack.

`tools/emu/test_core_midi_bundle.py` exécute boot/décompression/invalidation,
cache natif, getters, banque par pattern, transport, conditions et ordonnanceur,
puis réutilise les preuves Genie B, LFO CC et session de stockage avec **ces**
adresses. Genie Generate/Undo et Euclide restent limités à B, sans modifier A.
Les douze LFO MIDI émettent leurs CC sur les six canaux et les mutes purgent les
messages différés. Le nouveau test `test_core_midi_lfo_cc.py` accepte `--pattern-settings`
pour initialiser les réglages MBK2/3/4 à leur adresse réelle plutôt que l'ancienne
configuration RAM seule. Les preuves de session couvrent WRK/SEQ, migration,
identité de projet, publication protégée et reprise sur erreur ; FS simulé.

[À FAIRE] Validation matérielle du nouveau layout, persistance réelle et timing
MIDI ; réintégration des moteurs optionnels, puis knobs CC assignables et nudge
B-side natif. Les anciennes pages principale et Test3 sont inchangées.
