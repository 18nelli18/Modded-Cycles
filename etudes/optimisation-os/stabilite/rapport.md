# Stabilité de l'OS 1.13 et de la machine moddée : ce qui peut planter, geler, craquer ou corrompre

Travail du 17/10/2026, en lecture seule sur le dépôt (aucun fichier suivi modifié, rien de commité ni de publié).
Tout est fait sur le MAIN OS 1.13 officiel (`firmware/model-cycles_OS1.13.syx`), désassemblé (VA 0x40000400) et
exécuté dans Unicorn. Aucun résultat sur la machine : les essais matériels restent ceux de Maxime.

Étiquettes : **[FAIT]** vérifié (adresse et instruction, fichier:ligne, commande et sortie) ; **[DÉDUIT]** calculé à
partir de faits ; **[HYP]** plausible, non vérifié.

Fichiers de travail (dans `/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/stabilite/`) :

| Script | Ce qu'il prouve | Commande | Résultat |
|---|---|---|---|
| `preuve_machines.py` | gel de MACHINES avec une machine inconnue, et le correctif de 4 octets (OS d'origine) ou 6 octets (Model-TG) | `python3 preuve_machines.py` puis `python3 preuve_machines.py --tg` | `TOUT OK` (2 s chacun) |
| `preuve_midi_horloge.py` | blocage à IPL 7 de l'horloge MIDI sortante quand l'anneau d'octets est plein, et le correctif de 2 octets | `python3 preuve_midi_horloge.py` | `TOUT OK` |
| `preuve_surcharge.py` | ce que deviennent l'audio USB et l'heure musicale quand un bloc dépasse 100 % (vrai pilote USB de l'OS) | `python3 preuve_surcharge.py` | tableau du §3.3 |
| `mesure_pile.py` | profondeur de pile de la boucle des voix (origine, MACRO, ACID) | `python3 mesure_pile.py` | §5.3 |

Ils réutilisent les bancs du dépôt (`tools/emu/test_sdvintage_7th.py`, `test_syntakt_machines.py`, `test_usb_in.py`,
`mcengine.py`) sans les modifier. Le désassemblage complet de la section 3 (`dis.sh`, puis `os.dis`) et celui des sections 2 et 4
(`disimg.sh`) se refont à la demande. Ils ont été effacés après usage, pour ne pas garder de copie des fichiers
officiels.

---

## 0. En bref

| # | Défaut | Classe | Gravité | Correctif proposé | Prouvé en émulation |
|---|---|---|---|---|---|
| D1 | **MACHINES gèle** quand une piste a une machine que le firmware n'a pas (projet fait avec MACRO, ACID, moteurs du Syntakt…, rouvert sur l'OS officiel ou sur Model-TG seul) | bug de l'OS d'origine, recopié dans Model-TG ; déclenché par les données des mods | **haute** (gel, extinction obligatoire, constaté par Maxime le 12/10) | 2 × `moveq #-1` → `moveq #6` (4 octets) ; 3 de plus dans la copie de Model-TG | **oui**, correctif compris (`preuve_machines.py`) |
| D2 | **Gel complet** (son compris) si l'horloge MIDI sortante trouve l'anneau d'octets plein : attente active à IPL 7 que seul le niveau 4 peut vider | bug de l'OS d'origine, atteint après une surcharge longue | moyenne (il faut ≥ 1024 tops sans service du niveau 4 ; 4,7 s à 546 BPM, 21 s à 120 BPM) | `bgt.s` de l'attente → sortie (2 octets, 0x40001246) | **oui**, correctif compris (`preuve_midi_horloge.py`) |
| D3 | Un bloc qui dépasse 100 % : rendu perdu sans trace, heure musicale et USB en retard d'un bloc pour toujours ; avec `6ch-usbup`, **un seul bloc en retard laisse la file USB hors de son anneau** : flux 6 canaux abîmé jusqu'au redémarrage du flux | surcharge (OS d'origine : rien ne détecte ni ne rattrape) ; aggravé par `6ch-usbup` | moyenne (craquements USB persistants avec 6 canaux) | compteur de dépassements + rattrapage ; régulateur de file dans `feed.S` | simulé sur le vrai pilote (`preuve_surcharge.py`) ; correctif non prototypé |
| D4 | Piles des tâches : les interruptions s'empilent sur la pile de la tâche en cours ; la plus petite fait 2 Kio, avec son TCB et les globales du noyau **juste en dessous** | conception de l'OS ; risque pour les mods qui ajoutent du code profond dans le rendu | faible à moyenne [HYP] | budget de pile vérifié en émulation pour chaque mod ; diagnostic de hautes eaux | mesure partielle (`mesure_pile.py`) |
| D5 | Carte eMMC/SD : erreurs CRC de commande, bit de fin, DMA, auto-CMD12 ni activées ni traitées ; attentes sans délai | OS d'origine | faible (mémoire interne) [HYP] | délais aux attentes (gros travail) | lecture du code seulement |
| D6 | Pas de chien de garde : aucun accès à CWCR/CWSR dans le bootstrap, l'OS ni l'updater | OS d'origine | information : tout gel demande d'éteindre, et l'extinction forcée perd l'état non sauvegardé | aucun conseillé (§5.1) | lecture du code |
| D7 | Anneau de réception MIDI de 32 Kio : un tour complet de retard ne se voit pas | OS d'origine | faible (≥ 10,5 s de surcharge continue avec un flux MIDI dense) | — | lecture du code |
| D8 | Ce que `check_overlaps.py` et `registry.py` ne voient pas : RAM de travail, pile, ordre des crochets de démarrage, cache d'instructions, fichiers d'un build relus par un autre | outillage des mods | moyenne (D1 est de cette famille) | contrôles proposés au §6 | — |

Les deux correctifs prouvés (D1, D2) ne changent ni le son ni la charge. Ce sont des octets que les tweaks existants
n'écrivent pas (contrôlé sur les 282 fichiers de `tweaks/model-cycles_OS1.13/`).

---

## 1. Ce qui était déjà connu, classé

| Défaut connu | Source | Classe |
|---|---|---|
| MACHINES gèle sur un projet qui a une piste sur une machine ajoutée, **même sur l'OS officiel** ; le son continue | mémoire d'équipe `added-machine-project-freeze` (12/10, essais Chord Keys v2 de Maxime) ; mécanisme décrit dans notes/18 l.202-205 | **OS d'origine** (borne absente) déclenché par les mods → D1 |
| notes/18 l.174 : « Projet ou preset avec SDVtg relu sur l'OS officiel : […] aucun plantage attendu » | notes/18 l.174 | **erreur de la note** : contredite par la même note (l.204, « → gel »), par l'émulation (D1) et par le constat de Maxime |
| Correctif déjà fait, mais seulement dans les détours générés (`detours_asm()`, machine ou enregistrement hors limites → KICK) | notes/20 §5 l.153-155 | mods : MACRO, ACID, moteurs du Syntakt sont protégés ; **Model-TG seul, `sdvintage-7th`, `syntakt-vintage` et l'OS officiel ne le sont pas** (§4.3) |
| L'état n'est sauvegardé qu'à l'extinction par le bouton | dossier-technique §7.1 l.426-433 (Ess : « a limitation of the hardware ») | OS d'origine, limite matérielle |
| Le mode MUTE reste verrouillé après FUNC + une touche qui ouvre une boîte de dialogue | dossier-technique l.443 | OS d'origine (interface), sans effet sur la stabilité |
| Craquements et interface ralentie quand trop de voix sonnent | notes/25 §1 (mixage ≈ 30 %, voix d'origine ≈ 8 %, voix du Syntakt ≈ 15 % d'un bloc) ; notes/30, 36 | **surcharge** ; le régulateur n'existe qu'avec les moteurs du Syntakt (notes/35 §8) |
| Glitches de l'audio USB avec Model-TG en 6 canaux (« après 15-20 minutes ») | notes/35 §2 | **mod** (anneau 6 canaux trop petit, corrigé) + charge qui varie |
| MACRO + moteurs du Syntakt bloqués au logo sur la machine (cache d'instructions laissé allumé par le bootstrap) | mémoire `icache-boot-code` ; notes/50 §8 | **mod** (corrigé : invalidation avant d'exécuter le code recopié) |
| Relais THRU + MIDI du Cycles : octets mêlés au milieu des messages | notes/53 §7 | **mod** (limite de conception, dite aux utilisateurs) |
| L'essai « BTH à 3 états » du fork d'AveyCole gelait la machine (non importé) | mémoire `aveycole-midi-thru` | mod |
| Chord Keys v2 et `lfo-plus` écrivent les mêmes octets 0x4005b9c6..cd | mémoire `chord-keys-pr` | conflit de mods, **vu** par `check_overlaps.py` |
| Une mise à jour USB n'est vérifiée qu'une fois, par l'OS qui tourne ; le bootstrap démarre le conteneur 0x20000 sans contrôle | mémoire `usb-update-single-check` ; notes/41 §1 | conception : un OS qui plante au démarrage ne se répare que par le STARTUP MENU (MIDI IN), qui reste intact puisque seule la section 3 est touchée (règle 6) |

---

## 2. Carte des interruptions (ce qui protège quoi)

VBR = 0x40000000. Les 256 vecteurs sont d'abord mis à 0x40001976 (`main` 0x400cefa0). Le gestionnaire par défaut
monte à IPL 7, appelle le crochet `*0x4049fd64` (= l'écran de plantage 0x40078ce2, installé par 0x40078e84 :
« EXCEPTION V%02x-M%x-P%08x » et la pile) puis `halt` (0x40078e00) **[FAIT]**.

Le noyau change de tâche en 0x40000410 : il sauve d0-sp dans le TCB `*0x422fef30+12`. Il n'y a qu'un A7 et pas de
pile d'interruption à part : **les interruptions s'empilent sur la pile de la tâche interrompue** **[FAIT]**.

| Interruption | Source | Niveau | Gestionnaire | Rôle |
|---|---|---|---|---|
| DMA audio | eDMA 50 (INTC1, ICR 0xfc04c06a) | 6 | 0x400589c0 | `addql #1,0x40a78e08` (compteur de blocs), `0x40a78e04` = minuteur DMA 0, `0x40a78e0c = 1`, efface l'IRQ (`0xfc04401c = 50`), force le rendu (`orl #0x80000000,0xfc04c010`) **[FAIT 0x400589d4..0x400589fe]** |
| USB | INTC2 src 17 (ICR 0xfc050051) | 6 | — | |
| Rendu audio | src 63 forcée (ICR 0xfc04c07f) | 5 | 0x40058c5e | efface son bit de forçage dès l'entrée (`andl #0x7fffffff,0xfc04c010`, 0x40058c6c) ; choisit la moitié à écrire d'après le SADDR du DMA (`cmpil #0x4a3ed180`, 0x40058c78) ; écrit cette moitié **à la fin** (0x400567ba, 0x40059864..72) ; envoie 32 trames à l'USB (0x40002912, 0x40059392) ; heure musicale `0x8000184c += 2 × tempo` (0x400593ec..) **[FAIT]** |
| Top d'horloge MIDI | INTC0 src 44 | 5 (corps à IPL 7) | 0x4005420c | envoie 0xF8 (0x40082512), puis force src 57 **[FAIT]** |
| Pas du séquenceur | src 57 (ICR 0xfc048079) | 2 | 0x40054c1e | `0x40a78628 += 900000` (un tic, **sans rattrapage**), message de type 5 vers le rendu (abandonné si le pool est vide : `jsr 0x40091eb6 ; tstl d0 ; beqs`, 0x40054c6a..72) **[FAIT]** |
| Réception MIDI | eDMA 36 (INTC1 src 28) | 4, descend à 3 | 0x40001094 | vide l'anneau DMA de 32 Kio par l'analyseur `*0x4049dce0` (et le relais THRU, notes/53 §7) |
| Fin de DMA MIDI | eDMA 37 | 4 | 0x40001000 | |
| Émission UART9 | INTC1 src 53 (ICR 0xfc04c075) | 4 | 0x40000e8c | vide l'anneau d'octets de 1 Kio |

Dans le code audio, on ne trouve que des « sauver SR, monter à 7, remettre SR » : le rendu ne se ré-entre jamais
**[FAIT]**.

---

## 3. Un bloc qui dépasse 100 %

### 3.1 Réponses aux questions

- **Le DMA (6) et le rendu (5) peuvent-ils s'empiler ?** Le DMA interrompt le rendu : une seule couche, car le niveau 6
  masque le 6. Il ne fait que poser des drapeaux. Le rendu, lui, ne peut pas s'interrompre lui-même : le niveau 5 est
  masqué pendant qu'il tourne, et son unique bit de forçage est effacé à l'entrée. Il y a donc **au plus un rendu en
  attente**. Si deux interruptions DMA tombent pendant un même rendu, **un rendu est perdu sans trace**. Pas
  d'empilement de rendus, donc pas de croissance de pile due à la surcharge **[FAIT pour le code, DÉDUIT pour la règle]**.
- **L'anneau DMA de 64 trames peut-il être relu pendant qu'on l'écrit ?** Oui. La moitié est choisie à l'entrée et
  écrite à la fin. Un rendu qui finit après la bascule suivante écrit une moitié que le DMA a déjà commencé à lire
  (anciennes trames, puis nouvelles) : un **craquement sur les jacks**. Le rendu suivant rechoisit la moitié d'après
  SADDR, donc l'anneau **se recale tout seul** : pas de décalage durable **[FAIT pour le choix, DÉDUIT pour l'effet]**.
- **La pile peut-elle déborder ?** Pas à cause d'un dépassement : il n'y a pas d'empilement. Le pire cas est fixe : une
  tâche, puis le niveau 2, puis 3 (réception MIDI), puis 5 (rendu), puis 6, tous sur la pile de la tâche (§5.3)
  **[DÉDUIT]**.
- **L'heure musicale et l'USB perdent-ils la synchro ?** Oui, d'un bloc par rendu perdu, définitivement.
  - L'avance de l'heure musicale (2 × tempo) et l'envoi USB de 32 trames se font une fois par rendu, pas une fois par
    bloc **[FAIT 0x40059392, 0x400593ec]**.
  - Un rendu perdu met donc le séquenceur 0,667 ms en retard sur l'horloge audio, et la file USB 32 trames plus bas.
    Rien ne rattrape : le compteur de blocs `0x40a78e08` n'est lu que par l'ISR SOF de l'USB (0x40004338) **[FAIT]**.
  - Le drapeau `0x40a78e0c`, posé par le DMA et effacé par le rendu (0x400593dc), **n'est lu nulle part** : c'est un
    détecteur de dépassement que l'OS n'utilise pas **[FAIT : 2 références seulement]**.
- **Quand la charge reste au-dessus de 100 %**, les niveaux 4, 3, 2 et 0 ne passent plus.
  - Le pas du séquenceur (niveau 2, un seul bit de forçage) perd des tics, alors que l'horloge MIDI sortante (niveau 5)
    continue : le séquenceur prend du retard sur sa propre horloge **[DÉDUIT]**.
  - L'interface (tâches) s'arrête.

### 3.2 Ce qui protège, ce qui manque

| Protège **[FAIT]** | Manque |
|---|---|
| un seul rendu à la fois (niveau 5 masqué, bit effacé à l'entrée) | aucune détection de dépassement (`0x40a78e0c` jamais lu) |
| moitié de l'anneau rechoisie à chaque rendu d'après SADDR | aucun rattrapage de l'heure musicale ni des trames USB pour les rendus perdus |
| message séquenceur → rendu abandonné si le pool est vide (0x40054c70) | les tics perdus du séquenceur ne se rattrapent pas (`+= 900000` par passage) |
| le régulateur de charge (notes/25, 30, 36) **dans les builds avec moteurs du Syntakt** | rien pour Model-TG seul, MACRO, ACID (notes/35 §8 : « La surcharge pure […] reste possible avec Model-TG seul ») |

### 3.3 Simulation : la file USB après une rafale (vrai pilote USB, `preuve_surcharge.py`)

Méthode. Le banc de `tools/emu/test_usb_in.py` (vrai pilote USB de l'OS dans Unicorn, contrôleur et horloges
modélisés, +30 ppm), avec l'ordonnancement du §3.1 :
- un rendu dure autant que la charge du bloc ;
- deux interruptions DMA pendant un rendu → un rendu perdu ;
- « en retard » = le rendu finit après l'interruption DMA suivante ;
- charge de base 74-80 %, une rafale à 1,0 s, 5 s par passage.

La file est comptée en cases de l'anneau : 16 cases en stéréo d'origine, 9 avec `6ch-usbup`. Au-delà de l'anneau, des
cases encore en file sont réécrites : des trames sautées ou en double.

Sortie de `python3 preuve_surcharge.py`, mise en tableau (5 s par passage). Colonnes :
- « file » : avant la rafale → à la fin (2,5..5 s) ;
- « trous » : micro-trames vides entre 1,0 et 2,5 s ; il n'y en a aucune à la fin, dans tous les cas ;
- dernier nombre : trames sautées ou doublées sur tout le passage.

| Rafale | Rendus perdus | Blocs en retard | OS d'origine (stéréo, 16 cases) | `6ch-usbup` (9 cases) |
|---|---|---|---|---|
| 1 bloc à 110 % | 0 | 1 | file 6..11 → 5..11, 0 trou, 0 | file 1..6 → **5..10**, 4 trous, **12 002** |
| 1 bloc à 160 % | 0 | 3 | 6..11 → 5..11, 0 trou, 0 | 1..6 → 7..12, 6 trous, 12 009 |
| 3 blocs à 125 % | 0 | 6 | 6..11 → 5..11, 0 trou, 0 | 1..6 → 9..14, 8 trous, 22 |
| 6 blocs à 120 % | 1 | 6 | 6..11 → **2..8**, 2 trous, 0 | 1..6 → 7..12, 11 trous, 12 002 |
| 12 blocs à 110 % | 1 | 12 | 6..11 → 2..8, 2 trous, 0 | 1..6 → 7..12, 11 trous, 11 990 |
| 30 blocs à 106 % | 1 | 33 | 6..11 → 5..11, 5 trous, 0 | 1..6 → 10..15, 14 trous, 22 |
| 60 blocs à 106 % | 3 | 62 | 6..11 → 3..9, 14 trous, 0 | 1..6 → 8..13, 23 trous, 6 664 |

Le banc vérifie aussi ses points d'accroche :
- `ok OS d'origine : 0x40059382 calcule le bloc (jsr 0x4005979e), puis 0x40059392 l'envoie à l'USB (jsr 0x40002912)` ;
- `ok début de l'interruption de rendu : movel #32,%macsr en 0x40058ca0 (remplacé par l'appel de feed_isr)`.

Le nombre de trames abîmées varie beaucoup d'un cas à l'autre (22 ou 12 002). Il dépend de la position où la file se
pose par rapport à l'anneau.

Lecture **[DÉDUIT, simulation]** :
- **OS d'origine** : la file absorbe. On voit des trous pendant la rafale, puis la file reste plus bas après un rendu
  perdu, sans revenir.
- **`6ch-usbup`** : un seul bloc en retard (sans même un rendu perdu) peut laisser la file au-dessus de ses 9 cases
  pour toujours. Les cases en file sont alors réécrites, et le flux 6 canaux reste abîmé jusqu'à ce que le DAW relance
  le flux.

Réserve : l'ordonnancement est un modèle (rendu de durée fixe, pas de gigue d'interruption). notes/35 §7 rapporte des
essais 6 canaux réussis sur la machine, donc à confirmer par Maxime (§7, essai E3).

### 3.4 Interface affamée longtemps : les files débordent-elles ?

- **Réception MIDI** : un DMA remplit un anneau matériel de 32 Kio (0x4a3d8000, DMOD = 15), avec une interruption par
  octet. « Vide » se teste par `DADDR == index de lecture 0x4049dcd0` : un tour complet de retard ne se voit pas
  **[FAIT]**. À 3 125 o/s, il faut **10,5 s sans service du niveau 3** **[DÉDUIT]**. C'est impossible hors surcharge
  continue. Après un tour, l'analyseur lirait un mélange : notes collées, CC au hasard. Gravité faible.
- **Émission MIDI, messages** : l'anneau DMA de 4 Kio (0x4a3e1000). `0x40001100` attend activement qu'il y ait de la
  place, au niveau de l'appelant (0x40001116..0x4000114c) **[FAIT]**. Les appelants trouvés sont des tâches ou le niveau
  2. Le niveau 4 peut donc vider l'anneau, et l'attente finit **[HYP : tous les appelants n'ont pas été suivis]**. Avec
  `midi-both`, une SysEx relayée à plein débit prend toute la ligne (l'anneau d'octets passe d'abord, notes/53 §7) :
  l'attente peut durer le temps du relais, avec l'interface figée pendant ce temps **[HYP]**.
- **Émission MIDI, octets** : l'anneau de 1 Kio. Il ne déborde pas : il **bloque à IPL 7**, c'est le défaut D2 (§5.2).
- **USB-MIDI, émission** : 8 cases de 4 o (`0x404a098c & 31`, tampon 0x4a3e5000), sans attente. Une case pleine est
  réécrite **[FAIT 0x40003320..0x4000333c]**. Elle ne bloque jamais, mais perd des messages en rafale.
- **Messages séquenceur → rendu** : abandonnés si le pool est vide (§2) **[FAIT]**.
- **Non étudiés** : la file des événements de touches et de potards, la réception USB-MIDI, l'accumulation d'une SysEx
  reçue **[HYP]**.

---

## 4. MACHINES gèle avec un projet qui a une machine inconnue (D1)

### 4.1 L'endroit exact **[FAIT]**

Les 7 enregistrements de 76 o à `0x40a71540` sont construits au démarrage (0x400e0fc6..). L'enregistrement 0 est
« NONE », les enregistrements 1..6 sont KICK..CHORD. Deux accesseurs n'ont pas la bonne borne :

```
0x4004df5c  moveq #6,d1 ; move.l 4(sp),d0 ; cmp.l d0,d1 ; bcc.s 0x4004df68
0x4004df66  moveq #-1,d0                 <- n hors 0..6 : -1
0x4004df68  moveq #76,d1 ; muls.l d1,d0 ; addi.l #0x40a71540,d0 ; rts     -> 0x40a714f4, 76 o AVANT le tableau
0x4004df76  moveq #5,d1 ; … ; bcc.s 0x4004df90 (table 0x401091b4 : 01..06)
0x4004df80  moveq #-1,d0                 <- m hors 0..5 : même adresse
```

Qui le lit :
- L'ouverture de MACHINES : la lambda 0x400a2404 appelle 0x400148dc(piste) pour les 6 pistes. Celle-ci passe par le
  getter 0x40014042 (11 appelants) et copie les deux chaînes C++ de l'« enregistrement ». Ce sont des octets du BSS qui
  précèdent le tableau, copiés par le constructeur de copie 0x400f8f02, qui incrémente un compteur de références au
  hasard : c'est le gel décrit par notes/18 l.204.
- Les potards de l'écran principal : 0x4001e814 lit `vec[m]` (this+104, 6 entrées) **sans borne**, puis 0x4004df5c.
- Les 3 appelants de 0x4004df76 (0x4002628e, 0x4002ae90, 0x4002b0d4).

La boucle des voix, elle, est bornée (machine < 0 → 0, > 5 → 5) : **la piste joue CHORD, seule l'interface casse**.
C'est le constat de Maxime : le son continue.

Ce que fait le matériel avec le vrai BSS est **[HYP]**. En émulation, avec 76 o empoisonnés devant le tableau, la
lecture faute dans 0x400f8f02 ; la session du 12/10 avait vu une lecture à 0xfffffffc au même endroit. Une exception
irait à l'écran de plantage (§2) et couperait le son, or le son continue : plutôt une boucle ou un verrou sur des
données au hasard dans la tâche de l'interface.

### 4.2 Le correctif minimal et sa preuve **[FAIT]**

| Octets | Avant | Après | Effet |
|---|---|---|---|
| 0x4004df66 | `70ff` | `7006` | n hors 0..6 → l'enregistrement de CHORD |
| 0x4004df80 | `70ff` | `7006` | m hors 0..5 (et entrée > 6 de la table) → CHORD |
| Model-TG : 0x401bf7e2, 0x401bf806, 0x401bf81c | `70ff` | `7006` | mêmes trois sorties dans sa copie (record_at 0x401bf7ce, record_of 0x401bf7f2) |

Pourquoi CHORD : c'est ce que **joue** la boucle des voix pour une machine > 5. L'écran et les potards montrent alors la
machine qu'on entend. Les détours du Syntakt ramènent à KICK (notes/20 §5), mais leur boucle des voix est aussi
détournée. La règle à tenir partout : l'interface montre ce que le moteur joue.

Sortie de `python3 preuve_machines.py` (OS d'origine) :

```
  ok    accesseurs 0x4004df5c (0..6) et 0x4004df76 (0..5) identiques au stock
  ok    stock : hors limites -> 0x40a714f4, 76 o AVANT le tableau (le défaut)
  ok    corrigé : hors limites -> enregistrement de CHORD
  ok    0x400148dc, machines 0..5 : résultats identiques au stock, aucun accès faux
        machine    6 : stock 1 lecture(s) empoisonnée(s) + Invalid memory read (UC_ERR_READ_UNMAPPED) ; corrigé 0, 5 paramètres = CHORD
  (idem machines 7, 9, 100, -3)
  ok    potards (0x4001e814), machines 0..5 : identiques au stock
  ok    potards, machine hors limites : corrigé -> descripteurs de CHORD, aucun accès faux
  ok    stock : molette + vrai changement de machine (0x40014072) depuis 9 -> 5, aucun accès faux
  ok    corrigé : molette + vrai changement de machine (0x40014072) depuis 9 -> 5, aucun accès faux
TOUT OK
```

`python3 preuve_machines.py --tg` donne la même chose sur Model-TG : machines 0..6 identiques, 7, 8, 9, 100 et -3 →
CHORD, molette → 6. `TOUT OK`.

Le banc reprend `test_sdvintage_7th.UI` et l'empoisonnement de `test_syntakt_machines.py` (19 longs pointant vers une
zone non mappée devant le tableau). Il ajoute un tas factice sur `operator new` 0x400802e0. La molette et le
changement de machine (0x400a2712, 0x40014072) ne sont pas le défaut : ils lisent la nouvelle machine et ramènent à la
dernière.

- **Son** : identique. Les machines 0..5 donnent les mêmes appels et les mêmes résultats ; la boucle des voix n'est pas
  touchée.
- **Charge** : nulle. Un `moveq` remplace un `moveq`, sur un chemin qui ne sert que hors limites.
- **Conflits** : aucun. Les détours existants écrivent 0x4004df5c..61 et 0x4004df76..7b ; nos octets sont après, en code
  mort dans ces builds.
- **Récupération** : inchangée (section 3 seulement).
- **Effort** : petit.
  - Pour les builds sans machine ajoutée : un tweak de 4 octets. Maxime doit décider s'il est toujours appliqué ou
    coché. On ne peut pas corriger l'OS officiel lui-même : le conseil « repasser les pistes sur une machine d'origine
    avant de revenir à l'OS officiel » reste nécessaire.
  - Pour Model-TG : 3 entrées dans `MC_PATCHES` de `tools/gen_model_tg.py`. Il faut le clone de Model-TG, absent ici
    (pas de `vendor/`).
  - `sdvintage-7th` et `syntakt-vintage` gardent `moveq #-1` dans `machine7.S` / `machine8.S`. Ils ne sont pas dans le
    flasher, seulement dans `build.py` : priorité basse.

Variante plus générale, non prototypée : réécrire le getter 0x40014058..0x4001406b (20 octets). Il ferait une seule
lecture de la machine (au lieu de deux appels virtuels) et une borne sur l'octet `0x400148ab`, que chaque tweak à
machine ajoutée réécrit (7205 → 72NN) et qui est donc « la dernière machine du build » :
`2040 7128 0026 7239 4001 48ab b280 6402 2001 6002 70ff`. Elle couvre aussi les 11 appelants du getter.

### 4.3 Autres index lus d'un projet ou d'un kit sans borne

| Index | Où | État |
|---|---|---|
| machine → `vec[m]` des potards | 0x4001e814 (this+104, 6 entrées) | **sans borne [FAIT]**. Le correctif D1 ne la couvre pas seul : avec le correctif, `vec[m]` hors tableau donne une valeur quelconque, mais 0x4004df5c la ramène sur CHORD (vérifié : potards = ceux de CHORD) |
| machine (+38 dans le son) | getter 0x40014042 | sans borne ; ses lecteurs dépendent de D1 |
| numérotation des machines ajoutées | notes/31 l.296, notes/20 §5 | **différente d'un build à l'autre [FAIT]** : un projet peut jouer en silence une **autre** machine ajoutée sans planter. Ce n'est pas un plantage, mais c'est une corruption de sens |
| destination de LFO, id → k | 0x4005a4e8 : `moveq #borne,d1` puis comparaison | bornée (76 d'origine), notes/56 l.116 **[FAIT d'après la note]** |
| octet +512 de la piste (`arp`) | recopié sans borne (notes/32 l.62), inutilisé par l'OS | sans danger pour l'OS ; c'est au mod de borner sa lecture **[HYP : non relu dans le code du mod]** |
| octets +88..+91 du son (`lfo-plus`) | notes/56 §3 | idem **[HYP]** |
| getter virtuel 0x4006af62 | — | non étudié |

---

## 5. Autres points de robustesse

### 5.1 Chien de garde (D6)

- **[FAIT]** Aucun accès à CWCR (0xFC040016) ni à CWSR (0xFC04001B), en adressage absolu ou par une base 0xfc0400xx,
  dans la section 2 (bootstrap), la section 3 (MAIN OS) ni la section 4 (updater).
- Les seuls accès au module de contrôle sont :
  - des octets écrits dans 0xfc04002d / 0xfc04002f, horloges des périphériques (PPMCR0/1 : `lea 0xfc04002d,a0 ; move.b #17,(a0) ; #18 ; #19 ; #20 ; #32 ; #36`, 0x400004fa..0x4000051a) ;
  - `move.l d2,0xfc040024` avec d2 = 1023, en 0x4000561c (BCR, rafales du bus).
- Les noms des registres viennent du manuel du MCF5441x de mémoire **[HYP]**. Le chien de garde serait éteint au reset
  **[HYP]**. Il n'est en tout cas jamais armé ni nourri.
- Conséquence : tout gel (D1, D2, `halt` de l'écran de plantage) demande une extinction forcée, qui perd l'état non
  sauvegardé (dossier §7.1).
- **Pas de correctif conseillé** : un reset en plein jeu perdrait aussi l'état, et il faudrait nourrir le chien depuis
  une tâche sans casser le rendu. Gain faible, risque réel.

### 5.2 L'horloge MIDI sortante bloque à IPL 7 (D2)

**[FAIT]** Le chemin : top 0x4005420c (`move.w #0x2700,sr` d'entrée) → `jsr 0x40082512` (0xF8) → 0x400824c4 (port DIN
si bit 0 de `0x404e9b52`) → 0x40001564 (porte THR) → 0x40001232 :

```
0x4000123a  move.l 0x4049dccc,d0 ; cmpi.l #1023,d0 ; bgt.s 0x4000123a     <- attend une place, au niveau de l'appelant
0x40001248  move.w sr,d2 ; move.w #0x2700,sr
0x4000124e  tst.l 0x4049dca0 ; bne.s -> anneau       (un message part par le DMA 37)
0x40001256  UART libre (0xec074004 bit 2) ? -> move.b d1,0xec07400c (direct)
0x4000126c  sinon : range dans *0x4049dcac (1 Kio), compte++, coupe le DMA 37, arme l'IRQ d'émission (src 53)
```

L'anneau ne se vide que par l'émission UART 0x40000e8c et la fin de DMA 37, toutes deux au niveau 4. À IPL 7, aucune
ne peut venir. Le drapeau « message en cours » `0x4049dca0` n'est remis à zéro qu'en trois endroits **[FAIT]** :
0x40000f88 (émission UART, niveau 4), 0x40001080 (fin de DMA 37, niveau 4) et 0x4000136e (initialisation de l'UART
0x40001358).

**Scénario [DÉDUIT]**, avec l'envoi d'horloge activé :
- Pendant une surcharge continue (§3.1), le niveau 4 n'est jamais servi : `0x4049dca0` reste non nul, car la fin du
  DMA 37 n'arrive pas, et chaque top range son 0xF8 dans l'anneau.
- Au 1025e top, le top tourne à IPL 7 pour toujours. Tout s'arrête : le son répète les 64 trames de l'anneau DMA, et
  l'écran de plantage n'apparaît pas.
- Délai : 1024 tops à 24 par noire, soit 21 s à 120 BPM et 4,7 s à 546 BPM (`tempo-max`).
- Sans le défaut, la machine se serait remise dès la fin de la surcharge. Ici, une surcharge passagère devient un gel
  définitif.

**Correctif** : 0x40001246 `6ef2` (`bgt.s 0x4000123a`) → `6e7e` (`bgt.s 0x400012c6`). La cible est la sortie
`move.l (sp)+,d2 ; move.l (sp)+,d3 ; rts`, juste après le `move.w d2,sr`, que l'on saute exprès : SR n'a pas encore
été changé à cet endroit. Anneau plein → l'octet est jeté.

Sortie de `python3 preuve_midi_horloge.py` :

```
  ok   octets d'origine en 0x40001246 : 6ef2
  ok   aucun tweak n'écrit 0x40001246..0x40001247 (282 fichiers lus)
  ok   origine : UART libre, 0xF8 écrit dans 0xec07400c, anneau vide
  ok   corrigé : UART libre, 0xF8 écrit dans 0xec07400c, anneau vide
  ok   origine : 1024 tops rangés, le 1025e ne revient pas (PC 0x40001246 dans 0x4000123a..46, SR 0x2700 : IPL 7)
  ok   corrigé : les 1026 tops reviennent (le 1025e et le 1026e jettent leur octet)
  ok   corrigé : les 1024 premiers tops laissent anneau, index, compte et registres identiques à l'origine, top après top
  ok   corrigé : anneau plein inchangé (compte 1024) après les octets jetés
  ok   l'anneau contient 1024 x 0xF8
TOUT OK
```

- **Son** : identique (l'audio n'est pas touché).
- **MIDI** : identique tant que l'anneau n'est pas plein (prouvé octet pour octet). Le changement n'agit qu'avec
  1024 octets en attente, soit 330 ms de retard sur la ligne.
- **Charge** : nulle.
- **Risque** : faible. Un appelant de niveau 3 ou de tâche (relais THRU, octets temps réel) jetterait aussi au lieu
  d'attendre. Cela n'arrive que si le niveau 4 est affamé, car l'anneau d'octets passe avant le DMA (notes/53 §7).
  Variante plus prudente, à placer dans un masque libre : ne jeter que si l'IPL de l'appelant est ≥ 4.
- **Effort** : petit (un tweak de 2 octets, ou 2 octets ajoutés à un tweak).
- **Reste ouvert** : l'attente de `0x40001100` (anneau de 4 Kio) a la même forme. Elle n'est dangereuse que si un
  appelant tourne à IPL ≥ 4 **[HYP : non trouvé, non exhaustif]**.

### 5.3 Piles des tâches (D4)

**[FAIT]** Les 12 tâches créées par 0x400019ec(tcb, entrée, prio, base, taille) (sommet = base + taille − 12) :

| Entrée | Prio | Pile | Taille | TCB |
|---|---|---|---|---|
| 0x400020e6 (minuteries logicielles, liste `0x4049fd70`) | 10 | 0x4049fdc8 | **2 Kio** | 0x4049fd74 |
| 0x400015c4 (répartiteur de messages) | 9 | 0x4049eb3c | 4 Kio | 0x4049eae8 |
| 0x4008a0ba (stockage SD/eMMC) | 8 | 0x40fcbb10 | 4 Kio | 0x40fccb10 |
| 0x40053a6c (animation de démarrage, puis …) | 7 | 0x40a745c0 | 16 Kio | 0x40a785c0 |
| 0x40080674 | 7 | 0x40fb7460 | 32 Kio | 0x40fb740c |
| 0x40007d46 | 6 | 0x404a9974 | 160 Kio | 0x404a9100 |
| 0x40082082 | 3 | 0x40fc011c | 32 Kio | 0x40fc00c8 |
| 0x40044188, 0x40068c78 | 2 | 0x404e5a80, 0x40a7cb28 | 16 Kio | |
| 0x400054a2 | 1 | 0x404a4b58 | 16 Kio | |
| 0x40005410 (init) | 0 | 0x404a0b04 | 16 Kio | |
| 0x40078436 | variable | 0x40ea1660 | 16 Kio | |

- **[FAIT]** Pour la tâche de 2 Kio, la pile commence à 0x4049fdc8 et descend vers son propre TCB (0x4049fd74..c7).
  Plus bas viennent les globales du noyau : la liste des minuteries 0x4049fd70, le **crochet de plantage 0x4049fd64**,
  le pointeur de priorité 0x4049fd60. Un débordement corromprait d'abord le contexte sauvé de la tâche, puis ces
  globales. Ce serait un plantage sans écran, ou un écran de plantage qui saute au hasard. Même disposition pour la
  tâche de 4 Kio (TCB 0x4049eae8 sous 0x4049eb3c).
- **[FAIT]** Profondeur mesurée de la boucle des voix (`python3 mesure_pile.py`, crochet d'écriture sur la pile, les
  6 pistes sur la machine, trig au bloc 1, 40 blocs) :

  ```
  origine KICK..TONE   248 o   CHORD 252 o   MACRO 280 o (356 o au pire des 47 modèles, notes/55 l.257)   ACID 264 o
  ```
  (sous l'entrée de 0x400a7d4a, adresse de retour comprise ; « accès hors carte : 0 »).
- **[DÉDUIT]** Le rendu jusqu'à l'appel de la boucle des voix coûte 8 o (trame d'exception), plus 172 (`link #-168`,
  0x40058c5e), plus 20 (arguments et retour), soit 200 o. Le rendu fait donc **450 à 560 o** de pile, hors effets et
  sortie, non mesurés **[HYP]**. Il faut y ajouter le niveau 2 (80 o de trame + appels), le niveau 3 (analyseur et
  relais MIDI) et le niveau 6.
- **[HYP]** Pire cas empilé autour de 1 à 1,3 Kio, sur une tâche de 2 Kio dont les rappels ont leur propre profondeur.
  La marge existe sans doute pour l'OS d'origine, mais elle n'est **vérifiée par rien**. Un mod qui met du C profond
  dans le rendu (tableaux locaux) la mange en silence.
- **Proposé** :
  - en émulation, une mesure systématique de la pile ajoutée par chaque mod dans le rendu et dans les interruptions,
    avec un budget (par exemple 768 o sous l'entrée du rendu), comme le fait `test_macro.py` (`cost`) pour MACRO
    seulement ;
  - sur la machine, un firmware de diagnostic qui peint les piles au démarrage et affiche les hautes eaux (essai de
    Maxime).
  - Effort moyen, son identique.

### 5.4 eMMC / SD (D5)

**[FAIT]**
- 0x4008a9b8..c4 : `IRQSIGEN |= 0x00310003`. Sont activés CC, TC, CTOE (délai de commande), DTOE (délai de données)
  et DCE (CRC de données).
- L'ISR 0x4008a676 ne traite que les bits 16, 1, 21, 20 et 0. Ni activés ni traités : CCE (CRC de commande), CEBE,
  CIE, DEBE (bit de fin de données), AC12E, DMAE.
- Les attentes passent par 0x40001b3e, un sémaphore binaire **sans délai** (s'il est à 0, la tâche est mise en
  attente puis `trap #0`). Deux scrutations de PRSSTAT n'ont pas non plus de délai : `btst #10` en 0x4008abaa..b4 et
  `btst #11` en 0x4008ac26..30.

**[DÉDUIT]** Une erreur non couverte bloque pour toujours la tâche de stockage (prio 8). Tout ce qui l'attend s'arrête
avec elle : la sauvegarde à l'extinction (§5.5), le chargement et le navigateur. L'audio continue.

**[HYP]** Rare : mémoire soudée, et les délais matériels (CTOE, DTOE) couvrent les cas courants.

Correctif : des délais sur ces attentes. Il faut une attente avec délai dans le noyau, non cherchée ici. Effort grand,
gain faible : non prioritaire.

### 5.5 Coupure pendant la sauvegarde

- **[FAIT]** La sauvegarde a lieu à l'extinction propre (dossier §7.1). La fenêtre « Shutting down... »
  (`ShutdownNotificationWindow`) est montée en 0x4003e9b4.
- **[FAIT]** `Brain::saveProjectBackupSync` (lambda vers 0x40006b62) poste le travail « SaveBackupProject » par
  0x40068d0a, puis attend le sémaphore 0x404a8ce8 par 0x40001b3e, **sans délai**. Si la tâche de stockage est bloquée
  (§5.4), l'extinction attend pour toujours, et l'utilisateur finit par couper.
- **[HYP]** Atomicité de l'écriture : les chaînes `BackupHandler::move` / `BackupHandler::swap` existent, mais ce sont
  des routes du protocole de transfert USB. Rien n'a été vérifié sur le chemin de l'extinction (écriture en place, ou
  fichier temporaire puis échange). Une coupure pendant l'écriture peut donc abîmer le projet ou non : non établi.
- **Pour les mods [DÉDUIT]** : tout ce qu'un mod écrit dans les structures sauvegardées voyage avec le projet vers
  d'autres builds (index de machine ≥ 6, octet +512 d'`arp`, octets +88..91 de `lfo-plus`, valeur 2 de `midi-live-both`
  en 0x404e9b50, notes/53 §8). D1 en est l'exemple qui plante. Un mod qui fige la tâche de l'interface ou celle du
  stockage empêche aussi la sauvegarde à l'extinction.

### 5.6 Mise à jour et récupération

- **[FAIT]** (mémoire `usb-update-single-check`) Le bootstrap démarre le conteneur 0x20000 sans contrôle. Une coupure
  pendant l'écriture d'une mise à jour USB, ou un build qui plante au démarrage, laisse donc une machine qui ne démarre
  plus.
- Le STARTUP MENU (MIDI IN, bootstrap intact) reste le chemin de retour : c'est pourquoi la règle 6 (section 3
  seulement) est vitale.
- Rien à corriger, mais **aucun contrôle automatique ne vérifie qu'un build garde les sections 2 et 4 identiques**
  au-delà de `build.py` lui-même.

---

## 6. Ce que `check_overlaps.py` et `registry.py` ne vérifient pas encore (D8)

D'après leurs docstrings (`tools/check_overlaps.py` l.1-33, `tools/registry.py` l.1-34) **[FAIT]** :
- `check_overlaps.py` voit les écritures aux mêmes octets, le format, les `requires` et `conflicts`, et la suite des
  charges utiles `append` (`at`, `dest`, `END_LIMIT`).
- `registry.py` voit les masques, les caves, les crochets et les pointeurs. Il range à la main ce que les écritures ne
  montrent pas (`DECLARED` : `arp`, `lfo-plus`).

Non vérifié :

| Manque | Pourquoi ça compte | Contrôle proposé | Effort |
|---|---|---|---|
| **RAM de travail à l'exécution** (BSS, trou 0x423380b0..0x4233ffff, SRAM 0x80001c5c.. / 0x8000cac0.. des moteurs du Syntakt, 0x46700000.. de Model-TG) | deux mods sur la même RAM ne se voient pas si leurs `dest` diffèrent ; `DECLARED` est tenu à la main (mémoire `ram-above-bss` : un premier choix aurait écrasé un tampon DMA) | une clé `ram: [[début, fin]]` dans chaque tweak, vérifiée comme `dest` | petit |
| **Pile** ajoutée dans le rendu et les interruptions | §5.3 : tâche de 2 Kio, TCB et crochet de plantage dessous | mesure en émulation par preuve (`mesure_pile.py` généralisé), avec un budget | moyen |
| **Ordre des crochets de démarrage** (0x400004b2, `boot_extra_hook` de Model-TG, remise à zéro du BSS, copie en SRAM) et **cache d'instructions** | blocage au logo de MACRO + Syntakt (mémoire `icache-boot-code`) ; seul `test_macro_syntakt.py` modélise le cache (`icache_watch`) | le même guet du cache dans chaque preuve qui exécute du code recopié au démarrage | moyen |
| **Données d'un build relues par un autre** (index de machine, octets ajoutés aux sons et pistes, réglages) | D1 ; numérotation des machines différente selon le build (notes/31 l.296) | une preuve « projet croisé » : chaque build ouvre MACHINES et les potards avec des pistes sur 0..max de tous les builds | moyen |
| **Même état sans mêmes octets** (même variable RAM, même octet sauvegardé, deux détours dans une même fonction) | `midi-both` / `midi-live-both` (valeur 2 de 0x404e9b50) s'excluent par `conflicts` déclaré à la main | lister dans le tweak les variables de l'OS lues et écrites (`state: [...]`), et refuser deux écrivains | moyen |
| **Appels bloquants depuis une interruption** (`0x40001100`, `0x40001232`, sémaphores) | D2 | dans les preuves, un garde qui échoue si du code de mod appelle ces fonctions avec IPL ≥ 4 | petit |
| **Budget de charge** d'une combinaison | §3 : au-delà de 100 %, des rendus se perdent sans trace | `ref_mainos.py` donne les empreintes, pas les instructions par bloc : y ajouter le pire coût par bloc des mods cochés (comme `cost` dans `test_macro.py`) | moyen |

---

## 7. Correctifs et améliorations, classés

Gain de charge, méthode : instructions ajoutées par bloc, rapportées à environ 180 000 cycles par bloc (32 trames à
48 kHz ; cœur supposé à 270 MHz, la moitié du VCO de 540,672 MHz de la mémoire `audio-clock-48k` **[HYP]**). Aucun
de ces correctifs ne vise à alléger la charge : ils durcissent la machine.

| Rang | Correctif | Gain | Risque | Son identique | Effort | Preuve |
|---|---|---|---|---|---|---|
| 1 | **D1** : borne des enregistrements (0x4004df66, 0x4004df80 : `70ff` → `7006`) ; Model-TG 0x401bf7e2/806/81c par `MC_PATCHES` | supprime un gel reproduit en émulation et vu par Maxime ; 0 % de charge | très faible : chemin hors limites seulement, aucun chevauchement | **oui** (machines 0..5 identiques, prouvé ; la voix jouait déjà CHORD) | petit | `preuve_machines.py [--tg]` : TOUT OK |
| 2 | **D2** : attente de 0x40001232 → sortie (0x40001246 `6ef2` → `6e7e`) | une surcharge passagère ne fige plus la machine pour toujours ; 0 % | faible : n'agit qu'avec l'anneau plein | **oui** (audio non touché ; MIDI identique hors anneau plein, prouvé) | petit | `preuve_midi_horloge.py` : TOUT OK |
| 3 | **D3, USB 6 canaux** : régulateur de file dans `feed.S` (recaler, ou sauter / doubler une trame quand la file sort de la fenêtre) | flux 6 canaux qui se remet après un bloc en retard au lieu de rester abîmé ; quelques dizaines d'instructions par bloc (< 0,05 %) | moyen (chemin USB, essai DAW nécessaire) | jacks oui ; USB identique sans dépassement, à prouver avec `preuve_surcharge.py` | moyen | à faire |
| 4 | **D3, détection et rattrapage** : à l'entrée du rendu, `d = 0x40a78e08 − dernier` ; si `d > 1`, compter `d − 1` rendus perdus, avancer l'heure musicale de `d × 2 × tempo` et envoyer `d × 32` trames à l'USB (silence ou dernier bloc) | séquenceur et USB qui restent calés sur l'horloge audio ; compteur affichable pour le diagnostic ; environ 10 instructions par bloc (≈ 0,01 %) | moyen (heure musicale partagée avec le séquenceur et l'horloge MIDI) | **oui** sans dépassement (`d = 1` toujours) ; à prouver bloc pour bloc | moyen | à faire |
| 5 | **D8** : contrôles d'outillage (`ram:`, garde IPL, preuve « projet croisé », budget de pile et de charge) | évite la prochaine famille de D1 et D2 | nul (outils seulement) | sans objet | petit à moyen | — |
| 6 | **D4** : budget de pile en émulation + firmware de diagnostic des hautes eaux | vérifier la marge de la tâche de 2 Kio | nul en émulation ; le diagnostic se teste sur la machine | oui | moyen | partiel (`mesure_pile.py`) |
| 7 | Numérotation des machines stable d'un build à l'autre | un projet ne change plus de machine en silence | moyen (touche à tous les générateurs de machines) | oui pour les machines d'origine | grand | — |
| 8 | **D5** : délais aux attentes SD | une erreur de mémoire ne fige plus le stockage | moyen | oui | grand | — |
| — | Chien de garde (D6) | non conseillé (§5.1) | | | | |

---

## 8. Ce que Maxime pourrait essayer sur la machine (s'il le veut)

Rien n'a été essayé sur le matériel.

- **E1 (D1)** : un projet avec une piste sur MACRO ou ACID, rouvert sur un build Model-TG seul. MACHINES gèle
  aujourd'hui. Avec le correctif, l'écran montre CHORD et les potards de CHORD, et la piste joue ce qu'elle jouait.
- **E2 (D2)**, à risque de gel (extinction nécessaire) :
  - Envoi d'horloge activé, `tempo-max` à 546 BPM, une combinaison lourde sans régulateur (Model-TG + MACRO, 6 pistes
    qui sonnent) pour tenir la charge au-dessus de 100 % plus de 5 s.
  - Aujourd'hui, la machine doit rester figée une fois la charge retombée. Avec le correctif, elle doit se remettre.
  - Le scénario dépend de la surcharge réelle **[HYP]**.
- **E3 (D3)** : `6ch-usbup`, flux 6 canaux ouvert dans le DAW, puis un pic de charge bref (beaucoup de trigs d'un
  coup). Les craquements doivent cesser après le pic. S'ils durent jusqu'à l'arrêt du flux, la simulation du §3.3 est
  confirmée.

## 9. Limites de ce travail

- Le comportement exact du matériel dans D1 (boucle, verrou ou exception) est **[HYP]** : l'émulation empoisonne la
  zone, alors que le vrai BSS contient autre chose.
- D2 est prouvé sur le vrai code. Qu'une surcharge réelle tienne le niveau 4 affamé pendant 1024 tops est **[DÉDUIT]**
  de la règle des niveaux (aucun retour sous IPL 5 entre des rendus collés).
- D3 est une simulation : modèle d'ordonnancement simple, vrai pilote USB.
- Non étudiés : réception USB-MIDI, file des événements de l'interface, accumulation d'une SysEx reçue, getter
  0x4006af62, profondeur de pile des effets, de la sortie et des ISR USB, atomicité de l'écriture du projet.
- Les correctifs ne sont que des prototypes : pas de générateur, pas de JSON, rien dans le flasher. Ils suivraient le
  chemin habituel (note, générateur, preuve dans `tools/emu/`, `experimental`, PR en brouillon), au choix de Maxime.
