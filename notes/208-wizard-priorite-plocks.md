# 208 — Priorite des p-locks Wizard sur CTRL-ALL

Demande d'AveyCole le 30/10/2026 : les p-locks, notamment pitch, start et end,
doivent primer sur CTRL-ALL. Adresses : VA de l'OS 1.13.

## Reponse courte

Le candidat prive 2.63 conserve les valeurs de la note Wizard verrouillee
pendant le traitement de l'encodeur CTRL-ALL. Les modifications du son de base
restent disponibles pour la prochaine note non verrouillee. Confirmation sur
appareil en attente ; aucune publication du flasher.

## 1. Contrat natif et implementation

- [FAIT] Le getter natif `0x4000da2a` distingue une valeur verrouillee de
  l'absence de verrou. Le slot pitch est 10, start 11, end 12.
- [FAIT] Le frame courant commence a `0x800015ae`, 33 mots par piste.
  Le miroir de lissage commence a `0x800011e8`, apres sept mots communs.
- [FAIT] `0x423087f8` est le masque natif de restauration des parametres
  actifs. Il ne faut pas l'effacer pour proteger une note : cela casserait
  la restauration du son de base par `0x40058308`.
- `tools/machines/wizard_priority/control.c` entoure le callback Application
  de l'encodeur. Seules les pistes Wizard non exclues de CTRL-ALL sont prises
  en compte. Un son de pool courant est protege dans ses 33 slots.
- Capture et restauration du frame et du lissage sous une section critique
  courte ; aucun ajout au render DSP. Une transition de pattern ou de pas
  annule la restauration correspondante.
- Le module Song/ACID existant accueille ce code et ses donnees ; les bornes
  du linker et les cinq images sources epinglees restent verifiees.

## 2. Preuves et limites

[FAIT en emulation] `tools/emu/test_wizard_plock_priority.py` construit les
p-locks avec le setter natif `0x4000dece`, lit le getter natif et execute la
restauration native `0x40058308` sur le pas suivant. Les 32 slots de parametres
(machine exclue) passent, dont pitch/start/end. Le son de base est modifie,
la note verrouillee conserve sa valeur et la note suivante retrouve la base.
Le traitement effectif de l'encodeur CTRL-ALL est simule dans cette preuve :
elle ne constitue pas une reproduction complete du geste physique.

Les cinq editions passent les regressions Song, stockage et interface ; les
editions Full passent aussi le DSP ACID. Dix paquets Cycles/Samples passent
la signature, le boot Samples et les deux verificateurs natifs.

[A FAIRE] Verifier sur appareil les notes tenues au-dela du pas verrouille,
les trigs sans note, les changements de son de pool, les exclusions CTRL-ALL
et les mises a jour LFO concurrentes. Aucun resultat CPU physique annonce.

## 3. Publication2.63 autorisee

AveyCole demande explicitement de pousser le correctif Wizard2.63 sur main.
`tools/gen_wizard_plock_priority.py` reprend uniquement les bases2.62 epinglees,
le garde Wizard et le titre2.63. Song et articulation ACID restent prives.
Le chargeur sparse preserve les deux chargeurs precedents ; Optional deplace
leurs cinq pointeurs absolus avec gardes avant recompression du runtime.
Les cinq editions passent le getter/setter de p-lock et le refresh natifs.
