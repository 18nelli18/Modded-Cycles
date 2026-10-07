# 42 — Jouer les accords d'une gamme avec TRIG 1–16

Contribution de **Nico Heuser** ([byNicoHeuser](https://github.com/byNicoHeuser)),
[PR #46](https://github.com/18nelli18/Modded-Cycles/pull/46), intégrée au flasher par ce projet (renumérotation et
relecture au §14). Sa demande, dans sa propre conversation du **05/10/2026** : choisir une gamme pour CHORD, jouer
ses accords avec T1–T6, puis six positions supplémentaires avec un bouton maintenu. Il confirme **une seule piste
CHORD** et des extensions choisies par degré **en restant dans la gamme** ; il accepte de remplacer PAGE si cela gêne
le jeu. Le **06/10/2026**, il remplace cette demande par les boutons inférieurs **TRIG 1–16**, en conservant les
commandes habituelles des grands pads ; il demande aussi **MAJ** et les degrés sans suffixe **Ext** dans le menu.
Source : conversation locale, sans lien public. Adresses : VA de l'OS **1.13**. Les constats sur les pads du
05/10 sont conservés comme historique en §2 et §9 ; les révisions du clavier et du son sont détaillées en §11 et §12.

Tweak : [`45-chord-keys.json`](../tweaks/model-cycles_OS1.13/45-chord-keys.json), générateur
[`tools/gen_chord_keys.py`](../tools/gen_chord_keys.py), sources
[`tools/machines/chord_keys/`](../tools/machines/chord_keys/), preuves sous `tools/emu/` et test natif
[`tools/test_chord_keys.py`](../tools/test_chord_keys.py). **État au 07/10/2026 : expérimental.** Nico rapporte que
Chord Keys seul fonctionne sur son Model:Cycles (§13) ; pas encore d'essai de Maxime, et les combinaisons ne sont
vérifiées qu'en logiciel. Relecture de l'intégration et défauts connus au §14.

## Réponse courte

`[FAIT en émulation]` Le mod raccorde les boutons **TRIG 1–16**, un menu de réglage, le stockage des patterns et
le véritable moteur CHORD. Dans **FUNC + RETRIG**, activer **Keys** sur une piste CHORD, régler **Root**, **Scale**
et **I** à **VII**. Hors édition en grille, 1–7 jouent I–VII, 8–14 les mêmes degrés une octave plus haut, puis
15–16 I–II deux octaves plus haut. **RETRIG ne change plus de banque.** Le menu affiche **MAJ** pour majeur.
Les réglages restent propres à chaque piste du pattern ; les seize touches pilotent la piste CHORD sélectionnée.
T1–T6 retrouvent intégralement leur routage d'événements stock. Le DSP reste réglé par piste : comme les notes
séquencées ou MIDI, une note jouée par un grand pad peut donc recevoir les intervalles de Keys si elle est dans
la gamme. PAGE garde ses fonctions.

Les sept modes diatoniques et cinq choix d'extension sont implémentés, avec trois ou quatre voix. La tonique de
l'interface est limitée aux notes MIDI **24–48**, soit **C1–C3** selon la notation du menu. SHAPE choisit **BASE**,
**CLS0–3** ou **OPN0–3** pour les notes de la gamme lorsque Keys est actif. **I–VII** seuls choisissent les
extensions ; **COLOR** garde les gains natifs sans déplacer les octaves. Commencer avec **BASE** et **COLOR 32**. Les notes hors gamme gardent l'accord SHAPE stock.

Cette fonction était absente du dépôt. Le [Scale Lock de Model-TG](https://github.com/TinyGregAudio/Model-TG/blob/main/docs/USER_GUIDE.md#scale-lock)
transforme les notes du clavier suivant une gamme ; il ne choisit pas un accord par degré. **Model-TG est déclaré
incompatible** dans cette version : sa transformation des notes et son CHORD optimisé demanderaient une
intégration spécifique. La recherche ne démontre pas l'absence d'un autre mod dans tous les projets externes.

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

`[FAIT, relectures du 06 et du 07/10/2026]` **Pas de `m68k-linux-gnu-gcc`** : avec l'ABI SVR4 de la cible Linux,
GCC lit dans `a0` le pointeur rendu par une fonction appelée par pointeur, alors que l'OS le rend dans `d0`
(`0x4000eb90` : `move.l 4(sp),d0 ; addi.l #48,d0 ; rts`). Compilés ainsi, `selected_track` ou `key_velocity`
passeraient un registre au hasard à l'OS à chaque appui. Dans le JSON (m68k-elf), chaque résultat d'appel à l'OS,
pointeurs compris, est lu dans `d0`. Le générateur n'accepte donc que `m68k-elf-` (ou `M68K_CROSS`, hors cible
Linux), et ne place le code que dans ses quatorze masques : un code plus gros échoue au lieu de prendre ceux des
autres mods.
`[FAIT]` Le refus « symbole de code non aligné » obtenu avec GCC 13 sur la première version venait des tables
d'octets typées `t` dans les sections `.ckN` mixtes. Nico aligne désormais toutes les sections sur 2 (révision
SHAPE/COLOR), ce qui lève ce refus ; le reste des octets diffère toujours avec GCC 13, donc `--check` demande GCC 16.2.

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

Demande de Nico dans sa conversation : abandonner T1–T6 pour le clavier d'accords, jouer I–VII sur 1–7,
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

Demande de Nico, dans sa conversation : conserver I–VII pour les extensions,
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

**Source : retour de Nico dans sa conversation, sans lien public.** Après la révision SHAPE/COLOR du §12,
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

Nico publie aussi cette version sur le flasher de son fork. Ce dépôt n'en reprend que le firmware et la
documentation d'usage (§14).


## 14. Intégration dans ce dépôt (07/10/2026)

Branche `claude/chord-keys-flasher-ozqjas` (PR #50) : les commits de Nico sont repris tels quels (fusion de la tête
`696276b` de la PR #46), sans toucher à sa branche. Ajouts de l'intégration :

- **Numéros** : note 40 → **42** (40 et 41 sont pris par le navigateur multiligne et la PR #47), `44-chord-keys.json`
  → **`45-chord-keys.json`** (ordre 45), une seule version **1.23** dans les notes de version, tampon `2026-10-07-02`.
  Ordre et description sont des métadonnées : le générateur et le JSON changent à l'identique, les octets écrits non.
- **Crédit** : carte du flasher « par Nico Heuser », guide, README, PROVENANCE, BUILD.
- **Retiré**, car propre au fork : encadrés « flasher de Nico », badge « Testé seul / Combinaison : logiciel
  uniquement » (`hardware_scope`), carte placée en premier sans crédit, versions 1.22 à 1.26 du fork, conseils pour
  les patterns enregistrés avec ses versions précédentes (jamais publiées ici). Seul l'essai de Maxime fait passer un
  mod en `tested` (AGENTS.md, règle 3) ; le retour de Nico figure ici et dans le guide, sans badge.
- **Générateur** : `m68k-elf` seulement et quatorze masques seulement (§6).

`[FAIT, 07/10/2026]` Avec le `build.py` du dépôt : `chord-keys` seul donne le MAIN OS `47e399fb…ddda4e4cf`, la
combinaison `6ch-usbup,arp,trig-hold,tempo-max,boot-anim,syntakt-sd-cp-toy-bits-swarm,chord-keys` `6a9a68bc…1843dabf` ;
les sections 2, 4 et 5 restent identiques à l'officiel. `ref_mainos.py --check` : 17 407 combinaisons à jour.
`gen_flasher_tweaks.py --check`, `relocate_6ch.py --check`, `webbuild_check.sh`, `webflash_check.sh` et la page du
flasher (`webflash_smoke.sh` sans firmware) passent. **Non exécutés ici** : `gen_chord_keys.py --check` (GCC 16.2
absent) et les preuves en émulation de Nico (code d'un contributeur : accord de Maxime attendu).

`[FAIT, relecture du binaire, sans exécuter le code du contributeur]` Les 37 écritures : chaque accroche rejoue les
instructions d'origine ou revient à la fonction d'origine ; les quatorze masques sont identiques à `0x40172220`,
désignés une seule fois et jamais dépassés ; seul `0x400ff9cc` est partagé, avec Model-TG, déclaré en conflit.
Défauts connus, aucun ne bloque l'essai sur la machine :

- **Relâchement avalé** (moyen, `[FAIT]` sur le code désassemblé, effet audible `[HYP]`) : si une vue placée avant
  le clavier consomme le relâchement d'une touche d'accord, `held[touche].valid` reste levé. Le relâchement suivant
  de cette touche est alors consommé par le mod, même quand l'appui est allé au clavier d'origine (Keys OFF, autre
  piste, mode grille) : la note d'origine et son note-off MIDI ne partent jamais.
  - Déclencheur : PATTERN tenu. `0x40077720` → `0x4007739e` parcourt les vues enfants à rebours
    (PatternAndBankSelectView `0x40020a7a`, PadsView `0x4001d506`, puis KeyboardView, emplacement `0x400ff9cc`) et
    s'arrête au premier qui rend vrai. Avec UIStates+389 (`0x4006bb18`) levé, la vue des patterns rend 1 sur tout
    relâchement de TRIG, même sans avoir vu l'appui (`0x40020d3c` → `0x40020df0` → `0x40020e16` → `0x40020d5e`). Un
    relâchement supprimé par `KeyEvent::consume` (masque `0x40f95724`) n'est jamais posté : même effet.
  - Régression : sur l'OS d'origine, le prochain appui-relâchement de la touche, sur n'importe quelle piste, libère
    toutes ses notes (`0x40019d00`, seul chemin de note-off, sans minuterie). Avec le mod, seul un relâchement sur
    une piste non CHORD ou en Keys OFF la libère.
  - Essai : piste CHORD Keys ON, tenir TRIG 1, tenir PATTERN, lâcher TRIG 1, lâcher PATTERN ; passer sur une piste
    non CHORD, appuyer puis lâcher TRIG 1.
  - Correction : dans `ck_ui_key`, sur un premier appui (`(flags & 9) == 1`), appeler `release_key(&held[touche])`
    et remettre `valid` à zéro avant `handle_press`. L'OS ne poste un premier appui que sur un front montant : une
    entrée encore valide est donc forcément périmée. Recompilation avec GCC 16.2. Signalé à Nico sur la PR #46 le
    07/10/2026, avec ce correctif.
- **Notes au-dessus de 96** (faible) : le degré est tiré de la note avant que le moteur la borne à 96 ; une note MIDI
  97–127 reçoit l'accord de son propre degré sur une fondamentale 96. Les touches TRIG n'y arrivent pas (74 au plus).
- **Affichage** (cosmétique) : seul l'emplacement SoundParameterSet de SHAPE est accroché ; un p-lock de SHAPE affiché
  depuis un trig peut rester numérique. L'écran suit le pattern affiché, l'audio le pattern joué.
- **Partage de place libre** : réglé le 07/10/2026. Les mods de djd_oz (`46-level-pan-values`, `47-trigless-dim`)
  sont passés sur `0x4018dba8`, `0x4018f4b4`, `0x4018fc74` et `0x40192734`, hors des quatorze masques de Chord
  Keys. L'écoute des samples (`33-sample-preview`) partage `0x40183118`, `0x40185018`, `0x40185968` et
  `0x40185c58` avec Chord Keys : permis, car elle exige Model-TG, que Chord Keys exclut, et elle déclare le conflit.
