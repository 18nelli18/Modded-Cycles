# 98 — Persistance MIDI du noyau RAM actuel, candidat MPI1

Demande directe d’AveyCole le 16/10/2026 : reprendre la sauvegarde au-delà de
la RAM, expressément dans un build de test avant le principal. Source : cette
conversation. Générateurs `tools/gen_midi_persistence*.py`, sources propres
`tools/machines/midi_lanes/persistence.c` et `persistence_hooks.s`, preuve
`tools/emu/test_midi_persistence.py`. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT en émulation] Le candidat sauvegarde les données musicales de la Banque
actuelle dans deux copies annexes par pattern, puis les retrouve dans une
nouvelle instance d’émulateur dont la RAM est vide. Notes et timing live,
retrigger/chance/arp, assignations et locks CC, configurations des deux LFO
MIDI par voie sont inclus. **Persistance physique non confirmée.** Le flasheur
principal reste intégralement RAM, testé sur machine ; cette extension reste
expérimentale, sur une page distincte.

## 1. Pourquoi ne pas réactiver simplement l’ancien stockage

Le noyau confirmé de la note 97 utilise des notes de 1 584 octets par pattern,
des extensions retrigger de 3 120 octets et des locks CC de 9 216 octets dans
des tables privées séparées. Les assignations CC de 144 octets et les
configurations LFO MIDI de 192 octets sont partagées par le projet dans ce
noyau RAM. L’ancien stockage MBK2/3 attendait une banque contiguë étendue.
Réactiver ses hooks sur les pointeurs actuels ne suffit donc pas.

[FAIT] L’ancienne garde disque pouvait refuser toute écriture native après
poison, même hors sauvegarde annexe. La nouvelle garde observe les erreurs
pendant nos E/S et empêche seulement les prochains saves MIDI ; elle ne bloque
jamais un writer natif du projet A. Cela élimine un risque identifié dans le
code, sans établir la cause du défaut matériel historique.

## 2. Format et copies

MPI1 : header 48 + notes 1 584 + retrigger 3 120 + locks CC 9 216 + mappings
144 + LFO 192 = **14 304 octets par copie**. Le header contient magic/version,
taille, identité native du projet, slot 0–95, pattern 0–95 et génération,
CRC du payload et du header. Aucune adresse, phase, file ou état de tâche
n’est enregistré. Validation des domaines et CRC avant publication.

Chemins distincts : `/ModdedCycles/MPI1-SS-XXXXXXXX-PP-A` et `-B`. Les formats
anciens MBK/MCC ne sont ni importés ni remplacés. La génération choisit la
copie inactive ; le demi-cycle ambigu est refusé. La présence de fichiers
invalides ne compte jamais comme une absence. Sans copie valide, aucune
écriture automatique ne remplace les deux fichiers.

Un Save Project natif réussi déclenche la sauvegarde des patterns visités,
uniquement transport arrêté et IPL0. Les mappings/LFO partagés sont capturés
dans chaque pattern visité au moment du save. Une écriture annexe procède par
blocs de 512 octets maximum, reprend les écritures partielles positives,
finalise, ferme, rouvre et compare l’intégralité du record. Chaque pattern a
ses copies A/B ; le projet entier n’est pas une transaction atomique.

## 3. Raccordements natifs et publication

| VA | Contrat |
|---|---|
| `0x4000f762` | Capturer table/série/identité avant Save, rejouer son prologue |
| `0x4000f850` | Seulement si Save A réussit : annexe, résultat D0/SR/pile conservés |
| `0x4006a660` | Notification Load avec identité et slot, puis chaîne RAM originale |
| `0x4008b24a` / `0x4008b3f6` | Trampolines read/write physiques, observer les erreurs sans bloquer A |
| drain UI existant | Gardes de démarrage de la note 97 conservées ; restauration UI après Stop |

Load retire immédiatement la table B et annule ses notes via le mécanisme
atomique existant, sans allocation ni fichier. UI remet ensuite une table
vide, retire les anciens index privés et restaure le pattern actif à la
demande. Les autres patterns se restaurent lors de leur sélection. Un projet
non sauvegardé ou sans association de slot reste utilisable en RAM, sans
deviner un chemin. Le slot transmis par Load/Save réussi est prioritaire ;
working96 demande encore l’association native validée.

Une série Load nouvelle ou le démarrage de lecture annule l’E/S en cours.
Les allocations candidates ne sont pas publiées en cas d’échec. Les banques
remplacées restent vivantes tant que leurs index auxiliaires les référencent,
puis sont libérées après retrait des index, au changement de projet.

L’extension est ajoutée après la charge RAM actuelle. Les adresses absolues
internes proviennent exclusivement des relocations ELF, pas d’une recherche
d’entiers ressemblant à des pointeurs. La table d’API est liée aux symboles
de la recette réellement choisie. Noyau RAM, DSP, RETROSYN et TINY conservent
leur code musical. Model-TG reste interdit et Sample Wizard facultatif.

## 4. Vérification et reproduction

```sh
python3 tools/gen_midi_persistence.py --check
python3 tools/gen_midi_persistence_flasher.py --check
node tools/test_midi_persistence_flasher.js
python3 tools/emu/test_midi_current.py --case build/midi-persistence/all
python3 tools/emu/test_midi_persistence.py --case build/midi-persistence/all
python3 tools/check_midi_current_builds.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx --directory build/midi-persistence
```

Compilation : GCC m68k-linux-gnu 15.2, `-mcpu=54418 -Os -std=gnu99`, sans
runtime C externe. Données officielles et exports de tests exclusivement sous
`firmware/` et `build/`, ignorés par Git.

Preuves : corps ColdFire réellement relogés ; CRC/corruption en début et fin,
écritures partielles, refus open/alloc/write/flush/close/lookup/relecture,
redémarrage à RAM vide, récupération A après corruption B, isolation projets,
absence d’E/S IPL1–7 et lecture transport. Save et Load natifs sont exécutés
avec leurs vrais détours et épilogues ; cache/conversion/FS/périphériques
restent simulés. Cinq sélections : seule, supports, Wizard+ChordKeys, toutes
machines/options, toutes machines sans Wizard.

## 5. Essai matériel et limites

[À FAIRE matériel] Arrêter la lecture, éditer B, Save Project et relever le
popup exact. Attendre **MIDI SAVED**, redémarrer, recharger le même projet et
ouvrir B. Vérifier aussi un autre pattern et un autre projet, puis CC/LFO et
le build complet. Un `MIDI SAVE E##` ou `MIDI LOAD E##` signifie un échec,
même si le projet A a été sauvegardé normalement. Garder les projets utiles
hors de cet essai initial.

Codes : E10 ouverture lecture ; E11 poison disque ; E12 ouverture écriture ;
E13 écriture/préparation/finalisation/fermeture ; E14 lookup ; E15 allocation
snapshot ; E16 copies existantes sans récupération ; E17 valeurs snapshot ;
E18 relecture différente ; E19 dossier ; E20 restauration invalide ; E21/22
allocation restauration ; E23 restauration précédente échouée, recharger ;
E24 projet changé pendant save. L’interface indique aussi Stop, mémoire
insuffisante, propriétaire changé et restauration préalable requise.

Les sidecars sont **hors backup/export SysEx Elektron**. Pas d’autosave à
l’extinction, ni reprise des anciens formats. Les fichiers de projets
supprimés ne sont pas nettoyés automatiquement. Une nouvelle identité ou
Save As non cohérent est refusé au lieu d’attribuer les données à un autre
projet. La relecture peut venir du cache : elle n’établit pas seule la
durabilité physique. Coupure pendant écriture, latence et espace disque
restent à vérifier sur la machine ; aucune mesure matérielle n’est inventée.

## 6. Retour matériel et correction de reprise (16/10/2026)

[FAIT matériel rapporté par AveyCole] Le premier candidat affiche MIDI SAVED
sur un projet existant, mais B reste vide après Load, sans popup d'erreur.
Il signale aussi un échec de sauvegarde sur slot vide ; le geste précis et
le popup de ce second cas restent à confirmer.

[FAIT] Les chemins natifs `0x4000fb06` et `0x4000f872` renouvellent
l'identité live via `0x4000eb12`. L'égalité ancienne entre identité live
et fiche sauvegardée pouvait donc classer un projet chargé comme non associé,
sans tentative de lecture MIDI. Les anciens mocks donnaient la même identité
aux deux sources et masquaient ce défaut.

Le candidat preview.2 sépare `mp_owner` (garde RAM live) de `mp_key` (clé
disque). Une notification Load nommée fournit la clé source ; les drains
suivants et working96 utilisent la fiche native type 6 du slot courant,
sans égalité avec l'identité live renouvelée. Le format MPI1 reste identique.

[FAIT en émulation] La régression renouvelle l'identité après notification,
vérifie notes restaurées et gardées au drain suivant, puis charge working96
avec une autre identité live. Les fichiers seuls conservent la clé d'origine.
Les API de métadonnées et fichier restent simulées ; ce résultat ne prouve
pas encore le cycle matériel. Le principal RAM reste inchangé.

Le drain est maintenant suspendu entre entrée et sortie du Save natif :
il ne peut pas changer de propriétaire pendant que la fiche du nouveau slot
est absente puis créée. Les deux sorties, succès et échec, lèvent la garde.
Un échec A sur slot nommé affiche `MIDI: SAVE A FAILED`, sans écriture MIDI.
La preuve simule ces deux états de métadonnées entre entrée/sortie, exécute
aussi les vrais hooks Save sur slot 10, puis recharge ses notes après
renouvellement de l'identité. Cela couvre le geste précisé par AveyCole
(Save Project puis destination vide), sans prouver sa cause matérielle.

[À FAIRE] Retester ce chargement sur machine et diagnostiquer séparément
la sauvegarde sur slot vide. Aucun correctif de ce second cas n'est annoncé.

## 7. Promotion confirmee par AveyCole (16/10/2026)

[FAIT materiel rapporte] AveyCole confirme que test 2 restaure le MIDI en
entrant cote B, puis confirme explicitement que le projet a ete sauvegarde
dans un slot vide via Save Project. Il demande de promouvoir au principal
avec statut teste et d'indiquer clairement : chargement des donnees MIDI
uniquement en entrant cote B et uniquement lorsque la lecture est arretee.
Ce retour remplace les attentes materielles des sections precedentes pour
ces deux cas. Ne pas l'etendre a des essais de coupure ou de disque plein.

La promotion conserve exactement les octets firmware de test 2. Le script
`tools/promote_midi_persistence.py` reproduit les fichiers principaux : seuls
textes et metadonnees de statut changent. Le test navigateur `--main` compare
les cinq empreintes MAIN avec celles du candidat. Le bandeau, la carte, les
references rapides et la version 1.72 reprennent la condition de chargement.
