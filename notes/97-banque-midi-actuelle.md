# 97 — Banque MIDI autonome avec les machines actuelles

Demande directe d’AveyCole, 16/10/2026 : reprendre la dernière Banque MIDI
fonctionnelle pour une installation seule ou avec les autres fonctions. Source :
conversation de cette intégration. Générateurs `tools/gen_midi_current.py` et
`tools/gen_midi_current_flasher.py`, compositeur
`docs/flasher-midi-current-test/midi-bank.js`, preuves
`tools/emu/test_midi_current*.py`. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT en émulation] La Banque RAM se construit seule et avec la sélection
complète actuelle : RETROSYN, TINY, WAVE, ChordKeys, Sample Wizard facultatif,
Second LFO et une animation au choix. Aucune machine supplémentaire imposée.
L’intégration reste **expérimentale** : aucun résultat matériel n’a été fourni
pour ce nouveau placement. La page principale n’est pas modifiée.

## 1. Origine des corps propres

Le générateur récupère les huit profils natifs sans TG de la matrice de la
[note 80](80-banque-midi-support-facultatif.md). Les bits représentent Genie,
Second LFO et SCRAMBLE ; ChordKeys vient exclusivement du côté A actuel.
L’empreinte du fichier source et celles des corps bruts sont publiées dans le
catalogue généré. Le correctif TEMPO natif courant est réassemblé depuis
`tools/machines/midi_lanes/tempo.s`. Les fonctions musicales de Banque restent
celles des profils RAM facultatifs ; il ne s’agit pas d’une copie identique
octet par octet de l’ancienne intégration liée au sampler TG.

Crédits : Banque et adaptation de ce projet ; helpers de performance
TinyGregAudio sous MIT (`LICENSE-Model-TG.txt`). Ces helpers ne réintroduisent
ni carte TG, ni moteur TG, ni dépendance d’installation TG. Le garde du main
reste chargé et interdit les recettes TG. Aucune image Elektron n’est publiée.

## 2. Placement et démarrage

Un seul append compressé commence à `0x401aa140`. Il réunit les parties des
moteurs choisis, la Banque relogée après leur zone d’exécution et les copies
des petits supports existants. Avec toutes les machines et Wizard :
destination `0x46700000`, taille brute 703 004 octets, stockage 324 554 octets.
Sans Wizard : stockage 283 671 octets. Banque seule : 21 541 octets stockés.
La borne exclusive reste `0x40200000`, contrôlée à chaque composition.

Le compositeur conserve les propriétaires A courants. Les alias partagés sont
liés par nom, y compris les adresses identiques, puis les références absolues
internes sont relogées. Les empreintes de chaque recette d’origine sont
vérifiées avant transformation ; le résultat reçoit ses références séparées.
Le catalogue de référence global n’est pas muté. Une collision non comprise
arrête le build.

`current_boot.s` recopie les supports vers leur adresse basse, conserve les
zones protégées pendant le clear BSS natif et reprend `0x4000053a`. Les moteurs
PACK conservent leur initialiseur et leurs tables SRAM ; les moteurs aPLib
conservent leur décodeur et initialisation. Le cas Wizard sans moteur utilise
le masque libéré `0x4016cae8`, avec redirection du sprite `0x400b1106`.
Le corps ChordKeys partagé à `0x401c383c` reste protégé.

Les premiers callbacks LED/UI exigent les singletons concernés ; aucun
contexte B n’est alloué avant l’ouverture explicite. Le nouveau chargeur ne
fait aucun accès fichier ni émission MIDI. Aucun hook de sauvegarde B n’est
réactivé ; Save Project conserve son comportement A seulement.

## 3. Vérifications reproductibles

```sh
python3 tools/gen_midi_current.py --check
python3 tools/gen_midi_current_flasher.py --check
node tools/test_midi_current_flasher.js
python3 tools/check_midi_current_builds.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx
python3 tools/emu/test_midi_current.py --case build/midi-current/all --scheduler
python3 tools/emu/test_midi_current_audio.py --case build/midi-current/all --baseline build/retrosyn-chord-full-wizard-all-supermodel-startup
```

Le dernier baseline est produit par `tools/test_retrosyn_chord_flasher.js` sur
le flasheur principal. Toutes les images et exports de recettes intermédiaires
restent sous `build/`, ignoré par Git.

| Vérification | Résultat / portée |
|---|---|
| Navigateur, 21 sélections | Seule, huit supports, ChordKeys, Wizard, RETROSYN, Syntakt, MACRO, ACID, complet avec/sans Wizard et deux animations ; signatures et références vérifiées |
| Boot réel, 21 sélections | Décompression, clear, cache disque et code Banque exact ; pas d’allocation B précoce |
| Clavier B | 96 notes + 96 releases sur les six canaux ; données A inchangées |
| CC relogés | Six voies / 64 pas / 12 potards, CC0/valeur0, copie/clear ; interpolation slide dans les deux sens |
| Genie si choisi | Six voies B isolées, vélocités audibles, Undo exact, données A inchangées |
| TEMPO | Appui et release transmis au menu natif |
| Scheduler seule/complet/complet natif | Vingt réveils IRQ, quarante messages IPL0, pile dédiée, pas de spin |
| Parité Python/navigateur | 21 empreintes MAIN identiques |
| Audio A contre main testé | 17 moteurs, six pistes, huit blocs chacun : échantillons identiques, Banque inactive |

Ces preuves exécutent les fonctions réellement placées dans les SYX construits
par le navigateur, et non des copies réassemblées uniquement pour le test.

## 4. Limites et matériel attendu

[À FAIRE] Tester le démarrage à froid et les contrôles sur le Model:Cycles,
les messages MIDI physiques, CC locks/slides en lecture, l’enregistrement live,
TEMPO et retour B, Genie/SCRAMBLE/LFO choisis, les 17 moteurs et Sample Wizard
avec/sans installation. Les tests de locks/slides portent sur les fonctions
de données/interpolation, pas sur toute l’édition physique ou le timing DIN.
MOVEC est observé sans modèle matériel du cache ; les périphériques et
frontières UI sont simulés ; aucune charge CPU matérielle n’est revendiquée.
Les restrictions existantes de combinaisons partielles RETROSYN restent celles
du main. B reste exclusivement en RAM, sans persistance après extinction.


## 5. Testé sur la machine (16/10/2026)

AveyCole confirme directement : « Push MIDI Out bank to main as hardware tested ».
Cette confirmation du propriétaire autorise le statut tested et la publication
au principal. Aucun détail de protocole matériel ni mesure CPU supplémentaire
n’est inventé. Les octets de démarrage, des fonctions MIDI et des moteurs restent
ceux de la page de test confirmée ; seules intégration au principal, métadonnées,
textes et documentation changent. La Banque peut être installée seule ou avec
les machines actuelles dont RETROSYN et TINY ; Sample Wizard reste facultatif.
B reste en RAM et Model-TG reste bloqué.
