# 40 — Jouer les accords d'une gamme avec TRIG 1–16

Demande de Nico dans cette conversation, le **05/10/2026** : choisir une gamme pour CHORD, jouer ses accords avec
T1–T6, puis six positions supplémentaires avec un bouton maintenu. Il confirme **une seule piste CHORD** et des
extensions choisies par degré **en restant dans la gamme** ; il accepte de remplacer PAGE si cela gêne le jeu.
Le **06/10/2026**, il remplace cette demande par les boutons inférieurs **TRIG 1–16**, en conservant les
commandes habituelles des grands pads ; il demande aussi **MAJ** et les degrés sans suffixe **Ext** dans le menu.
Source : conversation locale, sans lien public. Adresses : VA de l'OS **1.13**. Les constats sur les pads du
05/10 sont conservés comme historique en §2 et §9 ; les révisions du clavier et du son sont détaillées en §11 et §12.

Tweak : [`44-chord-keys.json`](../tweaks/model-cycles_OS1.13/44-chord-keys.json), générateur
[`tools/gen_chord_keys.py`](../tools/gen_chord_keys.py), sources
[`tools/machines/chord_keys/`](../tools/machines/chord_keys/), preuves sous `tools/emu/` et test natif
[`tools/test_chord_keys.py`](../tools/test_chord_keys.py) et
[`tools/test_chord_harmony.py`](../tools/test_chord_harmony.py). **État de la nouvelle révision au 06/10/2026 :
expérimentale, sans essai matériel rapporté** (§15). Le retour de Nico seul sur Model:Cycles concerne
la version précédente (§13). Les §1–12 décrivent cette version historique, conservée par Controls LEGACY.

## Réponse courte

`[FAIT dans les sources de la révision §15]` TRIG 1–16 jouent les degrés de la piste CHORD sélectionnée,
avec Root, Scale et le niveau TRI/7/9/11/13 propre à chaque degré. En **Controls NEW**, **COLOR** choisit
DIATONIC, JAZZ ou TENSION ; **SHAPE** combine les neuf dispositions BASE/CLS0–3/OPN0–3 avec leur balance.
**Pads HARMONY** donne à T1–T6 des changements temporaires 9/11/13/SUS7/PARALLEL/V7. Le dernier pad
pressé prévaut ; au relâchement, retour au pad précédent encore tenu puis au réglage du degré.

**Controls LEGACY/NEW s'applique au pattern entier.** Les anciens patterns restent LEGACY jusqu'au choix
explicite NEW : leurs valeurs et locks ne sont pas réécrits. Les nouveaux patterns initialisés commencent
NEW, Pads TRACK et Keys OFF. Les réglages de pads sont par piste ; les gestes restent live et ne sont
pas enregistrés. Quatre voix maximum ; les extensions m7♭5 préservent la quinte diminuée en omettant
la tierce, et PARALLEL/V7 sont indisponibles sur les cibles diminuées.

Model-TG reste incompatible. Les notes reçues hors gamme gardent le son CHORD stock. Les détails,
la migration, les choix de balance, les nouvelles caves et l'état des preuves figurent en **§15**.
**Aucun résultat matériel de cette révision n'est revendiqué.** Les §13–14 conservent le retour matériel
antérieur et la discussion qui a mené à ces choix.

## 1. Comportement musical et limites

| Boutons | Degrés, de gauche à droite | Octave | Exemple en do majeur, TRI |
|---|---|---|---|
| TRIG 1–7 | I, II, III, IV, V, VI, VII | Root | C, Dm, Em, F, G, Am, Bdim |
| TRIG 8–14 | I, II, III, IV, V, VI, VII | Root + 1 | mêmes accords une octave plus haut |
| TRIG 15–16 | I, II | Root + 2 | C et Dm deux octaves plus haut |

`[FAIT]` Les seize positions montent sans redescendre au passage VII → I. Les réglages I–VII sont partagés à
toutes les octaves : l'extension de I s'applique aux touches 1, 8 et 15. Modes : ionien/majeur, dorien, phrygien, lydien, mixolydien, éolien/mineur naturel, locrien. Les gammes
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
quatre voix, pas des accords complets. SHAPE règle leur disposition ; COLOR règle leurs niveaux.

Le noyau portable accepte abstraitement MIDI 0–127 et refuse un accord dépassant 127 en entier, sans écrêtage.
La plage plus étroite du menu tient compte du moteur réel : son entrée borne la fondamentale à 96 et coupe des
opérateurs supérieurs aux fréquences élevées. La preuve exhaustive du DSP utilise PITCH/FINE 64 et COLOR 32 ;
elle ne garantit pas que toutes les transpositions extrêmes de PITCH/FINE gardent toutes les voix audibles.

La dernière frappe remplace l'accord précédent sur sa piste. Relâcher une ancienne touche ne coupe pas le nouvel
accord ; relâcher la dernière termine sa note, **sans retour automatique** à une touche précédente encore tenue. Une modification
du menu libère les notes actives de la piste avant de changer les réglages. Les fins de note gardent la piste et
la note capturées à l'appui, même si la sélection, Keys ou la machine changent ensuite. Les répétitions de maintien
des boutons ne rejouent pas l'accord. La vélocité provient du réglage de piste, comme le clavier chromatique stock.

Le moteur déduit le degré de la note reçue et de la gamme du **pattern actif**. Il n'ajoute pas de métadonnée
d'accord à chaque événement : les fondamentales enregistrées ou séquencées sont réinterprétées avec les réglages
courants. Modifier une extension change donc aussi le rendu des notes correspondantes du pattern. Le MIDI
sortant conserve la fondamentale transmise par le helper stock ; ce mod ne crée pas quatre notes MIDI sortantes.
La preuve live rec suit le vrai chemin jusqu'au message de note : TRIG 15, fondamentale 72, vélocité 97, retrig −1,
durée 20 000 et fin de note correcte pour cette troisième octave. **L'écriture finale du trig enregistré
n'est pas exécutée dans ce banc** ; la sauvegarde de la configuration et le rendu des fondamentales sont
contrôlés séparément.

## 2. Historique du 05/10/2026 : pads, deuxième banque et menu

Cette section décrit la version précédente. **Les deux hooks PadsView ci-dessous sont retirés** du tweak actuel ;
le raccordement KeyboardView et les libellés actuels sont décrits en §11.

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

Les mesures et le chemin COLOR ci-dessous décrivent la première version ; la séparation SHAPE/COLOR et les
mesures actualisées figurent en §12.

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

`[FAIT en émulation]` 14 000 accords (25 toniques × 7 modes × 5 extensions × 16 touches) ont les rapports attendus,
les gains attendus à COLOR 32 et un écart de phase inférieur à **1 cent** par rapport aux mêmes notes jouées comme
fondamentales stock. Les 128 valeurs de COLOR conservent les gains et déplacements d'octave du moteur.
En mode OFF, 570 updates sur les six voix restent identiques octet par octet ; les rendus PCM comparés restent
identiques. L'activation produit un PCM non nul différent du SHAPE stock.

Mesures du 05/10/2026, confirmées sur la révision à seize touches du 06/10 : le coût du vrai getter est inclus
dans la preuve audio/stockage. Pour six CHORD, le supplément observé est
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
lisent pas et leurs setters les préservent. La sauvegarde réelle B→A, le chargement A→B avec les hooks et la
copie complète des 30 710 octets conservent les six configurations. Les autres champs d'en-tête restent égaux
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

`[FAIT : version clavier TRIG, avant la révision SHAPE/COLOR du §12]` Le JSON contenait **30 écritures**, dont six accroches et douze paires code/redirection de masque.
**4 122 octets** de code, constantes et état sont placés dans douze masques 47×47 de 376 octets. Leurs sprites
sont redirigés vers le masque identique conservé à `0x40172220` :

| Cave | Octets écrits |
|---|---:|
| `0x4016b6f8` | 376 |
| `0x4016b9e8` | 376 |
| `0x40171f30` | 363 |
| `0x40172608` | 374 |
| `0x40179730` | 374 |
| `0x40182b38` | 374 |
| `0x40182e28` | 374 |
| `0x40183118` | 376 |
| `0x40185018` | 376 |
| `0x40185968` | 373 |
| `0x40185c58` | 376 |
| `0x4018cd48` | 10 |

Le seul état mutable propre aux touches est un tableau de seize captures à `0x40182e28`, initialisé à zéro dans l'image. Le calcul
audio utilise sa pile ; la configuration reste dans les patterns. Aucun payload externe ni code Syntakt n'est
nécessaire. Les adresses de fonctions exactes sont exportées dans `symbols` du JSON ; les preuves exécutent ces
adresses finales, sans substituer une compilation de test à une autre adresse.

Le générateur vérifie le SHA-256 du `.syx` et du MAIN OS officiel, les octets d'origine de chaque accroche, l'égalité
des masques, leur référence unique, les limites de chaque cave et les chevauchements avec les autres tweaks.
Il refuse tout symbole de code impair. **Leçon de placement** : une section assembleur peut annoncer un alignement
minimal de 1 ; après une chaîne de taille impaire, cela donnerait une entrée d'instruction impaire. Le placement
impose donc au moins deux octets à toutes les sections `.text`, `.rodata`, `.data` et `.bss`, y compris les tables
de saut que le compilateur classe en constantes. Les stubs de stockage déclarent `.balign 2`.
La preuve principale recherche également les pointeurs et branchements vers l'intérieur de toutes les séquences
d'instructions détournées : aucun n'a été trouvé dans l'image officielle.

Relecture historique du 05/10 des **plages complètes des onze premières caves** : les onze références réelles sont les pointeurs de
sprites redirigés. Deux ressemblances à des adresses intérieures chevauchent des instructions distinctes : en
`0x400befbe`, la fin de `pea 0x40134018` suivie de `move.l a4,-(sp)` forme artificiellement `0x40182f0c` ; en
`0x400f9a1e`, la fin de `move.l #0x40124018,(a2)` suivie de `move.l a2,-(sp)` forme `0x40182f0a`. Le candidat
`bra.w` en `0x4018595c` est dans les données d'un sprite. Aucun de ces trois résultats bruts ne constitue une
référence exécutable vers une cave ; leur désassemblage explique pourquoi ils sont écartés.
Le 06/10, le scan des 376 octets du nouveau masque `0x4018cd48` ne trouve que son pointeur de sprite
`0x400acdb2`, redirigé par le tweak, et aucun branchement entrant.

Compilation de référence : **GCC m68k-elf 16.2.0**, binutils **2.47**, `-mcpu=54418 -Os`, sections par fonction et
par donnée. Le `--check` doit utiliser une toolchain produisant les mêmes octets. Bootloader et updater restent
hors des écritures : seul le MAIN OS, section 3, est modifié.

## 7. Compatibilités

| Mod / fonction | Traitement |
|---|---|
| Model-TG / Model-TG-ST | **Conflit déclaré**, transformation Scale Lock et moteur CHORD à intégrer séparément |
| Arp | Stockage distinct ; menu stock conservé avant les dix nouvelles lignes ; accords TRIG sans répétition (`retrig=-1`), grands pads traités par l'OS et l'arpège |
| Trig-preview / trig-hold | PAGE et le consommateur de grille restent stock ; le hook KeyboardView laisse passer l'édition des pas et les modificateurs |
| 6ch-usbup / moteurs Syntakt | Pas de cave partagée ni modification du transport USB ; preuves combinées dans la suite |
| Samples OS | Installation d'un autre OS, pas une combinaison avec ce mod pour Cycles OS 1.13 |
| Autres machines | Grands pads toujours stock ; clavier TRIG stock si Keys est OFF ou la piste sélectionnée n'est pas CHORD ; wrapper audio uniquement sur l'update CHORD |

`[FAIT en émulation, révision du 06/10/2026]` La suite complète passe seule et avec **6ch-usbup, latching-mute, trig-preview,
browser-scroll, trig-hold, arp, tempo-max, boot-anim et les cinq moteurs Syntakt SD/CP/TOY/BITS/SWARM**.
L'absence de chevauchement d'octets ne prouve pas à elle seule une compatibilité fonctionnelle ; la suite exécute
les mêmes contrôles avec cette image combinée. Les résultats de la dernière révision sont suivis en §12.5.
**Le seul retour matériel reçu concerne Chord Keys sans autre mod** (§13). Toutes les combinaisons ci-dessus
restent sans essai matériel rapporté, y compris une session dense avec effets et USB.

Le banc du gouverneur, intégré à la commande combinée lorsqu'un mod expose ses symboles, exécute six accords
CHORD avec le vrai getter : à **50 % de charge simulée**, le PCM reste identique et aucune voix n'est volée ; un
pic isolé à **99 %** est ignoré ; des pics répétés provoquent le fondu à partir du **bloc 41**, puis le retrig
rejoue les accords. Les durées sont injectées dans le régulateur : cela prouve sa réaction, pas la charge réelle
de ces six accords sur le processeur.

## 8. Preuves et commandes

| Banc | Différence stock/modifié et contrôles | Limites |
|---|---|---|
| `tools/test_chord_keys.py` | Vrai C natif : exemples concrets, réglages indépendants, entrées refusées, 560 frontières MIDI, 71 680 cas | Pas le firmware ; gamme attendue dérivée par rotation des pas du majeur |
| `tools/emu/probe_chord_storage.py` | Code des caves finales, chargeur stock vs hooks, accesseurs, vrai B→A→B, copies, initialisation, APIs UI/audio | Sélection UI et observateur simulés ; pas de disque ou boot complet |
| `tools/emu/chord_ui_checks.py` | 130 contrôles : vrais KeyEvent/KeyboardView/helpers, dispatch des touches, PadEvent/PadsView stock comparés ; menu stock plus dix lignes ; vrai stockage ; chemin live rec jusqu'au message | Sélection du pattern et notification simulées ; dessin observé avant le pilote écran ; sorties notes/mutes observées avant leurs effets ; écriture finale du trig non exécutée |
| `tools/emu/chord_audio_checks.py` | Vrais hooks ColdFire, update et rendu, 14 000 accords, COLOR, PCM, isolation ; variante avec vrai getter et changements de pattern | Première partie instrumente seulement le getter ; seconde partie utilise des objets de projet préparés par le banc |
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

PAGE, puis d'autres modificateurs, ont été envisagés ; la version intégrée du 05/10 retenait RETRIG. Le consommateur virtuel
principal seul paraissait suffisant, mais l'exécution du vrai dispatch a révélé la nécessité du second thunk.
La recherche du stockage a écarté les bits restants de B[512] et démontré les réserves d'en-tête. Les premiers
prototypes de stockage compilés à une adresse temporaire ont ensuite été remplacés par la preuve des caves du JSON.

Les premiers contrôles web sur image synthétique passaient. `relocate_6ch.py --check` avait révélé une différence
préexistante avec les binutils locaux (204 octets pour `feed.S`, contre 208 dans le JSON versionné, cibles d'appel
différentes). **Cause ensuite établie** : binutils 2.47 optimise automatiquement deux `lea feed_pend` en adressage
relatif au PC. L'option assembleur **`-S`** désactive cette optimisation et reproduit les 208 octets attendus ;
`relocate_6ch.py --check` passe avec cette option, sans modifier le JSON existant. Le poste utilise un wrapper
local ignoré sous `build/binutils-repro/` pour fournir ce drapeau au contrôle historique.

## 10. Protocole matériel prévu avant le retour du 06/10/2026

`[À FAIRE : Maxime]` Ouvrir FUNC + RETRIG, vérifier que MAJ et les lignes I–VII tiennent à l'écran, activer Keys sur
CHORD, quitter l'édition en grille et parcourir TRIG 1–16. Comparer 1/8/15 et 2/9/16, changer chaque extension,
vérifier les notes tenues et leurs relâchements. Vérifier le jeu, la sélection et le retrig stock sur T1–T6,
TRACK/FUNC/PATTERN/QuickMute, l'édition des pas et le clavier chromatique avec Keys OFF. Vérifier
l'enregistrement/relecture des fondamentales, la sauvegarde/recharge/copie des patterns
et du projet, puis une session avec les autres mods compatibles, effets, USB et charge audio élevée.

**État lors de la rédaction de ce protocole : aucun essai matériel rapporté, statut `experimental`.**
Aucune affirmation sur l'écran physique, le temps réel ou le fonctionnement complet du matériel ne découle
de ces seuls bancs. Le retour ultérieur de Nico est consigné en §13 ; il ne détaille pas ces contrôles un par un.

## 11. Révision du 06/10/2026 : seize boutons TRIG, pads d'origine et menu raccourci

Demande de Nico dans la même conversation : abandonner T1–T6 pour le clavier d'accords, jouer I–VII sur 1–7,
recommencer à l'octave sur 8, puis poursuivre sur les seize boutons inférieurs. Il demande aussi de remplacer
MAJOR par MAJ et de retirer « Ext » des sept lignes du menu. Les deux dernières touches deviennent donc I–II
deux octaves au-dessus de Root. Chaque degré conserve son réglage d'extension à toutes les octaves.

`[FAIT]` Le noyau reçoit désormais un seul indice `key=0..15` : `degree=key%7`, `octave=key/7`. Le paramètre de
banque disparaît. Le DSP et le format des réglages restent identiques ; les anciens patterns conservent leurs
réglages. Les libellés du menu sont `Keys`, `Root`, `Scale`, `I`, `II`, `III`, `IV`, `V`, `VI`, `VII` et le
mode majeur s'affiche `MAJ`.

| Adresse / champ | Contrat actuel |
|---|---|
| `0x4007238c` | Constructeur KeyEvent ; code à `+12`, drapeaux à `+16` |
| Codes `16..31` | Boutons physiques TRIG 1–16, sans réutiliser PadEvent |
| `0x40077720` | Vrai dispatch KeyEvent du contrôleur, avec les vues prioritaires |
| `0x400ff9cc` | Unique pointeur KeyboardView redirigé vers `ck_ui_key`, placé à `0x40185968` |
| `0x4001a0d2` | Consommateur KeyboardView stock, repli du hook |
| `0x40019e7a` / `0x40019c84` | Helpers stock d'appui et de fin de note du clavier |
| `0x40015ac4` | Lecture de la vélocité de piste utilisée pour ces boutons sans capteur de force |
| `0x400cf9a8` → `0x4006b978` / `0x4006bb18` | État UI : édition en grille / autre mode réservé au chemin stock |
| `0x4010025c`, `0x401002b0` | Les deux pointeurs PadsView sont laissés aux valeurs officielles |

`[FAIT en émulation]` Les seize notes sont comparées au clavier chromatique stock, y compris le vrai dispatch
de TRIG 8. Le hook conserve les gardes stock de grille et de mode UI, ainsi que FUNC, TRACK et PATTERN. Les
PadEvent des six grands pads, leurs vélocités, la sélection, le retrig et QuickMute retrouvent leur chemin
stock. **Cette restauration concerne leurs commandes** : le DSP de la piste CHORD reste harmonisé avec Keys,
quelle que soit l'origine de la note (bouton inférieur, pad, séquenceur ou MIDI).

Les seize captures de note gardent piste et fondamentale jusqu'au relâchement. La dernière touche d'une piste
remplace l'accord précédent ; relâcher l'ancienne ne coupe pas la nouvelle, même après changement de sélection,
machine ou réglages. Un événement de répétition de maintien est consommé sans nouvelle note. Les accords du
clavier passent toujours `retrig=-1` : RETRIG ne change ni leur octave ni leur répétition ; l'arpège reste
utilisable via les commandes stock des grands pads.

`[FAIT : version antérieure à la révision SHAPE/COLOR du §12]` Cette génération produit les **30 écritures, 12 caves et 4 122 octets** détaillés en §6, sans
chevauchement avec les tweaks déclarés compatibles. L'alignement minimal de deux octets s'applique également
aux constantes et tables de saut, pas seulement aux instructions. Le nouveau hook remplace les deux anciens
hooks de pads ; aucun octet du bootloader ou de l'updater ne change.

`[FAIT : tests natifs et émulation]` Les preuves ciblées de cette révision couvrent **71 680 cas natifs et 560 frontières MIDI**,
**130 contrôles UI** et **14 000 accords DSP** sur les seize touches. Elles vérifient notamment MAJ et les sept
libellés raccourcis, le jeu sur la troisième octave et les relâchements. Les limites des bancs restent celles
du §8 : aucune preuve de temps réel ou d'affichage physique, et aucune écriture finale du trig live rec.

`[FAIT en émulation]` Le JSON final passe **195 contrôles seul** et **199 avec les mods compatibles** du §7.
Chaque suite couvre les 14 000 accords, avec un écart maximal de **0,877 cent**. Le gouverneur conserve le PCM à
50 % de charge simulée, ignore le pic isolé à 99 %, déclenche le fondu au bloc 41 en charge répétée et permet
ensuite le retrig. Les coûts d'instructions du §3 restent identiques à ceux de la version précédente.

Les empreintes `REF_MAINOS` ont été régénérées pour **17 407 combinaisons** et leur contrôle `--check` passe.
Le parcours exhaustif du flasher valide ces **17 407 combinaisons**, sans erreur JavaScript et avec couverture
exacte des choix proposés. Les générateurs, la compilation Python, la syntaxe JavaScript et les comparaisons
des builders/flashers passent également. Le fichier construit pour Chord Keys seul conserve à l’octet près
les sections 2, 4 et 5 de l’image officielle ; seule la section 3 change.
À la validation de cette révision, avant le retour matériel du §13 : essais attendus selon §10,
statut **expérimental**.

## 12. SHAPE pour la disposition, COLOR pour le mélange (06/10/2026)

Demande de Nico, dans cette conversation : conserver I–VII pour les extensions,
supprimer la proposition de palettes et séparer les inversions de SHAPE du mélange
de COLOR. Il valide explicitement cette organisation (« hagamos esto »).

`[FAIT : désassemblage]` L'update CHORD appelle le calcul des gains
`0x400aada4` en `0x400ab0c4`, avant de charger les rapports en `0x400ab0e4`.
Les changements d'octave de COLOR sont isolés en `0x400ab102..0x400ab154` ;
la suite commune est `0x400ab158`. Le hook des rapports peut donc charger les
quatre rapports, y compris celui du premier opérateur, puis rejoindre cette
suite en gardant les gains natifs. Le chemin inactif reprend en `0x400ab0ea`.
Les registres vivants sont d2 (hauteur), a2 (voix), a3 (paramètres) et SP.

`[FAIT en émulation]` SHAPE garde son domaine natif 0..37 et son CC17 :
0..3 = BASE ; 4..7, 8..11, 12..15, 16..19 = CLS0..CLS3 ;
20..23, 24..27, 28..31, 32..37 = OPN0..OPN3.
BASE conserve les intervalles du degré. CLS ramène les notes dans une octave,
les trie puis déplace la plus grave d'une octave vers le haut zéro à trois fois.
Avec une triade, CLS3 est donc la triade une octave plus haut. OPN applique la
même inversion puis relève d'une octave les positions impaires (indices 1 et 3)
et trie de nouveau. L'identité des notes et le nombre de voix ne changent pas.
Une valeur modulée négative est bornée sur BASE ; au-delà de 32, OPN3.

Le format des réglages I–VII reste identique. Les anciens patterns Keys ON
contiennent toutefois déjà une valeur SHAPE, précédemment ignorée : cette
révision lui donne un effet audible. Pour retrouver la disposition de référence,
mettre SHAPE sur BASE et COLOR à 32. Keys OFF et notes hors gamme restent stock.
Aucun résultat matériel n'est revendiqué.


### 12.1. Plafond aigu du premier opérateur

`[FAIT : désassemblage et émulation]` En `0x400ab1f2`, l'OS compare la fréquence
intermédiaire à `0x454800`. Au-delà, `0x400ab208..0x400ab20c` annule le gain des
opérateurs 1–3, mais conserve l'ancien incrément du premier. Les inversions
rendent ce chemin accessible : avec fondamentale MIDI 74, TRI et CLS3/OPN3,
PITCH 74 / FINE 95 reste en plage, tandis que FINE 96 dépasse le seuil. Une
frappe aiguë pourrait donc conserver la fréquence de la frappe précédente.

Le wrapper prépare uniquement en mode actif l'incrément du premier opérateur
(`voice+0x70`) au plafond déterministe `0x000bd2f1` (774 897). C'est la conversion
native du seuil : `((0x454800 * 0x57619f10) >> 31) >> 2`. Dans la plage normale,
l'update stock le réécrit avec la bonne fréquence. Dans l'extrême aigu, il reste
au plafond ; les autres voix conservent leurs coupures natives. Aucun hook ni
état partagé supplémentaire n'est nécessaire. Keys OFF conserve son chemin stock.

La régression persistante prépare deux incréments antérieurs différents, sur
les pistes 1 et 6, neuf dispositions, TRI et 9, et trois cas fondamentale/PITCH.
Elle contrôle l'indépendance de l'historique et le retour correct dans le grave.
Huit frontières PITCH/FINE vérifient le plafond exact, après reset et après une
note grave. La sonde indépendante d'investigation a comparé 1 152 combinaisons :
en plage, l'état complet des six voix reste identique ; hors plage, seul
l'incrément du premier opérateur change.

### 12.2. Preuve musicale et coût

`[FAIT en émulation]` Les 14 000 accords BASE restent conformes à la table
historique, avec un écart maximal de 0,877 cent face aux notes stock. Les
2 205 cas supplémentaires (7 modes × 5 extensions × 7 degrés × 9 dispositions)
conservent les classes de notes et le nombre de voix, avec un écart maximal de
0,811 cent. Les exemples indépendants de Do, Do maj7 et Do maj9 fixent les notes
attendues dans les neuf positions. Le balayage de COLOR couvre ses 128 valeurs
pour chaque disposition, sur TRI et 9 : mêmes gains natifs, aucun changement
d'octave. La triade garde le quatrième opérateur muet.

Les frontières signées Q8, PITCH/FINE, les six pistes et les changements
BASE → CLS1 → OPN3 → BASE sont contrôlés. Les paramètres d'origine et les
extensions persistantes restent intacts. Les tests fournissent les paramètres
effectifs au moteur ; ils ne prouvent pas la capture/relecture complète d'un
parameter lock ni le routage CC/LFO sur la machine.

Mesure du JSON final avec le vrai getter, six pistes CHORD, par bloc :

| État | Instructions stock | Instructions modifiées | Supplément |
|---|---:|---:|---:|
| Keys OFF | 51 368 | 54 254 | 2 886 |
| BASE | 51 488 | 55 475 | 3 987 (7,74 %) |
| OPN3 | 51 536 | 58 091 | 6 555 (12,72 %) |

Ces pourcentages comparent des **instructions émulées dans ce scénario**, pas
la charge CPU réelle. Le calcul utilise au plus quatre notes, des boucles
bornées et des entiers, sans allocation ni oscillateur ajouté. La pile observée
reste à 224 octets contre 104 pour l'OS (120 octets supplémentaires). La charge
réelle avec six accords ouverts, effets et USB doit être mesurée sur la machine.

### 12.3. Essai matériel complémentaire attendu

`[À FAIRE : Maxime]` Comparer BASE, CLS0–3 et OPN0–3 sur TRI, 7 et 9 ; vérifier
que changer COLOR ne déplace aucune octave et que modifier I–VII reste la seule
façon de choisir l'extension. Contrôler le nom Chord Voicing et les neuf valeurs
sans texte coupé. Passer de piste en piste avec Keys ON/OFF, vérifier les
parameter locks, CC17 et la modulation de SHAPE, puis sauvegarder/recharger.
Sur les anciens patterns Keys ON, remettre SHAPE sur BASE et COLOR à 32 avant
comparaison. Essayer les transitions grave/aigu/grave avec PITCH/FINE et six
pistes en OPN3 sous effets et USB. Les contrôles de §10 restent requis.


### 12.4. Affichage et implantation

`[FAIT : désassemblage et émulation]` Le descripteur SHAPE reste à
`0x4010eca0` (0..37, défaut 3, CC17), COLOR à `0x4010ec68` (0..127, défaut 32,
CC16). Les mots de paramètres, le format du projet et les dix lignes du menu
restent inchangés. L'objet de paramètres est identifié dans le tableau de six
objets de huit octets à `banque+504+8*piste`, obtenu par `0x4000eb9c` ; les
réglages d'une autre piste sélectionnée n'affectent donc pas son affichage.

| Accroche | Avant | Avec Keys ON sur CHORD, descripteur 72 |
|---|---|---|
| `0x400fd170` | formatter `0x4000a70e` | `ck_shape_format` fournit BASE / CLS0–3 / OPN0–3 |
| `0x400fd174` | dessin spécial `0x4000a66a` | `ck_shape_draw` affiche la valeur avec la police moyenne |
| `0x4001e4ca` | appel du nom `0x4000b22a` | `ck_shape_name` fournit Chord Voicing |

Le repli numérique stock utilise une police de 16 pixels : quatre caractères
occuperaient 67 pixels dans un panneau de 64. Le dessin contextuel utilise la
police stock `0x4014120c`, sept pixels par glyphe : **31 pixels** pour ces neuf
libellés. Les vraies métriques et routines de dessin sont exécutées dans la
preuve ; les neuf bitmaps sont différents et restent dans `x=81..111`,
`y=40..48` pour le popup testé. Le retour général du §13 ne détaille pas une vérification physique de chaque libellé. Les autres
machines, paramètres, objets et pistes avec Keys OFF délèguent aux routines
natives. Le libellé dépend de la piste, pas de la dernière note : une note MIDI
hors gamme conserve le SHAPE stock sonore même si ce popup affiche le voicing.

Le JSON final contient **37 écritures**, neuf accroches et quatorze paires
code/redirection. **5 035 octets** de code, constantes et état occupent les
masques suivants ; leur exemplaire graphique conservé est `0x40172220`.

| Cave | Octets écrits |
|---|---:|
| `0x4016b6f8` | 376 |
| `0x4016b9e8` | 374 |
| `0x40171f30` | 376 |
| `0x40172608` | 362 |
| `0x40179730` | 373 |
| `0x40182b38` | 376 |
| `0x40182e28` | 376 |
| `0x40183118` | 374 |
| `0x40185018` | 372 |
| `0x40185968` | 376 |
| `0x40185c58` | 372 |
| `0x4018cd48` | 376 |
| `0x4018d1b8` | 372 |
| `0x4018d4a8` | 180 |

Les deux nouvelles caves `0x4018d1b8` et `0x4018d4a8` ont seulement leurs
pointeurs de constructeur en `0x400acd76` et `0x400acd56`, tous deux redirigés.
Le scan des **376 octets complets des 19 réserves** ne révèle aucune nouvelle
entrée exécutable ; seuls les trois faux positifs déjà expliqués en §6
persistent. Les cinq réserves restantes gardent aussi une référence unique.
Le tableau mutable des seize captures reste en `0x40182e28` ; le calcul sonore
reste entièrement local à chaque appel. Aucun nouveau payload ni accès aux
sections autres que MAIN OS n'est ajouté.


### 12.5. Validation de la révision

`[FAIT en émulation]` Le JSON final passe **211 contrôles seul**, **215 avec
6ch-usbup, latching-mute, trig-preview, browser-scroll, trig-hold, arp, tempo-max,
boot-anim et les cinq moteurs Syntakt**. Dans la combinaison, les comptes avec
getter sont 52 987 → 55 873 en OFF, 53 100 → 57 089 en BASE et
53 141 → 59 685 en OPN3. Le régulateur garde le PCM à 50 % simulés, ignore le
pic isolé à 99 %, déclenche le fondu au bloc 41 en surcharge répétée et laisse
rejouer les accords après retrig. Il s'agit de durées injectées, pas d'une mesure
physique du calcul audio.

Le banc UI combiné mappe la charge Syntakt à `0x43000000`, comme le boot et le
banc audio, afin d'exécuter ses véritables accesseurs de descripteurs lors des
replis stock. Sans ce mapping de fixture, la preuve tentait un fetch non mappé
en `0x43033028` ; aucune correction de firmware n'était nécessaire.

Les générateurs `--check`, `relocate_6ch.py --check` avec le wrapper binutils
`-S` documenté en §9, la compilation Python, la syntaxe JavaScript, les
comparaisons builders/flashers et le parcours UI synthétique passent.
`REF_MAINOS --check` confirme les **17 407 références** régénérées. Le build
Chord Keys seul conserve à l'octet près les sections **2, 4 et 5** de l'image
officielle ; seule la section **3** change. Les fichiers firmware restent ignorés.

Le banc indépendant `tools/emu/test_governor.py` passe aussi ses **12 contrôles**
sur les cinq moteurs Syntakt, avec minuteur et gains de mixeur simulés : charge
normale, surcharge, choix des voix à éteindre, reprise et moyenne lente.

Le parcours réel du flasher valide exactement les **17 407 combinaisons**
proposées, avec concordance des références et aucune erreur JavaScript
(`SMOKE_JOBS=4 tools/webflash_smoke.sh …` : `ALL PARTS OK`). Les 8 192 références
contenant Chord Keys changent ; les 9 215 autres restent identiques.

Limite pratique : les positions ouvertes peuvent pousser des voix supérieures
hors plage sur les TRIG aigus, même avec PITCH/FINE neutres. Baisser Root, par
exemple à C2, laisse davantage de marge. La disposition BASE reste le point de
départ de référence. **À la clôture de cette validation logicielle, avant le retour du §13 : statut expérimental,
sans essai matériel rapporté.**

## 13. Chord Keys seul testé sur la machine par Nico (06/10/2026)

**Source : retour de Nico dans cette conversation, sans lien public.** Après la révision SHAPE/COLOR du §12,
Nico indique : « en mi maquina ya funciono perfectamente » et précise que le test a été fait **sans aucun
autre mod sur un vrai Model:Cycles**. Il demande de publier un flasher propre au fork et de distinguer ce
retour matériel des vérifications logicielles de compatibilité. Il s'agit du retour de **Nico, pas de Maxime**.
La méthode de transfert, la durée de la session et une liste détaillée de gestes testés n'ont pas été rapportées.

| Portée | Résultat et limite |
|---|---|
| Chord Keys seul, révision SHAPE/COLOR | Fonctionnement rapporté par Nico sur son Model:Cycles le 06/10/2026, sans autre mod ; ce retour ne vaut pas validation détaillée de tous les points des §10 et §12.3 |
| Chord Keys avec les mods compatibles | **Logiciel uniquement, aucun essai matériel rapporté** : 215 contrôles en émulation pour l'image combinant `6ch-usbup`, `latching-mute`, `trig-preview`, `browser-scroll`, `trig-hold`, `arp`, `tempo-max`, `boot-anim` et `syntakt-sd-cp-toy-bits-swarm` (les cinq moteurs) ; 211 contrôles avec Chord Keys seul |
| Toutes les sélections proposées avec Chord Keys | 8 192 combinaisons vérifiées par construction et empreintes au sein des 17 407 combinaisons du flasher ; cela ne signifie pas que chaque combinaison a reçu une émulation fonctionnelle complète |
| Model-TG / Model-TG-ST | Incompatibilité déclarée, non proposés avec Chord Keys |
| Samples OS | Autre OS, installation distincte de Chord Keys |

Les cinq moteurs de la preuve combinée sont **SD VINTAGE, CP VINTAGE, SY TOY, SY BITS et SY SWARM**.
Avec l'arpégiateur, les grands pads T1–T6 gardent son comportement ; les touches d'accords TRIG inférieures
ne déclenchent pas d'arpège. La compatibilité annoncée reste limitée à ces preuves logicielles et à leurs
scénarios ; les combinaisons nécessitent encore des essais sur un Cycles réel.

Le [flasher du fork de Nico](https://bynicoheuser.github.io/Modded-Cycles/flasher/) publie les patchs et construit
le firmware dans le navigateur à partir de l'OS officiel fourni par chaque utilisateur. Aucune image officielle
ou modifiée n'est distribuée. Ce site est distinct du flasher amont de Maxime.


## Présentation du flasher (06/10/2026)

À la demande de Nico dans ses annotations du site, la carte porte le nom **Chord Keys** et apparaît
avant les autres mods. Sa ligne de crédit et sa note détaillée sont retirées de la carte ; la rubrique
« Anciens patterns » est retirée du guide, dans les deux langues. La provenance reste conservée dans
les métadonnées. Seul l’ordre d’affichage change : l’ordre de construction, les patchs, les empreintes
et les statuts des essais restent identiques.

## 14. Projet de jeu harmonique et d'extensions par famille (06/10/2026)

**Source : discussion avec Nico, sans lien public.** Nico accepte le principe des pads de
modification harmonique et demande de reporter l'implémentation à une autre conversation.
Il demande ensuite de préciser les extensions musicales, communes aux réglages et aux pads,
avec leurs variantes et les références HiChord, Orchid et Nopia.

**Statut : conception uniquement.** Cette section ne décrit pas le firmware livré ; aucune
nouvelle preuve en émulation ni aucun essai matériel ne couvre ce projet. Le comportement
diatonique documenté plus haut reste celui de la version actuelle.

Les propositions ont évolué pendant la discussion : lire **§14.8 en priorité** pour
la décision de fusionner disposition et mélange sur SHAPE, et **§14.7** pour la matrice
simplifiée et les corrections de superposition. Les tableaux précédents conservent
l'historique du raisonnement et ne constituent pas des exigences cumulatives.

### 14.1. Principe accepté pour les pads

Dans un mode de pads HARMONY, les TRIG continuent à choisir les degrés. Les six pads sont
assignables ; leur affectation initiale proposée dans la discussion est la suivante :

| Pad | Action | Exemple |
|---|---|---|
| T1 | Extension 9 | Em7 → Em9 |
| T2 | Extension 11 ou ♯11 selon la famille | Dm7 → Dm11 ; Cmaj7 → Cmaj7(♯11) |
| T3 | Extension 13 | G7 → G13 |
| T4 | SUS, remplacer la tierce par la quarte | G9 → G9sus4 |
| T5 | Parallèle majeur/mineur, en conservant le niveau d'extension | Fmaj9 → Fm9 |
| T6 | Dominante de la cible, fixée à la septième | TRIG Am9 → E7 pendant l'appui, puis Am9 au relâchement |

Sans pad, le réglage enregistré du degré s'applique. Un pad d'extension **remplace
temporairement** ce choix ; il ne cumule pas les extensions et ne réécrit pas le pattern.
Ainsi, EXT 9 + pad 13 donne le voicing de 13 ; au relâchement, retour au voicing de 9.
EXT 9 + pad 9 ne change rien. L'assignation permettrait de choisir TRI ou 7 à la place.
Une seule modification harmonique est active à la fois dans la première version envisagée.

Objectif de jeu : pouvoir maintenir le pad avant le TRIG, ou modifier un accord déjà tenu,
puis revenir au réglage enregistré **sans redéclencher l'enveloppe**. Ce dernier point est un
objectif à prouver, pas une capacité déjà démontrée. Un mode TRACK conserve le jeu natif des
pads. Le routage exact des touches, la sélection des pistes et les combinaisons FUNC/mute
devront être spécifiés et prouvés avant toute modification.

### 14.2. Politique musicale recommandée, soumise à la discussion

**[PROPOSITION, pas encore une décision de Nico]** La fondamentale, la tierce, la quinte et
la septième de départ viennent du degré dans le mode choisi. L'extension vient ensuite
d'une table de familles, commune au menu et aux pads. Une triade majeure ne suffit donc
pas à décider de la septième : en do majeur, I et IV donnent maj7, V donne 7 dominante.
En la mineur naturel, le V reste Em ; le passage à E7 demande une transformation explicite.

Les intervalles se calculent depuis la fondamentale de l'accord : 9 = 14 demi-tons,
11 = 17, ♯11 = 18, 13 = 21. « Naturelle » ne veut pas dire « dans la tonalité globale » :
Em9 utilise F♯, Em11 utilise A, Em13 utilise C♯, même dans une progression en do majeur.

| Famille | EXT 7 | EXT 9 | EXT 11 | EXT 13 |
|---|---|---|---|---|
| Majeure avec septième majeure | maj7 | maj9 | maj7(♯11) | maj13 |
| Mineure avec septième mineure | m7 | m9 | m11 | m13 |
| Dominante | 7 | 9 | 7(♯11) | 13 |
| Semi-diminuée | m7♭5 | Repli m7♭5 proposé pour la première version | Même repli | Même repli |

Ce choix forme une palette ; il ne prétend pas déterminer la meilleure tension pour toute
mélodie ou toute progression. Le menu peut conserver les niveaux 9/11/13, mais le nom de
l'accord résultant doit indiquer la véritable altération, notamment ♯11.

**Variantes à distinguer explicitement :**

- Sur maj7, ♯11 est un choix lydien fréquent. La 11 naturelle est également possible,
  avec un frottement marqué contre la tierce majeure ; SUS remplace cette tierce au lieu
  de conserver ce frottement.
- Sur m7, 9 et 11 naturelles sont les choix de départ. La 13 naturelle donne une couleur
  dorienne ; ♭13 donne une autre couleur, notamment éolienne, et doit être nommée m7(♭13).
  Une ♭9 peut servir une couleur phrygienne volontaire. Le choix m(maj7) est aussi distinct
  de m7 ; il n'est pas déduit automatiquement de toute triade mineure.
- Sur dominante, 9 et 13 naturelles sont les valeurs de départ. ♭9, ♯9 et ♭13 sont de
  véritables tensions usuelles, à choisir explicitement. Pour la quarte, les solutions
  7sus4/9sus4 et 7(♯11) sont différentes : la première retire la tierce, la seconde la
  conserve. La recommandation ci-dessus choisit ♯11 pour EXT 11, puisque T4 donne SUS.
- Sur m7♭5, la 11 naturelle est une extension usuelle ; 9 naturelle ou ♭9 dépendent de
  la couleur recherchée, et ♭13 est une autre possibilité. Il n'existe pas de règle
  universelle imposant une 13 naturelle. Le repli proposé est une limitation volontaire
  de notre première version à quatre voix, pas une impossibilité musicale.
- add9 et 9 sont différents : add9 n'exige pas de septième, 9 en comporte une dans les
  voicings proposés. De même, 6/9 est un autre choix que 13.

### 14.3. Quatre voix : résultat sonore proposé

**[FAIT dans le code actuel]** `chord_keys.c` et `chord_audio.c` utilisent quatre voix au
maximum. Les niveaux 9/11/13 retiennent fondamentale, tierce, septième et tension, sans
quinte ; ils n'empilent pas toutes les tensions inférieures. La nouvelle politique
conserverait ce principe, avec des intervalles choisis par famille :

| Accord | Notes, avant disposition SHAPE |
|---|---|
| Cmaj9 | C–E–B–D |
| Cmaj7(♯11) | C–E–B–F♯ |
| Cmaj13 | C–E–B–A |
| Em9 | E–G–D–F♯ |
| Em11 | E–G–D–A |
| Em13 | E–G–D–C♯ |
| G9 | G–B–F–A |
| G7(♯11) | G–B–F–C♯ |
| G13 | G–B–F–E |
| G9sus4 | G–C–F–A |

Pour Bm7♭5, B–D–F–A utilise déjà les quatre voix. Omettre F supprimerait précisément
la quinte diminuée. Des voicings étendus restent possibles en omettant une autre note,
par exemple la fondamentale si un bassiste la joue, mais cela change les hypothèses du
jeu autonome. **Recommandation conservatrice pour la première version :** conserver
m7♭5 pour les demandes 9/11/13 sur cette famille, afficher le véritable résultat et
signaler cette limite dans le guide. Ne pas afficher une extension qui ne sonne pas.
Nico peut préférer une autre politique de voicing ; cette exception reste à valider
avec lui avant l'implémentation. m7♭5 ne doit pas être confondu avec dim7.

### 14.4. Références et limites de la comparaison

- [Open Music Theory, symboles](https://viva.pressbooks.pub/openmusictheory/chapter/chord-symbols/)
  distingue qualité de l'accord, intervalles des extensions et altérations explicites.
  Son chapitre [voicings](https://viva.pressbooks.pub/openmusictheory/chapter/jazz-voicings/)
  traite des omissions ; celui sur les [accords et modes](https://viva.pressbooks.pub/openmusictheory/chapter/chord-scale-theory/)
  explique pourquoi le contexte compte au-delà de la seule famille.
- [Wayne Naus, Berklee](https://college.berklee.edu/berklee-today-55) propose notamment
  9/♯11/13 sur maj7 et 9/11 sur m7 dans un exercice de réharmonisation. Il précise que
  les règles de cet exercice s'affranchissent de la fonction dans la tonalité ; ce
  tableau n'est pas une loi universelle, et l'absence de m13 n'en interdit pas l'usage.
- [HiChord, manuel bêta Rev 3.0](https://hichord.github.io/hichord-beta-updater/manual/#joystick),
  consulté le 06/10/2026 : le joystick applique des transformations momentanées et
  revient au départ au relâchement. Le mode Default produit notamment maj9 ou m9 ;
  sur l'accord diminué, son geste 9 donne m7♭5. Extended distingue add9, add11, min11,
  dom9 et dom7♯9 ; Chromatic propose d'autres couleurs. Ce sont des choix explicites
  de familles et de voicings. Notre règle ♯11 sur les accords majeurs et dominants
  n'est pas présentée comme l'algorithme de HiChord.
- [Orchid, documentation officielle](https://support.telepathicinstruments.com/hc/en-us/articles/16576229505167-Chord-Extensions-Explained) :
  les boutons d'extension ajoutent des notes et peuvent se combiner. Ce fonctionnement
  diffère de nos pads exclusifs. La page ne fournit pas une table complète de tensions
  automatiques pour chaque degré.
- [Nopia, entretien avec les créateurs](https://www.musicradar.com/music-tech/this-is-just-the-beginning-nopia-launches-on-kickstarter-and-hits-usd1-4m-in-24-hours) :
  les créateurs décrivent le centre tonal, le contrôle des extensions, les dominantes
  secondaires et l'emprunt modal. Aucune table publique exhaustive de leurs choix
  d'intervalles par degré n'a été trouvée ; ne pas leur attribuer notre matrice.

### 14.5. Reprise dans une autre conversation

**[À FAIRE]** Arrêter avec Nico les recommandations du §14.2, surtout ♯11 sur dominante,
13 naturelle sur mineur et le repli des semi-diminués. Définir le résultat de SUS et
PARALLÈLE pour chaque famille/niveau, la priorité de pads simultanés et la portée de
leur assignation. Les exemples simples ci-dessus ne constituent pas encore une table
complète de ces deux transformations.

La représentation actuelle réserve trois bits par degré ; des variantes supplémentaires
nécessiteraient un choix de stockage et de migration explicite. Préserver les anciens
patterns demande également de décider comment ils choisissent l'ancienne ou la nouvelle
politique harmonique. Le séquenceur ne stocke actuellement que la note fondamentale :
ne pas promettre l'enregistrement des gestes de pads avant d'en définir la représentation.
L'audio et l'UI devront partager les mêmes règles harmoniques, puis recevoir les preuves
requises par le dépôt, notamment pour le changement sans retrigger et le retour stock.

### 14.6. Palettes harmoniques proposées par Nico (06/10/2026)

**Source : suite de la même discussion.** Nico propose plusieurs palettes, par exemple
Jazz, Soul, Spanish et Tango, qui changeraient les choix d'extensions. Cette orientation
remplace l'idée d'imposer la matrice du §14.2 à tous les usages. Le contenu exact des
palettes ci-dessous reste une **proposition de conception**, sans implémentation.

La palette choisit les intervalles et le voicing réduit à partir du mode, du degré, de
la famille et du niveau d'extension demandé. La même règle sert aux settings et aux
pads. Des palettes peuvent partager certains accords : leur différence ne doit pas
être inventée pour remplir une table. Les noms de genres désignent des palettes
inspirées de ces pratiques, pas une statistique exhaustive ni une définition du genre.

| Palette envisagée | Orientation proposée |
|---|---|
| DIATONIC | Conserver exactement le calcul diatonique existant, y compris ses voicings et ses tensions parfois altérées |
| JAZZ | Départ sur la matrice §14.2 : 9 naturelles, 11 mineure/♯11 majeure et dominante, 13 naturelles ; une variante plus fonctionnelle ou altérée pourra être distincte |
| SOUL | Départ maj9, m9, m11 ; favoriser les dominantes suspendues pour 11 et 13, par exemple 9sus4 et 13sus4 |
| SPANISH | Explorer ♭9 et ♭13 sur les accords dominants appropriés, en distinguant dominante d'une tonalité mineure et accord de repos du flamenco phrygien |
| TANGO | Explorer les tensions de dominante selon la résolution, notamment ♭9 vers une cible mineure ; ajouter les choix explicites 6/m6 pour les accords de repos |

Exemple concret de différence à définir dans les tables : sur G7, EXT 11 donnerait
G7(♯11) en JAZZ et G9sus4 en SOUL ; EXT 13 donnerait G13 en JAZZ et G13sus4 en SOUL.
Voicings autonomes possibles à quatre voix : G–B–F–C♯, G–C–F–A, G–B–F–E et
G–C–F–E respectivement. Le dernier omet la 9. Sur Em, EXT 9 peut donner Em9 dans
les deux palettes. Ce recouvrement est voulu.

**Règles d'interface proposées :**

- Un sélecteur PALETTE s'applique à l'ensemble du clavier Chord Keys configuré et se
  sauvegarde avec ses réglages. Il ne faut pas devoir choisir une palette pour chaque degré.
- Les gestes restent prévisibles : T1 demande 9, T2 demande 11, T3 demande 13 ; la
  palette précise les altérations ou la suspension. T4/T5/T6 gardent leur rôle annoncé.
  T6 reste la dominante de la cible à la septième simple, conformément au §14.1 ;
  une variante qui l'enrichit serait un choix explicite supplémentaire.
- Le pad remplace le niveau enregistré pendant l'appui ; au relâchement, le degré
  revient au niveau enregistré, interprété dans la même palette. EXT 9 + pad 9
  continue donc à ne rien changer.
- Le nom affiché doit refléter les notes : ♭9, ♯11, sus, etc. TRI reste une triade.
  Les choix 6/m6, add9 ou 6/9, s'ils sont ajoutés, portent leur propre nom ; ne pas
  transformer silencieusement EXT 13 en m6 ou EXT 9 en add9.
- Le choix d'une palette ne change pas tacitement la fondamentale, le mode ou la
  qualité majeure/mineure de base. La suspension explicitement prévue est une
  exception décrite par la table. Les transformations PARALLÈLE/V7 restent explicites.
  SHAPE continue à choisir la disposition des notes ; pas de modification automatique
  de ce réglage par le nom du genre.

Un preset flamenco complet exigerait aussi de définir le mode et les qualités de degrés :
un repos sur E majeur avec F naturel ne s'obtient pas seulement en altérant la 9 d'Em.
Il faut distinguer ce futur preset complet de la seule palette d'extensions SPANISH.
De même, l'orientation TANGO ne doit pas être réduite à « toutes les extensions bémolisées ».

Repères consultés : [cours de Hayden Hill sur le neo-soul](https://www.pianogroove.com/live-seminars/neo-soul-jazz-harmony/)
(m9/m11, accords suspendus et 13), [Kai Narezo sur la rumba et le flamenco](https://www.berklee.edu/berklee-today/summer-2016/rumba)
(repos phrygien avec tierce majeure et ♭9),
[programme de piano harmonique du Conservatoire Julián Aguirre](https://web.consaguirre.com.ar/archivos/Prog_superior/2016-prog_piano_arm_inst_sup.pdf)
(travail de iiø–V7♭9–i avec différentes qualités de tonique, puis accompagnement
de tango/zamba). Ces références justifient des ressources musicales disponibles,
pas une mesure de fréquence des accords dans chaque genre.

**[À FAIRE]** Définir et écouter la table complète de chaque palette, y compris les
semi-diminués et les niveaux peu caractéristiques d'un style. Vérifier les voicings
à quatre voix avant de fixer les intitulés. Décider comment les anciens patterns
conservent DIATONIC et comment la palette des nouveaux patterns est initialisée.

### 14.7. Matrice simplifiée : éviter les fonctions concurrentes (06/10/2026)

**Source : nouvelle demande de Nico.** Il demande une table des extensions et des pads
pour chaque palette, sans superposition de fonctions, et veut vérifier le rôle des
différents modes. Si Spanish ne fait que choisir un autre mode, il préfère utiliser
le sélecteur de gamme existant. **Ce qui suit est une recommandation révisée à discuter,
pas une implémentation ni une validation par Nico des changements de mapping.**

#### Répartition des responsabilités

| Contrôle | Responsabilité |
|---|---|
| ROOT + SCALE | Fondamentales des sept degrés et familles des accords de base |
| PALETTE | Intervalles des extensions demandées ; ne change ni fondamentale ni tierce ni septième de base |
| EXT par degré | Niveau enregistré : TRI, 7, 9, 11, 13 |
| T1–T6 | Modification temporaire explicite, sans réécrire EXT |
| SHAPE | Disposition/inversions des notes retenues |

La suspension automatique de la proposition SOUL du §14.6 concurrençait directement
le pad SUS. La recommandation révisée retire cette suspension automatique : les
palettes d'extensions conservent la tierce. La distinction Jazz/Soul n'est donc plus
assez nette dans ces seules tables pour justifier deux choix. Leurs autres ressources
restent accessibles par les extensions, SUS, PARALLÈLE et SHAPE.

SPANISH ne devient pas un second sélecteur de gamme. `[FAIT dans le code]` SCALE offre
actuellement MAJ, DOR, PHR, LYD, MIX, MINOR, LOC. Le phrygien dominant n'en fait pas
partie. PHR donne une tonique mineure ; un repos flamenco avec tierce majeure exige
une transformation explicite ou un mode supplémentaire, avec ses nouvelles familles
à définir. Le phrygien dominant est un repère possible, pas une définition exhaustive
de la pratique flamenca.

TANGO n'est pas fixé comme palette indépendante sans règles supplémentaires justifiées.
6/m6 serait un choix explicite EXT 6, disponible dans tous les styles, et non un
changement caché de EXT 13. Un futur preset de style pourrait réunir des réglages
existants ; il ne devrait pas introduire une seconde logique de construction.

#### Trois palettes de départ proposées

Les intervalles sont relatifs à la fondamentale de l'accord joué, même lorsque ce
degré n'est pas la tonique du mode.

| Palette | Famille | EXT 9 | EXT 11 | EXT 13 |
|---|---|---|---|---|
| DIATONIC | Toutes | Degré diatonique +8 | Degré diatonique +10 | Degré diatonique +12 |
| JAZZ | maj7 | 9 | ♯11 | 13 |
| JAZZ | m7 | 9 | 11 | 13 |
| JAZZ | dominante 7 | 9 | ♯11 | 13 |
| TENSION | maj7 | 9 | ♯11 | 13 |
| TENSION | m7 | 9 | 11 | 13 |
| TENSION | dominante 7 | ♭9 | ♯11 | ♭13 |

TRI et 7 restent identiques entre les palettes. TENSION est un choix explicite de
dominantes plus tendues ; ce n'est pas une déduction de la résolution future ni
une promesse que cette résolution convient à la mélodie. Les tensions partagées
entre palettes ne sont pas des commandes dupliquées : ne pas modifier artificiellement
les accords pour rendre toutes les cases différentes.

Sur G7, les triplets de résultats JAZZ sont G9 / G7(♯11) / G13 ; TENSION donne
G7(♭9) / G7(♯11) / G7(♭13). Leurs voicings restent fondamentale, tierce, septième,
tension. Sur Cmaj7 et Em7, les deux palettes coïncident volontairement.

**Exception à traiter avant implémentation : m7♭5.** Pour éviter les trois commandes
équivalentes proposées au §14.3, ne plus recommander le repli silencieux 9/11/13 → 7.
Tant qu'un voicing étendu adapté n'est pas choisi, annoncer ces niveaux comme
indisponibles sur cette famille ; TRI et 7 conservent la quinte diminuée. Le code
actuel omet la quinte sur tous les degrés aux niveaux 9/11/13, donc une stricte
compatibilité des anciens patterns et cette nouvelle restriction ne sont pas
identiques. Leur migration reste à spécifier ; ne pas réécrire les anciens sons
implicitement. Des voicings sans fondamentale ou sans tierce pourraient permettre
ces tensions, au prix d'autres compromis : aucune impossibilité musicale n'est affirmée.

#### Mapping de pads révisé proposé

| Pad | Demande | Dépendance à PALETTE |
|---|---|---|
| T1 | 9 temporaire | Ligne EXT 9 de la table |
| T2 | 11 temporaire | Ligne EXT 11 de la table |
| T3 | 13 temporaire | Ligne EXT 13 de la table |
| T4 | SUS7 fixe : 1–4–5–♭7 | Aucune : toujours 7sus4, indépendant d'EXT enregistré |
| T5 | PARALLÈLE | Transformer la famille, puis recalculer le niveau EXT enregistré dans la palette |
| T6 | V7 de la cible | Aucune : septième dominante simple, comme au §14.1 |

Le T4 fixe est une **révision proposée** du SUS qui conservait EXT : il évite le
cas d'une 11 doublant la quarte suspendue ou d'une ♯11 frottant automatiquement
avec elle. Exemples : Cmaj13 → C7sus4, G9 → G7sus4. Les variantes 9sus4 et 13sus4
peuvent être des affectations explicites alternatives du pad assignable ; elles
ne sont pas appliquées par la palette. EXT 6 serait aussi un choix explicite,
avec C6 ou Cm6 selon la tierce, sans septième ajoutée ni altération par la palette.
Ces ajouts d'affectations et EXT 6 restent à valider avant de changer le menu.

Pour T5 : maj7 → m7, m7 → maj7, dominante 7 → m7 ; conserver la fondamentale et
le niveau EXT, puis résoudre la nouvelle famille. Exemples Fmaj9 → Fm9 et Fm9 →
Fmaj9. Il ne s'agit pas seulement de bouger une tierce en conservant chaque autre
note, ni d'une bascule qui resterait mémorisée. Sur une triade, le résultat reste
une triade. Sur m7♭5, ne pas inventer une conversion parallèle automatique.
Pour T6, la cible doit être majeure ou mineure : ne pas promettre une tonicisation
conventionnelle d'un accord diminué. Les cas non pris en charge doivent être visibles.

Un seul pad modificateur agit à la fois. Pour des appuis qui se chevauchent, proposition
déterministe : le dernier appuyé prévaut ; son relâchement restaure le précédent encore
tenu, puis le réglage enregistré lorsqu'il n'en reste aucun. Tous ces gestes nécessitent
encore une preuve d'émulation du changement sans retrigger.

**Limite assumée :** EXT 9 + T1 redemande le même accord. Éviter cette égalité en changeant
secrètement T1 en « retirer la 9 » rendrait le geste contextuel. Garder son sens constant
et permettre une autre affectation explicite (TRI, 7 ou 6, par exemple). Les settings
définissent le repos ; les pads définissent les écarts temporaires.

#### Interaction avec les sept modes actuels

Voici les tensions théoriques du **degré I** ; pour un autre degré, refaire le calcul
depuis sa propre fondamentale. Les trois valeurs représentent 9 / 11 / 13.

| SCALE | Famille de I | DIATONIC | JAZZ | TENSION |
|---|---|---|---|---|
| MAJ | maj7 | 9 / 11 / 13 | 9 / ♯11 / 13 | 9 / ♯11 / 13 |
| DOR | m7 | 9 / 11 / 13 | 9 / 11 / 13 | 9 / 11 / 13 |
| PHR | m7 | ♭9 / 11 / ♭13 | 9 / 11 / 13 | 9 / 11 / 13 |
| LYD | maj7 | 9 / ♯11 / 13 | 9 / ♯11 / 13 | 9 / ♯11 / 13 |
| MIX | 7 | 9 / 11 / 13 | 9 / ♯11 / 13 | ♭9 / ♯11 / ♭13 |
| MINOR | m7 | 9 / 11 / ♭13 | 9 / 11 / 13 | 9 / 11 / 13 |
| LOC | m7♭5 | ♭9 / 11 / ♭13 en théorie | Voicing étendu à définir | Voicing étendu à définir |

Les modes gardent leur rôle : fondamentales et familles des autres degrés diffèrent.
En revanche, une palette chromatique peut atténuer le caractère du mode sur un accord.
Exemples : I en mi phrygien + 9 donne F en DIATONIC et F♯ en JAZZ ; I en la mineur
naturel + 13 donne F en DIATONIC et F♯ en JAZZ ; III en do majeur + 9 donne F en
DIATONIC et F♯ en JAZZ, ce qui répond à la demande initiale Em9.

Le workflow reste donc cohérent, mais la garantie que toute note appartient à SCALE
n'existe qu'en DIATONIC **sans transformation chromatique explicite de pad**. SUS7,
PARALLÈLE et V7 peuvent eux-mêmes sortir du mode. Une 9 naturelle fixe sur tout m7
et une préservation absolue du caractère phrygien ne peuvent pas être promises ensemble.
La table illustre des choix du produit ; elle ne remplace pas l'écoute du contexte
et de la mélodie. Voir [accords et modes, Open Music Theory](https://viva.pressbooks.pub/openmusictheory/chapter/chord-scale-theory/).

### 14.8. Décision : SHAPE combine disposition et mélange, COLOR choisit la palette (06/10/2026)

**Source : discussion avec Nico, sans lien public.** Il propose : « podriamos mergear
COLOR y SHAPE en un solo knob, y usar el otro para variar las paletas ». Après la
proposition SHAPE → VOICING et COLOR → PALETTE ci-dessous, il répond : « dale en otro
chat arranco la implementacion ». **Orientation acceptée ; implémentation reportée
à une autre conversation.** Aucun code firmware, tweak ou résultat de test n'est
modifié par cette décision.

#### Organisation retenue pour la suite

| Commande | Rôle prévu avec Chord Keys actif |
|---|---|
| ROOT + SCALE | Fondamentales des degrés et familles des accords de base |
| I–VII / EXT | Niveau habituel de chaque degré : TRI, 7, 9, 11 ou 13 |
| SHAPE → VOICING | Une macro combinant disposition/inversions et balance des voix |
| COLOR → PALETTE | Trois états nommés : DIATONIC, JAZZ, TENSION, selon la matrice §14.7 |
| TRIG 1–16 | I–VII, I–VII à l'octave, I–II deux octaves plus haut |
| T1–T6 en HARMONY | Modifications temporaires selon la proposition §14.7 ; TRACK conserve le jeu natif |

La fusion signifie que disposition et balance ne sont plus deux réglages indépendants.
Le point de départ proposé et accepté dans son principe conserve **BASE, CLS0–3 et
OPN0–3**, avec une balance conçue pour chaque disposition. BASE reste le point de
départ équilibré. Les valeurs de gains et les transitions restent à concevoir et à
écouter ; aucun tableau de gains n'a été arrêté. Ne pas simplement parcourir toute
la plage de COLOR stock en parallèle de SHAPE : certaines valeurs atténuent des voix
jusqu'au silence. La nouvelle macro doit garder audible l'extension demandée.

COLOR choisit une palette par états discrets, affichés clairement, sans interpolation
chromatique entre les notes des différentes palettes. La même palette gouverne EXT
et les pads d'extension T1–T3. Elle ne change ni la fondamentale, ni le degré joué,
ni la disposition sélectionnée avec SHAPE. Exemple : III en do majeur, EXT 9,
DIATONIC → Em7(♭9), JAZZ → Em9 ; SHAPE continue à disposer et équilibrer les voix.

**Précision musicale issue de la discussion :** les extensions diatoniques sont
courantes, y compris en jazz. JAZZ désigne notre choix de tensions par famille, pas
« les extensions correctes » ni une mesure de ce qui est le plus souvent joué.
L'affectation automatique de ♯11 aux majeurs/dominantes et de 13 naturelle aux mineurs
est un choix de cette palette. La proposition de la prendre par défaut pour les
nouveaux patterns n'a pas fait l'objet d'une décision explicite ; le défaut reste
à définir. Les références et limites du §14.7 s'appliquent toujours.

#### Point de reprise pour l'implémentation

`[FAIT dans le code actuel]` `tools/machines/chord_keys/chord_voicing.c` calcule les
neuf dispositions ; `chord_audio.c` les applique avant l'appel au moteur stock.
Les gains natifs de COLOR sont encore conservés, tandis que ses déplacements
d'octave sont contournés (§12). Cette séparation offre une piste pour réaffecter
les paramètres ; elle ne prouve pas encore le fonctionnement de la nouvelle macro.

`[À FAIRE]` Dans la prochaine conversation :

- Définir les balances associées à SHAPE, le découpage des valeurs COLOR et leurs
  libellés ; garder un seul choix de palette cohérent entre moteur, écran et réglages.
- Compléter les cas encore ouverts du §14.7, notamment m7♭5 et PARALLÈLE avec DIATONIC,
  puis les règles d'assignation des pads et le routage des raccourcis de pistes/mute.
- Définir stockage et migration : les anciennes valeurs SHAPE/COLOR, y compris leurs
  parameter locks, ne doivent pas changer implicitement les sons des anciens patterns.
- Prouver les modifications sur l'accord tenu et le retour au relâchement sans
  redéclenchement de l'enveloppe ; vérifier les pads superposés, le retour TRACK/Keys OFF,
  la sauvegarde/relecture, les CC/LFO/locks et les combinaisons de mods applicables.
- Ne pas présenter l'enregistrement des gestes T1–T6 comme acquis : le séquenceur
  actuel ne conserve que la fondamentale ; leur représentation reste à définir.
- Suivre les générateurs, preuves, documentation et PR brouillon prévus par AGENTS.md.
  Cette nouvelle révision doit rester expérimentale jusqu'à son propre essai matériel.

La discussion s'arrête ici à la demande de Nico ; commencer l'implémentation dans
l'autre conversation en lisant **§14.7 puis §14.8**, sans reprendre les propositions
antérieures comme des fonctions supplémentaires cumulatives.


## 15. Implémentation des palettes et des pads harmoniques (06/10/2026)

**Source : demande explicite de Nico dans cette conversation** : « Arranquemos la implementacion […]
el uso de los pads T1-T6 para cambios temporales […] el knob de color para elegir entre DIATONIC,
JAZZ, y TENSION […] y el shape para la distribucion y equilibrio de esas notas. » Cette révision
met en œuvre la direction des §14.7–14.8. Les propositions précédentes restent un historique,
pas une liste de fonctions supplémentaires. **Aucun essai matériel de cette révision n'est rapporté.**
Le retour positif du §13 concerne uniquement la version précédente, installée seule.

### 15.1. Contrat musical retenu

`[FAIT dans les sources]` Root, Scale et I–VII gardent leurs rôles. COLOR fournit une palette unique
aux extensions enregistrées et aux demandes temporaires T1–T3 : **0–42 DIATONIC**, **43–85 JAZZ**,
**86–127 TENSION**. Les frontières réelles portent sur les mots signés Q8 aux valeurs `43*256`
et `86*256`, sans interpolation des notes. Les valeurs inférieures restent DIATONIC, les supérieures
TENSION. TRI et 7 sont indépendants de la palette.

- DIATONIC choisit les degrés +8/+10/+12 de la gamme pour 9/11/13.
- JAZZ choisit 9/♯11/13 sur maj7 et dominante, 9/11/13 sur m7 et m7♭5.
- TENSION garde les choix JAZZ, sauf la dominante : ♭9/♯11/♭13.

La famille provient de la tierce, de la quinte et de la septième diatoniques du degré joué.
JAZZ/TENSION n'inférent ni une résolution future ni le style de la pièce. Les quatre voix des
extensions ordinaires sont fondamentale/tierce/septième/tension. **Décision d'implémentation m7♭5 :**
au niveau 9/11/13, garder fondamentale/quinte diminuée/septième/tension et omettre la tierce.
Cela rend l'extension distincte sans perdre la quinte caractéristique. Le chemin LEGACY conserve
son ancien choix, y compris son omission de quinte ; aucune migration implicite de l'ancien son.

| Pad en HARMONY | Transformation | Limite |
|---|---|---|
| T1 | EXT 9 dans la palette courante | Ne réécrit pas I–VII |
| T2 | EXT 11 dans la palette courante | Ne réécrit pas I–VII |
| T3 | EXT 13 dans la palette courante | Ne réécrit pas I–VII |
| T4 | SUS7 fixe : 0, 5, 7, 10 demi-tons | Indépendant de la palette et d'EXT |
| T5 | Majeur/dominante → mineur ; mineur → majeur, même fondamentale et niveau EXT | Indisponible sur diminué |
| T6 | V7 de la cible : 7, 11, 14, 17 demi-tons au-dessus de sa fondamentale | Indisponible sur diminué |

Pour PARALLEL + DIATONIC, la famille parallèle détermine les tensions : majeure 9/11/13,
mineure naturelle 9/11/♭13. C'est une transformation chromatique explicite, pas une promesse de
rester dans Scale. Les autres palettes utilisent la table de la famille transformée. SUS7 reste
fixe ; les variantes assignables, EXT 6 et d'autres palettes évoquées plus haut ne sont pas ajoutées.
Sur une demande T5/T6 indisponible, l'audio conserve l'accord de base du degré avec la palette courante.

### 15.2. SHAPE, COLOR et chemin audio

`[FAIT : image officielle et sources]` Les descripteurs restent stock : table à `0x4010dce0`,
entrées de 56 octets. **COLOR = descripteur 71**, `0x4010ec68`, machine 5, paramètre 11,
0..127 Q8, défaut 32, CC16. **SHAPE = descripteur 72**, `0x4010eca0`, paramètre 12,
0..37 Q8, défaut 3, CC17. Les formatters contextuels réemploient les trois crochets du §12.4.

En NEW, SHAPE garde BASE/CLS0–3/OPN0–3 et leurs mêmes plages. Le wrapper lit la palette avant de
remplacer COLOR dans sa **copie locale** par 32, afin de disposer de trois gains supérieurs positifs.
Il calcule les intervalles, applique la disposition, appelle l'update CHORD original et pondère les
gains supérieurs. Les paramètres partagés, locks et valeurs de l'OS ne sont pas réécrits.
Le cadre local fait **100 octets** ; les offsets partagés avec le hook assembleur restent identiques.

| SHAPE | Pondérations des trois positions supérieures, en trente-deuxièmes |
|---|---|
| BASE | 32 / 32 / 32 |
| CLS0 | 30 / 26 / 28 |
| CLS1 | 26 / 32 / 28 |
| CLS2 | 28 / 26 / 32 |
| CLS3 | 32 / 28 / 26 |
| OPN0 | 22 / 28 / 32 |
| OPN1 | 28 / 22 / 32 |
| OPN2 | 32 / 22 / 28 |
| OPN3 | 28 / 32 / 22 |

Le premier opérateur conserve son niveau natif. Les autres poids vont de 22/32 à 1, soit Q15
22 528..32 768 ; aucune voix demandée n'est volontairement réduite à zéro. Les poids suivent
les positions ordonnées graves→aigus après disposition, pas une identité permanente de tierce ou
septième. C'est un choix de départ à écouter, pas un équilibre matériel déjà validé.

`[FAIT : désassemblage]` `0x400aada4` écrit les gains en `voice+0x0c`, `+0x10`, `+0x14`.
Le garde-fou aigu peut ensuite les annuler en `0x400ab20c`. La pondération finale **multiplie**
ces gains déjà calculés ; elle ne réactive donc jamais une voix coupée par cette protection.
BASE évite la multiplication pour conserver les bits de gain exacts. La triade garde le
quatrième opérateur muet. La protection du premier opérateur au plafond aigu du §12.1 est conservée.

### 15.3. Pads et durée du geste

`[FAIT dans les sources]` Deux entrées de PadsView sont détournées : pointeur `0x4010025c`
vers `ck_ui_pad`, et thunk `0x401002b0` vers `ck_ui_pad_thunk`. Les chemins de repli restent
`0x4001d180` et `0x4001d3d4`. Les gestes ne passent pas par un nouveau note-on : le getter audio
lit le modificateur temporaire au prochain update du moteur. Le contrat recherché est une
modification de l'accord tenu sans recommencer son enveloppe, puis une restauration au relâchement.

`[FAIT en émulation : banc des pads]` Une vue prioritaire peut intercepter le relâchement après
qu'un pad a été capturé par HARMONY : le test ouvre QuickMute après T3, puis relâche T3.
Un crochet commun en `0x4007746c` vers `ck_ui_pad_dispatch_hook` consomme uniquement les
relâchements de pads précédemment capturés, avant les vues prioritaires. Pour les autres événements,
il rejoue le prologue `4fefffc048d70c04` puis reprend le dispatcher stock en `0x40077474`.
Le test vérifie le retour du modificateur à zéro, sans note-off parasite ni mute du chemin stock.

Six captures retiennent pad, piste, identité d'en-tête de pattern et rang. Le dernier pad pressé
prévaut ; son relâchement redonne la main au précédent encore tenu. Les rangs sont compactés,
sans compteur croissant pouvant déborder. Une nouvelle frappe TRIG n'efface pas les pads encore
tenus. Les captures de relâchement restent reconnues après l'annulation du geste, pour éviter
d'envoyer au chemin stock un note-off dont il n'a pas reçu le note-on.

TRACK, FUNC, PATTERN, RETRIG et les événements marqués comme raccourcis conservent le chemin natif.
Changer Controls/Pads ou désactiver Keys efface les gestes ; le changement d'identité de pattern
audio invalide les captures précédentes : revenir au pattern ne ressuscite pas un ancien geste.
Un chargement ou reset annule seulement les gestes appartenant au buffer destination.
**Pads = N/A** s'affiche dans le menu pendant une demande
T5/T6 indisponible sur un TRIG tenu identifié comme diminué. Cet indicateur UI ne déduit pas
la note actuellement jouée par le séquenceur ou par MIDI ; cette limite est affichée dans le guide.

Les gestes T1–T6 sont **live uniquement**. Aucune représentation n'est ajoutée au séquenceur,
aucune extension n'est réécrite dans I–VII, aucun geste n'est sérialisé. L'enregistrement des
TRIG continue à conserver la fondamentale, pas une capture complète des notes entendues.

### 15.4. Stockage et migration explicite

`[FAIT dans les sources]` Les six mots Root/Scale/I–VII/Keys à `header+40..63` ne changent pas.
L'ancienne signature `0x434b01a7` signifie **Controls LEGACY** pour tout le pattern.
La nouvelle signature a pour base `0x434b0200`, avec les bits 0..5 comme masques Pads HARMONY
propres aux six pistes. Zéro signifie TRACK. **Controls s'applique aux six pistes du pattern**,
et non seulement à celle affichée ; cette portée est explicitée dans le guide et BUILD.md.

Le chargement reconnaît les deux signatures et préserve les mots de configuration. Les initialisations
nouvelles écrivent NEW, toutes les pistes en TRACK et Keys OFF. Choisir NEW pour un ancien pattern
est volontaire : les valeurs SHAPE/COLOR et les locks restent identiques mais leur interprétation
change. Revenir à LEGACY restaure le sens précédent. La sélection d'une révision remet les modes
Pads à TRACK ; la signature et les six mots sont sérialisés par les mécanismes déjà établis.
Les événements temporaires restent en RAM et sont exclus du format sauvegardé.

### 15.5. Réserves de code supplémentaires

`[FAIT : lecture exhaustive de l'image officielle]` Il existe exactement 22 exemplaires du masque
47×47 déjà connu : les 19 réserves du générateur, l'exemplaire conservé et les deux masques utilisés
par l'arp. Aucun autre exemplaire de cette forme n'est supposé libre.

L'inspection des constantes des constructeurs Bitmap trouve aussi **19 masques 35×35 identiques**
de 280 octets. Douze sont ajoutés comme réserves de Chord Keys, avec exemplaire conservé
`0x4014a660`. Un masque **33×48 de 384 octets**, `0x40158744`, partage celui conservé en
`0x4016ac78`. Le masque est une donnée graphique ; sa libération exige la redirection du constructeur.

| Réserve | Capacité | Constante du constructeur | Exemplaire conservé |
|---|---:|---|---|
| `0x40158744` | 384 | `0x400b7a5a` | `0x4016ac78` |
| `0x4016aa28` | 280 | `0x400b1480` | `0x4014a660` |
| `0x401699a8` | 280 | `0x400b1500` | `0x4014a660` |
| `0x401696a0` | 280 | `0x400b1540` | `0x4014a660` |
| `0x40166760` | 280 | `0x400b272e` | `0x4014a660` |
| `0x4016616c` | 280 | `0x400b2898` | `0x4014a660` |
| `0x40163fb8` | 280 | `0x400b34c8` | `0x4014a660` |
| `0x401625bc` | 280 | `0x400b3e2a` | `0x4014a660` |
| `0x40160e6c` | 280 | `0x400b482e` | `0x4014a660` |
| `0x40160b6c` | 280 | `0x400b4870` | `0x4014a660` |
| `0x40160864` | 280 | `0x400b48ac` | `0x4014a660` |
| `0x401601fc` | 280 | `0x400b4b4a` | `0x4014a660` |
| `0x4015f50c` | 280 | `0x400b5028` | `0x4014a660` |

Sur **chaque plage complète**, `build.refs_into` trouve uniquement la constante du constructeur,
aucune référence intérieure et aucun branchement. La comparaison de tous les octets avec l'exemplaire
conservé passe. Les plages et leurs redirections n'empiètent sur aucun tweak existant, y compris
ceux exclus fonctionnellement. Le générateur répète ces contrôles pour toute nouvelle réserve utilisée,
vérifie les dimensions poussées au constructeur et adapte le placement à sa capacité réelle.

La réserve totale atteint **10 888 octets** (19×376 + 12×280 + 384). Seuls les masques occupés
sont écrits et redirigés ; une fonction n'est jamais coupée entre deux masques. Cela conserve une
implantation entièrement en MAIN OS, sans nouvelle charge utile ni modification des autres sections.

`[FAIT : génération finale]` Le JSON final contient **60 écritures**, dont **12 accroches** et
24 paires code/redirection. **8 550 octets** de code, constantes et état occupent **24 masques**.
Les réserves restantes ne sont ni modifiées ni redirigées. Le build extrait puis reconstruit exactement
le MAIN OS attendu ; les sections compressées **2, 4 et 5 restent identiques octet pour octet**
à l'image officielle. Les quatre empreintes de référence figurent dans BUILD.md.

### 15.6. État des preuves et essai matériel

`[FAIT : exécution du noyau portable]` `tools/test_chord_harmony.py` passe : exemples indépendants
Em9, dominantes tendues, SUS7, PARALLEL et m7♭5 ; **245 comparaisons** DIATONIC/historique avec
exception m7♭5 explicite ; **5 145 harmonies et neuf SHAPE** ; **65 536 valeurs** COLOR/SHAPE,
gains actifs et inutilisés ; entrées invalides et transformations refusées sans sortie modifiée.
La lecture des treize nouvelles réserves de code passe les contrôles décrits au §15.5.
Ces résultats ne remplacent pas l'exécution du firmware final.

`[FAIT en émulation : JSON final]` La suite ColdFire passe **296 contrôles seule** et **304 avec
6ch-usbup, latching-mute, trig-preview, browser-scroll, trig-hold, arp, tempo-max, boot-anim et
les cinq moteurs Syntakt installés ensemble**. Elle couvre les anciennes règles LEGACY, les
palettes, l'accord tenu sans nouvelle attaque, le retour des pads superposés, la libération sous
QuickMute, l'isolation entre pistes/patterns, le stockage et la migration, les vrais glyphes
DIATONIC/JAZZ/TENSION et les paramètres effectifs COLOR/SHAPE. Le banc d'intégration transmet
séquentiellement les 72 octets de `held_pads` et l'en-tête de 64 octets de l'UI vers le DSP :
il ne simule pas une interruption
audio réellement concurrente à chaque écriture d'interface, ni le matériel complet.

Le régulateur combiné passe ses quatre scénarios pour LEGACY puis ses quatre scénarios pour
NEW/TENSION/OPN3 : accords audibles, charge normale à 50 % simulés, pic isolé à 99 % sans vol
de voix, surcharge répétée avec fondu au bloc 41 puis reprise après retrig. Les durées de charge
sont injectées ; cela ne mesure pas le temps réel de ces accords sur le processeur.
Le banc indépendant `tools/emu/test_governor.py` passe aussi ses **12 contrôles**, avec
**TOUT OK** et code de sortie zéro.

| Scénario NEW, six pistes CHORD, palette TENSION | BASE, instructions/bloc | OPN3, instructions/bloc |
|---|---:|---:|
| Chord Keys seul, getter natif compris | 59 006 | 61 754 |
| Avec tous les mods compatibles, getter natif compris | 60 488 | 63 488 |

La pile observée sous l'entrée update atteint 248 octets contre 104 pour le stock, soit
144 octets supplémentaires. Ces comptes d'instructions sont propres aux scénarios du banc ;
ils ne sont ni des cycles ColdFire ni un pourcentage de charge matérielle.

`[FAIT : contrôles de construction]` Générateur Chord Keys et `gen_flasher_tweaks.py --check`,
`relocate_6ch.py --check` avec le wrapper binutils `-S`, compilation Python, syntaxe JavaScript,
comparaisons builder Python/JS et validation SysEx passent. Le smoke synthétique termine
**ALL OK**. `REF_MAINOS --check` valide **17 407 références** ; la comparaison avec la révision
précédente confirme que seules les **8 192 combinaisons Chord Keys** changent et que les
**9 215 autres références restent identiques**. Le contrôle de roundtrip et la conservation
des sections 2/4/5 sont décrits au §15.5.

`[FAIT : smoke réel du flasher]` `SMOKE_JOBS=4 tools/webflash_smoke.sh` avec les deux fichiers
officiels valide les **17 407 combinaisons proposées**, toutes conformes à leur empreinte MAIN OS.
Les quatre parties terminent **ALL OK**, l'agrégation vérifie la couverture exacte des références,
et la commande termine **ALL PARTS OK, code de sortie zéro**. Le journal local ignoré est
`build/chord-harmony-smoke.log`. Les scénarios UI confirment aussi le badge expérimental de cette
nouvelle révision, seule ou combinée, en anglais et en français.

La preuve fonctionnelle complète couvre le mod seul et la combinaison groupée ci-dessus ; les
références et le smoke ne signifient pas que toutes les combinaisons ont reçu cette émulation
fonctionnelle complète. Aucun résultat matériel de cette nouvelle révision n'est revendiqué.

`[À FAIRE sur la machine]` Installer Chord Keys seul, garder une copie du projet, puis :

1. Charger un ancien pattern : vérifier LEGACY et le son/les locks d'origine ; passer volontairement
   à NEW, comparer les palettes, revenir à LEGACY, sauvegarder/recharger les deux choix.
2. Avec Root C2, MAJ, EXT 9, jouer III : DIATONIC donne Mim7(♭9), JAZZ Mim9. Sur V, comparer
   les niveaux 9/11/13 en JAZZ puis TENSION ; vérifier que TRI/7 ne changent pas de palette.
3. En HARMONY, tenir un TRIG puis T1, T2, relâcher T2 puis T1 : aucune nouvelle attaque,
   retour au précédent pad puis au réglage I–VII. Essayer les six pads, plusieurs ordres,
   changer de TRIG, puis changer de piste, pattern, Keys et mode Pads pendant un maintien.
4. Sur VII de MAJ et I de LOC, écouter les trois extensions m7♭5 ; vérifier T5/T6 indisponibles
   et le menu N/A sur un TRIG tenu. Comparer SUS7 et V7 sur les cibles majeures/mineures.
5. Balayer les neuf SHAPE : aucune extension en plage ne doit disparaître ; écouter les transitions
   et les notes aiguës. Contrôler les trois libellés COLOR complets, les locks, CC16/17 et LFO.
6. Vérifier TRACK/FUNC/PATTERN/mute/retrig/édition ; confirmer que les gestes de pads ne sont pas
   enregistrés. Après le test seul, essayer les combinaisons avec USB/effets et six pistes chargées.

La nouvelle révision reste **experimental**, même installée seule, jusqu'à son propre retour matériel.
