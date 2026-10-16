# Provenance des tweaks

| Fichier | Auteur | Origine |
|---|---|---|
| `52-lfo-secondary.json` | ce projet, page adaptée de TinyGregAudio | Assembleur original `tools/machines/lfo_secondary/`, généré par `tools/gen_lfo_secondary.py` ([note 58](../../notes/58-second-lfo.md)). Construction/destruction de page adaptée de Model-TG commit `70b39dd` (MIT, [licence](LICENSE-Model-TG)). Appelle le LFO natif sans distribuer son code. Testé sur machine par AveyCole le 11/10/2026, proposé au flasher principal ; réglages RAM uniquement. |
| `01-latching-mute.json`, `02-trig-preview.json`, `03-browser-scroll.json` | drumkilla | [drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks), commit `6e0b4df`, `tweaks/model-cycles_OS1.13/`. Repris **sans modification** (licence MIT, texte dans [`tools/mtlib/LICENSE`](../../tools/mtlib/LICENSE)), sauf `02-trig-preview.json` : une retouche de ce projet, 3 octets en `0x40148a30` (`tst.l d0 ; bne.w` devient `lsr.l #1,d0 ; bcs.w`, l'écoute accepte le séquenceur en pause) et une ligne de description ([note 34](../../notes/34-ecoute-en-pause.md)). |
| `10-6ch-multiout.json` | d'après scottmetoyer | Table de patchs de [scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output) (MIT), cible Cycles, mise au format tweak ([note 01](../../notes/01-ms-multi-output.md)). |
| `11-6ch-usbup.json` | ce projet | Dérivé de `10-6ch-multiout` par `tools/relocate_6ch.py` ([note 13](../../notes/13-6ch-upgrade-usb.md)). |
| `30-model-tg.json` | TinyGregAudio | [TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG), version `v1.1.0` (commit `70b39dd`), construit par son propre `build.py --modded-cycles` pour ce flasher (son `docs/PAYLOAD.md`) depuis une copie de sa source avec trois retouches de ce projet (`MC_PATCHES` de `tools/gen_model_tg.py` : en mode mute, chaque touche de piste mute tout de suite, au lieu d'attendre la sortie du mode, [note 31 §10](../../notes/31-model-tg.md) ; sa copie de `02-trig-preview.json` reçoit la même retouche que la nôtre, [note 34](../../notes/34-ecoute-en-pause.md) ; avec l'audio USB multipiste, une piste mutée n'est plus coupée net sur sa piste USB, [note 35 §3](../../notes/35-glitches-usb-multipiste.md)), généré par `tools/gen_model_tg.py`, plus l'envoi à l'USB à heure fixe de ce projet (`tools/usb_steady.py`, le même que dans `11-6ch-usbup.json`) et sa division des pistes par 2 plus courte (`tools/voice_loop.py`, [note 36](../../notes/36-regulateur-sans-coupures-inutiles.md)) ; l'identifiant, l'ordre, le nom, la description et la liste des incompatibilités sont aussi les nôtres. Licence MIT, texte dans [`LICENSE-Model-TG`](LICENSE-Model-TG). Empreinte du MAIN OS : `aa0740d7…` ; sans nos ajouts, `a049d724…`, celle que son auteur annonce pour la v1.1.0. |
| `30-model-tg-st.json` | TinyGregAudio, quatre retouches de ce projet | Même source et même build que `30-model-tg.json`, avec les mêmes retouches et le même envoi à heure fixe, et une ligne de plus changée (`REGION_END`, sa zone d'échantillons s'arrête 1 Mo plus bas, `ST_PATCHES` de `tools/gen_model_tg.py`), plus les adresses de ses symboles (dont l'état de ses slide trigs, pour nos tests). Base de la version combinée avec les moteurs du Syntakt (`31-syntakt-tg-….json`, ce projet), [note 31 §4](../../notes/31-model-tg.md). Licence MIT. |
| `20-sdvintage-snare.json` | ce projet | Compilé depuis `tools/machines/sdvintage/` par `tools/gen_sdvintage.py` ([note 14](../../notes/14-machine-sd-vintage.md)). |
| `25-macro.json`, `32-macro-tg.json` | Émilie Gillet (Braids), passerelle de ce projet | Machine MACRO : le code de Braids, le module d'Émilie Gillet ([pichenettes/eurorack](https://github.com/pichenettes/eurorack), commit `08460a6`, sous-module stmlib `e3bd7c9` ; fichiers `braids/macro_oscillator`, `analog_oscillator`, `digital_oscillator`, `resources` et `stmlib/utils/random`), compilé **sans modification** avec la passerelle de ce projet (`tools/machines/macro/macro.cc`, `rt.c`) par `tools/gen_macro.py`. Licence MIT, texte dans [`LICENSE-Braids`](LICENSE-Braids) (recopié à côté du flasher). La machine ne porte ni le nom du module ni celui de Mutable Instruments ; la carte du flasher et le guide disent d'où vient le code ([note 43](../../notes/43-machine-macro.md)). |
| `33-sample-preview.json`, `33-sample-preview-st.json` | ce projet | Écoute des samples dans le navigateur avec le Sampler de Model-TG : assemblée depuis `tools/machines/sample_preview/` (`sample_preview.S`, `sample_preview.ld`) par `tools/gen_sample_preview.py`, dans quatre masques de sprites 47×47 libérés (`0x40183118`, `0x40185018`, `0x40185968`, `0x40185c58`, `tools/sprites.py`, partagés avec Chord Keys qui exclut Model-TG) ; deux fichiers aux écritures identiques, l'un sur `model-tg`, l'autre sur `model-tg-st` ([note 46](../../notes/46-ecoute-des-samples.md), preuve `tools/emu/test_sample_preview.py`). S'appuie sur Model-TG de TinyGregAudio (MIT) : appelle ses fonctions aux adresses de ses symboles (exportés par `tools/gen_model_tg.py` dans les `symbols` de `30-model-tg*.json`), sans copier son code ; son accroche vide en `0x4008171e` (`pad_load_hook`) est remplacée par la nôtre, qui rejoue les deux instructions qu'elle déplaçait. |
| `40-arp.json` | ce projet | Arpégiateur à la place du retrig : compilé depuis `tools/machines/arp/` (`arp.c`, `arp_hooks.S`, `arp.ld`) par `tools/gen_arp.py`, dans quatre masques de sprites libérés (`0x4018a788`, `0x4016cba8`, et les masques 47×47 `0x40189930`, `0x4018a220`, `tools/sprites.py`). Réglages dans l'octet +512 de la piste du pattern, inutilisé par l'OS ([note 32](../../notes/32-arpegiateur.md)). |
| `41-trig-hold.json` | ce projet | Plus de temps pour effacer un trig (défaut de l'OS d'origine) : assemblé depuis `tools/machines/trig_hold/` (`trig_hold.S`, `trig_hold.ld`) par `tools/gen_trig_hold.py`, au début du masque de sprite libéré `0x4015c044` (`tools/sprites.py`), devant les stubs de `6ch-usbup` ([note 33](../../notes/33-effacer-un-trig.md)). |
| `42-tempo-max.json` | ce projet | Tempo jusqu'à 546 BPM au lieu de 300 : onze constantes (bornes du tempo et contrôles au chargement) et la remise dans le cycle du LFO en boucle, écrites par `tools/gen_tempo_max.py` d'après le MAIN OS officiel ([note 38](../../notes/38-tempo-546-bpm.md)). |
| `43-boot-anim.json` | ce projet | Animation de démarrage « modded-cycles » d'après le logo du site : assemblée depuis `tools/machines/boot_anim/` (`boot_anim.S`, `boot_anim.ld`) par `tools/gen_boot_anim.py`, à la place du corps de la tâche d'animation de démarrage de l'OS (`0x40053a6c`) ; police et dessin propres au projet ([note 39](../../notes/39-animation-demarrage.md)). |
| `44-midi-both.json` | ce projet | Avec THRU sélectionné, conserve le relais entrant de l'OS et neutralise les trois portes qui bloquaient l'émission générée ; le sélecteur OUT/THRU reste celui d'origine. Généré par `tools/gen_midi_both.py` ([note 50](../../notes/50-midi-out-thru.md)). |
| `45-midi-live-both.json` | ce projet | FUNC + appui sur le knob LEVEL/DATA, quand THR est affiché, bascule l'émission générée tout en gardant le relais MIDI entrant et l'affichage THR ; généré par `tools/gen_midi_live_both.py`, testé sur Model:Cycles par l'utilisatrice le 10/10/2026 ([note 50](../../notes/50-midi-out-thru.md)). Exclut `midi-both` et `midi-bth-three-state`. |
| `24-syntakt-<moteurs>-macro.json`, `31-syntakt-tg-<moteurs>-macro.json` (62 variantes) | [18nelli18/Modded-Cycles#70](https://github.com/18nelli18/Modded-Cycles/pull/70), code MACRO Braids d’Émilie Gillet (MIT) | Builds combinés générés par `tools/gen_macro_syntakt.py` ; moteurs du Syntakt conservés, MACRO ajoutée après eux ; charge utile compressée avec aPLib ; configuration testée sur machine : Model-TG + cinq moteurs ; autres choix expérimentaux ([note 51](../../notes/51-macro-avec-moteurs-syntakt.md)). |
| `48-multiline-browser.json` | adapté de [18nelli18/Modded-Cycles#52](https://github.com/18nelli18/Modded-Cycles/pull/52), d'après l'idée d'un membre de la communauté | Navigateur multi-ligne dans le masque 47×47 libéré `0x401904b4`, sans chevauchement avec les mods MIDI locaux ; sources et générateur conservés dans ce dépôt (`tools/machines/multiline_browser/`, `tools/gen_multiline_browser.py`), avec la preuve d'émulation upstream ([note 40](../../notes/40-navigateur-multiligne.md)). |

SHA-256 des fichiers de drumkilla, identiques à ceux du dépôt d'origine (sauf `02-trig-preview.json`, retouché) :

```
21de02b88903b2012c88f31ef3b593afa0b37f48c22884986961cee0fb5b0f47  01-latching-mute.json
fe7fb5218336272af8bb88a274d37ff249ab98415b2e327d2a49ae116da7b038  02-trig-preview.json   (d'origine)
ff53eb5def759c1fe3654522309b45b939e190e15a3e3e037eb39a8ae85665a8  02-trig-preview.json   (retouché, note 34)
fbfa29a8873e18831d860ae489440e89c308612437379589d5ed7fc670d5d234  03-browser-scroll.json
```

Autre ajout de notre côté : l'entrée `cave_refs_ok` de `device.json`, qui explique pourquoi l'écriture de `browser-scroll`
dans la table de glyphes de la police de chiffres est sans danger ([note 15 §2](../../notes/15-demandes-reddit.md#point-technique--une-exception-au-contrôle-des-caves)).

| `46-level-pan-values.json` | adapté de [18nelli18/Modded-Cycles#53](https://github.com/18nelli18/Modded-Cycles/pull/53), mod de djd_oz | Volume et pan numériques sur l'écran principal, pas de LEVEL/DATA de 1 ; assembleur dans le masque de sprite `0x4018f4b4` (`tools/gen_level_pan.py`, note 44). Testé sur Model:Cycles en amont. |
| `47-trigless-dim.json` | adapté de [18nelli18/Modded-Cycles#53](https://github.com/18nelli18/Modded-Cycles/pull/53), mod de djd_oz | LED des trigless trigs atténuée, clignotement conservé ; interruption du panneau, masque de sprite `0x40192734` (`tools/gen_trigless_dim.py`, note 45). Testé sur Model:Cycles en amont. |

## Générateur de séquence — flasher de test uniquement

`49-scale-gen.json` / `49-scale-gen-st.json` : générateur et accroche originaux,
page adaptée de Model-TG (TinyGregAudio, commit `70b39dd6787770ebefc7a2d78dea1678ec012679`,
MIT, `LICENSE-Model-TG`). Génération de notes/trigs en gamme et Undo, à la demande
d'aveycole ; `tools/gen_seq_gen.py`, sources `tools/machines/seq_gen/`, note 53.
Statut expérimental, aucune validation matérielle ; seulement dans `docs/flasher-test/`.

Variante de test `experimental/scroll/49-scale-gen*.json` : même origine TinyGregAudio/Model-TG (MIT), mise en page à quatre lignes défilantes dans les mêmes masques, générée par `tools/gen_seq_gen.py --scroll` (notes/53 §10). Réservée au flasher de test ; affichage matériel en attente.

Le 10/10/2026, AveyCole confirme le menu défilant sur machine. Les variantes de `experimental/scroll/` sont promues dans `49-scale-gen*.json` ; le générateur assemble ce menu par défaut. Voir notes/53 §11.

Variante expérimentale du générateur (10/10/2026) : PLAY/STOP dans la page,
velocity/decay/pan optionnels. Code original de ce fork ; construction de page
adaptée de Model-TG (TinyGregAudio, MIT, pin inchangé). Générateur
`tools/gen_seq_gen.py --dynamics`, preuve `tools/emu/test_seq_gen_dynamics.py`,
notes/53 §12. Test flasher seulement, résultat matériel attendu.

Transport et variations du générateur : test matériel confirmé par AveyCole le 10/10/2026, promus au catalogue principal 1.45 sans changement des écritures validées.

### Générateur étendu expérimental — 10/10/2026

`experimental/advanced/49-scale-gen*.json`, assemblage original Codex à la demande
d’AveyCole ; base de la page adaptée de TinyGregAudio/Model-TG (MIT, commit
70b39dd). Plages, modes de régénération, mutation, Euclid, tirage du son, mutes
et cartouche : `tools/gen_seq_gen.py --advanced`, notes/54. Catalogue autonome
`docs/flasher-test/`, aucun changement du principal. Preuves émulation et
navigateur ; pas de résultat matériel pour ces extensions.

Remplacement expérimental séquence seul : `experimental/sequence-only/`, même
origine et licence, `--advanced --sequence-only`. Suppression complète des routines
son ; cartouche agrandi avec glyphes originaux. 6238 octets / 48 masques, notes/54
§7. Preuves émulation/navigateur ; validation matérielle attendue.

| Fichier | Auteur | Origine |
|---|---|---|
| `experimental/scramble/50-scramble*.json` | ce projet ; popup Model-TG de TinyGregAudio (MIT) | Source originale `tools/machines/scramble/scramble.s`, générateur `tools/gen_scramble.py`, [note 55](../../notes/55-scramble.md). Model-TG épinglé à `70b39dd6787770ebefc7a2d78dea1678ec012679`. Six variantes de chaîne, test flasher 2 uniquement. |
| `experimental/queued/49-scale-gen*-queued.json` | ce projet ; page adaptée de Model-TG (TinyGregAudio, MIT) | Source `tools/machines/seq_gen/queue.s`, générateur `tools/gen_seq_gen.py --advanced --sequence-only --queued`, [note 56](../../notes/56-generation-differee.md). Préparation privée et copie à la frontière anticipée ; expérimental, test 2 uniquement. |

SCRAMBLE principal : sources originales `tools/gen_scramble.py --main`, Model-TG TinyGregAudio (MIT), notes/55 ; quatre variantes compatibles avec le générateur principal. Confirmé matériel par AveyCole le 11/10/2026.

Extensions du test 2 (11/10/2026) : `tools/machines/scramble/steps.s` est original,
avec setters de marque natifs et locks temporaires par événement ; cartouche
SCRAMBLE élargi, sans modifier les variantes principales testées. L'intro
SEQUENCE GENIE utilise des glyphes originaux dans `intro_large.s`. La génération
différée vérifie la vraie banque de lecture et les modes commun/par piste.
Générateurs `gen_scramble.py` et `gen_seq_gen.py`, notes 55/56. Expérimental.

SCRAMBLE par pas : code original, hook constructeur événement et marqueur de trig, note 55 ; dépend de Model-TG (TinyGregAudio, MIT). Testé sur machine par AveyCole le 11/10/2026 et promu au flasher principal sur sa demande.

## Synchronisation upstream 1.46 (11/10/2026)

Origine : 18nelli18/Modded-Cycles, commit `03941fd029e1730125463946b6d91f7ce8e28bee`. Sources, générateurs et preuves conservés.

| `25-macro.json`, `32-macro-tg.json` | Émilie Gillet (Braids), passerelle de ce projet | Machine MACRO : le code de Braids, le module d'Émilie Gillet ([pichenettes/eurorack](https://github.com/pichenettes/eurorack), commit `08460a6`, sous-module stmlib `e3bd7c9` ; fichiers `braids/macro_oscillator`, `analog_oscillator`, `digital_oscillator`, `resources` et `stmlib/utils/random`), compilé **sans modification** avec la passerelle de ce projet (`tools/machines/macro/macro.cc`, `rt.c`) par `tools/gen_macro.py`. Licence MIT, texte dans [`LICENSE-Braids`](LICENSE-Braids) (recopié à côté du flasher). La machine ne porte ni le nom du module ni celui de Mutable Instruments ; la carte du flasher et le guide disent d'où vient le code ([note 43](../../notes/43-machine-macro.md)). |
| `24-syntakt-<moteurs>-macro.json`, `31-syntakt-tg-<moteurs>-macro.json` | Émilie Gillet (Braids), passerelle de ce projet | Machine MACRO avec les moteurs du Syntakt, produits par `tools/gen_macro_syntakt.py` ([note 50](../../notes/50-macro-avec-moteurs-syntakt.md)) : la partie des moteurs est celle de `24-syntakt-<moteurs>.json` / `31-syntakt-tg-<moteurs>.json` (passerelle et régulateur repris octet pour octet ; code du Syntakt extrait **au build** de TON `Syntakt_OS1.42.syx`, aucun octet Elektron dans le JSON), la partie MACRO est compilée comme `25-macro.json` (même code de Braids, sans modification, licence MIT, [`LICENSE-Braids`](LICENSE-Braids)) ; la charge utile est rangée compressée et décompressée au démarrage. |
| `45-chord-keys.json` | Nico Heuser ([byNicoHeuser](https://github.com/byNicoHeuser)), [PR #46](https://github.com/18nelli18/Modded-Cycles/pull/46) | Clavier d'accords diatoniques sur une piste CHORD : TRIG 1–7 jouent I–VII, 8–14 les mêmes une octave plus haut, 15–16 I–II deux octaves plus haut ; T1–T6 gardent leurs commandes d'origine. Menu FUNC + RETRIG (Keys, Root, Scale, extension par degré), réglages dans les octets réservés de l'en-tête du pattern ; SHAPE choisit la disposition (BASE, CLS0–3, OPN0–3), COLOR le mélange des voix. Sources originales `tools/machines/chord_keys/`, générateur `tools/gen_chord_keys.py` (m68k-elf-gcc 16.2), code ColdFire dans quatorze masques 47×47 identiques redirigés. Aucune source tierce ajoutée. [Note 42](../../notes/42-clavier-accords-diatoniques.md), preuve `tools/emu/test_chord_keys.py`. Correction du relâchement avalé par ce projet (07/10/2026, note 42 §16, preuve `tools/emu/test_chord_keys_release.py`). Testé : par Nico seul (06/10/2026), puis par Maxime seul et avec six mods (07/10/2026), version corrigée comprise (10/10/2026). |
| `48-track-filter.json` | ce projet | Filtre par piste passe-bas / OFF / passe-haut, demandé sur le serveur Discord (forum feature-requests, 05/10/2026) : assemblé depuis `tools/machines/track_filter/` (`track_filter.S`, `tf_ui.S`, `track_filter.ld`) par `tools/gen_track_filter.py`, dans quinze masques de sprites 35×35 libérés (`tools/sprites.py`) ; lois de fréquence et de résonance du Model:Samples, recalculées par formule (aucun octet de son OS) ([note 47](../../notes/47-filtre-piste.md)). |
| `50-midi-both.json`, `51-midi-live-both.json` | AveyCole | [AveyCole/Modded-Cycles](https://github.com/AveyCole/Modded-Cycles), commit `ba5f8bb` (`tools/gen_midi_both.py`, `tools/gen_midi_live_both.py`, `tools/machines/midi_live_both/`), testés par AveyCole sur son Model:Cycles le 10/10/2026. Le fork n'indique pas de licence : à confirmer avec AveyCole avant la fusion. `midi-both` est repris octet pour octet (les trois portes de sortie MIDI du mode THR). `midi-live-both` : mêmes écritures et même code (132 o, identique octet pour octet), mais lié dans le masque de sprite 34x34 libéré `0x40192ba4` au lieu de `0x40167c50` (un des masques 35×35 restés libres dans le groupe qu'occupe le filtre par piste de la PR #55) ; source réécrite dans `tools/machines/midi_thru/`, générés par `tools/gen_midi_thru.py`, preuve `tools/emu/test_midi_thru.py` qui compare aussi avec la version du fork ([note 53](../../notes/53-midi-thru-aveycole.md)). |


## Banque MIDI expérimentale (11/10/2026)

`experimental/midi-bank/60-midi-bank-bundle.json` : code original de ce
projet dans `tools/machines/midi_lanes/`, généré par
`tools/gen_midi_bank_bundle.py`. Le chargeur/remise à zéro dans `boot.s`
est adapté du boot Model-TG de TinyGregAudio, MIT (`LICENSE-Model-TG`),
commit `70b39dd6787770ebefc7a2d78dea1678ec012679` ; le payload TG reste
inchangé. Installateur séparé `docs/flasher-midi-test/`, générateur
`tools/gen_midi_test_flasher.py`, preuves `tools/emu/test_midi_lane_*.py`,
`test_midi_bank_bundle.py` et `tools/test_midi_flasher.js`. Voir note 57 §19.
Aucun firmware Elektron distribué ; sources OS locales exigées. Banque RAM
seulement, expérimental, non testé sur matériel à cette date.


### Extension Genie côté B (12/10/2026)

`genie.s` et `genie_router.s` : adaptateurs originaux de ce fork autour
des algorithmes de Sequence Genie déjà présents, pour les six voies MIDI.
Aucune donnée ni routine Elektron copiée : appels résolus depuis la recette
existante et génération depuis les OS locaux. Candidat expérimental dans
`docs/flasher-midi-controls-test/` ; voir note 59 §9. Le mute MIDI seul a
été validé sur matériel par AveyCole ; Genie B et sortie rétablie restent
à tester. Sauvegarde persistante non incluse.

## Intégration Supermodel expérimentale du 13/10/2026

| Variante | Auteur | Origine |
|---|---|---|
| Variante ChordKeys Supermodel | Nico Heuser ; intégration 18nelli18 ; adaptation A.V. | MIT, PR87 `770369210cab889fd8642184632d7b9853afd33e` (source Nico `c34e7973139ed8f27c46b57666b66ec84c15f8e1`). Recette propre relogée, HARMONY RAM26 / ID disque33 pour isoler LFO2. Variante expérimentale utilisant le chargeur Banque MIDI, sauvegarde B désactivée. [Note 75](../../notes/75-chord-tg-supermodel.md). |
| Model-TG Slice varispeed | TinyGregAudio ; roterodamus ; adaptation A.V. | MIT, delta roterodamus `0c567d8c9e3d0c61837e1d91ac2f5c747ea9763f` sur base `70b39dd6787770ebefc7a2d78dea1678ec012679`, adresses exportées conservées. Une tranche choisie au trig, PITCH règle sa vitesse. Expérimental ; [Note 75](../../notes/75-chord-tg-supermodel.md). |
| Récupération / réadressage Banque MIDI RAM | ce projet | Vingt fragments propres relogés dans les corps disque inertes ; source flash réadressée après recompression. Aucun hook Save/Load B réactivé. Générateurs `gen_midi_bank_reclaim.py` / `gen_midi_bank_rebase.py`, preuves natives et [note 75](../../notes/75-chord-tg-supermodel.md). |


| Recettes RETROSYN 27, 28, 29, 37 | Coeur fourni par AveyCole ; passerelle ce projet | Archive retrosyn-core.tar.gz, sans licence declaree ; note 96. Generateurs tools/gen_retrosyn*.py. Les combinaisons reprennent les corps existants de MACRO, ACID, WAVE et TINY et leurs credits/licences. Aucune image Elektron incluse. |
| 20-sample-wizard.json | TinyGregAudio, roterodamus, A.V. | Recette Sample Wizard independante du catalogue main existant, extraite par gen_retrosyn.py --wizard-catalog ; licence LICENSE-Sample-Wizard.txt et credits existants conserves. |

| Banque MIDI autonome actuelle (page de test) | Ce projet ; helpers de performance TinyGregAudio | Huit profils RAM sans moteur TG de la matrice note 80, empreinte source et corps epingles ; correctif TEMPO reassemble, compositeur actuel et nouveau chargeur. MIT et credits existants conserves. Aucun firmware Elektron inclus. [Note 97](../../notes/97-banque-midi-actuelle.md). |

| MPI1 — persistance MIDI actuelle | Ce projet ; noyau RAM et helpers MIT credites note 97 | Nouveau codec/journal C et detours ABI propres, lies par relocations ELF aux backends existants. Aucune routine ou image officielle exportee. Sauvegarde sur slot vide et reprise confirmees sur machine par AveyCole le 16/10/2026 ; principal 1.72. Charger le MIDI en entrant cote B, lecture arretee. [Note 98](../../notes/98-persistance-midi-actuelle.md). |
| Control All Beat Repeat (principal 1.73) | TinyGregAudio, algorithme `rtg_*` MIT ; nouvelle adaptation autonome AveyCole / Modded-Cycles | Historiques audio/grille/fondus inspires de `docs/flasher/source/sampler/model_tg.s`. Aucun sampler, page ou FX master importes. Carte testee sur machine par AveyCole le 16/10/2026, TRACK + RETRIG maintenus uniquement ; [note 99](../../notes/99-beat-repeat-collectif.md), licence jointe aux sources et a la page de test. |


## Promotion materielle — 16/10/2026

AveyCole confirme le candidat 2 et demande « push to main as hardware tested! ». Promotion au principal 1.73 ; noyau compile et recettes identiques au test 2, statut et textes seuls modifies. Selection Control All et seize divisions pendant TRACK + RETRIG conserves. Cette confirmation ne mesure pas la charge CPU maximale. `tools/promote_beat_repeat.py --check` et les neuf comparaisons SHA navigateur principal/test verifient cette promotion.


## Feedback performance experimental (note 100)

Popup bref : helper propre du support commun Modded-Cycles, adapte sans multiplicateur ; aucune routine OS copiee. LEDs mute B : nouveau wrapper AveyCole / Modded-Cycles autour des backends propres epingles de note 97. Licence MIT du projet, credits beat repeat TinyGregAudio conserves. Sources `tools/machines/beat_repeat/popup.s` et `tools/machines/midi_lanes/mute_feedback.s` ; [note 100](../../notes/100-feedback-performance.md). Publication de test seulement ; principal inchange.
