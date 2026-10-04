# 34 — Écoute d'un pas : PAGE tourne la page après un Stop MIDI

Un défaut du tweak `trig-preview` de drumkilla (pas tenu + PAGE), le même dans Model-TG qui l'embarque. Analyse sur le
MAIN OS 1.13, correctif de 3 octets, preuve en émulation. Adresses : VA de l'OS 1.13.

## Le problème signalé

- **Retour de l'utilisateur** (04/10/2026), firmware du flasher avec Model-TG, les moteurs du Syntakt, l'arpégiateur et
  « Effacer un trig plus facilement » : l'écoute marche, puis « d'un seul coup » elle ne répond plus et **PAGE tourne la
  page** à la place. Tout le reste marche (les touches de pas posent et effacent les trigs). Rien de particulier ne la
  déclenche ; seul un redémarrage l'a fait revenir.
  > Source : messages de l'utilisateur dans la session du 04/10/2026.

## 1. Ce que teste l'écoute `[FAIT]`

Le code de drumkilla remplace le début du traitement de PAGE (code 15) dans `PatternGridView::consumeKeyEvent`
(`0x400224ee`, `jmp 0x401489fa`). Il ne joue le pas que si tous ces tests passent ; sinon il reprend le traitement
d'origine, où PAGE tourne la page au relâchement (`0x40022f64` puis `0x40022f70`).

| Test | Où | Condition pour jouer |
|---|---|---|
| Appui frais | `0x400724a0` | bit 0 des indicateurs, sans le bit 3 (maintien) |
| Sans FUNC | `0x40072490` | bit 1 à 0 |
| **Séquenceur** | `0x4005481a`, testé en `0x40148a30` | **`0x40a78874 \| 0x40a7883c` = 0** |
| Mode grille | `0x4006b978` | `UIStates` +357 et +358 |
| Pas de choix de pattern | `0x4006bb18` | `UIStates` +389 à 0 (mis par `PatternAndBankSelectView`, PATTERN + pad) |
| Un pas tenu dans la longueur | `0x4006bdfe` | pas tenus (+348, +352) et masque de longueur de la piste |
| Pattern et kit | `0x40a7887c`, `0x40a78888` | non nuls |

> Source : désassemblage du tweak (`tweaks/model-cycles_OS1.13/02-trig-preview.json`) et des fonctions appelées.

L'utilisateur pose des trigs normalement : le mode grille et le choix de pattern sont hors de cause (avec eux, les
touches de pas ne posent plus rien, `0x40022406` et `0x4002242a`). Reste l'état du séquenceur.

## 2. Trois états, pas deux `[FAIT]`

| Valeur de `0x4005481a` | Écrite par | Sens |
|---|---|---|
| 0 | `0x400546e2`, `0x40055f22` (STOP) | arrêt |
| 1 | `0x400542dc` (PLAY, Start MIDI `0x40080936`, Continue `0x400809dc`) | lecture |
| 2 | `0x40056060` | **pause** |

- La boucle principale traite les trois cas (`0x4000827e`) : 1 et 2 allument des voyants différents (`UIStates` +68 et +69,
  lus en `0x4001cce8` pour les touches 29 et 30). `0x4006ba76` ne compte comme lecture que la valeur 1.
- En pause, les drapeaux par piste (`0x40a78848`…`0x40a7885c`) valent 2 : le séquenceur ne construit plus d'événement de
  pas (`0x4005510e` ne traite que les pistes à 1).
- **`0x40056060` est appelée par PLAY pendant la lecture (`0x40024628`) et par le Stop MIDI** : entrée `0xFC` de la table
  des messages temps réel `0x40112960` → `0x40080a72`, si l'horloge MIDI est reçue (`0x40a70144`) et que la source le
  permet (`0x40091770`). Rien n'y vérifie que le séquenceur tournait (`0x40058b5e` rend toujours 0) : **un Stop MIDI met en
  pause un séquenceur à l'arrêt**. Il y reste jusqu'à PLAY, STOP ou un redémarrage.

L'écoute teste « différent de 0 » : en pause, elle refuse, et PAGE tourne la page. C'est le symptôme signalé.
`[HYP]` Le Stop vient de l'ordinateur branché en USB (le logiciel de musique l'envoie quand on arrête son transport) ou
d'un appareil sur l'entrée MIDI.

## 3. Le correctif

En `0x40148a30`, `tst.l d0 ; bne.w` devient `lsr.l #1,d0 ; bcs.w` (`4a80 6600` → `e288 6500`, même taille, même
destination) : le bit 0 sort dans la retenue, l'écoute ne refuse plus que la lecture (1). L'arrêt (0) et la pause (2) la
laissent jouer. La pause ne fait plus courir de risque au code de l'écoute, qui change un instant la probabilité de la
piste et la condition du pas : le séquenceur ne les lit pas en pause (§2).

- `tweaks/model-cycles_OS1.13/02-trig-preview.json` : les 3 octets dans l'écriture `1345021`, et une ligne de
  description. Le reste du fichier de drumkilla est inchangé (`PROVENANCE.md`).
- Model-TG : la même retouche sur sa copie du fichier (`tweaks/model-cycles_OS1.13/02-trig-preview.json` de son dépôt,
  appliquée par son `build.py`), dans `MC_PATCHES` de `tools/gen_model_tg.py`. `30-model-tg.json` et `30-model-tg-st.json`
  ne changent qu'en ces 3 octets, leur empreinte et leur description ; leur charge utile est identique. Les 31 tweaks
  `31-syntakt-tg-….json` restent les mêmes (`gen_syntakt_engines.py --tg --all --check`).
- Flasher web : `tweaks.js` régénéré, texte de la carte « Écoute d'un pas », `REF_MAINOS` régénéré (2 303 combinaisons,
  1 280 changent : toutes celles qui contiennent l'écoute ou Model-TG). Empreintes de `BUILD.md` mises à jour.

> Source : `tools/gen_model_tg.py`, `tools/ref_mainos.py`, `tools/gen_flasher_tweaks.py`, dans ce dépôt.

## 4. Preuve en émulation : `tools/emu/test_trig_preview.py`

Le banc de `test_trig_hold.py` (vraie chaîne des touches, vrai `PatternGridView::consumeKeyEvent`, vrai `UIStates`), avec
la construction de l'événement du pas (`0x400548ce`) et le changement de page (`0x40013958`) comptés.

| Situation | Code de drumkilla | Retouché |
|---|---|---|
| Arrêt, pas tenu + PAGE | joue | joue |
| Lecture | page tournée | page tournée |
| Pause | **page tournée** | joue |
| Après un Stop MIDI reçu à l'arrêt (vrai `0x40080a72`, état 0 → 2), trois appuis sur PAGE | **3 pages tournées** | 3 écoutes |

Le trig reste dans tous les cas. **TOUT OK** seul, avec Model-TG, avec `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold`
(la combinaison de l'utilisateur) et avec les trois tweaks de drumkilla, `6ch-usbup`, l'arpégiateur et `trig-hold`.
Aussi repassés : `test_trig_hold.py` (avec Model-TG + moteurs, avec les tweaks de drumkilla), `test_model_tg.py`
(les deux tweaks Model-TG), `test_model_tg_syntakt.py`, `webbuild_check.sh`, `webflash_check.sh`, et
`webflash_smoke.sh` avec les OS Cycles 1.13 et Syntakt 1.42 : la vraie page du flasher reconstruit chaque combinaison
proposée et tombe sur son empreinte de référence.

## 5. Essai sur la machine `[FAIT]`

**Testé le 04/10/2026** sur un vrai Model:Cycles, avec `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp`
construit par `build.py` (MAIN OS `2f1276ac…`, le même que le flasher) : « ça marche nickel ».
> Source : message de l'utilisateur dans la session du 04/10/2026.

Protocole proposé :

1. Avec l'ancien firmware, quand PAGE se met à tourner la page : appuyer une fois sur **STOP**. L'écoute doit revenir
   (le séquenceur repasse à l'arrêt). Pas fait : l'utilisateur a flashé directement le firmware corrigé.
2. Flasher le firmware corrigé, puis refaire la même séance : l'écoute doit marcher aussi après un arrêt du logiciel de
   musique.
3. Contrôle : séquenceur en lecture, pas tenu + PAGE tourne toujours la page (comportement voulu par drumkilla).
