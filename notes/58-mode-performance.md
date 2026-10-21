# 58 - Quinze macros de performance par motif

Contribution source anonyme demandee le 18/10/2026 : quinze commandes de performance a quatre destinations, avec montants par motif, sauvegardes et copier/effacer/coller. Sources `tools/machines/performance15/`, constructeur `tools/gen_performance15.py`, preuve `tools/emu/test_performance15.py`, [guide bilingue](../docs/guide/performance-mode.md). Adresses : VA de l'OS 1.13.

## En bref

[FAIT] Le code reprend le prototype autonome v31 : FUNC + GATE ouvre PERF ; LEVEL/DATA choisit une macro et son clic ouvre SET. Les quinze potentiometres suivent le panneau. Chaque macro porte quatre destinations piste/FX et un montant0-127. FUNC + RECORD copie toute la macro, FUNC + PLAY l'efface, FUNC + STOP la colle.

[FAIT] Cette contribution reste **source autonome et experimentale**. Aucun JSON n'est installe dans le catalogue des tweaks et aucune carte n'est ajoutee au flasheur. `tools/build.py --all` ne l'inclut donc pas. Aucun resultat du mainteneur n'est suppose : le retour positif sur le prototype autonome est un retour independant, pas la validation materielle de ce depot.

[FAIT] Les sources originales du contributeur sont proposees sous MIT, attribution collective neutre « Performance Mode contributors ». Les identifiants personnels, chemins de poste, captures, journaux locaux et images firmware sont exclus. Les courts octets de garde natifs restent des octets de l'OS, pas du code relicencie sous MIT.

## 1. Code natif concerne

| Adresse | Role |
| --- | --- |
| `0x4000045c` | Copie SRAM au demarrage ; crochet de copie de notre charge utile |
| `0x400060fe` | Repartition des touches avant les ecouteurs racine |
| `0x400764ec` | Invocation d'un recepteur de touche, apres les ecouteurs |
| `0x4001aa4e`, `0x4001f4f0` | LEVEL/DATA et encodeurs de parametres |
| `0x4001b22a` | Dessin de MainView et des deux ecrans |
| `0x400597a8` | Appel du lissage des cibles audio ; source native preservee |
| `0x40054d70`, `0x4005571e`, `0x40055510` | Publication IRQ immediate, frontiere de motif et arret/restauration |
| `0x4005b2ae`, `0x4005d080` | Encodeur et decodeur de kit |
| `0x4001040e`, `0x400107d8` | Sauvegarde et rechargement natifs TEMP/motif |
| `0x40080064` | Allocateur natif pour les grandes banques d'etat |

[FAIT] Le generateur verifie le SHA-256 du SysEx officiel et du MAIN OS, puis les35 sequences `old` avant toute modification. Les detours rejouent leurs prologues courts, lus/verifies dans le fichier de l'utilisateur, et ne reproduisent pas des routines natives entieres. Les autres sections du conteneur sont conservees et verifiees apres reconstruction.

## 2. Memoire et chargement

[FAIT] Le chargeur est ajoute a la fin officielle de l'image, `0x401aa140`. Il appelle la vraie copie SRAM d'origine, copie notre code a `0x42339000`, puis rend la pile. Le lieur refuse que le code/etat statique depasse `0x42340000`. La reference actuelle comporte17032 octets et finit a `0x4233d288`. Le presse-papiers occupe60 octets de cet etat. Aucun masque de sprite n'est pris.

[FAIT] Les banques de definitions utilisent53696 octets alloues par l'allocateur natif ; la banque TEMP de session utilise50304 octets a sa premiere utilisation. Aucune allocation n'est faite dans le crochet audio ou les ponts IRQ. Le tampon audio est consomme synchroniquement par le site de lissage natif ; son cout et son absence de reentrance sous les autres mods restent a revalider avant integration.

[FAIT] La compilation de cette proposition suit `-mcpu=54418` et `-msoft-float`, avec GCC m68k-elf16.2.0 et binutils2.47. Le prototype independant utilisait un profil5475 ; le resultat compile ici n'est donc **pas annonce comme l'image deja essayee sur appareil**. Les sources fonctionnelles sont conservees ; la preuve est relancee sur cette compilation.

## 3. Persistance et presse-papiers

[FAIT] Une definition contient quinze macros et soixante destinations. Le record utilise256 octets dans la marge du kit serialise a `+0x1d00` d'un bloc natif de `0x1e00` octets. Les champs natifs utilises se terminent avant cette marge dans l'encodeur OS1.13 analyse. Le conteneur de projet et les tailles de kits restent inchanges.

[FAIT] Schema3 : entete16 octets, soixante entrees4 octets et CRC32 de la charge240 octets. Chaque entree conserve profondeur signee et identite16 bits. Pour chaque macro, les4 bits faibles de son montant occupent le demi-octet haut de la premiere piste ; ses3 bits forts celui de la deuxieme. Les3 bits bas conservent T1-T6/FX ; les bits inutilises sont valides. Les anciens records schema2 chargent des montants nuls. Les identites indisponibles restent inactives et conservees.

[FAIT] Le changement effectif de motif recharge definitions et montants ; une simple mise en file d'attente ne les change pas. Les trois ponts IRQ conservent registres et statut. Les sources canoniques des sons ne sont pas remplacees par les offsets des macros. Au rechargement TEMP, le record de session est fourni au decodeur avant sa notification native afin de ne pas publier un etat transitoire vide.

[FAIT] Le presse-papiers est une copie de valeurs, distincte du presse-papiers natif. Effacer le garde ; changer de projet ou redemarrer le vide. Les combinaisons possedees sont interceptees avant les ecouteurs, une seule fois par geste. Les relachements et clics synthetiques ne fuient pas vers copier/effacer/coller natifs. Hors PERF/SET ou derriere un menu natif, le chemin normal reste actif. Les mutations publient les records et recalculent les cibles anciennes/nouvelles.

## 4. Preuve et reproduction

```sh
python3 tools/gen_performance15.py --cycles firmware/model-cycles_OS1.13.syx --check
python3 tools/test_performance15.py
python3 tools/emu/test_performance15.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/gen_performance15.py --cycles firmware/model-cycles_OS1.13.syx \
  --output build/performance15/local-test.syx
```

[FAIT en emulation] Unicorn execute les vraies instructions du demarrage, du constructeur KeyEvent, de la boucle d'ecouteurs, de l'activation IRQ, du traitement des encodeurs et des codecs de kit. Les services UI, le tas, le consommateur final des ecouteurs et la sortie du lissage sont interceptes et annonces comme tels. Les flux MMC et les voix DSP ne sont pas emules dans cette preuve.

| Verification | OS d'origine | Prototype compile |
| --- | --- | --- |
| Demarrage natif | SRAM initialisee, pas de charge Performance | SRAM puis copie exacte de notre charge utile |
| Transport ordinaire | Ecouteurs et repartiteur appeles | Meme boucle native |
| Montant et audio | Source native du lissage | Cible modulee continue, source native intacte |
| Copier/effacer/coller | Comportement natif | Quatre lignes, montants, signes et identites conserves sur15 macros et2 ecrans |
| Frontiere IRQ | Pointeurs natifs seulement | Rappel du record du motif et du montant |
| Kit encode/decode | Champs natifs | Meme codec plus record de macros |
| Projet change | Pas de presse-papiers Performance | Presse-papiers dedie invalide |

La preuve comporte154 verifications ; les huit tests de catalogue et de garde passent. La reconstruction SysEx est relue : checksums, HMAC et sections autres que3 identiques. La reference MAIN OS est `3cc3d77d057b37445e679f1de389ac7a3fdfa5942151d9f051befd511a0d0b1f` (autonome, GCC16.2.0).

## 5. Limites et integration a examiner

[FAIT] Les ecarts directs avec les ecritures catalogue existantes concernent `level-pan-values` : `0x400081f2`, `0x4001aa4e`, `0x4001b22a`. Cette combinaison doit etre interdite ou fusionnee explicitement. L'absence d'autre recouvrement direct ne prouve pas la compatibilite : les chaines de demarrage, l'etat natif, le cout IRQ et les formats de sauvegarde sont aussi des contrats.

[A FAIRE] Avant toute carte de flasheur : declarer le format sauvegarde dans le registre ; decider la chaine de payload/boot avec les moteurs Syntakt et Model-TG ; mesurer le budget audio/gouverneur ; tester les touches avec arp, chord-keys, lfo-plus, MIDI et les menus ; definir les conflits ; creer le tweak catalogue et ses preuves combinees ; regenerer registre, hashes de reference et assets bilingues du site. Le prototype ne fournit ni profils de machines supplementaires ni LFO2.

[A FAIRE] Validation du mainteneur : entree/sortie des deux ecrans, quatre destinations dont FX et LFO, absence d'action transport parasite, absence d'offset restant apres effacement/collage, A1/A2 pendant lecture, TEMP et projet/redemarrage, CONFIG > UPGRADE et confirmation LEVEL/DATA. La presente PR reste un brouillon source et n'active aucune nouvelle combinaison utilisateur.

## 6. Controles du depot

[FAIT] `gen_flasher_tweaks.py --check`, `check_overlaps.py`, `registry.py --check`, compilation Python, equivalence web/Python et validation SysEx web passent. Le smoke test utilise la meme entree JavaScript avec jsdom installe localement dans `build/`.

[A FAIRE] `relocate_6ch.py --check` signale que `11-6ch-usbup.json` ne correspond pas a sa regeneration avec les outils locaux. Le generateur, ses sources USB et ce JSON ne sont pas modifies par cette contribution ; le fichier n'est pas regenere dans cette PR. Les hashes/combinaisons des moteurs Syntakt et Model-TG ne sont pas annonces comme valides pour ce prototype non inscrit au catalogue.

## 7. Mise a jour du 21/10/2026 : rappel TEMP et edition en lecture

[FAIT] CONFIG > MACROS propose RLD: OFF/ON. La preference de session commence OFF. ON conserve les montants courants M5/M10/M15 pendant le rechargement TEMP du motif actif ; les douze autres montants et toutes les destinations/profondeurs sont rappeles. Le record TEMP reste inchange. Le decodeur applique les trois montants avant la publication native, y compris sans cache de session ; le contexte est efface au retour. Le format schema3 reste identique. Les libelles de huit/sept caracteres evitent le depassement du panneau droit.

[FAIT] L'ancienne edition emettait `0x400d1f98` sans descripteur de changement, meme pour une macro sans destination active. L'ecouteur natif du projet `0x4000e25c` appelle alors `0x4005950e`, qui efface l'etat du kit audio. La nouvelle publication de metadonnees demande directement les jobs natifs de miroirs `0x4000a12e` et `0x4000a276`, puis propage la modification au parent via `0x400d0f6c`. Les vrais encodeurs de kits conservent ainsi les records sans notifier un remplacement complet du kit a l'audio. Les notifications natives de rechargement restent actives. Aucun octet de firmware ou routine native complete n'est ajoute aux sources.

[FAIT en emulation] La preuve Unicorn mise a jour comporte154 verifications : les101 precedentes, preference OFF, rappel selectif puis retour OFF sans mutation TEMP, reproduction du reset par le vrai ecouteur natif, modifications des quinze montants sans reset et vrais jobs/encodeurs pour les deux miroirs. Les services de scheduling, de parent/observable et le stockage physique restent substitues. La compilation54418 de cette PR est reverifiee separement du prototype5475.

[A FAIRE] Le prototype autonome v34 a fait l'objet d'un retour positif anonyme sur appareil pour les changements de macros en lecture. Ce retour ne valide pas le binaire54418 de cette PR ni ses combinaisons : statut toujours experimental, verification du mainteneur encore requise. Aucun nom, identifiant utilisateur, chemin local ou capture de cet essai n'est publie.
