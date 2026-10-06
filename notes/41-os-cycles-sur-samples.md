# 41 — L'OS Cycles sur un Model:Samples, avec retour par USB

Demande de Maxime (05/10/2026, fil du projet) : « dans le même fonctionnement que pour flasher son Cycles avec le
webflasher, une section qui permet de flasher son Model:Samples avec l'OS du Cycles, en USB, retour en arrière en USB
possible, via l'onglet Samples OS ».
Générateur : `tools/crossflash.py --to samples` (aller) et `--back-samples` (retour) ; portage JS
`MCBuilder.cyclesForSamples` / `MCBuilder.samplesBack` (`docs/flasher/builder.js`).
Preuve : `tools/emu/test_crossflash_samples.py`. Adresses : VA de l'OS 1.13.

## En bref

- **L'aller par USB marche tel quel** : le conteneur officiel du Samples (bootstrap, updater, signature Samples) avec
  le MAIN OS du Cycles passe les deux portes d'une mise à jour USB du Samples, qui ne vérifient que le conteneur et sa
  signature ([15 §3.4bis](15-demandes-reddit.md)).
- **Le retour par USB était impossible** avec l'OS Cycles d'origine : verrou à deux clés, le miroir exact de
  [15 §3.4bis](15-demandes-reddit.md). L'OS Cycles qui tourne n'accepte qu'un fichier signé Cycles, le bootstrap
  Samples n'installe qu'un fichier signé Samples, et un fichier ne porte qu'une signature.
- **Correctif : 32 octets dans le MAIN OS Cycles.** Sa clé de vérification vient d'une constante de 32 octets
  (`0x401296b2`) lue par une seule fonction. On la recalcule pour qu'elle donne la **clé du Samples**. Les deux portes
  exigent alors la même clé, et l'OS Samples officiel, inchangé, repasse par USB.
- La clé n'est jamais dans le dépôt : la page et le script la dérivent du `.syx` officiel du Samples de l'utilisateur,
  comme `mtlib` le fait pour toute signature.
- `[FAIT en émulation]` sur le vrai code de vérification des deux OS ; **pas encore essayé sur un vrai Model:Samples**.
  Le menu de démarrage du Samples n'est jamais touché : par le MIDI IN, il reste la voie de secours.

## 1. Les deux portes d'une mise à jour USB, sur un Model:Samples

Rappel de [15 §3.4bis](15-demandes-reddit.md) : l'OS qui tourne reçoit le `.syx` (SysEx de `CONFIG › UPGRADE` ou
protocole de Transfer, [37](37-flash-rapide-usb.md)), vérifie le conteneur, le copie en staging (flash `0x20000`) et
redémarre ; le **bootstrap** re-vérifie alors le staging avec **sa** clé et l'installe.

| Situation | Porte 1 : l'OS qui tourne | Porte 2 : le bootstrap | Fichier qui passe les deux |
|---|---|---|---|
| Samples d'origine, aller | OS Samples, clé Samples | Samples, clé Samples | conteneur Samples + MAIN OS Cycles (`--to samples`) |
| Samples sous OS Cycles **d'origine**, retour | OS Cycles, **clé Cycles** | Samples, **clé Samples** | **aucun** |
| Samples sous OS Cycles **de la page**, retour | OS Cycles, **clé Samples** (32 octets changés) | Samples, clé Samples | l'OS Samples officiel, transport Cycles (`--back-samples`) |

## 2. La vérification dans l'OS Cycles `[FAIT]`

`0x4005a0e4 (a2 = [longueur][checksum][conteneur])` est appelée par les trois chemins de mise à jour du MAIN OS :

| Appelant | Rôle |
|---|---|
| `0x400860a0` | réception SysEx (`CONFIG › UPGRADE`) |
| `0x4006ce92` | protocole d'Elektron Transfer (le `.syx` reçu en mémoire, extrait par `0x400813c2`) |
| `0x40092314` | écriture en staging (`0x40092304` : re-vérifie, efface et écrit à partir de `0x20000`) |

Elle renvoie 1 si tout va bien, sinon :

| Étape | Fonction | Échec |
|---|---|---|
| checksum de contenu (somme des mots `(i+1) ^ w`) | `0x40081e26` | 3 |
| HMAC-SHA256 du conteneur | `0x40052750` | 4 |
| alimentation suffisante (broches, tension) | `0x400530ca` | 5 |

**Rien n'y dépend du modèle, sauf la clé.** Aucun contrôle de l'en-tête du conteneur (octet `0x04`), du nom ou des
sections : un conteneur Samples bien signé passerait.

`0x40052750 (données, longueur)` dérive la clé exactement comme `mtlib.container.find_key` :

```
40052758  pea 0xc ; pea 0x40129650        copie "REVERB SEND\0" (12 o) sur la pile
40052788  move.b (a0)+,-(a1)              la même chaîne à l'envers
40052792  … jsr 0x400786fc (x2)           SHA-256 des 11 octets, à l'endroit et à l'envers
400527c0  lea 0x401296b2,a1               C : 32 octets
400527c6  … eor …                         clé = SHA(s) ^ SHA(s inversée) ^ C
400527fa  jsr 0x400785b8                  HMAC-SHA256(clé, données[0 .. longueur-32])
4005280a  …                               comparaison avec les 32 derniers octets
```

- `"REVERB SEND"` (`0x40129650`) est aussi un **nom de paramètre affiché** (deux références : `0x4005275e` et
  `0x4010a924`, la table des noms) : on n'y touche pas.
- `C` (`0x401296b2`) n'a **qu'une** référence dans tout le MAIN OS : `0x400527c2`. La changer ne change que la clé.
- Contrôle : avec le `C` d'origine, la formule redonne la clé que `mtlib` tire du bootstrap Cycles
  (`8c0e4553…9a0b98bd`) ; le script refuse de continuer sinon.

## 3. Le correctif

```
C' = cléSamples ^ SHA-256("REVERB SEND") ^ SHA-256("DNES BREVER")
```

écrit à la place de `C` (`0x401296b2`, 32 octets). `cléSamples` est celle que `mtlib` tire du `.syx` officiel du
Samples (son bootstrap) ; elle est aussi celle que dérive le MAIN OS Samples ([15 §3.4](15-demandes-reddit.md),
`"DELAY TIME"` + `0x4012a37e`).

- Aucune place libre utilisée, aucun code ajouté : 32 octets de données.
- La section 3 est recompressée avec `aplib.repack` (seuls les octets touchés deviennent des littéraux), relue et
  comparée.
- Ce n'est **pas** un tweak JSON : ses octets dépendent de la clé du Samples, qu'on ne versionne pas (règle 1 du
  dépôt). Le script et la page la calculent depuis le fichier de l'utilisateur.

Effets de bord, voulus :
- l'OS Cycles de la page **refuse** l'OS Cycles officiel et tout firmware Model:Cycles avec mods (signés Cycles),
  y compris une mise à jour proposée par Elektron Transfer. Sans le correctif, la porte 1 l'accepterait et la porte 2
  le rejetterait : même résultat, rien d'écrit, mais après un redémarrage trompeur ;
- il **accepte** `--to samples` (signé Samples) : une future version se met à jour par USB, à condition de l'emballer
  dans le transport Cycles (§4) ; la page ne le propose pas encore.

## 4. Le fichier de retour : l'OS Samples officiel dans le transport Cycles

L'OS Cycles ne route la mise à jour que pour l'identifiant produit `0x11` et l'octet appareil `0x0C`, base des sommes
de contrôle des paquets (miroir des contrôles 1 et 2 de [15 §3.4](15-demandes-reddit.md)). `--back-samples` reprend
le flux décodé de l'OS Samples officiel **tel quel** (préambule, conteneur, signature Samples) et le réemballe avec
`syx.wrap(…, 0x11, séquence de départ du Cycles)` : le même emballage que tous les firmwares Model:Cycles que la page
envoie déjà.

Une fois reçu, c'est octet pour octet le conteneur officiel du Samples : la porte 2 est celle d'une mise à jour
officielle du Model:Samples.

## 5. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_crossflash_samples.py` fait tourner `0x4005a0e4` (Cycles) et son équivalent dans l'OS Samples (trouvé
par son appel au HMAC `0x40051728`), vérification d'alimentation court-circuitée :

| Fichier | OS Samples d'origine | OS Cycles d'origine | OS Cycles de la page |
|---|---|---|---|
| OS Samples officiel | accepte | — | — |
| `--to samples` (aller) | **accepte** | refuse (4) | accepte |
| `--back-samples` (retour) | — | **refuse (4)** : le verrou | **accepte** |
| OS Cycles officiel | — | accepte | **refuse (4)** |
| retour avec un octet changé | — | — | refuse |

Et en plus :
- `--to samples` : sections 2, 4, 5 et en-tête du conteneur identiques à l'officiel Samples, HMAC valide avec la clé
  du bootstrap Samples (porte 2) ;
- son MAIN OS ne diffère de l'OS Cycles officiel que dans les 32 octets de `0x401296b2` ;
- `--back-samples` décodé = flux de l'OS Samples officiel, en-tête SysEx `F0 00 20 3C 11 00 7F 01 0C`.

Ce qui n'est **pas** émulé : la réception SysEx/Transfer elle-même (même transport que les firmwares Cycles déjà
envoyés par la page, testés sur la machine) et le bootstrap Samples (la porte 2 voit des conteneurs signés avec sa
propre clé, comme une mise à jour officielle).

Empreintes (SHA-256) :

| Fichier | SHA-256 |
|---|---|
| `model-cycles_OS1.13_for-model-samples.syx` (`--to samples`) | `c06c23f31e50fac6ad40cd0f633acd4a7da4f63c929dff563dae887b93105dd4` |
| son MAIN OS | `b6fbc48f7d7d07cecae3859e07270fa2298f393e8afa2643144bdb4efc317aad` |
| `model-samples_OS1.13_back-from-cycles-os.syx` (`--back-samples`) | `d63ce13dd1a5039d11b60d3f69d4e88e9d0f56fb2e7350c105ec641d32083680` |

## 6. Dans le flasher

Onglet *Samples OS*, trois choix : *Model:Cycles → OS Samples* (l'existant, [15 §3.2](15-demandes-reddit.md)),
*Model:Samples → OS Cycles* et *Model:Samples : retour à son OS*, ces deux-là étiquetés **expérimental**. Les deux
fichiers officiels sont demandés (Cycles puis Samples). La page refuse un résultat dont le SHA-256 diffère de la
référence (`REF_CYCLES_ON_SAMPLES`, `REF_SAMPLES_BACK`).

Avec la méthode rapide, la page demande qui répond : l'aller ne part que vers une machine qui répond Model:Samples, le
retour que vers une machine qui répond Model:Cycles. Cas sans danger qu'elle ne peut pas distinguer :
- l'aller envoyé à un **Model:Cycles sous OS Samples** (il répond Model:Samples) : porte 1 acceptée, porte 2
  (bootstrap Cycles) refusée, l'OS Samples reste ([15 §3.4bis](15-demandes-reddit.md), vu sur la machine le 29/09) ;
- le retour envoyé à un **vrai Model:Cycles** : refusé à la porte 1 (signature).

## 7. Ce qui reste à vérifier sur la machine `[À FAIRE]`

Sur un vrai Model:Samples (Maxime) :
1. sauvegarde des samples et projets avec Transfer ;
2. *Model:Samples → OS Cycles*, méthode rapide : la machine redémarre en Model:Cycles (Transfer la voit Model:Cycles),
   les machines du Cycles jouent, le panneau répond ;
3. ce que l'OS Cycles fait des données du Samples (projets, +Drive) ;
4. *Model:Samples : retour à son OS*, méthode rapide : retour au Model:Samples, samples et projets présents ;
5. en secours si 4 échoue : menu de démarrage du Samples et l'OS Samples officiel par le MIDI IN.
