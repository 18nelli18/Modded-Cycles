# 88 — ACID : articulation et profil Devil Fish

Demande de Ruslan (31/10/2026), après l'« articulation ACID » de la version 2.64 d'AveyCole (son dépôt
AveyCole/Supermodel, notes/206–207 : glissement 50..360 ms et legato, sous SETTINGS + potard) : la même chose chez
nous, plus un profil Devil Fish. Écrit ici d'après le manuel de la Devil Fish et la page « TB-303's unique
characteristics » de Robin Whittle, pas d'après le code d'AveyCole : « manuel p. N » = *User Manual for the Devil
Fish mods to the TB-303* (https://www.firstpr.com.au/rwi/dfish/Devil-Fish-Manual.pdf), « 303-unique » =
https://www.firstpr.com.au/rwi/dfish/303-unique.html. Adresses : VA de l'OS 1.13.

## En bref

- Une ligne **ACID** sur la page **Mod Settings** (SETTINGS › Mods, notes/72) ouvre la page **ACID** : **Slide**,
  **Tie**, **Accent**, **Decay**. LEVEL/DATA pressé passe à la valeur suivante. Réglages 1..4 de l'enregistrement
  MODS (`0x404e9b80`, octets 6..9), à côté de USB Audio (réglage 0). La page ACID est une `MenuView` que la page Mod
  Settings pousse comme le Config Menu pousse Mod Settings (`acid_open`, pointeur partagé `acid_h`).
- La machine ACID les lit à chaque trig (`acid_set`, `tools/machines/acid/acid.c`). Valeur 0 de chacun (le défaut,
  et sans enregistrement valide ou sans Mod Settings) : ACID d'avant, **au bit près** (§4).
- Globaux, pas par piste ni par pas : comme une Devil Fish, un seul appareil. Pas de p-lock, pas de destination de
  LFO.
- `[FAIT en émulation]` tout ce qui suit. **À essayer sur la machine** (§5).

## 1. Ce qui manquait

Le slide d'ACID (notes/54) est une seule décision : une note dont la longueur (LEN) dépasse le trig suivant est
liée, l'OS ne voit pas ce trig (ni fondu ni relance de l'ampli), le MEG continue, et la hauteur glisse avec la
constante d'Open303 (`ACID_SLIDE_A`, τ = 21,7 ms ; le RC de la 303 est 100 k × 0,22 µF = 22,0 ms, manuel de la
Devil Fish p. 16). Pas d'accent : la vélocité ne règle que le gain de l'OS (le premier accent, sur CONTOUR, a été
retiré : notes/54).

## 2. Les réglages

| Réglage | Valeurs (0 en gras) | Effet |
|---|---|---|
| Slide | **303**, OFF, 60, 120, 180, 240, 360 | temps du glissement. 303 : `ACID_SLIDE_A`. OFF : la hauteur saute (coefficient 1). 60..360 : temps audible de la Devil Fish (p. 4), soit 2,64 τ (103,3 k × 0,22 µF = 22,7 ms pour 60 ms, p. 16) |
| Tie | **ON**, OFF | OFF : un trig lié n'est plus caché à l'OS : l'ampli et le MEG repartent (trig `ACID_GLIDE` du cœur), seule la hauteur glisse depuis la note d'avant. Le glissement garde le temps d'Slide |
| Accent | **OFF**, LOW, MID, HIGH | une note dont le gain de vélocité (`0x40fe4cd0`) atteint 110 est accentuée : son MEG décroît en 200 ms (la plus courte de la 303, comme le circuit d'accent : 303-unique, « MEG »), et il charge l'accent sweep (§3). LOW, MID, HIGH : la montée de la coupure pour un MEG plein, 1, 2 ou 3 octaves |
| Decay | **303**, DF | DF : DECAY couvre 30 ms .. 3 s (Normal Decay de la Devil Fish, p. 4) au lieu de 200 ms .. 2 s (`ACID_DEC_DF`) |

- Un accent sur une note liée (slide) ne relance pas le MEG : il change sa vitesse de décroissance et charge
  l'accent sweep depuis le MEG en cours (comportement connu : « un slide accentué est surtout plus fort »).
- La vélocité règle toujours le gain de l'OS ; l'accent n'ajoute pas de gain (le « VCA boost » de la 303 n'est pas
  repris : la vélocité le fait déjà).
- Un réglage changé s'entend à la note suivante.

## 3. L'accent sweep

Le circuit de la 303 (303-unique, « The real fun is in the Accent Sweep Circuit ») : le MEG des notes accentuées
charge le condensateur C13 (1 µF) par une diode et 47 k + 100 k, qui se vide par 100 k ; la coupure reçoit le
curseur d'un potard de 100 k qui est la **2e section du potard de RESONANCE** : en bas, une impulsion presque
directe (100/147 du MEG, moins la charge) ; en haut, la tension de C13, lissée, qui monte plus haut à chaque accent
de suite parce qu'elle ne se vide pas entre deux.

Dans le cœur (`acid_block`, une fois par bloc de 32 trames, seulement si Accent n'est pas OFF) :

```
e = note accentuée ? MEG : 0
si e > C : C += (e - C) × ACID_ACC_CHG      (τ 147 ms)
sinon    : C -= C × ACID_ACC_DIS             (τ 100 ms)
sweep = r × C + (1 - r) × max(0, 0,68 e - C)  r = RESO (SHAPE), 0..1
coupure (1/16 d'octave) += sweep × ACID_ACC_T[réglage]
```

Mesuré sur la référence (test_acid, `accent_sweep`) : crêtes de la charge sur trois accents de 100 ms de suite
0,378, 0,570, 0,671 du MEG, puis 0,603 sur la note sans accent qui suit (elle se vide) ; une note accentuée est
1,5 fois plus brillante (écart moyen d'un échantillon au suivant) qu'une note sans accent.

## 4. Preuves

- Cœur seul : l'ancien `acid_dsp.h` (commit de base) et le nouveau, réglages à 0, sur 20 000 blocs tirés au hasard
  (notes, potards, trigs, slides, remises à zéro) : sorties identiques octet pour octet.
- `tools/emu/test_acid.py` : la passerelle modélisée en Python lit le même enregistrement MODS que la machine dans
  l'OS émulé ; à chaque bloc la sortie avant la chaîne d'ampli reste exactement la référence (`acid_ref.c`, 4
  champs de plus). Section « articulation » : 11 séquences du vrai séquenceur — sans enregistrement, enregistrement
  faux (octet de contrôle), valeurs hors bornes (= 303) ; Slide OFF, 360 ms ; Legato OFF (trigs vus de l'OS :
  `TGG` au lieu de `TSS`) seul et avec Slide 240 ms ; Accent HIGH sur 127 × 3 puis 64 (accents `1 1 1 0`,
  décroissance courte) ; Accent LOW sur un slide accentué ; Decay DF ; tout à la fois.
- Place : code et tables d'ACID 6 704 o (6 068 avant), variables 912 o (744) ; Mod Settings : trois masques 46 × 31
  de plus (`0x40170ad8`, `0x40171bc8`, `0x401728f8`, `0x40184988`) et un 35 × 35 (`0x40167c50`), libres sur la chaîne
  complète des PR au 31/10/2026, pour la page ACID ; `check_overlaps.py` sans conflit.

## 5. À essayer sur la machine

Rapport d'un utilisateur (Model:Cycles, 01/11/2026), firmware de test `os-lofi-df2` (cette branche sur la chaîne
lo-fi) : page Mod Settings › ACID, Slide, Tie, Accent et Decay essayés, « tout fonctionne ». La liste ci-dessous
reste à couvrir pour un essai complet.


- Mod Settings › ACID : quatre lignes, « n/4 », valeurs lisibles (HIGH, 360) ; retour en arrière ; le réglage revient
  après extinction.
- Slide 360 sur LEN 1.06 ; OFF ; Tie OFF (chaque note attaque, la hauteur glisse).
- Accent HIGH, RESO haut, vélocités 127 sur trois pas de suite : la montée « wow » qui grandit ; RESO bas :
  un claquement court.
- Decay DF, DECAY au minimum : un « tic » de filtre de 30 ms.
- Charge du processeur avec six pistes ACID, Accent HIGH.

## 6. Hors de cette version

Soft attack (0,3..30 ms), suivi de la coupure par la note (2,7 kHz/V), Accent Decay réglable (fixé à 200 ms ici),
Sweep Speed (Fast/Slow), overdrive jusqu'à 66,6 ×, muffler : relevés dans la spécification, pas faits. Une ligne de
Mod Settings de plus chacun, ou un vrai potard par piste (il faudrait des mots de paramètre libres).
