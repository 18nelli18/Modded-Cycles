# 53 — Générer une séquence dans la gamme choisie

Demande d'aveycole dans Codex, le 10/10/2026 : un raccourci qui pose des trigs et
choisit des notes dans la gamme de Model-TG. Dépôt cible :
[aveycole/modded-cycles](https://github.com/aveycole/modded-cycles).
Générateur : `tools/gen_seq_gen.py`, sources : `tools/machines/seq_gen/`.
Preuves : `tools/emu/test_seq_gen*.py`. Adresses : VA de l'OS 1.13.

## Réponse courte

[FAIT en émulation] Le prototype ouvre une page avec **SETTINGS + PAGE**, génère
les notes et trigs de la piste sélectionnée et sait annuler la dernière génération.
Les modifications passent par les notifications de l'OS jusqu'à sa copie au
format séquenceur. Les deux bases `model-tg` et `model-tg-st` sont couvertes.

[À FAIRE] Démarrage complet, présentation réelle de la page et lecture audio de
bout en bout, puis essai matériel. **Prototype hors flasher**, aucun firmware
construit ni publié. Une preuve partielle n'est pas un résultat matériel.

## 1. Commandes et comportement

Tourner DATA sélectionne une des sept lignes. Appuyer sur DATA entre dans
l'édition d'un champ ; tourner change la valeur ; appuyer termine l'édition.
Les deux dernières lignes déclenchent immédiatement Generate ou Undo.

| Ligne | Valeurs |
|---|---|
| Scale | CHROM, MAJ, MIN, DOR, PENTA (pentatonique majeure) |
| Root | C à B |
| Low note / High note | Numéros MIDI 0 à 127, bornes incluses |
| Density % | Probabilité de poser un trig par pas, 0 à 100 |
| Generate | Remplace les trigs de notes dans la longueur active de la piste |
| Undo | Restaure l'état précédant la dernière génération, tant que la page reste ouverte |

[FAIT] Les champs Scale et Root utilisent les variables partagées de Model-TG ;
ce ne sont pas de nouveaux réglages par piste. Les bornes et la densité restent
en mémoire jusqu'au redémarrage. Le défaut est 48–72, densité 50 %.

[FAIT] Generate et Undo refusent le transport actif. Un intervalle sans note
permise refuse Generate. Un refus affiche « Check range/stop ». Aucun réglage
n'est sauvegardé dans un octet présumé libre du pattern.

[FAIT] La page consomme les touches de jeu et de transport. BACK, SETTINGS,
PAGE, TRACK ou PATTERN ferment la page sur un nouvel appui. Undo disparaît à la
fermeture et refuse de restaurer une autre piste. Une nouvelle génération
remplace la sauvegarde précédente. Il s'agit d'un Undo à un niveau.

## 2. Raccourci et accroche

Le relevé porte sur Model-TG épinglé au commit
`70b39dd6787770ebefc7a2d78dea1678ec012679` et les documents upstream au commit
`9225c7a36208ecba3eca3bc4ab205f8e67a46373`.
Le [registre upstream](https://github.com/18nelli18/Modded-Cycles/blob/9225c7a36208ecba3eca3bc4ab205f8e67a46373/tweaks/model-cycles_OS1.13/REGISTRY.md)
recense la mémoire et les accroches, pas une table exhaustive de raccourcis.

| Combinaison existante | Affectation relevée |
|---|---|
| FUNC + PAGE | Menu SCALE / Scale Lock |
| FUNC + RETRIG | Retrig et arpégiateur |
| SETTINGS + MACHINES | Mode de lecture |
| SETTINGS + PUNCH | Options Model-TG |
| SETTINGS + REC | Rééchantillonnage |
| SETTINGS + RETRIG | Effets master / repeat |
| SETTINGS + BACK | Arrêt des effets |
| SETTINGS + trig | Slide |
| Trig maintenu + PAGE | Écoute du pas |

[FAIT] Aucun raccourci dédié SETTINGS + PAGE trouvé dans ces sources. Le nouveau
lecteur rend la priorité à FUNC + PAGE et aux pages Model-TG actives (menu,
retrig, slices). Les autres événements sont transmis au lecteur original.

| Adresse | Rôle |
|---|---|
| `0x4007240c` | Getter de code touche, déjà détourné par Model-TG |
| `0x40072434` | Événement de clic DATA |
| `0x400724a0` | Nouvel appui pour fermer |
| `0x400a22b0` | Constructeur OS de la page MACHINES |
| `0x40117918` | Groupe vtable copié, 176 octets |
| `0x4007700e` | Présentation de page |
| `0x400f43ca` / `0x400f4486` | Destructeurs OS |

[FAIT] Le tweak exige Model-TG : son `old` à l'accroche est le saut installé par
cette base, et son détour chaîne vers le symbole `key_hook` du build épinglé.
Les adresses des variables TG viennent de l'ELF, jamais d'une copie manuelle.
L'événement utilise +8 pour l'horodatage, +12 pour le code, +16 pour les flags.
Le code peut être lu plusieurs fois : pointeur et horodatage rendent l'ouverture
idempotente, même quand le tampon est réutilisé et les touches relâchées dans
l'ordre inverse.

## 3. Écriture et synchronisation de piste

| Adresse / décalage | Rôle |
|---|---|
| `0x400cf866` → `0x4000f23e` | Objet de piste courant |
| `0x40016402` | Longueur active de piste |
| vtable +40 | Getter des données brutes |
| données +0..127 | 64 mots de drapeaux de pas |
| données +580..643 | Notes (255 = héritée) |
| données +713 | Longueur, mot non aligné |
| `0x40016642` | Setter OS de note, événement `0x400ff59c` |
| `0x4001908a` → `0x400d72be` → `0x400180d6` | Notification de piste éditable et synchronisation |
| `0x400156e6` → `0x4005b642` | Fermeture différée et conversion vers le format séquenceur |

[FAIT] Une génération conserve une copie des 722 octets de piste dans la page.
Un pas actif pose les bits 0 et 9 et retire le bit 1 (trigless). Un silence
retire seulement le bit 0 ; les autres flags et les données de p-lock restent.
Le stockage externe de p-locks n'est pas effacé. Les conditions et le retrig
existants peuvent donc encore influencer les nouveaux trigs.

[FAIT] Ne pas appeler le setter de flags pour effacer un trig : son chemin de
suppression réinitialise aussi les réglages de pas. Le prototype écrit les
flags puis appelle le setter de note, qui émet la même classe de notification.
Undo restaure les 722 octets puis notifie les pas actifs.

[FAIT en émulation] Avec la vraie vtable `0x400ff894`, les vraies notifications,
RTTI et masques 64 bits, les fermetures générées appellent la conversion OS.
Les flags arrivent au même décalage, les notes au décalage +128 du format
séquenceur. Le résultat est identique à une conversion complète stock ; Undo
rétablit exactement les deux copies. L'ordonnanceur est simulé : les fermetures
sont copiées puis exécutées après la notification, pas remplacées par une
conversion Python.

[À FAIRE] Exécuter la véritable file de tâches et la lecture audio ; vérifier
sur matériel les p-locks, conditions, enregistrement/sauvegarde et changements
externes pendant la page. Le contrôle « arrêté » n'est pas une transaction qui
bloque un Start MIDI concurrent.

## 4. Algorithme

[FAIT] Xorshift32 déterministe, état de 32 bits ; zéro est remplacé par une graine
non nulle. On construit la liste des notes autorisées dans les bornes, puis on
choisit une note de cette liste pour chaque trig. Aucune seconde quantification
Scale Lock n'est appliquée aux notes écrites. Longueur 1 à 64, densité 0 à 100.
Les entrées invalides ne changent ni la sortie ni la graine.

Masques chromatiques relatifs à la fondamentale : `fff`, `ab5`, `5ad`, `6ad`,
`295` (chromatique, majeure, mineure, dorien, pentatonique majeure).

## 5. Place réservée par le prototype

[FAIT] Treize masques 34×34 de 272 octets sont redirigés vers leur copie
identique gardée `0x4016bfc8`. Chaque contenu et son unique référence alignée
sont vérifiés sur l'OS officiel. Le linker refuse tout dépassement de masque ou
section non placée. Le code, les tables et l'état statique occupent 3 093 octets.

| Masque | Référence constructeur |
|---|---|
| `0x4016f8c8` | `0x400b0b3c` |
| `0x40173848` | `0x400b0350` |
| `0x401780a8` | `0x400af946` |
| `0x401784e8` | `0x400af832` |
| `0x401835b8` | `0x400adedc` |
| `0x40184df8` | `0x400adbc8` |
| `0x40185308` | `0x400adb8c` |
| `0x40185f48` | `0x400ad9c4` |
| `0x40186238` | `0x400ad988` |
| `0x40189618` | `0x400ad364` |
| `0x4018af88` | `0x400ad18a` |
| `0x4018b1a8` | `0x400ad16e` |
| `0x4018ff64` | `0x400ac7fc` |

Le masque `0x40192ba4` du même groupe reste libre. La page est allouée sur
1 280 octets : objet OS de 208 octets, sauvegarde de 722 octets, sortie de
64 notes, marge. Le constructeur et les deux destructeurs réels passent en
émulation ; allocation et présentation sont simulées.

[FAIT] Les variantes se déclarent incompatibles entre elles. Pas de charge
utile supplémentaire, pas de modification du bootstrap, de l'USB ou de l'audio
ISR. Audit des écritures avec le fork et ces branches upstream :

- `claude/chord-keys-flasher-ozqjas` : `e96f5c5fcb1635e82354d92e86bf775abd8a1f2e`
- `claude/djd-oz-mods-0vgnze` : `2bfd4616b407bbabcb2204775ef1c58973c52a05`
- `claude/headphone-cue-k48r6s` : `ce8c1ac0791bd7326de84fed0bda7ec503bdbed3`
- `claude/discord-filter-439loo` : `bd5182bb933a857b06b89fb83df9b83c2f6c545e`

Aucun nouveau conflit introduit. Le vérificateur relève séparément 62 erreurs
préexistantes d'ensembles MACRO/Syntakt trop grands dans les sources réunies ;
ce n'est pas un audit global entièrement vert. Aucun de ces problèmes ne vient
du prototype, qui n'ajoute aucune charge utile.

## 6. Reproduire

Préparer le Model-TG épinglé et GNU binutils m68k (assemblage `-march=cfv4e`,
version utilisée 2.43), puis :

```sh
CROSS=m68k-elf- python3 ../model-tg/build.py --assemble-only
python3 tools/gen_seq_gen.py --cycles firmware/model-cycles_OS1.13.syx --model-tg ../model-tg --cross m68k-elf-
python3 tools/gen_seq_gen.py --cycles firmware/model-cycles_OS1.13.syx --model-tg ../model-tg --cross m68k-elf- --check
M68K_CROSS=m68k-elf- python3 tools/emu/test_seq_gen.py
python3 tools/emu/test_seq_gen_key.py --cycles firmware/model-cycles_OS1.13.syx --model-tg ../model-tg --cross m68k-elf-
python3 tools/emu/test_seq_gen_track.py --cycles firmware/model-cycles_OS1.13.syx --cross m68k-elf-
python3 tools/emu/test_seq_gen_menu.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/emu/test_seq_gen_sync.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/emu/test_seq_gen_space.py --upstream ../upstream-cycles --git 9225c7a36208ecba3eca3bc4ab205f8e67a46373 --git e96f5c5fcb1635e82354d92e86bf775abd8a1f2e --git 2bfd4616b407bbabcb2204775ef1c58973c52a05 --git ce8c1ac0791bd7326de84fed0bda7ec503bdbed3 --git bd5182bb933a857b06b89fb83df9b83c2f6c545e
```

Le build Model-TG s'exécute depuis son propre dépôt. Les JSON du prototype
restent dans `build/seq_gen/` (ignoré), hors catalogue et hors site. Aucun octet
de firmware officiel n'est ajouté aux sources versionnées.

## 7. Résultats et limites

| Preuve | Résultat observé |
|---|---|
| Algorithme | 8 772 cas, cinq gammes, douze fondamentales, bornes, graine zéro, répétabilité, registres/pile/canaris |
| Raccourci | Lectures répétées, réutilisation de tampon, deux ordres de relâchement, priorité Model-TG, autres touches identiques |
| Écriture | 60 pistes aléatoires, 722 octets restaurés, vrais getter/setter OS, transport et note invalide refusés |
| Menu | Deux variantes, sept lignes, encodeur, actions, limites notes/densité, autre piste, réouverture, allocation refusée |
| Durée de vie | Vrais constructeur/destructeur de page, observateurs/fermetures, destruction puis réouverture |
| Synchronisation | 18 cas (longueurs 1/16/64, densités 0/35/100), vrais flags et notes copiés, Undo exact côté séquenceur |
| Générateur | 13 masques/références, SHA stock, chaînage Model-TG, tailles des sections, --check |

[À FAIRE] Intégration de démarrage et présentation réelle, vérification visuelle
sur écran, lecture audio complète et essai matériel. Après ces preuves,
intégration expérimentale au catalogue avec provenance et guide bilingue, puis
PR brouillon ; aucun statut « tested » sans retour matériel.

Crédit : construction de page adaptée de Model-TG, TinyGregAudio, MIT,
`LICENSE-Model-TG` déjà présent dans `tweaks/model-cycles_OS1.13/`.

## 8. Flasher de test demandé par aveycole (10/10/2026)

L'utilisateur demande explicitement : « Add it to a test flasher with all existing
mods ». Le prototype est donc proposé dans `docs/flasher-test/`, toujours
**expérimental et non testé sur matériel**. Le catalogue et le flasher de
production restent inchangés.

Base actualisée : `a956de9bc523e560d1362e75bbf8f43b28bd26e8`. Tous les mods
proposés par cette production sont repris, dont les nouveaux mods d'affichage,
le navigateur multiligne et MACRO avec les moteurs Syntakt. Le test charge le
catalogue de production puis ajoute les deux tweaks `49-scale-gen*.json`.
Le générateur de page `tools/gen_test_flasher.py` recalcule les empreintes des
mods et des combinaisons depuis les OS officiels locaux. Il réutilise seulement
le relevé des références des caves, filtré par combinaison ; les contrôles des
références neutralisées et des octets attendus restent exécutés.

La carte exige Model-TG et prend `scale-gen-st` avec MACRO ou Syntakt. Le
générateur est indépendant de la machine de la piste : il écrit ses trigs et
notes. Le résultat musical dépend de la machine (accordage des percussions,
mode de lecture du Sampler). Aucun résultat matériel n'est déduit de cela.

`tools/check_overlaps.py` passe maintenant sur le catalogue actualisé : 154
tweaks, 16 303 écritures, 134 ensembles de charges utiles. Les anciens problèmes
de taille MACRO/Syntakt du relevé initial sont corrigés dans cette nouvelle base.
Les preuves UI et séquenceur sont rejouées avec cette base. Les contrôles Web
vérifient catalogue complet, dépendance, variante combinée, textes EN/FR,
construction depuis les fichiers officiels et refus d'une empreinte modifiée.

Reproduire le flasher de test (après `gen_seq_gen.py`) :

```sh
python3 tools/gen_test_flasher.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx
python3 tools/gen_test_flasher.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx --check
NODE_PATH=/chemin/vers/jsdom/node_modules node tools/webflash_seq_gen_check.js firmware/model-cycles_OS1.13.syx firmware/Syntakt_OS1.42.syx
```

Les fichiers officiels restent ignorés ; aucune image firmware n'est distribuée.

## 9. Testé sur la machine (10/10/2026)

AveyCole rapporte : « Tested on real hardware, it works, go ahead and add it to my main ». Le générateur du flasher de test fonctionne sur son Model:Cycles. Les options exactes installées et les machines essayées ne sont pas précisées ; ce retour ne prouve pas chaque combinaison. À sa demande, promotion dans le flasher principal et statut `tested`, sans changement des octets du firmware.
