# 212 — Numéro de séquence SysEx sur 21 bits

Rapport (Model:Samples, 01/11/2026) : le flasher web, méthode classique, s'arrête sur
`Transfer error: MIDIOutput.send: Invalid MIDI message` ; par le menu de démarrage (FUNC + allumage, OS UPGRADE)
avec C6, l'écran reste sur `RECEIVING...` et rien n'est installé.
Correctif : `docs/flasher/builder.js` (`wrap`, `rewrap`, `invalidMessages`), `tools/mtlib/syx.py` (idem),
`docs/flasher/flasher.js` (`sendSysex` refuse un fichier invalide), `tools/flash.py`, `tools/rewrap_syx.py`.
Preuve : `tools/test_sysex_sequence.js` (dont le récepteur du bootstrap transcrit). Adresses : OS 1.13.

## En bref

- Chaque paquet de données porte `7E s2 s1 s0` : un numéro de séquence de **21 bits** en trois octets de 7 bits,
  comme le départ et le nombre de paquets des marqueurs `7F 01` / `7F 02`. `wrap()` écrivait `7E 00 (seq >> 7)
  (seq & 0x7F)`, sans masquer `seq >> 7`.
- Les fichiers d'Elektron partent de la séquence 242 : au paquet 16 142, la séquence atteint 16 384 et l'octet
  du milieu vaut `0x80`, un octet d'état au milieu d'un SysEx. Tous les paquets suivants sont invalides.
- Touchés : **toutes les images publiées de plus de ~16 140 paquets** : Full 2.62 à 2.64, Lite et Optional depuis
  2.56, et leurs versions pour Model:Samples. Full 2.61 (16 052 paquets) passait de justesse.
- Effets : Web MIDI refuse le paquet 16 143 (méthode classique, Model:Cycles comme Model:Samples) ; un outil SysEx
  (C6, SysEx Librarian, `flash.py`) l'envoie, le récepteur perd le fil et attend sans fin. La méthode rapide
  (protocole Transfer) passait : le `.syx` voyage dans des blocs codés sur 7 bits et l'OS le relit en mémoire,
  où `0x80 << 7` redonne par hasard la bonne valeur.
- `[FAIT]` Les trois récepteurs lisent bien 21 bits ; le correctif est donc le bon encodage, pas un contournement.

## 1. Les récepteurs `[FAIT]`

Même fonction de décodage, `(b0 << 14) + (b1 << 7) + b2`, appelée sur les trois octets qui suivent `7E` :

| Récepteur | Décodeur | Appel |
|---|---|---|
| bootstrap Model:Samples (menu de démarrage, MIDI IN) | `0x8000355c` | `0x8000360a`, sur `paquet + 1` (section 2, VA = offset + `0x800003fc`) |
| MAIN OS Model:Cycles (CONFIG › UPGRADE, relecture du `.syx` reçu par Transfer) | `0x40081c5c` | `0x40081ccc`, sur `message + 7` |
| MAIN OS Model:Samples | `0x40080ca8` | même code |

Dans le bootstrap (`0x800035ca`), un paquet hors séquence ou au checksum faux met l'état de réception à 0 et pose
un drapeau d'erreur (`0x80007a04`) qu'aucun code ne relit : l'écran garde `RECEIVING...`, la barre figée. Rien
n'est vérifié ni écrit tant que le dernier paquet n'est pas reçu (`0x80003b36` n'est appelé qu'après), donc la
machine redémarre sur son OS précédent. Tampon de réception en DDR (`0x40000000`), sans limite de taille.

## 1bis. Le checksum couvre l'octet 7 `[FAIT]`

Les récepteurs recalculent le checksum sur les 119 octets `7..125` du message (bootstrap `0x80003622`, OS
`0x40081cda`) : `(dev + Σ ((k + dev) ^ octet[7 + k])) & 0x7F`, `dev` = octet appareil (`0x0C` Cycles, `0x0A`
Samples). La formule de mtlib (octets `8..125`, masque `(V − i) & 0x3F`, base `C0`) lui est égale **tant que
l'octet 7 vaut 0** (20 000 paquets aléatoires sur 20 000 par produit) et ne l'est jamais sinon. Or l'octet 7 est
le haut du numéro de séquence : il passe à 1 au paquet 16 142. Un premier correctif, avec le bon numéro mais
l'ancien checksum, restait bloqué sur `RECEIVING...` (rapport du 01/11/2026, menu de démarrage avec C6, après
16 142 paquets acceptés sur 16 194) ; le récepteur transcrit dans `tools/test_sysex_sequence.js` reproduit cet
arrêt au même paquet.

## 2. Le correctif

- `wrap()` (JS et Python) : `7E` puis `p21(seq)`, et le checksum des récepteurs (§1bis). Un fichier de moins de 16 384 − départ paquets ne change pas
  d'un octet (`s2` vaut 0) : `wrap(unwrap(x)) === x` pour les OS officiels Model:Cycles et Model:Samples 1.13.
- `rewrap(raw)` : même flux, même produit, même séquence de départ, réemballé. Conteneur, MAIN OS et signature
  inchangés. La page l'applique aux images épinglées **après** le contrôle de leur SHA-256 (les fichiers publiés
  restent tels quels, voir §3), et aux fichiers déposés par l'utilisateur ; l'emballage pour Model:Samples passe par
  `wrap()` et sort déjà juste.
- `sendSysex()` refuse un fichier contenant un octet ≥ `0x80` entre `F0` et `F7` avant le premier message ;
  `flash.py --verify` aussi, et propose `tools/rewrap_syx.py`.
- Optional : `recipe.universal_sha256` change (`f1f15bdf…` → `7235c961…`). Réencodé à l'ancienne, le nouveau
  fichier redonne exactement l'ancienne empreinte : seuls les octets de séquence et les checksums de paquet changent.
- Checksum de paquet : voir §1bis ; `devChecksum` (JS) / `device_checksum` (Python) remplacent l'ancienne formule
  dans `wrap`, `unwrap` et `verify`. L'ancienne (`msgChecksum`, `checksum`) reste pour le lecteur Syntakt.

## 3. Ce qui reste à faire

- Republier les images (Full, Lite, Optional) réemballées, avec leurs nouveaux `syxSha256`, quand le propriétaire
  du dépôt le décide. `rewrap` dans la page rend cela facultatif pour le flasher, pas pour les téléchargements
  directs des fichiers.
- `[À FAIRE]` Sur la machine : méthode classique (Model:Cycles) et menu de démarrage (Model:Samples) avec un
  fichier réemballé de plus de 16 142 paquets.
