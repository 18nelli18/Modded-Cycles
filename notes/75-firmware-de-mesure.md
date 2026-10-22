# 75 — Firmware de mesure : où passe le temps de l'audio, sur la machine

Demande de Maxime (22/10/2026), après l'analyse des dix chantiers d'allègement du processeur : « Fait le firmware de
mesure, puis le chantier 2 ». Les chiffres de l'analyse viennent d'un modèle (1,54 cycle par instruction, 15 cycles par
ligne de 16 o relue en SDRAM, notes/27, 28, 70) ; le chantier 2 (le code chaud en SRAM, chargé selon le projet) se
décide sur ce que coûte vraiment une ligne de code absente du cache, et sur ce que le cache garde d'un bloc à l'autre.

Générateur `tools/gen_mesure.py`, sources `tools/machines/mesure/` (`mesure.c`, `mesure_hooks.S`), preuve
`tools/emu/test_mesure.py`. **Pas une carte du flasher** : un .syx de diagnostic, construit sur le .syx officiel de
l'utilisateur comme `build.py --os`, pour Maxime.

## En bref

- L'OS de `os.json` à l'octet près, plus : 12 appels de l'interruption audio chronométrés, l'heure d'entrée de
  l'interruption, le temps libre de l'interface, des essais d'étalonnage ; trois écrans de plus dans la page System de
  Model-TG (DATA vers la droite, après ses deux écrans).
- 4,4 Ko de code dans 33 masques de sprites libres de l'OS ; variables en `0x4233a000..0x4233c100`, dans le trou
  libre au-dessus du BSS de l'OS (notes/56 §3.5.2, sous le step record `0x4233e800`).
- Coût permanent : environ 300 instructions par bloc (0,3 % d'un bloc) ; les essais et l'essai A/B seulement quand
  leur écran est affiché.
- `[FAIT en émulation]` (§5). Pas encore lu sur la machine (§4).

## 1. Ce qui est mesuré

Minuteur DMA 0 (`0xfc07000c`, compteur libre à 135,168 MHz, 90 112 ticks par bloc de 32 trames, 7,4 ns).

### 1.1 Écran AUDIO (écran 2 de la page System)

Moyenne sur 750 blocs (0,5 s), en % de la durée d'un bloc :

| Case | Ce que c'est |
|---|---|
| SEQ | de l'entrée de l'interruption à l'appel de la fonction audio, moins l'audio venu de l'USB : séquenceur, événements, décomptes, et l'envoi à l'USB du bloc précédent (notes/35 : il part au début de l'interruption suivante) |
| USB | audio venu de l'USB (`0x40002ae0`) et mise en file de l'envoi (`0x4015c2d6`) |
| SMOOTH | lissage des paramètres (`0x40058474`) |
| LFO | les LFO (`0x40183646`, LFO 2, 3, 4) |
| VOICES | la boucle des voix (`fx_early` de Model-TG : la préparation des effets, puis les 6 voix) ; la part de chaque piste est l'écran 1 de Model-TG |
| POST | le reste de la fonction audio : modulation de vélocité, après les voix (Model-TG, gain de vélocité), recopie des gains, `0x40056ea8`, le régulateur de charge (`audio_end`) |
| DIST | Volume + Dist (`0x40056f58`) |
| OUTPUT | l'étage de sortie (Model-TG, puis mixeur, envois, delay, reverb, master, codec : `0x400567ba`) |
| TOTAL | de l'entrée de l'interruption à la fin de l'envoi à l'USB |
| PEAK | le pire bloc de la fenêtre |
| IDLE | le temps où l'interface n'avait plus rien à faire (boucle d'attente de la tâche de priorité 0) |
| OTHER | 100 − TOTAL − IDLE : l'interface au travail, les autres interruptions (panneau, USB), la fin de l'interruption audio |

### 1.2 Écran BENCH (écran 3)

Tant qu'il est affiché, un essai par bloc, à la fin de l'interruption audio ; le meilleur temps de la fenêtre. En
cycles du processeur, d'après l'essai de l'horloge (1 056 instructions d'un cycle) :

| Case | Essai |
|---|---|
| CPU | la fréquence du cœur : 1 056 `addq` en N ticks de 135,168 MHz |
| ALU, ALU SR | cycles par instruction d'un noyau de calcul (`add`, `eor`, `lsl`, `sub`), dans le cache (2e passage) et recopié en SRAM |
| MAC, MAC SR | idem, un noyau de filtre (lecture, produits de l'EMAC, écriture) |
| MEM, MEM SR | idem, une recopie de 1 Ko (`move.l (a0)+,(a1)+`) |
| LINE, LINE SR | cycles par ligne de 16 o de code droit (8 `addq`), dans le cache et en SRAM |
| I-MISS | ce que coûte une ligne de code absente du cache : le code droit cache d'instructions vidé, moins dans le cache |
| D-MISS | ce que coûte une ligne de données absente du cache : 1 Ko lu après l'avoir chassé, moins dans le cache |
| RD SR | cycles par mot lu en SRAM |

La SRAM empruntée est la zone de travail des voix (`0x8000bec0..`, notes/26), écrite avant d'être lue à chaque
bloc : sauvée avant l'essai, rendue après. Le code droit (128 lignes, 2 Ko) est écrit au démarrage en
`0x4233b000` par la vue sans cache, puis le cache d'instructions est invalidé.

### 1.3 Écran COLD (écran 4)

Tant qu'il est affiché, un bloc sur deux commence cache d'instructions vide (CACR de l'OS sans DCINVA, comme
`mod_settings`, notes/72). Les deux moyennes côte à côte : TOTAL, VOICES, OUTPUT, et GAIN = froid − normal.

- Si GAIN est faible, le cache est déjà presque vide au début de chaque bloc (l'interface le chasse entre deux
  blocs) : tout le code de l'audio est relu en SDRAM à chaque bloc, et le passer en SRAM rend le prix de ses lignes.
- Si GAIN est fort, le cache garde du code d'un bloc à l'autre : le gain du chantier 2 sera moindre.

Plus : RD UNC (cycles par mot lu par la vue sans cache) et RD C (dans le cache).

## 2. Comment c'est fait

| Où | Quoi |
|---|---|
| 12 appels (`SITES`) | `jsr cible` → `jsr m_w_k` : met de côté le retour, note l'heure, appelle la cible, note la durée (détruit `d1` et `a1`, libres pour un appel C ; aucune cible n'y lit d'argument, vérifié) |
| `0x40059392` | l'envoi à l'USB, le dernier appel du bloc : la même sonde, puis `m_block_end` |
| `0x4005966a` | le vecteur de l'interruption audio, posé au démarrage : `isr_prof` de Model-TG → `m_isr` (note l'heure, puis `isr_prof`) |
| `0x4000543a` | la boucle d'attente de la tâche de priorité 0 → `m_idle` (le compteur de temps libre de l'étude, notes/70) |
| bloc de Model-TG `0x401b6fb6` | le choix de l'écran de `sys_render` → `m_sys` (écrans 0 et 1 : les siens ; 2 à 4 : `m_render`) |
| bloc de Model-TG `0x401b1ca4` | le cran de DATA de la page System : jusqu'à l'écran 4 au lieu de 1 |

Le bloc de Model-TG est retouché dans une copie du tweak `model-tg-st` au moment du build (même taille, aucune adresse
ne bouge). `build.py` a maintenant une fonction `build_syx` (la fin de `main`, sans changement), que `gen_mesure.py`
appelle.

## 3. Construire

```sh
python3 tools/gen_mesure.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.41.syx \
  -o build/modded-cycles-os_2.1-mesure.syx
```

Le code est compilé à chaque fois : un autre GCC donne un autre MAIN OS (`956910cc…0a2b` avec `m68k-elf-gcc` 16.2,
`4ac9cd54…8426` avec le 13.3 d'Ubuntu 24.04), le même OS autour.

## 4. Protocole (à faire par Maxime)

Ouvrir la page : SETTINGS → DEVICE CONFIG → System (la ligne après Transfer, notes/31). DATA vers la droite : écrans 0 (CPU, PEAK, RAM, FREE) et 1 (les
pistes) de Model-TG, puis AUDIO, BENCH et COLD. Les valeurs d'un écran ne valent que pendant qu'il est affiché (et
une demi-seconde après) ; noter ce que montre chaque écran au bout de 2 s environ.

1. **BENCH, séquenceur à l'arrêt** (les essais rallongent un bloc sur 14, jusqu'à 10 % pour celui des données) :
   toutes les cases.
2. **AUDIO**, sur trois projets :
   - à l'arrêt ;
   - les 6 machines d'origine, un trig sur chaque pas des 6 pistes ;
   - un projet typique (machines ajoutées, MODAL, Sampler, effets).
3. **COLD**, sur le projet typique, avec une charge moyenne (4 pistes) : les invalidations ajoutent du temps un bloc
   sur deux, le régulateur peut éteindre des voix si la charge est déjà haute.

## 5. Preuves `[FAIT en émulation]`

`tools/emu/test_mesure.py` (22/10/2026), **TOUT OK** :

1. **Octets** : 4 462 octets changent par rapport à l'OS de `os.json`, tous dans les 80 écritures du firmware de
   mesure (33 masques et leurs constantes, 12 appels, le vecteur, la boucle d'attente) ; 11 octets du bloc de
   Model-TG, dans le choix de l'écran et le cran de DATA.
2. **Son** : 6 pistes (KICK, SDVtg, MACRO, ACID, MODAL, CHORD) jouées par le vrai séquenceur (`seqrig`) pendant
   420 blocs : la sortie des voix et l'état des 6 voix identiques, bloc par bloc, à l'OS sans sondes ; les sondes
   notent leur retour et leurs durées (minuteur qui avance à chaque lecture).
3. **Écrans** : 750 blocs de durées connues, puis la vraie `sys_render` de Model-TG sur chaque écran : AUDIO montre
   les valeurs attendues (SEQ 4.5 %, VOICES 33.2 %, TOTAL et PEAK 73.2 %…) ; les écrans 0 et 1 restent ceux de
   Model-TG ; DATA va de l'écran 0 au 4, un par cran.
4. **Essais** (un cycle par instruction, deux instructions par tick) : BENCH montre 269 MHz, ALU 1.00 dans le cache
   et en SRAM, I-MISS et D-MISS 0.00 (l'émulation n'a pas de cache) ; la SRAM est rendue intacte après 760 blocs
   d'essais ; le code droit est bien écrit ; avec COLD affiché, un bloc sur deux est froid.
5. **`m_isr`** : l'heure d'entrée notée, `d0` et la pile intacts, une invalidation seulement pour un bloc froid,
   puis `isr_prof` ; **`m_idle`** : les écarts courts comptés, une interruption non.

Trouvé en route : au 1er bloc après le démarrage, la période était lue depuis 0 (une heure absolue) ; elle n'est plus
comptée.

## 6. Chronologie

- 22/10/2026 : demande de Maxime ; firmware, preuve, protocole.
