# Étage de sortie du Model:Cycles OS 1.13 : mesure et optimisations

Étude « sortie » de l'optimisation de l'OS d'origine (demande de Maxime du 17/10/2026). Périmètre : tout ce qui suit
la boucle des voix dans le calcul d'un bloc : gain de vélocité `0x40056d9c`, Volume + Dist `0x40056f58`, clic du
métronome `0x40056ea8`, mixeur `0x400567ba` (delay `0x40057488`, reverb `0x400579c4`, `0x40057942`, `0x400573fa`,
envois, master, anneau du codec).

Tout ce qui est ici vient de l'émulation (Unicorn, code de l'OS d'origine) et du désassemblage. **Aucun résultat
matériel.** Étiquettes : [FAIT] vérifié (commande, adresse, sortie citée), [DÉDUIT] calculé à partir de faits,
[HYP] plausible non vérifié. Fichiers de travail : ce dossier (liste au §9).

## 0. Résumé

1. L'étage de sortie coûte **28,7 % d'un bloc** au modèle des notes 27-28 (29,3 % caches vidés), **quel que soit le
   contenu** : silence, une piste, six pistes, avec ou sans effets, même nombre d'instructions à 20 près (§2) [FAIT].
2. Une bonne moitié de ce travail est inutile avec les réglages par défaut : saturateur de Dist calculé quand Dist
   est à 0, delay et reverb calculés en entier quand rien n'y entre ni n'en sort, envois calculés avec des gains nuls
   (§3) [FAIT].
3. Trois prototypes, prouvés en émulation contre l'OS d'origine (sortie identique à l'échantillon près, SRAM et
   lignes en DDR identiques) : p1 Volume + Dist (+3,9 %), p2 sommeil exact du delay et de la reverb (+8,1 % en
   instructions, ~8,9 % au modèle de cache), p3 envois nuls sautés (+1,9 %). Ensemble, réglages par défaut, six pistes : **28,7 % → 14,2 % d'un bloc** au modèle
   de cache, bloc entier 79,3 % → 64,6 % (§4) [FAIT en émulation]. Effets en service : jamais plus lent que l'OS
   d'origine de plus de ~0,1 % en instructions, ~0,5 % au modèle avec les lignes de code des détours (§4.4) [FAIT].
4. Limite trouvée : une fois servis, **le delay et la reverb ne retombent jamais exactement à zéro** (reste continu
   du delay, cycle limite de la reverb, ≤ 24 pas de 24 bits au codec) ; p2 ne s'endort donc exactement que si
   l'effet n'a pas servi depuis la mise sous tension. Une purge de ces restes (non identique, −111 dBFS) le rendrait
   utile après usage (§5, piste 4, conçue sans prototype).
5. Autres pistes chiffrées, non prototypées : préparation de l'eDMA plus tôt (attente cachée, gain seulement sur la
   machine), variantes A/B du volume, anneau écrit par le cache (§5).

## 1. Le banc : le vrai code de sortie, bloc par bloc

`banc.py` part de `tools/emu/seqrig.py` (vraie interruption audio) mais **n'en saute plus** l'étage de sortie : les
crochets `ret0` posés par `seqrig` sur `0x40056f58`, `0x40056ea8`, `0x400567ba` sont retirés (`banc.py:197-213`).
Ce qu'il fallait pour que ce code tourne [FAIT, `banc.py`] :

- **DDR vue deux fois** : un seul tampon de 16 Mo projeté par `mem_map_ptr` à `0x42000000` (avec cache) et
  `0x4a000000` (sans cache), comme le matériel : lignes du delay `0x4a400000`, de la reverb `0x4a340000`
  (9 × 64 Ko) et `0x4a3d0000` (8 × 4 Ko), anneau du codec `0x4a3ed080`.
- **eDMA simulé** (`class EDMA`) : les TCD `0xfc045000 + 32·canal` en MMIO ; écrire START dans un CSR exécute toute
  la chaîne (SMOD/DMOD, scatter-gather jusqu'au dernier TCD, DONE). Canal 30 (`0x4005802e`, START en `0x400582ae`) :
  2 prises du delay de 272 o, 8 lignes courtes de 144 o, 9 lignes longues de 144/160 o ; canal 42 (`0x400573fa`,
  START en `0x40057480`) : 256 o vers la ligne du delay, 17 × 128 o vers la reverb. 37 transferts par bloc, aucun
  accès non projeté [FAIT, `analyse_rw.py`, journal eDMA].
- **Init de l'OS** : `0x4005974c` (effets puis voix), réglages par défaut `0x400449ce` (`0x404e9b54 = 2` : son
  interne vers la sortie), tables des descripteurs `0x4005a274`, sons par défaut `0x400618f2` par piste, kit chargé
  par l'OS lui-même `0x400595a8` (Track Level 100, effets aux défauts des descripteurs : Delay Time 23, Fdbk 32,
  Reverb Size 42, Tone 64).
- **Mesure** (`trace.py`) : crochets de code et de mémoire, plus une sonde des chargements faits par les MAC avec
  chargement (exécutés par `tools/emu/emac.py`, invisibles aux crochets d'Unicorn). Caches simulés de 8 Ko,
  4 voies, lignes de 16 o, LRU, copyback avec allocation en écriture pour `0x40000000..0x47ffffff` ; la pile du banc
  (`0x9000xxxx`) compte comme de la SDRAM cachée (la vraie pile est en SDRAM : `0x400004f2 moveal #0x48000000,%sp`).
  Coût = 1,54 cycle par instruction + 15 cycles par ligne transférée, 166 667 cycles par bloc (notes 27-28).

Limites du banc [FAIT par construction] : l'eDMA est instantané (l'attente `0x4005697e` ne tourne qu'une fois) ; la
latence des accès non cachés n'est pas modélisée ; 6 voix réelles de l'OS (KICK..CHORD), trigs par `seqrig`.

Contre-épreuve d'outillage (piège signalé par l'agent « voix » : avec unicorn 2.1.4, un crochet de lecture posé après
la traduction d'un code ne voit pas ses lectures tant qu'on ne vide pas le cache de traduction) : la mesure « six »
refaite avec `uc.ctl_flush_tb()` après la pose des crochets (`mesure_flushtb.py`) donne exactement les mêmes chiffres
pour tout l'étage de sortie ; seul `memcpy 0x4008f1f0`, déjà exécuté pendant l'initialisation, était sous-compté
(24 lectures) [FAIT]. Les comptes d'instructions n'en dépendent pas.

## 2. Mesures

### 2.1 Par poste (six pistes qui jouent, réglages par défaut) [FAIT, `mesure.py`, `mesures.log`, `mesure2.log`]

| Poste | Instructions/bloc | Lignes I manquées | % d'un bloc (chaud) | % (caches vidés) |
|---|---:|---:|---:|---:|
| Gain de vélocité `0x40056d9c` | 598 | 7 | 0,62 | 0,62 |
| Volume + Dist `0x40056f58` | 6 071 | 47 | 6,04 | 6,14 |
| Clic du métronome `0x40056ea8` | 236 | 11 | 0,35 | 0,43 |
| Mixeur (corps, envois, master, ×4, anneau, prép. eDMA) | 8 722 | 167 | 9,92 | 10,33 |
| Delay `0x40057488` | 2 659 | 40 | 2,83 | 2,84 |
| Reverb `0x400579c4` + pointeurs `0x40057942` | 8 410 | 103 | 8,86 | 8,85 |
| eDMA écritures `0x400573fa` | 30 | 9 | 0,11 | 0,11 |
| **Total** | **26 726** | **384** | **28,74** | **29,33** |

Bloc émulé entier (interruption + fonction audio) : 79,3 % au modèle (81,9 % caches vidés).

**Coût constant** [FAIT] : total de l'étage, en instructions par bloc : silence 26 747, une piste 26 728, six pistes
26 726, six pistes avec envois 40/40 26 726, queues d'effets seules (voix éteintes) 26 729 (`mesures_*.json`). Rien
ne dépend du contenu : chaque boucle tourne 32 trames, à chaque bloc.

**Cohérence avec la machine** [DÉDUIT] : le profil de notes/31 §7 mesure « sortie » autour de `0x40059872` (le seul
mixeur) à 19-20 % et « entre les voix et la sortie » à 5-6 % ; le modèle donne mixeur + delay + reverb + eDMA =
21,7 % et vélocité + memcpy + Volume + Dist + clic = 7,1 %. Delay + reverb : 11,7 % au modèle, « ~12 % » sur la
machine (notes/31 §7). Écart de l'ordre de 10 %, dans la marge du modèle.

### 2.2 Par boucle [FAIT, `loops.py pc_six.json`]

| Boucle | Instr./bloc |
|---|---:|
| Volume + Dist : **saturateur**, 32 trames × 2 pistes, 3 paires (`0x40057084..0x40057100`) | 4 224 |
| Volume + Dist : fondu dry/wet (`0x400571c4..`) | 1 344 |
| Delay : prises + fondu A/B (992), filtre (724), sortie + contre-réaction (364), entrée + écriture ligne (537) | 2 617 |
| Reverb : passe-tout sur 8 lignes courtes (`0x40057b4c`) | 2 676 |
| Reverb : 8 autres boucles de 32 trames (464 à 842 chacune) | 4 951 |
| Mixeur : envois delay (2 appels `0x40056716`) / envois reverb (2 appels `0x40056698`) | 1 116 / 1 244 |
| Mixeur : master 8 entrées (2 appels `0x40056610`) | 1 372 |
| Mixeur : variante A (414), variante B (396), passages par zéro (712), choix A/B + bornes + anneau (924) | 2 446 |
| Mixeur : désentrelacements (6 appels, 594), copies USB (295 + 233), gains des pistes (629), prép. eDMA (443) | 2 194 |

**Passes sur les tampons de 32 trames** : environ 54 boucles de 32 trames par bloc dans l'étage [DÉDUIT du décompte
par adresse de `pc_six.json`], dont 30 dans le mixeur, 9 dans la reverb, 4 dans le delay.

### 2.3 Accès non cachés [FAIT pour le nombre, HYP pour le coût]

- **64 écritures non cachées par bloc**, toutes dans l'anneau du codec (`0x4a3ed080 + 256·demi`, boucle
  `0x40056cf2..0x40056d28`, `movel %d2,%a4@(0,%a1:l)`), aucune lecture non cachée par le CPU dans l'étage
  (`noncache_w_acc = 64` dans tous les scénarios). Les lignes du delay et de la reverb ne sont touchées que par
  l'eDMA.
- Méthode d'estimation du coût : `0x4axxxxxx` est non caché et **précis** (CACR, rapport de « systeme ») : chaque
  écriture attend la fin de son cycle de bus. Si une écriture simple vers la DDR2 (bus de 8 bits) bloque le cœur
  20 à 40 cycles [HYP], les 64 écritures coûtent 1 300 à 2 600 cycles, soit **0,8 à 1,5 % d'un bloc**, en plus du
  modèle. Écrire l'anneau par l'alias caché puis `cpushl` de ses 16 lignes coûterait 16 × 15 = 240 cycles au modèle
  plus 16 `cpushl` [DÉDUIT, piste 8 du §5]. Non mesurable en émulation.

### 2.4 Attente de l'eDMA [FAIT pour l'ordre, HYP pour la durée]

- `0x4005697e..0x4005698a` : `movew 0xfc0453de,%d0 ; andl #16 ; bnes` : le CPU attend que le canal 30 ait chargé
  son dernier TCD (ESG à 0). Le dernier TCD (`CSR = 1`, ligne longue 8, 160 o) peut encore être en cours après
  l'attente : c'est le temps du delay (~2 700 instructions) qui le couvre avant que la reverb ne le lise.
- Entre le START (`0x400582ae`) et l'attente, le CPU exécute **1 895 instructions** (~2 900 cycles, 11,7 µs à
  250 MHz) [FAIT, comptage]. La chaîne transfère 2 864 o depuis la DDR non cachée. À 100-200 Mo/s effectifs [HYP],
  il lui faut 14 à 29 µs : **attente de 0 à ~2,5 % d'un bloc**, invisible en émulation. À mesurer sur la machine
  (§7).

## 3. Le travail inutile ou refait

1. **Saturateur de Dist calculé quand Dist est coupé** [FAIT] : 4 224 instructions par bloc (3 paires × 2 pistes ×
   32 trames). Le fondu `0x400571c4` le multiplie par la part « wet », nulle tant que VOL+DIST ≤ 60 (le défaut ; test
   `cmpi.l #15360` de `0x4005710a`). Résultat exactement nul, calculé quand même.
2. **Delay et reverb calculés en entier quand rien n'y entre** [FAIT] : 11 069 instructions par bloc avec les
   envois à 0 (défaut des sons, `envoi delay G 0x40a78bd0 = [0]*6`, `envoi reverb G 0x40a78b9c = [0]*7`, sortie de
   la commande du §4.3). Leurs entrées, leurs états et leurs lignes sont nuls ; leurs sorties aussi.
3. **Envois calculés avec des gains nuls** [FAIT] : 2 360 instructions (4 appels de 6 ou 7 MAC × 32 trames) pour
   écrire des zéros.
4. **Variantes A/B du volume quand il ne change pas** [FAIT pour le code, DÉDUIT pour le gain] : le master est
   calculé deux fois (A : ancien volume `0x4013e770/774`, `0x40056bf6..` ; B : nouveau volume `0x4013e778`,
   `0x40056c3e..`), puis un passage par zéro est cherché (`0x40056c78..0x40056cb0`, `ff1`) pour basculer de A à B sans
   clic. Volume inchangé : A = B, la recherche ne sert qu'à faire avancer le compteur `0x40a78978` (bascule forcée
   après 64 blocs).
5. **Tampon du clic remis à zéro mot par mot à chaque bloc** [FAIT] : `0x40056f3e..0x40056f4a` (`clrl %a4@(0,%d0:l:4)`,
   ~5 instructions par mot, ~160 par bloc) même métronome éteint.
6. **Les restes ne meurent jamais** [FAIT, `queue2.py`, `residu.py`] — ce n'est pas du travail refait mais c'est ce qui
   borne le sommeil exact :
   - **delay** : après une salve (Delay Time 1, Fdbk 32), il se fige sur un **point fixe continu** : ligne remplie de
     −52, sortie −204 sur les deux canaux, état du filtre `0x8000b8dc = (−128, −128, −204, −204)`, identique de bloc en
     bloc (`residu.py 700 40 0 1 32 42`, blocs 697-699). Il atteint l'anneau du codec : valeurs `[0, 3]`.
     Cause [DÉDUIT] : arrondi par troncature des MAC (`MACSR = 0xa0`, fractionnaire sans arrondi) dans la boucle de
     contre-réaction ; `−fb·x` tronqué vers −∞ a un point fixe non nul.
   - **reverb** : sortie qui descend jusqu'à ~1 100-1 400 (sur 2^31) puis **oscille sans fin** (`q2_A.log`, blocs
     2 000 à 2 750 : 1 376, 1 206, 1 289, 1 128 ; lignes à 4 603), soit 20 à 24 pas de 24 bits au codec (−111 dBFS).
   - L'OS n'efface la ligne du delay (4 Mo, `0x40057260`) et celles de la reverb (`0x4005770e`) qu'en `0x4005974c`,
     appelée par `0x40059632` depuis le démarrage (`0x4000577a`) et trois chemins qui écrivent `OK\r\n`, `###\r\n`
     (console de test, `0x40042746`, `0x400436dc`, `0x400438d8`) [FAIT pour les appels, HYP pour leur rôle]. Ni un
     changement de kit ni un chargement de projet ne remet ces restes à zéro [HYP : aucun autre appelant trouvé].
7. **Ce que Model-TG fait déjà** [FAIT, désassemblage de sa charge utile MIT dans `30-model-tg.json`, `0x401b71b0..`] :
   il redirige les appels du delay (`0x4005699f`), de la reverb (`0x40056a2f`) et des pointeurs (`0x40056a39`), et
   coupe les effets après **16 384 blocs (~11 s)** où voix, sortie du delay et de la reverb restent sous **±65 536**
   (`cmpil #65536` en `0x401b719e`, `cmpil #16384` en `0x401b727e`). En sommeil il saute aussi les pointeurs et
   l'eDMA (`0x401b7298`). Non identique (restes sous −90 dBFS jetés, lignes figées), et il ne dort que dans le
   silence complet des voix : jamais pendant qu'on joue sans effets. Il ne concerne que les firmwares avec Model-TG.

## 4. Prototypes prouvés en émulation

Les trois prototypes sont des détours dans le code de l'OS vers du code à nous, placé dans des masques de sprites
marqués libres au §1 de `REGISTRY.md` (ici seulement écrits dans l'image émulée ; un vrai tweak redirige aussi la
constante du masque, `sprites.redirect_write`). Aucun ne recopie de code d'Elektron : les détours remettent les
instructions remplacées (≤ 8 o, `old` d'un tweak) et rejoignent l'OS.

Écritures dans l'OS (toutes vérifiées contre les octets d'origine par le test) :

| Proto | Adresse | Octets d'origine | Remplacés par |
|---|---|---|---|
| p1 | `0x40057062` | `286f0038206f0040` | `jmp vd_check ; nop` |
| p2 | `0x40057516` | `2f03260dea83` | `jmp dz_check` |
| p2 | `0x40057ac8` | `2a7c8000a9b0` | `jmp rz_check` |
| p2 | `0x40057dc6` | `207c8000ad20` | `jmp rz_mod` |
| p3 | `0x40056716` | `4fefffe048d70cfc` | `jmp s6_check ; nop` |
| p3 | `0x40056698` | `4fefffd848d73cfc` | `jmp s7_check ; nop` |

Masques : p1 `0x40152d38` (48×22), p2 `0x401592bc` (48×22, 70 o), `0x40185f48` (34×34, 220/272 o), `0x4018d918`
(41×41, 256/328 o), p3 `0x4015943c` (48×22, 134 o).

Aucune de ces adresses n'est écrite par un des 282 tweaks (31 763 écritures parcourues : 0 dans les six détours et
les cinq masques ; dans `0x40056400..0x40058480`, seuls `model-tg` et `model-tg-st` écrivent, aux appels du mixeur,
pas dans ces routines) [FAIT, `scan_tweaks.py`].

### 4.1 p1 — Volume + Dist sans saturateur quand le wet est nul (`proto/vd_skip.S`)

- **Ce qu'il change** : en entrée de chaque paire de pistes (`0x40057062`), si le wet de fin du bloc précédent
  (`0x40a78c2c + 8p`, `+4`) est nul et que VOL+DIST lissé ≤ 60 sur les deux pistes, saut direct au calcul dry/wet
  `0x40057100`. Le saturateur ne tourne plus.
- **Pourquoi c'est exact** : le fondu `0x400571c4` multiplie la sortie du saturateur par un wet qui va de l'ancien au
  nouveau ; nul aux deux bouts, il est nul sur tout le bloc et `0 × x = 0` exactement. Seule différence d'état : les
  tampons du saturateur `0x8000bc98..0x8000bd98` gardent leur ancien contenu (lus seulement par ce fondu, × 0).
- **Preuve** [FAIT, `test_proto1.py`, `bqgim176l.output`] : 160 blocs, 6 pistes, envois 30/30, VOL+DIST qui passe
  le seuil dans les deux sens en glissant (pistes 1 → 70, 4 → 100, 3 → 61 puis retour à 60) : anneau, USB et
  6 pistes après Volume + Dist identiques à chaque bloc.
- **Gain** : 6 071 → 1 862 instructions (**+3,89 %** d'un bloc) quand les 6 pistes sont à ≤ 60, 1,3 % par paire ;
  −19 instructions (−0,02 %) quand Dist sert.

### 4.2 p2 — Sommeil exact du delay et de la reverb (`proto/fx_lib.S`, `fx_dly.S`, `fx_rev.S`)

Principe : **si tout ce qu'une fonction lit est nul, tout ce qu'elle écrit est nul** (calcul linéaire, MAC
fractionnaires : `0 × c = 0`, aucun terme constant). On le vérifie au début, et on écrit ces zéros nous-mêmes.

Ce que chaque fonction lit et écrit a été relevé sur le banc, par phase, sur 40 blocs avec bruit puis silence
(`analyse_rw.py`, `analyse_rw.json`) [FAIT] :

- **Delay** — lit avant d'écrire : gains `0x8000a100` (4), pointeur `0x8000b570`, prise A `0x8000b590..b694` (65 mots),
  prise B `0x8000b6a0..b7a4` (65), état du filtre `0x8000b8dc` (4), entrée `0x8000b990` (64). Écrit : `a100`, tampon
  d'écriture `b590..b690`, temporaire `b7dc..b8dc`, `b8dc`, sortie `0x8000ba90` (64). Il accumule aussi sur
  `acc1..acc3` laissés par l'appelant (`0x40057532 macl … %acc2`, `0x4005757a … %acc1`).
- **Reverb** — lit avant d'écrire, dans les parties « son » : entrée (64), états `0x8000a2d0` (32, écrit en fin de
  bloc et relu au suivant), `0x8000a47c` (16), `0x8000a4c8` (2), et les 17 tampons que l'eDMA remplit (lignes
  longues `0x8000a9b0 + 176k`, courtes `0x8000afe0 + 160k`). Coefficients (`a3dc`, `a3f0`, `a4bc`, `b510`, tables
  `0x4013f484`, `0x4010c38c`) : pas du son. La modulation `0x40057d72..0x40057dc4` (lit `0x423087e4`) est
  autonome.

**Delay** (détour `0x40057516`, après le prologue qui pose `b7c8..b7d8` ; vivants : d3, d6, d7, a4, a5, fp) : dort si
`acc1..acc3`, `b8dc`, l'entrée et les deux prises (fenêtres de 65 mots depuis `*0x8000b570` et `+272`, toujours
remplies par l'eDMA : 272 o moins un décalage ≤ 12) sont nuls. Alors : sortie et temporaire à zéro, gains `a100`
avancés de 32 pas exactement comme la boucle (`x += (cible − x) & ~31`, modulo 2^32), `MACSR = 0xa0`, épilogue
`0x40057704`. Sinon les 3 instructions remplacées et retour en `0x4005751c`.

**Reverb** (détour R1 `0x40057ac8`, fin du prologue : acc0..acc3 vidés par `0x40057ab4..0x40057ac2`, aucun registre
vivant) : dort si l'entrée, les 3 états et les 17 fenêtres sont nuls (683 mots, table `tab:` de `fx_rev.S` ; lignes
modulées 4 et 8 : 37 mots, car leur lecture glisse de `−4·a3dc`). Alors : sortie, temporaires `a1d0..a3d0`,
`a3f8..a47c` et les 8 mots `0x8000afdc + 160k` (écrits à 0 par l'OS) à zéro ; repère `MAGIC` dans `sp@(48)` (mort
après `0x40057a82`) ; saut à la modulation de l'OS `0x40057d72`, gardée telle quelle ; détour R2 `0x40057dc6` :
repère vu → épilogue `0x40057f9e`.

- Décalage des lignes modulées : `|a3dc| ≤ 1` [DÉDUIT] : oscillateur de rotation `0x8000a3d0 = 5 846 984`
  (0,00272 rad par bloc, ~0,65 Hz ; jamais écrit par le code, seulement lu en `0x400580b4`), amplitude 2^21 en
  unités de 2^−18 = 8 échantillons, donc au plus 0,022 échantillon de glissement par bloc. Mesuré : voir §4.4.
- **L'eDMA et le temps** [HYP sur le matériel] : avec le delay endormi, la reverb arrive plus tôt sur des tampons que
  le dernier TCD du canal 30 remplit peut-être encore (§2.4). Le sommeil du delay attend donc DONE (bit 7 de
  `0xfc0453de`), au plus 4 096 lectures, avant de rendre la main. En émulation DONE est déjà là.

Ce que p2 ne touche pas : la préparation et les transferts eDMA, les pointeurs `0x40057942`, le temps du delay lissé
(`0x4005802e`), la modulation de la reverb : les lignes continuent d'avancer comme dans l'OS d'origine, et le réveil
reprend exactement là où l'OS d'origine serait.

### 4.3 p3 — Envois sautés quand leurs gains sont nuls (`proto/send_skip.S`)

- `0x40056716` (envois delay, 6 entrées) et `0x40056698` (envois reverb, 7 entrées dont le delay) font, pour 32 trames :
  `acc0 −= Σ g_t·x_t ; sortie[2i] = movclr acc0 ; g_t += pente_t`. Si `acc0`, les gains et les pentes sont nuls,
  chaque sortie vaut 0 et les gains ne bougent pas : on écrit les 32 zéros (un mot sur deux) et on rend la main.
- Gains relevés sur le banc [FAIT] : envois à 0 → `0x40a78bd0`, `0x40a78bb8`, `0x40a78b9c`, `0x40a78b80` tout à 0
  (même la 7e entrée, delay → reverb, à 0 avec les envois à 40).

### 4.4 Preuve et gain des trois ensemble

`test_combo.py` : OS d'origine et OS modifié côte à côte, 6 pistes (trig tous les 40 blocs), réglages tournés comme
des potards (le lissage de l'OS glisse), 4 phases de 100 blocs. Comparé à chaque bloc : anneau du codec, mix USB,
voix, **SRAM entière** (sauf `0x8000bc98..bd98` avec p1, §4.1), accumulateurs et MACSR ; tous les 25 blocs : empreinte
SHA-256 des lignes en DDR (4 Mo du delay, 17 lignes de la reverb).

[FAIT, `test_combo.log`] : **identique sur 400 blocs** (anneau, USB, voix, SRAM entière sauf `0x8000bc98..bd98`,
EMAC à chaque bloc ; lignes en DDR tous les 25 blocs). Instructions de tout l'étage de sortie, moyenne par bloc :

| Phase (100 blocs) | OS d'origine | p1+p2+p3 | Gain | Sauts |
|---|---:|---:|---:|---|
| 1 réglages par défaut (envois 0, VOL+DIST 60) | 27 054 | 11 986 | **+13,92 %** | saturateur 300/300 paires, delay 100, reverb 100, envois 400/400 |
| 2 envoi delay 40 piste 2, VOL+DIST 90 piste 0 | 27 061 | 16 627 | +9,64 % | saturateur 200, reverb 100, envois reverb 200 |
| 3 + envoi reverb 50 pistes 1 et 4 | 27 068 | 24 497 | +2,38 % | saturateur 200 |
| 4 tout ramené à 0 / 60 | 27 060 | 24 422 | +2,44 % | saturateur 200 (voir ci-dessous) |

Phase 4 : le lissage de l'OS ramène les réglages en glissant ; dans `lissage.py` (`lissage.log`) le gain d'envoi de la
piste 2 vaut exactement 0 et le wet de la paire 0 aussi **340 blocs (0,23 s) après** le retour du potard, puis les
valeurs lissées tombent exactement sur leur cible (bloc 699) [FAIT] : p1 et p3 repartent d'eux-mêmes, plus tard que
les 100 blocs de la phase. Le delay et la reverb, eux, restent éveillés (restes du §3.6).

`test_proto2.py` (p2 seul, 5 phases de 120 blocs, dont les effets qui passent d'endormis à éveillés et les
paramètres des effets qui glissent) :

[FAIT, `test_proto2.log`] : **identique sur 600 blocs** (anneau, USB, voix, SRAM entière, EMAC à chaque bloc ;
lignes en DDR tous les 25 blocs), réveils compris. Instructions du delay et de la reverb (détours compris) :

| Phase (120 blocs) | Delay | Reverb | Gain | Blocs endormis (delay / reverb) |
|---|---|---|---:|---|
| 1 envois à 0 | 2 659 → 463 | 8 206 → 1 595 | **+8,14 %** | 120 / 120 |
| 2 envoi reverb 40 | 2 659 → 463 | 8 206 → 8 324 | +1,92 % | 120 / 0 |
| 3 delay + reverb | 2 659 → 2 689 | 8 206 → 8 248 | −0,07 % | 0 / 0 |
| 4 envois à 0 (restes) | 2 659 → 2 689 | 8 206 → 8 236 | −0,06 % | 0 / 0 |
| 5 restes, Delay Time 127 puis 5, Fdbk 0, Size 127 | 2 659 → 2 689 | 8 205 → 8 235 | −0,06 % | 0 / 0 |

Décalage des lignes modulées mesuré sur les 600 blocs : `a3dc` entre 0 et 1 (fenêtres de 37 mots suffisantes).
Avec Fdbk 0 et un Delay Time court (phase 5), le delay ne se rendort pas non plus dans les 120 blocs de la phase
(reste dans la ligne ou dans l'état du filtre, non distingué) [FAIT pour le constat, HYP pour la cause].

Modèle de cache (`mesure2.py`, `mesure2.log`) [FAIT en émulation] :

| Scénario | OS d'origine | p1+p2+p3 | dont détours |
|---|---:|---:|---:|
| Six pistes, réglages par défaut, caches chauds | 28,74 % | **14,16 %** | 2,62 % |
| Idem, caches vidés | 29,33 % | **14,69 %** | 2,58 % |
| Six pistes, envois 40/40 (effets en service) | 28,74 % | 25,22 % | 0,49 % |
| Bloc émulé entier, réglages par défaut | 79,3 % | **64,6 %** | |

Par poste, réglages par défaut : Volume + Dist 6,04 → 2,04 ; mixeur 9,92 → 7,61 ; delay 2,83 → 0,14 ; reverb 8,86
→ 0,66 ; lignes d'instructions manquées 384 → 306. Effets en service (envois 40/40) : delay et reverb inchangés
(2 657 et 8 410 instructions) ; seul p1 gagne (Dist à 60) ; les vérifications de p2 et p3 coûtent ~100 instructions
et ~25 lignes de code manquées, soit ~0,3-0,5 % au modèle.

## 5. Liste classée des optimisations

Gain en % d'un bloc (166 667 cycles), au modèle des notes 27-28 sauf mention. « Exact » = identique à l'échantillon
près en émulation, prouvé par comparaison bloc par bloc avec l'OS d'origine.

| # | Optimisation | Gain | Son identique | Risque | Effort | État |
|---|---|---|---|---|---|---|
| 1 | p2 Sommeil exact du delay + reverb | **+8,1 %** en instructions (~8,9 % au modèle) quand ils n'ont pas servi depuis la mise sous tension (envois à 0) ; +1,9 à 2,0 % si seul le delay dort ; −0,07 % éveillés | oui | faible | moyen | prototype prouvé |
| 2 | p1 Saturateur sauté quand Dist est coupé | **+3,9 %** (6 pistes à VOL+DIST ≤ 60, le défaut), 1,3 % par paire ; repart 0,23 s après le retour à 60 | oui (état : tampons du saturateur non réécrits, lus × 0) | faible | faible | prototype prouvé |
| 3 | p3 Envois sautés quand leurs gains sont nuls | **+1,9 %** (envois à 0 ; ~2,0 % au modèle) ; ~0,9-1,0 % par sorte d'envoi inutilisée ; repart 0,23 s après le retour du potard à 0 | oui | faible | faible | prototype prouvé |
| 4 | Purge des restes des effets, puis p2 | +8,1 % après ~1-3 s sans entrée (au lieu de jamais) | **non** : retire un reste ≤ 24 pas de 24 bits (−111 dBFS) | faible | moyen | conçu, non prototypé (§5.3) |
| 5 | Préparation eDMA (canal 30) avant les voix | 0 à ~2,5 % **sur la machine seulement** (attente cachée) | oui | moyen (état EMAC au nouveau point d'appel ; conflit avec Model-TG en `0x400567d6`) | moyen | conçu (§5.4) |
| 6 | Vérification réduite de p2 (indicateur + 512 blocs) | +0,9 % de plus quand ils dorment | oui, sous une hypothèse (personne d'autre n'écrit leurs lignes) | faible | faible | conçu (§5.5) |
| 7 | Anneau du codec écrit par le cache + `cpushl` | 0,5 à 1,5 % [HYP] sur la machine | oui | moyen (cohérence avec le DMA du codec) | faible | idée |
| 8 | Variantes A/B fusionnées, volume inchangé | ~0,9 % | oui si le compteur de passages par zéro est tenu exactement | moyen | moyen | idée |
| 9 | Remise à zéro du tampon du clic par `movem` | ~0,15 % | oui | très faible | très faible | idée |
| — | Code chaud de la sortie en SRAM | — | — | — | — | impossible : SRAM pleine (notes/23 §3) |
| — | Gain de vélocité fusionné ailleurs | — | non : 0x7fffffff × x ≠ x | — | — | écarté |

### 5.1 p2, p1, p3 : risques et conflits

- **Stabilité** : jamais plus lent que l'OS d'origine de plus de ~0,1 % en instructions (vérifications qui sortent au
  premier mot non nul), ~0,5 % au modèle de cache ; la charge baisse seulement quand un effet ou une Dist est inutilisé. Conséquence [HYP] : un régulateur de
  charge (Model-TG, notes/36) qui laisse jouer plus de voix grâce à cette marge la reperd d'un coup de ~11 % quand on
  monte un envoi ; il faut le dire aux utilisateurs, ou que le régulateur compte large.
- **Récupération** : section 3 seulement ; bootloader et updater intacts ; un mauvais détour n'empêche pas le STARTUP
  MENU (MIDI IN).
- **Conflits** (`REGISTRY.md`) : aucun tweak n'écrit aux six adresses ni dans les cinq masques [FAIT]. Model-TG
  appelle le delay (`jmp 0x40057488`) et la reverb (`jsr 0x400579c4`) d'origine depuis ses enveloppes : les détours
  de p2, à l'intérieur, restent actifs [FAIT, désassemblage `0x401b721c`, `0x401b7244`] ; son propre sommeil passe
  avant. À prouver avec `--with 6ch-usbup,model-tg-st,…` comme toute nouvelle mod (règle 5 d'AGENTS.md).
- **Masques** : un vrai tweak doit rediriger la constante de chaque masque utilisé (`0x400b9726`, `0x400b7404`,
  `0x400b73e4`, `0x400ad9c4`, `0x400acd1a`) vers la copie gardée, puis régénérer `REGISTRY.md`.
- **Variables** : aucune ; p2 utilise un mot mort de la pile de la reverb, p1 et p3 lisent l'état de l'OS.

### 5.2 Ce que p2 n'apporte pas (limite mesurée)

Une fois qu'un effet a reçu du son, ses restes (§3.6) gardent au moins un mot non nul : p2 reste éveillé jusqu'au
prochain redémarrage. Il sert donc aux projets qui n'utilisent pas le delay ou la reverb (ou pas encore), ce qui est
le défaut des sons. Le delay et la reverb se jugent séparément (un projet avec reverb et sans delay garde +1,9 à 2,0 %).

### 5.3 Piste 4 — Purge des restes (non identique)

Si l'entrée de l'effet est nulle et sa sortie sous ±4 096 (sur 2^31, −114 dBFS ; restes mesurés : 204 pour le delay,
~1 400 pour la reverb) pendant T blocs (1 500 = 1 s), on force ses lectures à zéro pendant L blocs, le temps que
l'eDMA réécrive toute la ligne de zéros (reverb : 64 Ko / 128 o = 512 blocs ; delay : 4 Mo / 256 o = 16 384 blocs,
~11 s), puis p2 prend le relais exactement. Pendant la purge le calcul est déjà sauté (comme p2), seuls les tampons
d'écriture sont mis à zéro. Différence avec l'OS d'origine : le reste jeté, ≤ 24 pas de 24 bits au codec. Un retour
de signal pendant la purge l'arrête (le reste encore présent ailleurs dans la ligne revient, sous −111 dBFS).
Contrairement à Model-TG, l'eDMA et les pointeurs continuent : les lignes restent cohérentes.

### 5.4 Piste 5 — Préparer l'eDMA avant les voix

La préparation `0x4005802e` ne dépend que de l'état laissé par le bloc précédent et du temps de delay lissé
(`a2@(428)`, posé par `0x40058474` au début de la fonction audio `0x400597a8`) [FAIT, désassemblage `0x4005802e..`]. Appelée
juste avant la boucle des voix (`0x4005980a`) au lieu de `0x400567d6`, elle a toute la boucle des voix (~45 % d'un
bloc) pour finir : l'attente `0x4005697e` ne tourne plus jamais. Mêmes données, même ordre des états
(`0x423087e4`, `a3dc..` écrits avant leur lecture par la reverb) : son identique, prouvable sur le banc. Points
durs : la préparation pose `MACSR = 0x20` et vide acc0/acc1 (Model-TG reproduit exactement ces effets à la place de
l'appel : `a93c00000020a1c0a3c0` en `0x400567d6`) ; au nouveau point il faut les sauvegarder et les rendre, ou montrer
que la boucle des voix ne lit ni l'un ni l'autre. Conflit avec Model-TG, qui déplace déjà cet appel dans son
enveloppe du delay. Gain inconnu tant que l'attente n'a pas été mesurée sur la machine (§7).

### 5.5 Piste 6 — Vérification réduite de p2

En sommeil, p2 relit chaque bloc les 683 mots de la reverb (~1 300 instructions sur 1 595). Les lignes ne sont
écrites que par le canal 42 depuis les tampons que p2 laisse nuls ; après 512 blocs de sommeil (une ligne longue
entière réécrite), seule l'entrée peut encore réveiller la reverb. Un compteur (dans le masque) ramène le sommeil à
~250 instructions. Pas pour le delay : un changement de Delay Time peut viser une partie de la ligne écrite avant
le sommeil, il faut garder ses 130 mots de prises.

## 6. Ce que le son garde, et comment le prouver

- p1, p2, p3 : `test_combo.py` (ensemble) et `test_proto1.py`, `test_proto2.py` (seuls), OS d'origine contre modifié
  sur le même banc, bloc par bloc ; ils sortent en échec au premier écart et disent où.
- Pour un vrai tweak : refaire ces preuves avec les mods installables avec lui (`--with …`), et les jouer longtemps
  (le sommeil doit tenir des heures : c'est une égalité stricte, pas une mesure).

## 7. Ce qu'il faudrait mesurer sur la machine (à demander à Maxime, rien n'est mesuré ici)

1. **L'attente eDMA** `0x4005697e` : un firmware de mesure qui compte les tours de la boucle (max et moyenne, affichés
   comme le régulateur de notes/31) dirait si la piste 5 vaut 0 ou 2,5 %.
2. **p1+p2+p3** : la page de charge (notes/31 §7) avec un projet sans effets ni Dist, puis le même avec envois et
   Dist : écart attendu ~14 points au repos, ~3,5 points effets en service.
3. **Écoute** : aucun changement attendu ; tourner les envois et VOL+DIST pendant la lecture (réveils du sommeil).

## 8. Notes pour les autres études

- L'interface étouffe au-dessus de ~85 % de moyenne (COMMON.md) : p1+p2+p3 ramènent le bloc émulé de 79,3 à 64,6 %
  dans le cas par défaut, sous ce seuil avec de la marge [DÉDUIT du modèle, à confirmer sur la machine].
- notes/31 §7 rangeait « delay et reverb ~12 % » dans « ce qu'on ne peut pas gagner sans rien perdre » : c'est vrai
  quand ils servent, faux quand ils ne servent pas.

## 9. Fichiers (dans ce dossier)

- `banc.py` (le banc), `trace.py` (modèle de cache), `mesure.py`, `mesure2.py` (mesures), `loops.py` (par boucle),
  `analyse_rw.py` (ce que lisent et écrivent delay et reverb), `queue.py`, `queue2.py`, `residu.py` (restes).
- `proto/vd_skip.S` (p1), `proto/fx_lib.S`, `proto/fx_dly.S`, `proto/fx_rev.S` (p2), `proto/send_skip.S` (p3),
  `proto/asm.py` (assemblage : `m68k-linux-gnu-as -mcpu=54418`).
- Preuves : `test_proto1.py`, `test_proto2.py`, `test_combo.py`, `lissage.py`, `mesure_flushtb.py`,
  `scan_tweaks.py` (écritures des 282 tweaks dans les zones des prototypes) ; sorties `test_proto2.log`,
  `test_combo.log`, `lissage.log`, `mesures.log`, `mesure2.log`, `q2_A.log`, `queue.log` ; sortie de p1 :
  `/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/tasks/bqgim176l.output`.
- Rien n'est écrit dans le dépôt ; aucun octet de l'OS n'est recopié dans ces fichiers (seulement les `old` de ≤ 8 o
  des détours, cités au §4).
