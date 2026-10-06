# 42 — Jouer les accords d'une gamme avec les six pads

Contribution de **Nico Heuser** ([byNicoHeuser](https://github.com/byNicoHeuser)),
[PR #46](https://github.com/18nelli18/Modded-Cycles/pull/46) du **06/10/2026**, intégrée au flasher par ce projet
(relecture et renumérotation au §11). Sa demande, dans sa propre conversation du **05/10/2026** : choisir une gamme
pour CHORD, jouer ses accords avec T1–T6, puis six positions supplémentaires avec un bouton maintenu. Il confirme
**une seule piste CHORD** et des extensions choisies par degré **en restant dans la gamme** ; il accepte de remplacer
PAGE si cela gêne le jeu. Source : conversation locale, sans lien public. Adresses : VA de l'OS **1.13**.

Tweak : [`45-chord-keys.json`](../tweaks/model-cycles_OS1.13/45-chord-keys.json), générateur
[`tools/gen_chord_keys.py`](../tools/gen_chord_keys.py), sources
[`tools/machines/chord_keys/`](../tools/machines/chord_keys/), preuves sous `tools/emu/` et test natif
[`tools/test_chord_keys.py`](../tools/test_chord_keys.py). **Statut : expérimental, aucun essai matériel rapporté.**

## Réponse courte

`[FAIT en émulation]` Le mod raccorde les pads, un menu de réglage, le stockage des patterns et le véritable moteur
CHORD. Dans **FUNC + RETRIG**, activer **Keys** sur une piste CHORD, régler **Root**, **Scale** et **I Ext** à
**VII Ext**. T1–T6 jouent I–VI ; **RETRIG maintenu** donne VII puis I–V à l'octave supérieure. PAGE garde ses
fonctions. Les réglages sont propres à chaque piste du pattern ; les six pads pilotent la piste CHORD sélectionnée.

Les sept modes diatoniques et cinq choix d'extension sont implémentés, avec trois ou quatre voix. La tonique de
l'interface est limitée aux notes MIDI **24–48**, soit **C1–C3** selon la notation du menu. COLOR garde les gains
et déplacements d'octave stock ; commencer à **32** pour entendre le voicing de référence. SHAPE est remplacé
pour les notes de la gamme lorsque Keys est actif. Les notes hors gamme gardent l'accord SHAPE stock.

Cette fonction était absente du dépôt. Le [Scale Lock de Model-TG](https://github.com/TinyGregAudio/Model-TG/blob/main/docs/USER_GUIDE.md#scale-lock)
transforme les notes du clavier suivant une gamme ; il ne choisit pas un accord par degré. **Model-TG est déclaré
incompatible** dans cette première version : sa transformation des notes et son CHORD optimisé demanderaient une
intégration spécifique. La recherche ne démontre pas l'absence d'un autre mod dans tous les projets externes.

## 1. Comportement musical et limites

| Banque | T1 | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|---|
| Première | I | II | III | IV | V | VI |
| RETRIG maintenu | VII | I + octave | II + octave | III + octave | IV + octave | V + octave |
| Do majeur, première | C | Dm | Em | F | G | Am |
| Do majeur, deuxième | Bdim | C ↑ | Dm ↑ | Em ↑ | F ↑ | G ↑ |

`[FAIT]` Les douze positions montent sans redescendre au passage VII → I. Les réglages I–VII sont partagés à
l'octave. Modes : ionien/majeur, dorien, phrygien, lydien, mixolydien, éolien/mineur naturel, locrien. Les gammes
pentatoniques et les mineures harmonique/mélodique ne sont pas implémentées.

| Choix | Positions diatoniques jouées | Notes omises |
|---|---|---|
| TRI | 1, 3, 5 | aucune ; quatrième opérateur rendu muet |
| 7 | 1, 3, 5, 7 | aucune |
| 9 | 1, 3, 7, 9 | 5 |
| 11 | 1, 3, 7, 11 | 5, 9 |
| 13 | 1, 3, 7, 13 | 5, 9, 11 |

Ces nombres sont des positions **dans la gamme**, pas des intervalles chromatiques fixes. En do majeur, III9
produit **mi–sol–ré–fa**, VII9 **si–ré–la–do**. Les extensions de cinq notes ou plus sont donc des voicings à
quatre voix, pas des accords complets. Les déplacements d'octave de COLOR restent disponibles.

Le noyau portable accepte abstraitement MIDI 0–127 et refuse un accord dépassant 127 en entier, sans écrêtage.
La plage plus étroite du menu tient compte du moteur réel : son entrée borne la fondamentale à 96 et coupe des
opérateurs supérieurs aux fréquences élevées. La preuve exhaustive du DSP utilise PITCH/FINE 64 et COLOR 32 ;
elle ne garantit pas que toutes les transpositions extrêmes de PITCH/FINE gardent toutes les voix audibles.

La dernière frappe remplace l'accord précédent sur sa piste. Relâcher un ancien pad ne coupe pas le nouveau ;
relâcher le dernier termine sa note, **sans retour automatique** à un pad précédent encore tenu. Une modification
du menu libère les notes actives de la piste avant de changer les réglages. Les fins de note gardent la piste et
la note capturées à l'appui, même si la sélection, la banque, Keys ou la machine changent ensuite.

Le moteur déduit le degré de la note reçue et de la gamme du **pattern actif**. Il n'ajoute pas de métadonnée
d'accord à chaque événement : les fondamentales enregistrées ou séquencées sont réinterprétées avec les réglages
courants. Modifier une extension change donc aussi le rendu des notes correspondantes du pattern. Le MIDI
sortant conserve la fondamentale transmise par le helper stock ; ce mod ne crée pas quatre notes MIDI sortantes.
La preuve live rec suit le vrai chemin jusqu'au message de note : fondamentale 59, vélocité 100, retrig −1,
durée 20 000 et fin de note correcte après un changement de banque. **L'écriture finale du trig enregistré
n'est pas exécutée dans ce banc** ; la sauvegarde de la configuration et le rendu des fondamentales sont
contrôlés séparément.

## 2. Pads, deuxième banque et menu

`[FAIT]` Les pads passent par **PadEvent**, distinct des KeyEvent des boutons.

| Adresse / champ | Rôle |
|---|---|
| `0x40074072` | Constructeur PadEvent |
| Événement `+12`, `+16`, `+20`, `+24`, `+28` | Source, état (1 appui / 0 relâchement), pad (1–6), vélocité, FUNC |
| `0x4000879a` / `0x400087de` | Construction des appuis / relâchements |
| `0x4007746c` | Dispatch du contrôleur, vues prioritaires avant PadsView |
| `0x4001cf04` / `0x4001d180` | Constructeur / consommateur stock de PadsView |
| `0x4010025c` | Pointeur virtuel principal, redirigé vers `ck_ui_pad` |
| `0x401002b0` | Pointeur de l'interface secondaire, redirigé vers `ck_ui_pad_thunk` |
| `0x4001d3d4` | Thunk stock : corrige `this` de −16 avant le consommateur |
| `0x4001d05e` / `0x4001d0fc` | Relais stock d'appui / fin de note |
| `0x4001cb3e` | Appel du constructeur FUNC + RETRIG, redirigé vers `ck_ui_menu_ctor` |

`[FAIT en émulation]` Rediriger seulement le pointeur principal ne suffit pas : le dispatch réel utilise
l'interface secondaire à `PadsView+16`. Le thunk du mod garde la correction de −16. Le consommateur stock est
appelé lorsque Keys est OFF, la piste sélectionnée n'est pas CHORD ou FUNC/TRACK/PATTERN est maintenu.
QuickMute consomme bien ses événements avant le clavier d'accords dans le vrai contrôleur émulé.

RETRIG est la touche 4. Dans Keys, il choisit la banque au moment de l'appui ; l'appel du helper de note passe
`retrig=-1`, empêchant la répétition de concurrencer ce geste. **FUNC + RETRIG** conserve le constructeur du menu
stock, puis ajoute dix lignes : Keys, Root, Scale, I Ext, II Ext, III Ext, IV Ext, V Ext, VI Ext, VII Ext.
Les lignes existantes du menu, dont celles de l'arpège lorsqu'il est présent, restent construites.
La vélocité suit le réglage stock : valeur globale lorsque la vélocité fixe est activée, sinon force de la frappe.
Les deux chemins sont vérifiés avec le vrai wrapper de pads.

PAGE (touche 15) commande FILL lorsqu'elle est maintenue et change de page au relâchement dans la grille
(`0x40022f64` / `0x40022f70`, notes/34). Son entrée `0x400224ee` est utilisée par trig-preview et Model-TG.
Le mod n'accroche aucune de ces adresses : le choix de RETRIG répond à la préférence de Nico sans détourner PAGE.

## 3. Véritable moteur CHORD

| Adresse / champ | Rôle |
|---|---|
| `0x400aae88` | Entrée update CHORD, `jmp chord_audio_update ; nop` sur 8 octets |
| `0x400aae90` | Suite après le prologue rejoué par `chord_audio_original` |
| `0x400ab0e4` | Calcul du pointeur des rapports, remplacé par `jsr chord_audio_ratios` |
| `0x400ab24c` | Rendu CHORD stock conservé |
| `0x4012142c` | Table stock des rapports Q26 |
| Voix `+0x50`, `+0xc8`, `+0x140`, `+0x1b8` | Quatre rapports, pas d'opérateur `0x78` |
| `0x42308828`, pas `0x31c` | Six structures de voix ; identification de la piste sans état global |

`[FAIT]` Le wrapper copie les 33 mots de paramètres dans un cadre local de **92 octets**, avec quatre rapports,
un marqueur et le nombre de voix. Cette copie existe aussi en mode OFF : le hook interne peut lire le marqueur
sans sortir du tableau natif. Il ne modifie pas les paramètres partagés et n'utilise aucun état de calcul global.

Pour une note de la gamme avec Keys actif, les rapports sont calculés avec une table indépendante
`round(2**(n/12) * 2**26)`, `n=0..23`. La copie locale utilise SHAPE 7 pour rendre les quatre opérateurs disponibles,
puis le hook fournit les rapports diatoniques **avant** les opérations COLOR stock. Pour TRI, le gain de la
quatrième voix est ensuite mis à zéro. Enveloppes, rendu, gains COLOR, PITCH et FINE restent traités par l'OS.

`[FAIT en émulation]` 10 500 accords (25 toniques × 7 modes × 5 extensions × 12 pads) ont les rapports attendus,
des gains non nuls sur les voix attendues à COLOR 32 (les valeurs exactes ne sont comparées au SHAPE 7 stock que dans le balayage de COLOR) et un écart de phase inférieur à **1 cent** par rapport aux mêmes notes jouées comme
fondamentales stock. Les 128 valeurs de COLOR conservent les gains et déplacements d'octave du moteur.
En mode OFF, 570 updates sur les six voix restent identiques octet par octet ; les rendus PCM comparés restent
identiques. L'activation produit un PCM non nul différent du SHAPE stock.

Le coût du vrai getter est inclus dans la preuve audio/stockage : pour six CHORD, le supplément observé est
**2 880 instructions par bloc en mode OFF** et **3 627 en mode ON**, soit environ **5,6 % / 7,0 %** du compte stock
de ce scénario. Ce sont des instructions Unicorn, **pas des cycles ni une mesure de charge du MCF54415**.
Dans la combinaison avec les cinq moteurs Syntakt et les autres mods ci-dessous, les comptes passent de
52 987 à 55 867 en mode OFF et de 53 122 à 56 777 en mode ON : **+2 880 / +3 655 instructions**.
Le temps réel avec USB, effets et autres machines reste un point de test matériel.
Le banc vérifie aussi la conservation de `d2-d7/a2-a6` et de SP ; la pile maximale observée est de **224 octets**
contre **104** pour l'appel stock, soit **120 octets supplémentaires** dans ce scénario.

## 4. Réglages persistants : en-tête du pattern

`[FAIT]` L'octet `B[512]` de chaque piste, sérialisé dans `A[704]`, appartient déjà à l'arpège (notes/32).
Ses trois bits libres ne suffisent pas. Le mod utilise les réserves de l'en-tête de pattern, après preuve des
lectures et copies stock ; il ne modifie pas le format ni la taille du projet.

| Structure / routine | Adresse ou taille |
|---|---|
| Pattern de travail B | 30 710 octets ; six pistes de 722 octets |
| En-tête B | `B+30642`, 64 octets ; identité à `B+30706` |
| Pattern sérialisé A | 14 800 octets ; en-tête à `A+14736` |
| Chargement d'en-tête | `0x4005b3b4` : lit les champs 0..28 et 38 |
| Copie/sauvegarde d'en-tête | `0x4005b4c4` : conserve les 64 octets |
| Sauvegarde / chargement du pattern | `0x4005ba0a` / `0x4005b894` |
| Initialisation d'en-tête / pattern | `0x40061526` / `0x400615e8` |

Allocation choisie dans les 64 octets :

| Octets | Contenu |
|---|---|
| 32..35 | Signature versionnée `0x434b01a7` |
| 40..63 | Six mots de configuration, quatre octets par piste |
| Tous les autres | Préservés par le code du mod |

Un mot contient `actif[31]`, `mode[30:28]`, `tonique[27:21]`, puis les sept extensions de trois bits dans
`[20:0]`. Validation : mode < 7, tonique 24..48, toutes les extensions < 5. Le défaut est **OFF / C3 / majeur /
triades**, `0x06000000`. Une signature absente ou un mot invalide ne peut activer le mode. Au chargement, si l'un
des six mots est invalide, les six sont remis au défaut ; un ancien pattern reçoit donc Keys OFF.

| Hook | Instructions stock rejouées | Retour |
|---|---|---|
| `0x4005b4a8` → `ck_storage_load_hook` | `moveq #1,d0 ; move.b 28(a3),28(a2)` | `0x4005b4b0` |
| `0x40061564` → `ck_storage_init_hook` | `move.b d0,27(a0) ; pea 16` | `0x4006156c` |

Les hooks sauvent `d0-d1/a0-a1` ; l'ABI C préserve `d2-d7/a2-a6`. Les accès au tag et aux mots sont faits octet
par octet, car un en-tête B peut n'être aligné que sur deux octets. Le setter, le reset et le chargement du mod
masquent brièvement les interruptions, puis rétablissent le SR précédent. Le banc contrôle qu'aucune de leurs
écritures de configuration n'est visible avec IPL inférieur à 7.

`[FAIT en émulation]` Le chargeur stock ne lit ni n'écrit ces réserves. Les accesseurs d'en-tête testés ne les
lisent pas et leurs setters les préservent. La sauvegarde réelle B→A et le chargement A→B avec les hooks
conservent les six configurations ; la copie des 30 710 octets passe par le `memcpy` de l'OS (`0x4008f1f0`), ce
qui ne prouve pas le copier-coller de pattern de l'interface (à vérifier sur la machine). Les autres champs d'en-tête restent égaux
au résultat stock. L'initialisation avec conservation garde les réglages ; l'initialisation normale les désactive.

## 5. Lecture UI/audio : suivre le bon pattern

Les expériences de l'arpège ont montré le danger d'une copie audio périmée. Aucun cache global de réglages n'est
introduit ici :

- **UI** : singleton `*0x40fe4228`, sélection via `0x4000f208`, objet d'en-tête à `pattern_object+44`, données
  à `pattern_object+60`. Le setter appelle le notify virtuel `[4]` de l'en-tête, comme les setters stock A.On.
- **Audio** : pattern actif `*0x40a7887c`, identité lue à `+30706`. Son objet est retrouvé dans le tableau du
  singleton à `+5192 + 732 × identité` ; le getter lit son pointeur d'en-tête `+60`. Pas d'appel UI, allocation,
  attente ou verrou depuis l'interruption audio. Singleton nul, pattern ≥ 96 ou piste ≥ 6 rendent le défaut OFF.

`[FAIT : désassemblage]` Le tableau de 96 objets est construit en `0x40011408`. `0x4000ea46` lie les objets à
`raw_base+28+30710×pattern` via `0x4000c5d0`, qui relie l'en-tête à `B+30642`. Au démarrage `0x40006cae` fournit
la base fixe `0x406fa024` : les en-têtes sont des sous-zones du buffer du projet, pas des allocations individuelles.
`[FAIT en émulation]` Le vrai raccordement `0x4000c5d0`, avec les vtables stock du pattern, de l'en-tête, des six
pistes et des plocks, retrouve ces sous-zones puis les déplace toutes lorsque le buffer B est remplacé.

`[FAIT en émulation]` Les vraies APIs `ck_ui_config_get/set` et `ck_audio_config` voient immédiatement une
modification du pattern actif. Éditer un autre pattern n'altère pas cette lecture ; changer l'identité active ou
remplacer le pointeur d'en-tête est pris en compte dès l'appel suivant. Les patterns 0, 1 et 95 sont couverts.

**Portée** : le banc construit les objets minimaux avec leurs vraies vtables. Il ne rejoue pas le boot complet ni
le chargement du projet avec toutes ses interruptions. Les écritures propres au mod sont vérifiées sous IPL7 ;
la copie stock complète est vérifiée après son retour, sans simuler une interruption entre deux de ses écritures.

## 6. Code, état et génération

`[FAIT]` Le JSON actuel contient **29 écritures**, dont sept accroches et onze paires code/redirection de masque.
**3 916 octets** de code, constantes et état sont placés dans onze masques 47×47 de 376 octets. Leurs sprites
sont redirigés vers le masque identique conservé à `0x40172220` :

| Cave | Octets écrits |
|---|---:|
| `0x4016b6f8` | 376 |
| `0x4016b9e8` | 376 |
| `0x40171f30` | 376 |
| `0x40172608` | 373 |
| `0x40179730` | 375 |
| `0x40182b38` | 376 |
| `0x40182e28` | 352 |
| `0x40183118` | 376 |
| `0x40185018` | 376 |
| `0x40185968` | 368 |
| `0x40185c58` | 192 |

Le seul état mutable propre aux pads est un tableau de six captures, initialisé à zéro dans l'image. Le calcul
audio utilise sa pile ; la configuration reste dans les patterns. Aucun payload externe ni code Syntakt n'est
nécessaire. Les adresses de fonctions exactes sont exportées dans `symbols` du JSON ; les preuves exécutent ces
adresses finales, sans substituer une compilation de test à une autre adresse.

Le générateur vérifie le SHA-256 du `.syx` et du MAIN OS officiel, les octets d'origine de chaque accroche, l'égalité
des masques, leur référence unique, les limites de chaque cave et les chevauchements avec les autres tweaks.
Il refuse tout symbole de code impair. **Leçon de placement** : une section assembleur peut annoncer un alignement
minimal de 1 ; après une chaîne de taille impaire, cela donnerait une entrée d'instruction impaire. Le placement
impose donc au moins deux octets à toute section `.text`, et les stubs de stockage déclarent `.balign 2`.
La preuve principale recherche également les pointeurs et branchements vers l'intérieur de toutes les séquences
d'instructions détournées : aucun n'a été trouvé dans l'image officielle.

Relecture statique des **plages complètes des onze caves** : les onze références réelles sont les pointeurs de
sprites redirigés. Deux ressemblances à des adresses intérieures chevauchent des instructions distinctes : en
`0x400befbe`, la fin de `pea 0x40134018` suivie de `move.l a4,-(sp)` forme artificiellement `0x40182f0c` ; en
`0x400f9a1e`, la fin de `move.l #0x40124018,(a2)` suivie de `move.l a2,-(sp)` forme `0x40182f0a`. Le candidat
`bra.w` en `0x4018595c` est dans les données d'un sprite. Aucun de ces trois résultats bruts ne constitue une
référence exécutable vers une cave ; leur désassemblage explique pourquoi ils sont écartés.

Compilation de référence : **GCC m68k-elf 16.2.0**, binutils **2.47**, `-mcpu=54418 -Os`, sections par fonction et
par donnée. Le `--check` doit utiliser une toolchain produisant les mêmes octets. Bootloader et updater restent
hors des écritures : seul le MAIN OS, section 3, est modifié.

`[FAIT, relecture du 06/10/2026]` **Pas de `m68k-linux-gnu-gcc`** : avec l'ABI SVR4 de la cible Linux, GCC lit dans
`a0` le pointeur rendu par une fonction appelée par pointeur, alors que l'OS le rend dans `d0` (`0x4000eb90` :
`move.l 4(sp),d0 ; addi.l #48,d0 ; rts`). Compilés ainsi, `selected_track` et `ui_header_object` passeraient un
registre au hasard à l'OS à chaque appui de pad. Le JSON (m68k-elf) lit bien `d0` (`2f00` en `0x40185174` et
`0x401850fa`). Le générateur n'accepte donc que `m68k-elf-` (ou `M68K_CROSS`, hors cible Linux).
`[FAIT]` Le refus « symbole de code non aligné » obtenu avec GCC 13 vient des tables d'octets (`scales`,
`voicings`…) : chaque section `.ckN` mélange code et données, donc `nm` les marque `t`, et seules les sections
`.text` reçoivent un alignement de 2. Avec GCC 16.2, elles tombent sur des adresses paires par hasard ; le code ne
lit ces tables qu'octet par octet. Aligner toutes les sections sur 2 lèverait ce faux refus (une simulation avec
les tailles de GCC 16.2 donne le même placement), mais n'a pas été appliqué faute de pouvoir le vérifier avec
GCC 16.2 ici.

## 7. Compatibilités

| Mod / fonction | Traitement |
|---|---|
| Model-TG / Model-TG-ST | **Conflit déclaré**, transformation Scale Lock et moteur CHORD à intégrer séparément |
| Arp | Stockage distinct ; menu stock conservé avant les dix nouvelles lignes ; en jeu Keys, RETRIG choisit la banque |
| Trig-preview / trig-hold | Aucun hook ajouté à PAGE ou aux touches de pas |
| 6ch-usbup / moteurs Syntakt | Pas de cave partagée ni modification du transport USB ; preuves combinées dans la suite |
| Autres machines | Pads stock si la piste sélectionnée n'est pas CHORD ; wrapper audio uniquement sur l'update CHORD |

`[FAIT en émulation]` La suite complète passe seule et avec **6ch-usbup, latching-mute, trig-preview,
browser-scroll, trig-hold, arp, tempo-max, boot-anim et les cinq moteurs Syntakt SD/CP/TOY/BITS/SWARM**.
L'absence de chevauchement d'octets ne prouve pas à elle seule une compatibilité fonctionnelle ; la suite exécute
les mêmes contrôles avec cette image combinée. Le test matériel doit encore couvrir une session dense avec effets
et USB.

Le banc du gouverneur, intégré à la commande combinée lorsqu'un mod expose ses symboles, exécute six accords
CHORD avec le vrai getter : à **50 % de charge simulée**, le PCM reste identique et aucune voix n'est volée ; un
pic isolé à **99 %** est ignoré ; des pics répétés provoquent le fondu à partir du **bloc 41**, puis le retrig
rejoue les accords. Les durées sont injectées dans le régulateur : cela prouve sa réaction, pas la charge réelle
de ces six accords sur le processeur.

## 8. Preuves et commandes

| Banc | Différence stock/modifié et contrôles | Limites |
|---|---|---|
| `tools/test_chord_keys.py` | Vrai C natif : exemples concrets, réglages indépendants, entrées refusées, 420 frontières MIDI, 53 760 cas | Pas le firmware ; gamme attendue dérivée par rotation des pas du majeur |
| `tools/emu/probe_chord_storage.py` | Code des caves finales, chargeur stock vs hooks, accesseurs, vrai B→A→B, copies, initialisation, APIs UI/audio | Sélection UI et observateur simulés ; pas de disque ou boot complet |
| `tools/emu/chord_ui_checks.py` | Vrais PadEvent/PadsView/helpers, pointeurs virtuels, contrôleur et QuickMute ; menu stock plus dix lignes ; vrai stockage ; chemin live rec jusqu'au message | Sélection du pattern et notification simulées ; dessin observé avant le pilote écran ; sorties notes/mutes observées avant leurs effets ; écriture finale du trig non exécutée |
| `tools/emu/chord_audio_checks.py` | Vrais hooks ColdFire, update et rendu, 10 500 accords, COLOR, PCM, isolation ; variante avec vrai getter et changements de pattern | Première partie instrumente seulement le getter ; seconde partie utilise des objets de projet préparés par le banc |
| `tools/emu/test_chord_keys.py` | Assemble les preuves et vérifie le tweak final, seul et avec les mods sélectionnés | Aucune mesure ni validation matérielle |

```sh
python3 tools/test_chord_keys.py
python3 tools/gen_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx --check
python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx \
  --with 6ch-usbup,latching-mute,trig-preview,browser-scroll,trig-hold,arp,tempo-max,boot-anim,syntakt-sd-cp-toy-bits-swarm \
  --syntakt firmware/Syntakt_OS1.42.syx
python3 tools/emu/probe_chord_storage.py --cycles firmware/model-cycles_OS1.13.syx
```

Environnement des preuves du 05/10/2026 : Python 3.14, Unicorn 2.1.4, NumPy 2.5.3. Sur le poste de développement
macOS, Unicorn nécessite une exécution hors sandbox : sinon `mem_map` reçoit SIGILL avant toute instruction.
Les images officielles et fichiers extraits restent sous `firmware/` et `build/`, ignorés par Git.

Validation finale du 05/10/2026 : **160 contrôles seuls**, **164 avec les mods compatibles**, et les **12 contrôles** du banc historique du gouverneur passent. Les générateurs, la compilation Python, les comparaisons des builders/flashers et le parcours UI synthétique passent également. `REF_MAINOS --check` et le parcours réel du flasher couvrent exactement **17 407 combinaisons**, toutes conformes. Ce dernier conserve les clics et le builder réels ; un parcours Gray et des shards contigus évitent les reconstructions intermédiaires, avec un cache de test limité à 32 images.

## 9. Historique de l'investigation du 05/10/2026

La première étape était explicitement **un prototype non installable**, sans générateur ni stockage réservé.
Les six familles du noyau C, **55 vérifications** de `probe_chord_keys.py --inject-intervals` et **33** de
`probe_chord_pads.py` ont établi séparément le calcul musical, le moteur et les événements stock.

La sonde initiale a observé les 35 formes SHAPE 3–37 avec COLOR 32 ; les indices 38, 43 et 127 étaient bornés sur
la forme 37 pour la hauteur. Elle injectait des rapports **dans la RAM de l'émulateur**, en `0x400ab158` : ce
n'était pas un hook firmware, et elle ne testait pas le rendu. Les douze neuvièmes de do majeur avaient alors un
écart maximal de **0,489 cent** ; le balayage final plus large admet moins de 1 cent à cause de la quantification
stock des fréquences graves. La forme Major coupait la quatrième voix, d'où le choix interne de SHAPE 7 et du
contrôle explicite des gains. Les notes 96, 97, 108 et 127 ont révélé la borne et les coupures de voix aiguës.

PAGE, puis d'autres modificateurs, ont été envisagés ; la version intégrée retient RETRIG. Le consommateur virtuel
principal seul paraissait suffisant, mais l'exécution du vrai dispatch a révélé la nécessité du second thunk.
La recherche du stockage a écarté les bits restants de B[512] et démontré les réserves d'en-tête. Les premiers
prototypes de stockage compilés à une adresse temporaire ont ensuite été remplacés par la preuve des caves du JSON.

Les premiers contrôles web sur image synthétique passaient. `relocate_6ch.py --check` avait révélé une différence
préexistante avec les binutils locaux (204 octets pour `feed.S`, contre 208 dans le JSON versionné, cibles d'appel
différentes). **Cause ensuite établie** : binutils 2.47 optimise automatiquement deux `lea feed_pend` en adressage
relatif au PC. L'option assembleur **`-S`** désactive cette optimisation et reproduit les 208 octets attendus ;
`relocate_6ch.py --check` passe avec cette option, sans modifier le JSON existant. Le poste utilise un wrapper
local ignoré sous `build/binutils-repro/` pour fournir ce drapeau au contrôle historique.

## 10. À vérifier sur la machine

`[À FAIRE : Maxime]` Ouvrir FUNC + RETRIG, activer Keys sur CHORD, parcourir les deux banques, changer chaque
extension, vérifier les notes tenues et leurs relâchements, TRACK/FUNC/PATTERN/QuickMute et le comportement normal
avec Keys OFF. Vérifier l'enregistrement/relecture des fondamentales, la sauvegarde/recharge/copie des patterns
et du projet, puis une session avec les autres mods compatibles, effets, USB et charge audio élevée.

**Aucun essai matériel rapporté. Le statut reste `experimental` jusqu'au retour de Maxime ; aucune affirmation
sur l'écran physique, le temps réel ou le fonctionnement complet du matériel ne découle de ces seuls bancs.**
