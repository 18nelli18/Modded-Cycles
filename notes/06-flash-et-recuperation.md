# 06 · Build, flash, vérification et récupération (Model:Cycles)

Procédures tirées de ms-multi-output (README, `build.py`, `tools/flash.py`), complétées par ma lecture du code.
⚠️ Flasher un OS modifié se fait **aux risques de l'utilisateur** et peut annuler la garantie. Le mod n'est ni fait ni supporté par Elektron.

---

## 0. Prérequis (checklist)

- [ ] **Le Model:Cycles tourne en OS 1.13.** La table de patchs est figée sur 1.13 ; une autre version = portage à refaire.
      `[À FAIRE]` Relever la version installée, et vérifier si Elektron a publié un OS plus récent que 1.13.
- [ ] **`model-cycles_OS1.13.syx` officiel** (zip sur elektron.se), SHA-256 `44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c`.
      C'est **aussi l'image de secours** : la garder à portée.
- [ ] **Interface MIDI** : sa sortie → **MIDI IN** du M:C (jack TRS 3,5 mm, types A et B acceptés), par câble jack stéréo depuis une sortie TRS
      ou par l'adaptateur DIN fourni ([12](12-flash-par-jack-trs.md)). **Le menu de démarrage ignore l'USB MIDI.** Sans MIDI IN, pas de retour possible.
- [ ] **Sauvegarde** des projets et sons (Elektron Transfer).
- [ ] Alimentation stable ; ne pas toucher à la machine pendant `UPDATING FLASH`.
- [ ] Python ≥ 3.9, compilateur C, venv avec `mido`, `python-rtmidi` (et `numpy` pour l'analyse).

## 1. Construire l'image (`--target cycles`)

```sh
git clone https://github.com/scottmetoyer/ms-multi-output.git
cd ms-multi-output
./setup.sh                                          # clone + compile elektron-firmware-tool dans vendor/
python3 -m venv .venv
.venv/bin/pip install mido python-rtmidi numpy
python3 build.py --target cycles --syx /chemin/model-cycles_OS1.13.syx
```

Sortie attendue (`mc-multi-output.syx`) :
```
  applied 29 patch runs
  patched section 3 matches the tested image
  sha256 9c631bc276baaae52270a8256a0213b3c1e9076f9b192137bd6e06d887fe22f6
  ✅ reproducible build: byte-identical to the tested image
```
**Sans la dernière ligne ✅, ne pas flasher.** Cause probable : la version d'`elektron-firmware-tool` a changé ([05 §3](05-methode-patch.md#3-build-reproductible-modèle-à-suivre)).

## 2. Flasher

1. **Mode OS UPGRADE** : éteindre, maintenir **[FUNC]**, allumer, puis **[TRIG 4]** (« OS UPGRADE »).
   `[À CONFIRMER]` Cette séquence est documentée pour le M:S : vérifier le menu de démarrage dans le manuel du M:C.
2. **Essai à blanc** (liste les ports MIDI et contrôle l'image) :
   ```sh
   .venv/bin/python tools/flash.py mc-multi-output.syx --allow-any-device
   ```
   ⚠️ **Piège n°1** : `flash.py` **refuse toute image dont le device id n'est pas `0x0F` (Samples)**, et ce dès l'essai à blanc.
   Pour le Cycles (`0x11`), **`--allow-any-device` est obligatoire**. Le README ne le signale pas.
3. **Envoi** :
   ```sh
   .venv/bin/python tools/flash.py mc-multi-output.syx --allow-any-device --port "NOM DE L'INTERFACE MIDI" --pace 1.4 --send
   ```
   ⚠️ **Piège n°2** : le garde-fou contre le port USB MIDI de l'appareil ne teste que la chaîne `model:samples`.
   Il **ne reconnaît pas `Elektron Model:Cycles`**. Choisir le port de l'**interface MIDI** reliée au MIDI IN, sinon rien n'est écrit et aucune erreur n'apparaît.
4. **Surveiller l'écran** : `READY TO RECEIVE` doit passer à **`RECEIVING...`** en quelques secondes.
   S'il reste sur `READY TO RECEIVE`, l'image est **ignorée sans erreur** (mauvais conteneur ou mauvais port), même si le compteur monte jusqu'à 100 %.
5. Durée **~6 à 7 min** (≈ 890 ko à 3125 o/s × 1,4). **Ne rien couper pendant `UPDATING FLASH`.** L'appareil redémarre seul.
6. Bloqué sur `RECEIVING...` indéfiniment : un paquet a été perdu. C'est sans danger : éteindre, rallumer, recommencer, et augmenter `--pace` si besoin.
   À 1.0, le buffer de l'interface finit par déborder.

## 3. Vérifier (premier vrai Model:Cycles)

```sh
system_profiler SPAudioDataType | grep -A4 "Model:"      # attendu : Input Channels: 6
```

Plan de test à dérouler **et à consigner** (c'est l'information qui manque au projet amont) :
- [ ] 6 canaux visibles, 48 kHz ; capture de 32 bits (`pcm_s32le`) avec le séquenceur en marche.
- [ ] **Carte des canaux** : muter les pistes une à une, chaque canal doit s'éteindre au bon endroit.
- [ ] `analyse_dupes.py capture.wav` : chaque canal actif doit ressortir `CLEAN`, les canaux mutés `CONSTANT/DC`.
- [ ] **LEVEL / VOLUME+DIST de piste** : est-il appliqué **avant** le point de prélèvement sur le Cycles ? (inconnu, `[À TESTER]`).
      Mesurer aussi la distorsion au-delà de ~70 (dossier §5.1).
- [ ] Les 6 machines (KICK, SNARE, METAL, PERC, TONE, CHORD) sur chaque piste, y compris le **changement de machine par pas** (dossier §4.3).
- [ ] Retrigs rapides, CTRL ALL, changement de pattern, tempo extrême : pas de clic ni de doublon.
- [ ] L'USB MIDI marche toujours (notes et clock) : les jacks MIDI font partie de la config audio.
- [ ] Session longue (30 min et plus), débranchement et rebranchement USB, mise en veille de l'hôte.
- [ ] Windows : FlexASIO (MME, DirectSound, WASAPI partagé) à 48 kHz.
- [ ] Sauvegarde et extinction normales (bouton power) : rien ne doit changer.

Retour à l'auteur : l'auteur demande qu'on **ouvre une issue** sur son dépôt, que ça marche ou non.
C'est une publication, donc **demander l'accord de l'utilisateur avant de poster**.

## 4. Récupération (revenir à l'OS officiel)

1. Éteindre, maintenir **[FUNC]**, allumer, **[TRIG 4]** (OS UPGRADE).
2. Envoyer l'**OS officiel** par le **MIDI IN** :
   ```sh
   .venv/bin/python tools/flash.py model-cycles_OS1.13.syx --allow-any-device --port "NOM DE L'INTERFACE MIDI" --pace 1.4 --send
   ```
- Cela marche **même si le MAIN OS ne démarre plus** : le bootloader est dans un secteur que les mises à jour n'écrivent jamais.
  ms-multi-output l'a utilisé « de nombreuses fois » pendant le développement.
- Tant que le mod est installé, **`CONFIG → UPGRADE` par USB ne fonctionne plus** (descripteurs du bootloader réutilisés comme code).
  La voie MIDI IN du menu de démarrage n'est pas affectée. Reflasher l'OS d'origine rétablit l'upgrade USB.

## 5. Cross-flash (pour mémoire : M:S → Cycles 6 canaux)

- `python3 build.py --target cycles-crossflash --syx model-cycles_OS1.13.syx --container model-samples_OS1.13.syx`
- On garde le conteneur **Samples** et on ne remplace que la section 3 : le bootloader du M:S n'accepte que `0x0F`.
- L'unité s'annonce `Elektron Model:Cycles`. Pour revenir, le secours reste `model-samples_OS1.13.syx`.
  Un post Reddit affirmait qu'il fallait un conteneur Cycles : **c'est faux, testé**.
- ⚠️ Le Cycles OS tourne alors sur des données de projet Samples : comportement de sauvegarde non exploré, **sauvegarder le +Drive avant**.

## 6. Méthode de flash de l'Octatrack (pour mémoire, **ne s'applique pas** au M:C)

L'OT accepte aussi un `.bin` sur la carte CF (format ELUP : XOR à rétroaction et checksum, cf. `octa-bt-pt/tools/make_bin.py`).
Son menu de secours est [FUNC] + allumage, puis **[TRIG 3]**. Les Models n'ont pas de carte CF : **uniquement le SysEx**.
