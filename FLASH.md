# Flasher son Model:Cycles — guide détaillé

> ⚠️ **À lire en entier avant de flasher.** Installer un firmware modifié **met la garantie en jeu** et peut, en cas d'erreur, rendre l'appareil temporairement inutilisable. Le risque de « brick » **définitif** est très faible car la récupération passe par un bootloader que la mise à jour n'écrit jamais — **à condition de pouvoir envoyer du MIDI sur l'entrée MIDI IN de l'appareil** ([§5](#5-récupération-revenir-à-loriginal)). Tu fais ça à tes risques. Rien ici n'est affilié à Elektron.

---

## 1. Comprendre ce qu'on fait

Un firmware Elektron est un fichier `.syx` (SysEx MIDI). Flasher = **envoyer ce fichier à l'appareil** pendant qu'il attend une mise à jour.

Le point le plus important, et le plus souvent mal compris :

> **La mise à jour par le menu de démarrage ne fonctionne QUE par l'entrée MIDI IN de l'appareil (sa prise jack TRS 3,5 mm), PAS par son port USB.**

C'est écrit noir sur blanc dans le manuel Elektron (§13.4). Il te faut donc une **interface MIDI USB** dont la sortie arrive sur le **MIDI IN du Model:Cycles**, par l'un de ces branchements :
- **interface à sortie MIDI en jack TRS 3,5 mm** + **un simple câble jack stéréo 3,5 mm** mâle-mâle. C'est le plus simple. Prends un câble stéréo à 3 contacts (TRS) : ni mono, ni à 4 contacts (TRRS) ;
- **interface MIDI DIN** (prises rondes à 5 broches) + **l'adaptateur TRS → DIN fourni** avec le Model:Cycles (kit CA-3) et un câble DIN. Un câble DIN mâle → jack TRS fait la même chose d'un seul tenant.

Le MIDI IN du Model:Cycles accepte les deux brochages TRS (type A et type B) : n'importe quelle sortie MIDI TRS convient.
En revanche, la **sortie casque** de l'ordinateur ne suffit pas : elle sort de l'audio, pas du MIDI.
Détails, liste d'interfaces et piste expérimentale « sortie casque » : [`notes/12-flash-par-jack-trs.md`](notes/12-flash-par-jack-trs.md).

Le port USB du Model:Cycles sert à l'audio et à la mise à jour « normale » via l'appli Transfer, mais **pas** à récupérer un appareil.
Et le mod 6 canaux de référence (`6ch-multiout`) casse justement cette mise à jour par USB.
La variante `6ch-usbup` devrait la garder, mais c'est à tester ([note 13](notes/13-6ch-upgrade-usb.md)).
Donc pour le modding : **tout passe par le MIDI IN**, et le secours y passera toujours.

---

## 2. Préparatifs (à faire une fois)

- [ ] **Une interface MIDI** dont la sortie est reliée au MIDI IN du Model:Cycles : sortie TRS + câble jack stéréo, ou sortie DIN + adaptateur fourni ([§1](#1-comprendre-ce-quon-fait)).
- [ ] **Le firmware officiel `model-cycles_OS1.13.syx`** (dézippé depuis elektron.se). C'est **aussi ton image de secours** : garde-le à portée.
- [ ] **Sauvegarde tes projets** avec Elektron Transfer (le flash peut affecter le contenu).
- [ ] **Le fichier `.syx` à flasher** : soit l'officiel, soit un firmware modifié construit avec [`BUILD.md`](BUILD.md) :
  ```
  python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout
  ```
  → produit `model-cycles_OS1.13_mod.syx`. Avec `-t 6ch-usbup`, tu obtiens la variante qui devrait garder la mise à jour par USB
  (jamais flashée : suis le protocole de la [note 13](notes/13-6ch-upgrade-usb.md) §6).

---

## 3. Flasher — la méthode simple (scripts fournis)

Les scripts installent tout seuls Python, les dépendances MIDI, **vérifient** le fichier, puis lancent le flash en te guidant.

### macOS / Linux

Dans un terminal, place-toi dans le dossier du projet et lance :
```bash
./flash.sh
```
Ou en visant un fichier précis :
```bash
./flash.sh model-cycles_OS1.13_mod.syx
```
Vérifier seulement, sans rien envoyer :
```bash
./flash.sh --verify model-cycles_OS1.13_mod.syx
```
> macOS : si `./flash.sh` refuse de s'exécuter, fais d'abord `chmod +x flash.sh`. Le compilateur peut être demandé une fois (`xcode-select --install`).
> Linux : si l'installation de `python-rtmidi` échoue, le script t'indique les paquets à installer (en-têtes ALSA), par ex. `sudo apt install libasound2-dev build-essential`.

### Windows

Double-clique **`flash.bat`** (ou lance-le depuis l'invite de commandes). Pour un fichier précis :
```bat
flash.bat model-cycles_OS1.13_mod.syx
```
> Il faut **Python 3** (python.org, en cochant « Add Python to PATH », ou le Microsoft Store). Si l'installation de `python-rtmidi` réclame un compilateur, installe « Microsoft C++ Build Tools » puis relance.

### Ce que le script fait, dans l'ordre

1. Trouve le `.syx` (priorité au `*_mod.syx` le plus récent).
2. Installe Python + `mido` + `python-rtmidi` dans un environnement isolé (`.venv`).
3. **Vérifie le fichier** : identifiant Elektron, produit `0x11 (Model:Cycles)`, et **chaque checksum**. Il refuse un fichier douteux.
4. Te rappelle le branchement et la mise en mode réception.
5. Te fait **choisir le port MIDI** (celui de ton interface) et **confirmer**, puis envoie.

---

## 4. La séquence de flash, écran par écran

1. **Branche** l'interface (sa sortie MIDI → MIDI IN de l'appareil, [§1](#1-comprendre-ce-quon-fait)) et l'interface à l'ordinateur.
2. **Mets l'appareil en réception** :
   > éteindre → **maintenir [FUNC]** → **allumer** → relâcher → **[TRIG 4]** (OS UPGRADE)

   L'écran affiche **`READY TO RECEIVE`**.
3. **Lance le script** et laisse-le envoyer. Surveille l'écran de l'appareil :
   - il doit passer de `READY TO RECEIVE` à **`RECEIVING…`** en quelques secondes ;
   - **s'il reste sur `READY TO RECEIVE`**, l'image est ignorée en silence → tu n'as pas choisi le bon port (prends celui de **l'interface**, pas « Model:Cycles »), ou le câble n'est pas OUT→IN, ou c'est un câble jack mono.
4. La progression s'affiche (~5 à 7 min). **Ne coupe RIEN**, surtout quand l'écran indique **`UPDATING FLASH`** : c'est le seul moment vraiment délicat.
5. L'appareil **redémarre tout seul** quand c'est fini. Il peut aussi mettre à jour son « bootstrap » au premier redémarrage — laisse-le faire.

Vérifier que le mod multipiste a pris (macOS) :
```bash
system_profiler SPAudioDataType | grep -A4 "Model:"
#   Input Channels: 6
```

---

## 5. Récupération (revenir à l'original)

Si l'appareil ne démarre plus, se bloque, ou que tu veux simplement revenir en arrière :

1. éteindre → maintenir **[FUNC]** → allumer → **[TRIG 4]** (OS UPGRADE) ;
2. envoie le **`.syx` officiel** par la **même** méthode :
   ```bash
   ./flash.sh model-cycles_OS1.13.syx          # macOS/Linux
   flash.bat model-cycles_OS1.13.syx           # Windows
   ```

Ça marche **même si le firmware principal est cassé**, parce que le menu de démarrage vit dans une zone que la mise à jour n'écrit jamais. C'est pour cette raison qu'une **interface MIDI reliée au MIDI IN** (par câble jack stéréo ou par l'adaptateur DIN) est obligatoire : c'est le seul chemin de secours.

---

## 6. En cas de souci

| Symptôme | Cause probable | Solution |
|---|---|---|
| L'écran reste sur `READY TO RECEIVE`, la progression monte quand même | mauvais port, câble pas OUT→IN, câble jack mono (TS) au lieu de stéréo (TRS), ou port USB de l'appareil choisi | choisis le port de **l'interface MIDI** ; vérifie le câble (jack stéréo à 3 contacts) ; en STARTUP MENU l'USB ne marche pas |
| Bloqué sur `RECEIVING…` indéfiniment | un paquet a été perdu | sans danger : éteins/rallume, re-entre en OS UPGRADE, relance avec `--pace 2.0` |
| `aucun port MIDI de sortie détecté` | interface non branchée / non reconnue | branche l'interface avant de lancer ; vérifie qu'elle apparaît dans le système |
| `python-rtmidi` ne s'installe pas | compilateur ou en-têtes manquants | suis le message du script (Xcode sur macOS, ALSA sur Linux, C++ Build Tools sur Windows) |
| `le fichier ne se vérifie pas` | `.syx` corrompu ou mauvaise version | reconstruis-le avec `tools/build.py`, ou re-télécharge l'officiel |

Régler la cadence d'envoi si des paquets se perdent (défaut 1.4) :
```bash
python3 tools/flash.py model-cycles_OS1.13.syx --port "NOM DE TON INTERFACE" --send --pace 2.0
```

---

## 7. Depuis Chrome, sans rien installer (Web MIDI)

Le **[flasher web](https://18nelli18.github.io/Modded-Cycles/flasher/)** fait tout dans le navigateur : il **construit**
l'image modifiée à partir de **ton** OS officiel, puis l'**envoie** par Web MIDI. Il marche sur **Chrome, Edge ou Opera**
sur ordinateur (Web MIDI n'existe pas sur Firefox ni Safari). **Tout reste local** : aucun fichier n'est envoyé à un serveur,
aucune image firmware n'est fournie. La page est en anglais, avec un bouton **FR** (automatique si ton navigateur est en français).

Quatre étapes, de haut en bas :
1. **Choisir** : onglet *Mods* (coche les mods voulus) ou *Official firmware* (renvoie l'OS officiel tel quel, pour revenir
   en arrière ou faire une répétition sans risque).
   - **Audio USB 6 canaux** : une fois coché, deux variantes : garder la mise à jour de l'OS par USB (`6ch-usbup`, recommandé)
     ou la version de référence (`6ch-multiout`) ;
   - **Machine SD VINTAGE** (caisse claire vintage, à la place de SNARE, [note 14](notes/14-machine-sd-vintage.md)).
2. **Déposer l'OS officiel** `model-cycles_OS1.13.syx` : il est reconnu à son empreinte, et le firmware est **construit
   automatiquement** (pas de bouton). La page **exige** le MAIN OS de référence de chaque combinaison (voir [BUILD.md](BUILD.md)),
   sinon elle refuse. Un `.syx` qui n'est pas l'OS officiel est accepté s'il est valide, mais envoyé **tel quel**.
3. **Brancher** : *MIDI interface → MIDI IN* (recommandé, marche toujours, voie de secours : FUNC + allumage, TRIG 4) ou
   *USB cable only* (`CONFIG › UPGRADE`, seulement depuis l'OS officiel ou `6ch-usbup`). La page présélectionne le bon port
   et prévient si tu choisis le port USB du Model:Cycles pour le menu de démarrage.
4. **Flasher** : le bouton indique ce qui manque encore ; pendant l'envoi, progression, temps restant et bouton **Stop** ;
   l'écran reste allumé (garde l'onglet au premier plan). Les réglages rares (marge de vitesse, téléchargement du `.syx`,
   journal) sont dans *Advanced*.

En local : `python3 -m http.server` dans `docs/`, puis `http://localhost:8000/flasher/` (Web MIDI exige `https://` ou `localhost`).

Fidélité vérifiée sans matériel : `tools/webflash_check.sh` compare le **vérificateur** JS à `tools/mtlib/syx.py`,
et `tools/webbuild_check.sh` compare le **constructeur** JS (`docs/flasher/builder.js`) à `tools/build.py` (aPLib + conteneur + HMAC)
à l'octet près, sur une image synthétique. `tools/webflash_smoke.sh` joue le parcours complet de la page dans jsdom
(avec `tools/webflash_smoke.sh model-cycles_OS1.13.syx`, il vérifie aussi les 5 combinaisons sur le vrai OS).
Les tables de patchs de la page viennent de `docs/flasher/tweaks.js`, généré depuis `tweaks/` par `tools/gen_flasher_tweaks.py` (`--check` en CI).

## 8. Méthode manuelle (sans les scripts)

Tu peux aussi flasher avec n'importe quel logiciel SysEx (SysEx Librarian sur macOS, l'outil C6 d'Elektron, etc.) : mets l'appareil en OS UPGRADE et envoie le `.syx` sur le port de l'**interface reliée au MIDI IN**. Nos scripts font exactement ça, en ajoutant la vérification et la cadence adaptée.

Détails techniques du transport et de la récupération : [`notes/06-flash-et-recuperation.md`](notes/06-flash-et-recuperation.md).
