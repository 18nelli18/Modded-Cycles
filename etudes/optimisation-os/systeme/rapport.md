# Volet « système » : interruptions, tâches, écran, caches et mémoire, séquenceur — Model:Cycles OS 1.13

Agent « systeme », 17/10/2026. Lecture seule sur le dépôt ; tout le travail est dans ce dossier.

Repères : `[FAIT]` = vu dans le code de l'OS 1.13 d'origine (adresse et instruction), dans une sortie d'outil ou en
émulation ; `[DÉDUIT]` = calculé à partir de faits ; `[HYP]` = plausible, pas vérifié. Adresses : VA du MAIN OS
(section 3, `0x40000400` + décalage) ; bootstrap (section 2) en `0x80010000`. « % d'un bloc » : modèle des notes 27-28
(1,54 cycle par instruction, 15 cycles par ligne de 16 o en SDRAM, 166 667 cycles par bloc), étalonné sur la machine
(notes/27 §2).

## 0. En bref

- **Le plus gros gaspillage trouvé est la mémoire, pas l'organisation des tâches.** À chaque bloc, l'audio exécute
  **17,4 Ko de code** différent (voix 9,3 Ko, étage de sortie 6,4 Ko, le reste 1,7 Ko), deux fois la taille du cache
  d'instructions (8 Ko). Résultat : **presque chaque ligne de code est relue en SDRAM à chaque bloc**, même quand
  l'interface ne fait rien (1 111 défauts pour 1 113 lignes, environ **10 % d'un bloc**) `[DÉDUIT, modèle]` (§4.3).
  Réordonner le code ou verrouiller une moitié du cache n'y change presque rien (c'est un manque de place, pas un
  conflit) ; ce qui marche, c'est d'exécuter ce code ailleurs.
- **Piste n° 1 : la SRAM d'origine, réorganisée.** 30 Ko des 64 Ko de SRAM tiennent les tables d'ondes de CHORD, qui ne
  servent que si une piste joue CHORD. La note 28 les a déjà sorties pour les moteurs du Syntakt (son inchangé, prouvé,
  mesuré sur la machine). Dans la place libérée, le code chaud de l'OS d'origine tient en entier : voix, LFO, lissage et
  interruption de rendu (21,3 Ko) dans la 1ʳᵉ zone (22,6 Ko), étage de sortie (7 600 o) dans la 2ᵉ (8,2 Ko). **Gain estimé : 5 à 9 points
  d'un bloc** sur un motif à 6 pistes (6 machines différentes, dont CHORD), son identique à l'échantillon près
  (§4.4, `cachesim_sram.py`). Elle ne s'applique qu'aux firmwares **sans** moteurs du Syntakt : ceux-ci occupent déjà
  cette SRAM.
- **Les interruptions et les tâches coûtent peu.** Tout ce qui coupe l'audio (niveaux 6 et 7 : panneau à 12 kHz, USB à
  8 kHz pendant le flux, DMA audio) fait environ **1 à 1,5 point d'un bloc** `[DÉDUIT, émulation]` (§2). Le noyau
  multitâche est léger (changement de contexte : une vingtaine d'instructions) (§3.1).
- **Attentes actives** (§3.6) : l'écran (jusqu'à 1,5 ms par image, dans la tâche de l'interface), le DMA du delay et de
  la reverb (de 0 à environ 2,4 % d'un bloc, dans le rendu, trouvé par l'agent « sortie »), l'effacement et l'écriture de
  la flash SPI (pendant les sauvegardes). Aucune ne touche le son ; seule celle du DMA allonge le rendu.
- **Séquenceur** (§5) : 0,4 % d'un bloc à vide, jusqu'à 3,4 % (cache chaud) ou 6 % (cache froid) quand 6 trigs avec
  10 p-locks tombent dans le même bloc. Le pic vient de l'application des paramètres de chaque événement
  (`0x400583da`, 46 % du pire bloc). On ne peut pas l'étaler sans perdre la précision au bloc près ; on peut l'alléger.
- **Firmware de mesure** (§6) : un compteur de temps libre, dans la boucle d'attente de la tâche de priorité 0, est
  prototypé et **prouvé en émulation** (écart ≤ 0,3 point, ne touche que son compteur). Avec quelques sondes, il dirait
  sur la machine où partent les 23 % qui restent à l'interface.

| # | Piste | Gain estimé | Son identique | Risque | Effort |
|---|---|---|---|---|---|
| 1 | SRAM réorganisée : tables de CHORD en SDRAM, code chaud d'origine en SRAM (§4.4) | 5 à 9 points par bloc, tout le temps (6 pistes jouées) ; jusqu'à 11 avec les états des voix si on trouve 4,8 Ko de plus | oui (même code, mêmes données ; preuve comme `test_sram_code.py`) | moyen (relocalisation du code d'origine, crochet de démarrage partagé ; incompatible avec les moteurs du Syntakt) | élevé |
| 2 | Firmware de mesure : temps libre + sondes (§6) | 0 (il mesure) ; il conditionne les pistes 3 à 6 | oui | faible (firmware de diagnostic, pas une carte du flasher) | faible à moyen |
| 3 | Étage de sortie seul en SRAM (sous-ensemble de 1, §4.4) | environ 3 points par bloc, tout le temps, même à l'arrêt | oui | moyen | moyen |
| 4 | Séquenceur : préparer les p-locks hors du rendu (§5) | 1 à 2,5 points sur le bloc du trig seulement (pics), 0 en moyenne | à prouver (mêmes valeurs au même bloc) | moyen | élevé |
| 5 | Verrouiller une moitié du cache I et/ou D (§4.5) | 1,7 à 4 points (modèle), moins une fois la piste 1 faite | oui | moyen (l'interface n'a plus que la moitié des caches ; à mesurer) | faible à moyen |
| 6 | Écran : horloge SPI × 2 (§3.4) | interface : jusqu'à 0,75 ms par image redessinée en entier (2,5 % du temps à 30 images/s) ; 0 pour l'audio | oui | faible à moyen (vitesse maximale du contrôleur de l'écran inconnue) | très faible |
| 7 | DMA du delay et de la reverb lancé plus tôt (§3.6, domaine de « sortie ») | 0 à 2,4 points (attente réelle inconnue) | à prouver | moyen | moyen |
| 8 | Flash : dormir au lieu de tourner pendant l'effacement (§3.6) | interface, pendant les sauvegardes seulement ; inconnu | oui | moyen | moyen |
| — | À ne pas faire : panneau sous le niveau de l'audio, USB regroupé, alignement des boucles, `stop` dans la boucle d'attente (§2.3, §4.5) | ≤ 1 point, ou rien | — | visible (LED, touches) ou nul | — |

## 1. Méthode et outils

- Désassemblage complet de la section 3 (`sec3.dis`) et du bootstrap (`sec2.dis`) ; `dis.sh 0xdébut 0xfin`.
- Émulation Unicorn du vrai code de l'OS d'origine :
  - `scripts/isrrig.py` : banc des interruptions hors audio (cadre d'exception factice, arrêt sur `rte`, comptage des
    instructions, des lignes de code et de données et des accès aux périphériques). Sert au panneau, à l'USB, à l'écran.
  - `scripts/seqcost.py`, `scripts/seqprof.py` : coût du séquenceur dans l'interruption de rendu, avec `seqrig.py` du
    dépôt.
  - `scripts/trace.py` : trace complète de 4 blocs (interruption de rendu, voix, mixeur, effets, sortie codec) avec le
    banc de l'étage de sortie de l'agent « sortie » (`optim/sortie/banc.py`, lu tel quel), 6 pistes KICK, SNARE, METAL,
    PERC, TONE, CHORD, sons par défaut, déclenchées au bloc 2 ; sortie `trace_play.npz`.
  - `scripts/cachesim.py`, `scripts/cachesim_sram.py` : caches 8 Ko + 8 Ko, 4 voies, lignes de 16 o, LRU, sur cette
    trace ; scénarios chaud, pollué (K lignes étrangères entre deux blocs), vidé.
  - `scripts/screencost.py`, `scripts/usbcost.py` : envoi d'une image à l'écran, coût fixe de l'USB.
  - `proto/idle.S`, `proto/idle_proto.py` : compteur de temps libre.
- Horloge : le bus tourne à 135,168 MHz `[FAIT]` (l'OS divise son compteur de temps par `#135168000` en `0x40005472` ;
  le minuteur DMA 0 compte à cette fréquence, `bridge_engines.c:215`). Le cœur tourne sans doute à 2 × bus =
  270,336 MHz `[HYP]` (le MCF54415 est donné pour 250 MHz) ; les notes comptent 250 MHz. Les gains en « points d'un
  bloc » restent comparables entre eux ; leur valeur absolue peut être 8 % trop forte.

## 2. Les interruptions

### 2.1 La table des vecteurs `[FAIT]`

- VBR = `0x40000000` (`movec %d0,%vbr` en `0x400cefc2`). `0x400cefa0` remplit les 256 vecteurs avec le gestionnaire
  par défaut `0x40001976` (qui appelle le rappel `0x4049fd64`), puis pose les vecteurs 0, 24, 64 et 128 sur
  `0x400019a6`, règle le PIT0 (`jsr 0x400019b4` : PMR `0xa4ff`, PCSR `0x053f`, niveau 1), passe en SR `0x2000` et lance
  la première tâche par `trap #0`.
- Les autres vecteurs sont posés par les pilotes à leur initialisation (une écriture dans `0x40000000 + 4 × n`, et le
  niveau dans l'ICR du contrôleur : INTC0 `0xfc048040 + source`, INTC1 `0xfc04c040 + source`, INTC2 `0xfc050040 +
  source` ; vecteur = 64 + source, 128 + source, 192 + source).
- Interruptions forcées par logiciel (INTFRCL, `0xfc04c014` pour INTC1) : c'est ainsi que l'OS chaîne un travail
  urgent court (niveau haut) et sa suite plus longue (niveau bas).

### 2.2 Inventaire

| Vecteur | Source, niveau | Gestionnaire | Rôle | Fréquence | Coût par appel (émulation) | % du processeur |
|---|---|---|---|---|---|---|
| 205 | PIT0, INTC2/13, niv. 1 (et forcé, et `trap #0` = vecteur 32) | `0x40000410` | changement de contexte | 100/s + chaque réveil de tâche | ~20 instructions, dont 12 sous `move #0x2700,%sr` | < 0,01 % `[DÉDUIT]` |
| 207 | PIT2, INTC2/15, niv. 3 | `0x400020b8` | réveille la tâche des minuteurs | 120/s (PMR 17600) | court | < 0,01 % `[DÉDUIT]` |
| 208 | PIT3, INTC2/16, **niv. 6** | chaîne de 12 phases : `0x40059cd0`, `0x40059d2c` × 8 (colonnes, lit l'ADC `0xfc094012`), `0x40059db8` × 3 (LED) | balayage du panneau | 12 000/s | début 20 instr. / 4 accès périph. ; colonne 36 / 7 ; LED 34 / 3 | ~0,9 % avec la suivante `[DÉDUIT]` |
| 130 | INTC1/2 forcée, niv. 3 | `0x40059e64` | touches, encodeurs (table `0x4010dab0`), pads (`0x400598b8` × 6) | 1 000/s | 480 instr. / 2 accès | (compté ci-dessus) |
| 170 | eDMA ch50, INTC1/42, **niv. 6** | `0x400589c0` | début de bloc : horodatage, force le rendu | 1 500/s | ~20 instr. | 0,02 % `[DÉDUIT]` |
| 191 | INTC1/63 forcée, niv. 5 | `0x40058c5e` (variante `0x40051340` posée par `0x4005153a`) | **rendu audio** : séquenceur, USB entrant, `jsr 0x4005979e`, envoi USB | 1 500/s | 72 500 instr. (bloc à 6 pistes) | 77 % (notes/23 §6 bis) |
| 209 | USB OTG, INTC2/17, **niv. 6** | `0x40004318` | horodatage des micro-trames, rappels SOF, force la suite | 8 000/s pendant le flux audio | 60 instr. / 8 accès (UI + SRI) | ≥ 0,3 % |
| 134 | INTC1/6 forcée, niv. 4 | `0x40005078` | suite de l'USB : tour des 8 points d'accès (`ENDPTCOMPLETE 0xfc0b01bc`), retrait des dTD, rappels de données | 8 000/s pendant le flux | 100 instr. / 11 accès sans rien à retirer, plus les rappels | ≥ 0,5 % |
| 156, 157 | eDMA ch36, ch37, INTC1/28-29, niv. 4 | `0x40001094`, `0x40001000` | réception et émission DMA de l'UART9 (MIDI) | au rythme du MIDI | court | négligeable |
| 181 | INTC1/53, niv. 4 | `0x40000e8c` | UART9 `[HYP]` | au rythme du MIDI | court | négligeable |
| 99 | DTIM3, INTC0/35, niv. 2 | `0x4003eaf8` | message 5 à la tâche de l'interface (cadence des images) | 30/s | court | négligeable |
| 98 | DTIM2, INTC0/34, **niv. 7** | `0x40052830` | un coup : lit l'ADC (RSLT1, RSLT2 → `0x422ff160/164`), touche le DAC1 ; armé par `0x40053376` depuis le rappel `0x40053242` | ~1,9/s | court | négligeable |
| 108 | INTC0/44 forcée, niv. 5 `[HYP]` | `0x4005420c` | horloge MIDI (0xF8 par `0x40082512`) ; forcée par le rendu (`0x40059430`) et par `0x40080578` ; force la 121 | 24 par noire | court | négligeable |
| 121 | INTC0/57 forcée, niv. 2 | `0x40054c1e` | tic du séquenceur à 24 ppq (+900 000 sur `0x40a78628` ; un pas = 5 400 000) ; construit les événements d'un pas | 48/s à 120 BPM | 630 à 690 instr. par trig | ≈ 0,02 % (6 trigs par pas) `[DÉDUIT]` |
| 223 | eSDHC, INTC2/31, niv. 3 | `0x4008a676` | carte/mémoire : sémaphores | pendant les accès | court | — |
| 67 | EPORT3, niv. 3 | `0x4008a640` | sémaphore | rare | court | — |
| 192 | INTC2/0, niv. 3 | `0x4008a75c` | fin du canal eDMA 59 : sémaphore | pendant les accès | court | — |
| 97 | DTIM1, INTC0/33, niv. 2 | `0x4008f394` | délai à un coup : sémaphore | à la demande | court | — |

Sources : désassemblage des gestionnaires et de leurs mises en place `[FAIT]` ; coûts par `isrrig.py`, `usbcost.py`
`[FAIT, émulation]` ; % = instructions × 1,54 × fréquence / 250 MHz, plus les entrées d'exception `[DÉDUIT]`.

Le panneau, mesuré sur 30 cycles de 12 phases (`python3 scripts/isrrig.py sec3.bin`) : **13 interruptions,
≈ 850 instructions et 58 accès aux périphériques par milliseconde** `[FAIT, émulation]`, soit environ 2 400 cycles par
ms avec les entrées d'exception et les accès lents, **≈ 1 % du processeur** `[DÉDUIT]`.

### 2.3 Ce qui coupe l'audio, et à quel prix

Le rendu tourne au niveau 5 : seuls les niveaux 6 et 7 l'interrompent.

- Panneau (niv. 6) : ≈ 1 % du processeur, dont environ 0,8 point tombe pendant le rendu (77 % du temps) et l'allonge
  d'autant `[DÉDUIT]`.
- USB (niv. 6), seulement pendant le flux audio : la partie au niveau 6 fait 60 instructions par micro-trame ≈ 0,3 %,
  plus ses lignes de code (19) souvent chassées par l'audio entre deux micro-trames : 0,3 à 0,6 point pendant le rendu
  `[DÉDUIT]`. La suite (niveau 4) et ses rappels de données attendent la fin du rendu : ils ne l'allongent pas.
- DMA audio (niv. 6) : 20 instructions par bloc, c'est le départ du bloc lui-même.
- DTIM2 (niv. 7) et les sections masquées à 7 (changement de contexte, 5 instructions de lecture atomique dans
  l'USB en `0x40004322..0x40004344`) : négligeable.
- **Total : 1 à 1,5 point d'un bloc** `[DÉDUIT]`. Descendre le panneau sous le niveau 5 gagnerait au plus 0,8 point,
  mais ses phases attendraient la fin du rendu (jusqu'à 0,5 ms) : LED multiplexées inégales (scintillement), balayage
  des touches irrégulier. **Non recommandé.**

### 2.4 L'USB pendant le flux `[FAIT]`

- Le contrôleur lève une fin de transfert à chaque micro-trame : les dTD portent IOC (`0x00408080`, posé en
  `0x40004406`). USBINTR d'origine `0x157` : SOF coupé.
- Le rappel SOF de mesure du débit (`0x4000238e`, inscrit par `0x40002d8e` au démarrage du flux) ne fait presque
  jamais lever d'interruption à lui seul :
  - le bit SRI d'USBSTS se lève à chaque micro-trame même sans interruption ; `0x40004318` le lit à chaque fin de
    transfert (`0x4000437e`) et appelle alors les rappels SOF ;
  - `0x4000238e` sort tout de suite tant que moins de 80 micro-trames (10 ms) ont passé (`cmpl` en `0x400023ac`) ;
    sinon il active SRE (`bset #7` en `0x400023c8`) pour recevoir la micro-trame suivante à l'heure exacte, mesure,
    puis coupe SRE (`bclr #7` en `0x400023e8`).
- Coût fixe par micro-trame : 60 + 100 instructions (`usbcost.py`), deux entrées d'exception, 19 accès aux registres
  de l'USB, 36 lignes de code `[FAIT, émulation]` → **0,8 % au moins**, plus les rappels de données
  (copie des trames, notes/35) `[DÉDUIT]`. Rien de sûr à y gagner : la séparation en deux niveaux est bien faite.
- Rappel de la note 35 : l'envoi vers l'ordinateur part **après** le calcul du bloc (`0x40059392`) ; tout ce qui rend
  la durée du rendu variable rend l'envoi variable. Les pistes de ce rapport réduisent la durée du rendu sans la rendre
  plus variable.

## 3. Hors interruption : le noyau, les tâches, l'écran

### 3.1 Le noyau `[FAIT]`

- Préemptif, 16 priorités. Listes des tâches prêtes en `0x422feec8 + 4 × prio`, pointeur vers la plus haute en
  `0x4049fd60`, tâche courante en `0x422fef30`.
- Changement de contexte `0x40000410` : masque tout (`move #0x2700,%sr`), sauve les 16 registres
  (`moveml %d0-%sp,%a0@(12)` en `0x4000041e`), prend la tête de la liste la plus haute, acquitte le PIT0, restaure,
  `rte`. Déclenché par le PIT0 (100 Hz), par INTFRCL bit 13 (réveil d'une tâche depuis une interruption) et par
  `trap #0`.
- Sémaphores : attente `0x40001aca`, signal `0x40001c80` ; verrou `0x40001cc4` / `0x40001df6` ; boîte aux lettres
  `0x40001fba`. Création de tâche : `0x400019ec(tcb, entrée, prio, base_pile, taille)`.
- **Boucle d'attente** : la tâche de priorité 0 (`0x40005410`) crée la tâche de démarrage puis tourne sur
  `bras 0x4000543e` (`60fe`), **sans `stop`**. Elle ne coûte rien à personne (elle ne tourne que quand tout le reste
  dort), mais elle est l'endroit idéal pour mesurer le temps libre (§6).

### 3.2 Les tâches `[FAIT]` (création par `0x400019ec`, rôle `[HYP]` sauf mention)

| Entrée | Priorité | Pile | Rôle |
|---|---|---|---|
| `0x400020e6` | 10 | 2 Ko | minuteurs à 120 Hz (rappels ci-dessous) `[FAIT]` |
| `0x400015c4` | 9 | 4 Ko | ? |
| `0x4008a0ba` | 8 | 4 Ko | stockage ? |
| `0x40080674` | 7 | 32 Ko | MIDI ? (envoi, changement de vitesse `0x40080dd0`) |
| `0x40053a6c` | 7 | — | animation de démarrage `[FAIT]` (notes/39) |
| `0x40007d46` | 6 | 160 Ko | **interface** (image par `0x400075da`) `[FAIT]` |
| `0x40082082` | 3 | 32 Ko | ? |
| `0x40044188` | 2 | 16 Ko | après l'initialisation du codec |
| `0x40068c78` | 2 | 16 Ko | ? |
| `0x40078436` | variable (d2) | 16 Ko | ? |
| `0x400054a2` | 1 | 16 Ko | démarrage |
| `0x40005410` | 0 | 16 Ko | attente |

Rappels de la tâche des minuteurs (un rappel de masque m tourne quand le bit correspondant du compteur à 120 Hz
change) `[FAIT]` : `0x4007f914` (1, maintien des touches), `0x400811fc` (1), `0x4008e7ca` (1, LED), `0x4008ec4c`
(2 : 60 Hz), `0x4000530e` (4 : 30 Hz, USB), `0x40080902` (4), `0x4004288c` (0x10 : 7,5 Hz), `0x40053242` (0x40),
`0x400053b4` (0x80 : compteur de temps sur 64 bits `0x404a0aa4`, depuis le minuteur DMA 0), `0x40044178` (0x100),
`0x400539b8` (animation de démarrage).

### 3.3 Ce qui vole du temps à l'interface

- L'interface (priorité 6) n'a que le temps que l'audio laisse : 23 % à l'arrêt avec l'OS d'origine (notes/23 §6 bis).
  Au-dessus d'elle : minuteurs, MIDI, stockage, et toutes les interruptions.
- `[DÉDUIT]` (§4.3) : comme l'audio fait passer 17,4 Ko de code dans un cache de 8 Ko à chaque bloc (toutes les
  0,67 ms), **le code de l'interface est chassé du cache à chaque bloc** et repart à froid. L'interface paie donc
  aussi le manque de place du cache d'instructions. Si le code de l'audio s'exécute en SRAM sans passer par le cache
  (§4.2, `[HYP]`), l'interface garde tout le cache.

### 3.4 L'écran `[FAIT]`

- `0x400075da` (tâche de l'interface) : si la vue racine doit être redessinée (`0x40076be4`), tout l'arbre des vues est
  redessiné dans un Bitmap 128 × 64 (`0x40070172`, `0x40076c1a`, `0x400062e0`), puis `0x4008e622` l'envoie. Cadence :
  30 images/s au plus, au rythme du message du DTIM3 `[DÉDUIT]`.
- `0x4008e622` compare les deux tampons de 1 Ko (`0x401492f0` / `0x401492f4`) par blocs de 8 × 8 pixels, octet par
  octet (bloc (d3, j) = octets d3 + 64 j + 8 i, `0x4008e63c..0x4008e696`). Pour chaque bloc changé, `0x4008e580`
  envoie la position (3 trames, `0x40053f64`) puis les 8 octets (`0x40053fb0`) par `0x40053e74`, qui remplit la file du
  DSPI1 puis **attend en boucle la fin de file** (`btst #28` sur `0xfc03c02c` en `0x40053ee6..0x40053ef0`). Puis les
  tampons sont échangés.
- DSPI1 : CTAR2 = `0x46000223` (posé par le bootstrap) → trames de 9 bits, SCK = 135,168 / 2 / 8 = 8,448 MHz
  `[DÉDUIT]` (décodage des champs FMSZ, PBR, BR).
- Coût (`python3 scripts/screencost.py sec3.bin`, DSPI modélisé, attente calculée à part) `[FAIT, émulation]` :

| Blocs changés | Instructions | Temps CPU (250 MHz) | Attente SPI active | À 30 images/s |
|---|---|---|---|---|
| 0 | 9 405 | 58 µs | 0 | 0,17 % du temps |
| 1 | 9 638 | 59 µs | 12 µs | 0,21 % |
| 16 (une ligne de texte) | 12 797 | 79 µs | 188 µs | 0,80 % |
| 64 (demi-écran) | 22 573 | 139 µs | 750 µs | 2,67 % |
| 128 (écran entier) | 35 789 | 221 µs | 1 500 µs | 5,16 % |

  Plus le dessin des vues dans le Bitmap, pas mesuré (il dépend de la page) `[HYP : du même ordre ou plus]`.
- Ce que ça coûte à qui : l'attente tourne dans la tâche de l'interface, interruptions ouvertes ; **l'audio n'y perd
  rien**. L'interface perd jusqu'à 1,7 ms par image redessinée en entier, soit **jusqu'à 22 % du temps qui lui reste**
  (5,2 % sur 23 %) pendant les redessins complets (changement de page, défilement) `[DÉDUIT]`.
- Pistes :
  - **Horloge SPI × 2** : BR 3 → 1 (÷ 8 → ÷ 4) dans CTAR2 donnerait 16,9 MHz ; l'attente passe de 1,5 à 0,75 ms par
    plein écran. Les contrôleurs d'écran de ce genre acceptent souvent 20 MHz `[HYP : contrôleur et câblage
    inconnus]`. Un mot à écrire à l'initialisation de l'OS (le bootstrap, lui, reste intact : la récupération ne change
    pas). Son identique ; preuve en émulation triviale (mêmes trames) ; risque : écran brouillé si le contrôleur ne
    suit pas, à essayer sur la machine.
  - Attente par interruption (EOQF → sémaphore) : l'interface ne gagne rien (elle attend quand même), seules les tâches
    de priorité < 6 en profitent. Gain faible, effort moyen. Non prioritaire.

### 3.5 LED, potards, sauvegarde `[FAIT]`

- LED : 3 phases de multiplexage dans le balayage à 12 kHz (`0x40059db8`), état mis à jour à 120 Hz (`0x4008e7ca`).
- Potards : l'ADC (RSLT0, `0xfc094012`) est lu dans les 8 phases de colonnes du balayage ; RSLT1-2 dans le DTIM2 à
  ~1,9 Hz.
- Sauvegarde : la carte/mémoire eSDHC travaille par interruptions et sémaphores (bien) ; la flash SPI (DSPI0) tourne en
  attente active (§3.6).

### 3.6 Les attentes actives

Recherche systématique (`scripts/polls.py` : lecture d'un registre de périphérique suivie d'un branchement vers
elle-même ; 62 boucles, triées à la main) :

| Où | Quoi | Qui attend | Durée | Effet |
|---|---|---|---|---|
| `0x40053ee6` | fin de file du DSPI1 (écran) | tâche de l'interface | 12 µs par bloc de 8 × 8, ≤ 1,5 ms par image | interface seulement (§3.4) |
| `0x4005697e..0x4005698a` | `TCD30.CSR.ESG` : DMA DDR → SRAM des lignes du delay et de la reverb (2 864 o) | **rendu audio** (mixeur `0x400567ba`) | 0 à ~16 µs par bloc `[HYP]` | **0 à 2,4 points d'un bloc** (agent « sortie », `optim/sortie/rapport.md` § eDMA) |
| `0x4008fd1c..0x4008fd30`, `0x40090214..0x40090228`, `0x40090276..`, et 4 autres | état de la flash SPI (RDSR `0x05`, bit WIP) : écriture de page, effacement 4 Ko (`0x20`) et 64 Ko (`0xd8`) ; entre deux lectures, 10 000 tours de `tpf ; subq ; bne` (≈ 0,2 ms) | la tâche qui sauve (appelants `0x40042b7e`, `0x40092334` ; priorité `[HYP]`) | effacement : dizaines à centaines de ms `[HYP, puce non identifiée]` | si la tâche est au-dessus de l'interface, l'interface gèle pendant l'effacement `[HYP]` |
| `0x4008f46c` | délai actif sur le PIT1 | init du codec (`0x400443d8..`), `0x4005a0a2` | µs | démarrage |
| `0x40044422..0x400445aa` | I2C (codec) | démarrage | — | aucun |
| `0x40001310`, `0x40080dd6` | UART9 vide (avant un changement de vitesse du MIDI, `0x40080dd0` écrit UBG2 depuis la table de 11 vitesses `0x4011299c`) | MIDI | rare | aucun |
| `0x40005178` | USB, setup (1 000 tours au plus) | suite de l'USB | rare | aucun |
| `0x4000543e` | boucle d'attente | priorité 0 | tout le temps libre | voulu (§6) |

## 4. Caches et mémoire

### 4.1 Les registres `[FAIT]`

- **CACR = `0xa50ce100`** (`0x40000548`) : cache de données en marche (DEC), tampon d'écriture (DESB), mode par défaut
  hors ACR = non caché précis (DDCM = 10), invalidation (DCINVA) ; cache de branchements (BEC, BCINVA) ; cache
  d'instructions en marche (IEC, SPA, IDPI), **instructions cachées par défaut (IDCM = 0)**, invalidation (ICINVA).
  Aucun verrou : DHLCK (bit 27) = IHLCK (bit 12) = 0. Disposition des bits comme en notes/50.
- **ACR0 = `0x4007e020`** (`0x40000552`) : `0x40000000..0x47ffffff` en copyback. Il n'y a que 3 `movec` dans tout le
  MAIN OS : CACR, ACR0, VBR. ACR1 reste à 0 après le bootstrap (Model-TG le règle).
- Le bootstrap décompresse l'OS avec CACR `0xa508e000`, ACR0 `0x4003e000` (writethrough) et ACR1 `0x0000e020`
  (`0x80010428..0x80010442`), puis remet ACR0 = ACR1 = 0 et CACR = `0x0008c000` (`0x80010480..0x80010490`) avant le saut
  dans l'OS. Writethrough pendant la décompression : aucune ligne sale, l'invalidation par l'OS est sûre `[DÉDUIT]`.
- **RAMBAR1 = `0x80000235`**, écrit par le bootstrap (`movec %d0,%rambar1` en `0x80010de0`, dans `0x80010d70` qui mène
  ensuite à la décompression `jsr 0x80010424` en `0x80010e84`) ; l'OS ne le change pas (notes/27 §3.3). Décodage
  `[HYP : disposition des champs prise des autres manuels ColdFire, celui du MCF5441x n'a pas pu être lu]` : base
  `0x80000000`, bit 9 (priorité du cœur sur la moitié haute), bits 5-0 = C/I, **SC**, UC masqués, SD et UD permis,
  valide. Si c'est bien ça, **les lectures d'instructions en SRAM ne passent pas par le port direct** : elles passent
  par le cache d'instructions et la barre transversale (comme le DMA, qui lit et écrit la SRAM, agent « sortie »).
  Le code en SRAM resterait alors dans le cache d'instructions, avec des remplissages rapides. À mesurer (§6.3).
- SRAM : 64 Ko, accès aux données en un cycle, hors cache (notes/26 §1) ; remplie au démarrage par `0x4000045c`
  depuis `0x4019b590..0x401aa140` (agent « voix », `optim/voix/sram_voix.txt`) :
  - `0x80000000..0x80001c5c` : structures du système, paramètres et lissage (`0x8000100c`, `0x800011e8`, `0x800015a0`),
    sorties des pistes `0x80001858` ;
  - **`0x80001c5c..0x800074b4` (22,6 Ko) et `0x8000cac0..0x8000eae0` (8,2 Ko) : les 30 tables d'ondes de CHORD**,
    lues par CHORD seul (`0x400a8060`), froides quand aucune piste ne joue CHORD ;
  - `0x80008000..` : réserve de dTD de l'USB, ring USB `0x80009800`, étage de sortie `0x8000a100..0x8000bd18`, brouillon
    des voix `0x8000be50..0x8000c8f0`, sinus `0x8000eae0..` ;
  - les états des 6 voix ne sont pas en SRAM : `0x42308828 + 0x31c × t`, 4 776 o en SDRAM cachée.
- Pile : chaque tâche a la sienne en SDRAM cachée (taille au §3.2) ; les interruptions tournent sur la pile de la tâche
  interrompue `[HYP]`.

### 4.2 Ce que fait un bloc à la mémoire `[FAIT, émulation]`

Trace de 4 blocs en régime établi (`trace.py`, puis `regions.py`) : **72 527 instructions, 1 113 lignes de code
distinctes (17,4 Ko)**, 467 lignes de données cachées, 9 553 accès en SRAM, 87 accès non cachés.

| Région | Étendue | Lignes chaudes | Instructions |
|---|---|---|---|
| Voix (6 machines) | `0x400a7d10..0x400ab7c0` (15,0 Ko) | 597 (9,3 Ko) | 42 282 |
| Étage de sortie (mix, delay, reverb) | `0x40056520..0x400582d0` (7,4 Ko) | 395 (6,2 Ko) | 28 970 |
| Lissage, interruption de rendu, fonction audio | `0x40058470..0x400597f0` (4,9 Ko) | 50 | — |
| LFO | `0x400918b0..0x40091d90` (1,2 Ko) | 40 | — |
| Ailleurs (USB entrant, memcpy…) | — | 31 | — |

Données : états des voix (`0x423xxxxx`) 254 lignes, `0x40a7xxxx` 59, tables `0x4011..0x4013` environ 87,
`0x40fexxxx` 36.

### 4.3 Simulation de cache

`python3 scripts/cachesim.py trace_play.npz` `[FAIT, sortie du modèle]` :

| Scénario entre deux blocs | Défauts I | Défauts D | Réécritures | % du bloc | + verrou ½ I | + verrou ½ D | + les deux |
|---|---|---|---|---|---|---|---|
| chaud (rien d'autre ne tourne) | 1 111 | 140 | 63 | 78,84 | 77,17 | 78,14 | 76,48 |
| pollué 512 lignes | 1 113 | 436 | — | 81,59 | 79,91 | 79,08 | 77,39 |
| vidé | 1 113 | 468 | 22 | 81,44 | 79,76 | 79,12 | 77,43 |

- Le modèle colle à la machine : 77 % de moyenne et 80-87 % de pic mesurés (notes/23 §6 bis) ; l'agent « sortie » trouve
  78,5 % avec son propre découpage (`optim/sortie/mesures.log`).
- **Code : 1 111 défauts pour 1 113 lignes, même à chaud.** Le code de l'audio ne tient pas dans le cache : chaque
  ligne est chassée avant d'être réutilisée au bloc suivant. Coût : 1 111 × 15 = 16 700 cycles, **10 % d'un bloc**
  `[DÉDUIT]`. L'interface n'y est pour rien (chaud = vidé).
- **Données : la pollution par l'interface coûte jusqu'à 2,6 points** (chaud → vidé ; notes/31 §7 mesure 45,5 → 50,1 %
  avec Model-TG, même ordre).
- Conséquences :
  - **réordonner ou aligner le code ne sert à rien** : c'est un manque de place, pas un conflit d'ensembles ;
    l'alignement des boucles gagnerait au plus une ligne par boucle et par bloc (< 0,1 %) `[DÉDUIT]` ;
  - le verrouillage d'une moitié du cache d'instructions ne garde que 256 lignes sur 1 113 : −1,7 point ;
  - ce qui paie, c'est de **sortir le code chaud de la SDRAM**.

### 4.4 Piste n° 1 : la SRAM réorganisée pour le code d'origine

**Ce qui change** (même mécanisme que notes/28-29, sur le code d'origine) :
1. Les 30 tables d'ondes de CHORD restent en SDRAM (copie dans la charge utile, construite au build depuis le fichier de
   l'utilisateur ; les 31 pointeurs `0x40118594..0x4011860c` réécrits) — déjà fait et prouvé pour les moteurs du
   Syntakt (notes/28 §2-3, CHORD « fonctionne normalement » sur la machine, notes/29 §1).
2. Le code chaud d'origine est recopié dans la place libérée par le crochet de démarrage, relocalisé :
   - 1ʳᵉ zone (22 616 o) : voix `0x400a7d10..0x400ab7c0` (15 024 o) + lissage, rendu et fonction audio
     `0x40058470..0x400597f0` (4 992 o) + LFO `0x400918b0..0x40091d90` (1 248 o) = 21 264 o ;
   - 2ᵉ zone (8 224 o) : étage de sortie `0x40056520..0x400582d0` (7 600 o).
   Les appelants (boucle des voix, table des machines, vecteur du rendu posé par `0x4005153a`, appels du mixeur) sont
   redirigés ; les références relatives au PC qui sortent des blocs déplacés sont recalculées (outillage de relocation
   de notes/17 et `tools/relocate_6ch.py`).

**Gain estimé** — `python3 scripts/cachesim_sram.py trace_play.npz` `[FAIT, sortie du modèle]`, motif à 6 pistes
(6 machines différentes, dont CHORD, qui paie ici ses tables en SDRAM) :

| Scénario | Origine | SRAM hors cache | SRAM par le cache (remplissage 4 cycles) | + états des voix en SRAM |
|---|---|---|---|---|
| chaud | 78,84 % | 70,83 % (−8,0) | 73,49 % (−5,3) | 67,56 % (−11,3) |
| pollué 512 | 81,59 % | 72,82 % (−8,8) | 75,44 % (−6,2) | 69,82 % (−11,8) |
| vidé | 81,44 % | 72,77 % (−8,7) | 75,37 % (−6,1) | 70,05 % (−11,4) |

- Défauts I : 1 111 → 0 à 31. Défauts D : +146 lignes par bloc, les tables de CHORD (512 lectures par bloc), soit
  +1,3 point quand une piste joue CHORD (notes/27 §3.3 estimait +1,2) ; sans CHORD, le gain est plus grand d'autant.
- **5 à 9 points d'un bloc**, tout le temps (l'OS d'origine calcule toutes les pistes et les effets même à l'arrêt,
  notes/23). Avec moins de machines différentes, moins de code de voix : le gain baisse vers 3 points (étage de sortie
  seul) `[DÉDUIT]`.
- **Étalonnage** : le même modèle prédisait −11,5 points pour 5 moteurs du Syntakt passés en SRAM (notes/28 §4) ; la
  machine a donné −8 points avec 4 d'entre eux (76 → 68, notes/29 §1) `[FAIT]`. Le modèle est donc un peu optimiste ;
  d'où la fourchette.
- Effet sur l'interface : son temps libre passe de 23 % à environ 29-32 % du processeur, +30 à +40 % de temps
  `[DÉDUIT]` ; et si l'instruction en SRAM ne passe pas par le cache, tout le cache d'instructions lui reste (§3.3).
- Les états des 6 voix (4 776 o, 190 lignes lues et réécrites par bloc) rapporteraient 3 points de plus, mais il n'y a
  plus de place dans ce plan ; les octets à zéro de la fin des deux zones de départ (2 880 + 2 320 o) sont peut-être
  libres `[HYP : à vérifier qu'aucun code ne les utilise comme BSS]`.

**Son** : identique à l'échantillon près (même code, mêmes données, seules les adresses changent). Preuve en
émulation : comme `test_sram_code.py` et `test_syntakt_machines.py` (notes/29 §3) — sortie des 6 pistes et de l'étage
de sortie comparée échantillon par échantillon entre l'OS d'origine et l'OS modifié, sur tous les motifs de
`seqrig.py` ; vérifier qu'aucune instruction ne s'exécute plus dans les anciennes adresses, que le crochet de démarrage
remplit les deux zones et laisse le reste de la SRAM intact (`boot_hook_ok()`).

**Risque** : moyen.
- Relocation de code d'origine : il faut trouver toutes les références (absolues vers l'intérieur, relatives vers
  l'extérieur, tables de sauts, pointeurs de fonctions) ; une seule oubliée = plantage. L'émulation complète (bloc
  entier) les attrape presque toutes.
- **Incompatible avec les moteurs du Syntakt** (qui occupent ces deux zones, `tools/gov_asm.py:33` `SRAM_BANKS`) :
  `conflicts` à déclarer, ou un répartiteur de SRAM commun plus tard. S'applique à l'OS seul et aux mods sans moteurs
  du Syntakt (tempo, arp, trig-hold, MACRO, ACID… à vérifier un par un).
- Crochet de démarrage partagé (chaîne `boot_extra_hook`, notes/43) ; le bootstrap et l'updater ne changent pas :
  récupération intacte.
- Contention en SRAM entre le code et les données de l'audio : inconnue (notes/28) ; la v7 n'a rien montré de
  gênant.

**Effort** : élevé (un générateur `gen_sram_stock.py` qui extrait au build les 4 blocs du fichier de l'utilisateur,
relocation, crochet, preuve). Une première étape plus simple : **l'étage de sortie seul** (un bloc contigu de 7 600 o
dans la 2ᵉ zone, ~3 points, aussi à l'arrêt) — piste n° 3 du tableau.

### 4.5 Autres pistes de cache

- **Verrouiller une moitié du cache** (IHLCK / DHLCK) sur les lignes de l'audio qui manquent le plus (2 par ensemble) :
  −1,7 point (I), −0,7 à −2,5 (D), −2,4 à −4,2 (les deux) au modèle (§4.3). Mais l'interface n'a plus que 4 Ko de
  chaque cache, et la façon de remplir la moitié verrouillée (invalider, toucher les lignes voulues, poser le bit) est
  `[HYP]` (manuel non lu). Son identique. Gain bien plus faible que la piste 1, et en partie redondant avec elle.
  À essayer seulement avec le firmware de mesure (§6), en regardant aussi la fluidité de l'interface.
- **Données de l'audio en SRAM** : les états des voix (ci-dessus) ; le reste est déjà en SRAM.
- **ACR1 non caché pour le delay et la reverb** : abandonné — leurs lignes passent par le DMA (ch30, ch42) vers la SRAM,
  pas par le cache (agent « sortie ») ; il ne resterait que les 64 écritures de l'anneau du codec.
- **`stop #0x2000` dans la boucle d'attente** : aucun gain de calcul (elle ne tourne que quand tout dort), peut-être
  un peu moins de chaleur `[HYP]`. Non recommandé ; la boucle sert mieux au compteur du §6.

### 4.6 Ce qui se vérifie en émulation, ce qui demande la machine

| Vérifiable en émulation | Demande la machine |
|---|---|
| le son identique à l'échantillon près, après relocation | le vrai coût d'une ligne relue en SDRAM (le « 15 cycles ») et le vrai CPI |
| les instructions, les lignes de code et de données touchées | si le code en SRAM passe par le cache d'instructions (RAMBAR SC/UC) et à quelle vitesse |
| qu'aucune instruction ne tourne aux anciennes adresses | la contention en SRAM entre code et données, et avec le DMA |
| les adresses écrites par un prototype (rien d'autre que son compteur) | la durée réelle du DMA ch30 (l'émulation le rend instantané) |
| le comportement du séquenceur et des événements | la vitesse maximale de l'écran, la fluidité de l'interface, l'effet du verrou de cache |

## 5. Le séquenceur

**Mesures** (`python3 scripts/seqcost.py sec3.bin` : corps de l'interruption de rendu `0x40058ca0 → 0x40059382`,
jusqu'au `jsr` de la fonction audio) `[FAIT, émulation]` :

| Cas | Instructions | Cache chaud | Cache froid |
|---|---|---|---|
| aucun événement (arrêt, ou pas sans trig) | 406 | 0,38 % | 1,20 % |
| 1 trig, sans p-lock | 758 | 0,70 % | 2,53 % |
| 6 trigs dans le même bloc | 2 248 | 2,08 % | 4,35 % |
| 1 trig, 10 p-locks | 1 001 | 0,92 % | 2,81 % |
| 6 trigs dans le même bloc, 10 p-locks chacun | 3 706 | 3,42 % | 5,95 % |

- La construction des événements d'un trig se fait **avant**, hors du rendu, dans le tic du séquenceur (vecteur 121,
  niveau 2) : 630 à 690 instructions par trig. Le bloc qui suit le trig revient à 416-466 instructions.
- **D'où vient le pire cas** (`python3 scripts/seqprof.py sec3.bin`, 6 trigs × 10 p-locks, 3 868 instructions) :
  `0x400583da` (applique les paramètres d'un événement, ~27 instructions par entrée) **1 794 (46 %)** ; corps de
  l'interruption 1 084 ; `0x40058308` 222 ; `0x400585a8` 162 ; le reste < 110 chacun. Il croît donc avec le nombre de
  trigs × p-locks du même bloc, et le cache froid double presque son prix (code et données du séquenceur chassés par
  l'audio, §4.3).
- Moyenne : environ 1 % d'un bloc à 120 BPM (un pas toutes les 125 ms = 1 bloc sur 188 porte un trig) ; pire bloc :
  3,4 à 6 %.
- **Peut-on l'étaler ?** Pas sans changer le son : chaque événement doit être appliqué au bloc où il tombe (et à sa
  place dans le bloc). En revanche :
  - **préparer les p-locks hors du rendu** : `0x400583da` recopie chaque valeur dans les cibles du lissage
    (`0x800015a0..`) ; le tic du séquenceur (niveau 2, hors rendu) pourrait préparer le vecteur complet des
    paramètres, et le rendu n'aurait plus qu'à le désigner. Gain : 1 à 2,5 points **sur le bloc du trig seulement**
    (0 en moyenne) ; mais c'est ce bloc qui fait les pics, et un bloc isolé au-dessus de 90 % fait couper le régulateur
    (notes/29 §4) : plus de stabilité les jours où 6 notes partent ensemble. Son identique à prouver (mêmes valeurs au
    même bloc, sortie identique échantillon par échantillon sur des motifs avec p-locks) ; risque moyen ; effort élevé
    (sémantique de `0x400583da` à décoder) ;
  - le code du séquenceur (interruption, `0x400583da`) est déjà dans la région « lissage et rendu » de la piste 1 : la
    piste 1 lui enlève l'essentiel de son surcoût à froid.
- Le gros du pic du trig n'est pas le séquenceur mais les voix qui démarrent leurs notes (notes/25 : « 6 notes lourdes
  sur le même pas : 1ᵉʳ bloc > 100 % ») : domaine de l'agent « voix ».

## 6. Le firmware de mesure

Aucune de ces durées n'est dans l'émulation (pas d'horloge réelle) : il faut les relever sur la machine. Le minuteur
DMA 0 (`0xfc07000c`, 135,168 MHz, compteur libre) sert de chronomètre ; l'affichage reprendrait celui du compteur de
charge des firmwares de diagnostic (nom de la machine, toutes les 750 blocs, notes/23 et 28 §5).

### 6.1 Compteur de temps libre — prototype prouvé en émulation `[FAIT]`

- `proto/idle.S` (44 o) : remplace les 6 octets `4fef 0018 60fe` (`lea %sp@(24),%sp ; bras .`) en `0x4000543a` par
  `jmp idle`. La boucle relit le minuteur et **cumule les écarts courts** (< 128 cycles de bus, ≈ 0,95 µs) dans un
  compteur ; un écart long veut dire que la tâche a été interrompue (interruption ou autre tâche) : non compté. Les
  registres d0-d2 sont sauvés par le changement de contexte (`0x4000041e`).
- `python3 proto/idle_proto.py sec3.bin idle.bin` : vrai code de l'OS jusqu'au saut, minuteur modélisé, vols de temps
  qui imitent la machine (blocs audio à 1 500/s, panneau à 12 000/s, USB à 8 000/s, images de l'interface à 30/s) :

| Charge audio, interface | Temps libre vrai | Compté | Écart |
|---|---|---|---|
| 77 %, 5 % | 20,64 % | 20,65 % | +0,01 point |
| 50 %, 10 % | 48,35 % | 48,43 % | +0,08 |
| 90 %, 2 % | 8,13 % | 8,11 % | −0,02 |
| 0 %, 0 % | 97,69 % | 97,97 % | +0,28 (interruptions de moins de 128 cycles comptées comme libres) |

  Écritures hors du compteur : aucune ; instructions hors de la boucle : aucune.
- Pour le vrai firmware : le code va dans un masque libre de `REGISTRY.md` (ici `0x40152d38`, pour l'émulation
  seulement ; il faut rediriger son sprite) et le compteur en BSS libre ; le seuil de 128 cycles doit rester au-dessus
  d'un tour de boucle sur la machine (une lecture de registre lente + 7 instructions) `[HYP]`.

### 6.2 Sondes

Chaque sonde : lire `0xfc07000c` à l'entrée et à la sortie, cumuler durée, nombre et maximum en BSS. Détour par un
`jmp` vers un stub, comme les autres mods.

| Sonde | Où | Ce qu'elle dit |
|---|---|---|
| temps libre | `0x4000543a` (§6.1) | où va le temps quand l'audio en prend 77 % |
| image de l'interface | entrée et sortie de `0x400075da` | images/s, ms par image (dessin + envoi) |
| envoi à l'écran | `0x4008e622` | ms par image, blocs envoyés ; vérifie le §3.4 |
| attente du DMA du delay | boucle `0x4005697e` | durée réelle (piste 7) |
| panneau, USB | `0x40059cd0`/`0x40059d2c`/`0x40059db8`, `0x40004318` | durée vraie des interruptions de niveau 6 |
| flash | `0x400901e0`, `0x40090242`, `0x4008fc32` | durée des effacements, et quelle tâche (`0x422fef30`) |

### 6.3 Petits bancs au démarrage (une fois, résultat affiché ensuite)

Pour étalonner le modèle dont dépendent tous les chiffres de cette étude :
- lecture de 64 Ko de SDRAM par pas de 16 o, cache invalidé : le vrai prix d'une ligne (le « 15 cycles ») ;
- une boucle connue : le vrai CPI et la fréquence du cœur (250 ou 270 MHz) ;
- 4 Ko de code en ligne droite copiés en SRAM, exécutés deux fois de suite : si le 2ᵉ passage est plus rapide, le code
  en SRAM passe par le cache d'instructions (RAMBAR SC/UC, §4.1) ; comparé au même code en SDRAM.

Le firmware de mesure ne change pas le son (preuve : sortie identique échantillon par échantillon, comme
`test_meter.py`) ; c'est un firmware de diagnostic construit à part, pas une carte du flasher.

## 7. Limites

- Le manuel de référence du MCF5441x n'a pas pu être lu (accès réseau refusé) : les sources d'interruption sont déduites
  du code, la disposition des bits de RAMBAR vient des autres ColdFire.
- Le modèle de coût est celui des notes, étalonné sur quelques mesures ; ses chiffres absolus sont des ordres de
  grandeur. Les classements entre pistes sont plus sûrs que les points eux-mêmes.
- La trace est un seul motif (6 pistes, 6 machines, sons par défaut, sans p-lock, sans USB) ; l'interface n'est pas
  émulée (sa pollution est simulée par des lignes au hasard).
- Le dessin des vues de l'interface, les rappels de données de l'USB, les tâches dont le rôle est marqué « ? » n'ont pas
  été mesurés.
- Rien n'a été construit pour la machine ; aucun résultat matériel n'est revendiqué ici.
- Piège d'Unicorn 2.1.4 signalé par l'agent « voix » : un crochet de lecture posé après la traduction d'un code ne voit
  pas ses lectures tant qu'on ne vide pas le cache de traduction (`uc.ctl_flush_tb()`). Vérifié ici : la trace refaite
  avec vidage (`scripts/trace_flush.py`, `trace_play_flush.npz`) donne 27 accès de plus sur 22 700 par bloc, et les mêmes
  chiffres de cache à 0,01 point près ; `scripts/seqcost_flush.py` redonne exactement le tableau du §5. Les autres bancs
  posent leurs crochets avant toute émulation. Les 686 lignes de code de la fonction audio sans mixeur trouvées par
  « voix » (`optim/voix/rapport.md` §2.4) recoupent les 597 + 50 + 40 = 687 lignes du §4.2.

## 8. Fichiers de ce dossier

- `rapport.md` (ce fichier)
- `dis.sh`, `sec3.dis`, `sec2.dis`, `render.dis`
- `scripts/isrrig.py`, `scripts/seqcost.py`, `scripts/seqcost_flush.py`, `scripts/seqprof.py`, `scripts/trace.py`,
  `scripts/trace_flush.py`, `scripts/cachesim.py`,
  `scripts/cachesim_sram.py`, `scripts/regions.py`, `scripts/screencost.py`, `scripts/usbcost.py`, `scripts/polls.py`
- `trace_play.npz`, `trace_play_flush.npz`
- `proto/idle.S`, `proto/idle.bin`, `proto/idle_proto.py`
