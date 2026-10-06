# 41 — Fondations portables pour les réglages et le chaînage des LFO

Demande de Lachlan, 06/10/2026 : préparer une contribution de code originale,
vérifiable sur l'hôte, pour les trois LFO supplémentaires par piste. L'objectif
final reste quatre LFO complets : toutes les ondes et destinations d'origine,
synchronisation, reset, Fade, Start Phase, édition et persistance.
Sources : `tools/lfo_foundation/` ; test : `tools/test_lfo_foundation.py`.
Cette contribution n'alloue aucune place dans l'OS et ne propose aucun tweak.

## En bref

[FAIT sur l'hôte] Le noyau C garde des réglages clairsemés, applique les edits et
copies atomiquement, écrit et relit une section LF4S liée à un conteneur opaque.
Le contrat Python vérifie que chaque LFO supplémentaire reçoit la publication
précédente et republie seulement sa destination. Le test joint relit les réglages
des trois instances puis vérifie ce chaînage sur six pistes.

Les sorties de modulation sont synthétiques. Il n'y a pas de calcul d'onde, de
DSP original exécuté, de menu, d'écriture média ou de résultat matériel dans
ce test. Cette fondation n'est pas une implémentation installée de quatre LFO.

## 1. Origine du code

Les algorithmes viennent du travail original de lachlanfysh :

| Composant | Source d'origine | Commit d'introduction |
| --- | --- | --- |
| Contrat de publication et six tests | `lfo_four_publication_contract.py`, `test_lfo_four_publication_contract.py` | `51a67fc3d1f24468f67a2bf09a0e51018c8d025b` |
| Table clairsemée, codec LF4S, validation et copie | C embarqué dans `lfo_four_sound_extension.py`, tests hôte de `test_lfo_four_sound_extension.py` | `9a97aaa60df2e20981ee3949c4398f37efba61ff` |

L'extraction conserve le format LF4S v1 et les invariants utiles, en donnant aux
algorithmes une API C11 explicite. La table utilise une recherche binaire. Les
lots et copies travaillent dans une table temporaire puis publient une seule
fois ; la copie lit toujours la source non modifiée, même en cas de chevauchement.

Les adaptateurs de propriétaire, adresses RAM, copie du conteneur d'origine,
valeurs par défaut embarquées et hooks de redémarrage ne sont pas repris. Les
tests facultatifs dans l'émulateur et leurs dépendances ne sont pas repris.
Les dimensions relatives du contrat de publication sont des faits d'interface,
pas des instructions de l'OS. Les fixtures sont créées dans le test.

Lachlan a approuvé MIT pour les nouveaux fichiers originaux et uniquement la
nouvelle ligne 41 de l'index. Le [périmètre explicite et la notice](../tools/lfo_foundation/LICENSE)
ne donnent aucune licence globale au dépôt ni aux autres fichiers.

## 2. API de réglages

Chaque clé logique représente un Sound, avec 48 octets de configuration : trois
enregistrements de 16 octets pour les instances supplémentaires. L'application
fournit le domaine de clés, la capacité de lignes non standard, les 48 octets de
défauts, une borne pour chaque mot big-endian et, éventuellement, un allocateur.
Le domaine accepte 1 à 65 535 clés ; les tests exercent notamment 6 720 clés.

`lf4s_get` matérialise les défauts pour une clé absente. `lf4s_set` édite une clé ;
`lf4s_apply` applique un petit lot avec clés uniques. Les lignes devenues standard
sont supprimées avant les insertions, pour réutiliser la capacité libérée.
`lf4s_copy` remplace une plage entre espaces logiques, avec les mêmes défauts et
la même borne, y compris si la source et la cible se chevauchent.

Sur échec de validation, capacité ou allocation, l'état publié reste identique.
`lf4s_reset` est une migration explicite sans extension. Une section absente ou
tronquée passée à `lf4s_load` est une erreur ; elle ne remet pas silencieusement
les réglages à zéro.

L'appelant doit sérialiser les accès et conserver les tampons empruntés stables
et disjoints pendant l'appel. Les opérations allouent et peuvent déplacer des
lignes ; elles ne sont pas destinées à l'interruption audio. La borne commune
des mots n'est pas une validation complète des champs WAV, DST, MUL, etc.
Cette validation métier appartient au futur adaptateur.

## 3. Format LF4S v1

Tous les entiers du fichier sont big-endian. Aucune structure C brute n'est
écrite. Taille totale : `28 + 52 * nombre_de_lignes` octets.

| Octet | Champ |
| ---: | --- |
| 0 | Magic `LF4S` (4 octets) |
| 4 | Version 1, u16 |
| 6 | Taille de ligne 52, u16 |
| 8 | Taille totale, u32 |
| 12 | Nombre de clés logiques, u16 |
| 14 | Nombre de lignes, u16 |
| 16 | Taille du conteneur de base opaque, u32 |
| 20 | CRC32 du conteneur de base, u32 |
| 24 | Lignes : clé u16, réservé u16 nul, 48 octets XOR des défauts |
| fin − 4 | CRC32 de l'en-tête et des lignes, u32 |

Les clés sont strictement croissantes. Doublons, clés hors domaine, réservé non
nul, ligne entièrement standard, valeur hors borne, taille ou CRC erronés sont
refusés avant allocation et publication. Une sortie trop courte laisse son
contenu et la longueur retournée inchangés.

Les défauts et la borne ne sont pas enregistrés dans LF4S v1 : l'application doit
maintenir le même schéma entre save et load. Cette contribution conserve la
version d'origine, elle ne prétend pas convertir des schémas incompatibles.
Le CRC associe la section aux octets du conteneur ; il n'authentifie pas le fichier.
`lf4s_save` produit une section en mémoire ; il n'effectue aucune écriture durable.

## 4. Contrat de publication

Le tampon fourni par l'appelant contient 476 octets. Sur chaque piste, les
16 octets de contrôles commencent à `16 + 66 * piste`. La copie privée reprend
tout le tampon déjà publié et remplace uniquement ces contrôles.

Le contrat accepte NONE (0) et les 13 coordonnées de destination (10 à 22).
Le mot sélectionné est à `14 + 66 * piste + 2 * destination`. NONE et DEPTH
neutre (`0x4000`) conservent le tampon vivant ; les autres cas copient seulement
ce mot depuis la sortie fournie. Un clamp dans une sortie privée à profondeur
neutre ne doit donc pas affecter les paramètres vivants.

`compare_snapshot` refuse une copie privée périmée, la perte d'un octet sans
rapport ou des contrôles incorrects. Il ne valide ni les valeurs numériques de
modulation ni le calcul de phase. Un futur test sur le code original devra
fournir ses propres sorties et comparer les captures complètes à ce contrat.

## 5. Preuve indépendante sur l'hôte

Depuis la racine du dépôt :

```sh
python3 tools/test_lfo_foundation.py
```

Le script utilise la bibliothèque standard Python, `ctypes` et le compilateur
**natif** `cc`. Il compile seulement `settings.c` en C11 dans un répertoire
temporaire, avec `-Wall -Wextra -Werror -pedantic -O2`, puis supprime le résultat.
Aucun argument ou fichier de firmware n'est accepté. Pas de dépendance à
Unicorn, QEMU ou à un compilateur croisé.

[FAIT sur l'hôte, 06/10/2026] 24 méthodes passent, zéro skip : 15 tests de
réglages, 7 de publication et 2 de composition. Python 3.9.6, Apple clang 21.0.0,
hôte arm64 Darwin. Les sous-cas ne sont pas comptés comme des LFO complets.

Le codec est comparé à un encodeur Python indépendant avec `struct` et `zlib` ;
les 6 720 clés sont relues et la section réécrite doit être identique. Les tests
exercent les défauts non nuls, l'ordre, les CRC, les fichiers malformés, les
copies Sound/plage/Projet, les deux sens de chevauchement, les échecs de
capacité, les échecs d'allocation et la libération des tables temporaires.
Les tests joints emploient les trois enregistrements restaurés par piste et des
marqueurs synthétiques successifs, avec refus d'une copie privée périmée.

## 6. Intégration restante

[À FAIRE] Définir les identités canoniques Sound/Projet et les opérations qui
remplacent ces identités ; l'API n'infère aucune identité d'une adresse ou piste.
L'éditeur doit valider les champs, convertir les défauts, appliquer les edits
au stockage puis matérialiser une copie stable pour le rendu.

[À FAIRE] Définir un conteneur versionné unique contenant la base et LF4S,
le traitement des anciens projets, les limites, les erreurs et la publication
durable. Coordonner le stockage et l'espace des menus avec le travail Chord Keys
de PR 46 s'il est intégré. Ne pas ajouter aveuglément une seconde queue de fichier.

[À FAIRE] Relier l'ordre LFO1 puis LFO2–4 au vrai rendu, avec états de phase/RNG
séparés, sync/reset/Fade/Start Phase, toutes les ondes/destinations, paramètres
verrouillés, enregistrement, changement de profil et cycle de vie des objets.

[À FAIRE] Prouver l'intégration sur l'OS officiel, seule et avec les autres mods,
la concurrence, les échecs de stockage, les budgets RAM/pile/temps et le démarrage.
Les essais physiques de Maxime devront vérifier commandes/OLED, audio,
transport/MIDI, sauvegarde, copie et rechargement après extinction. Aucun
résultat d'émulation ou de matériel n'est déclaré par cette contribution.
