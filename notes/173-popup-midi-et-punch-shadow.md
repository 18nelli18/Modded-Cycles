# 173 — Popups Mod Setup, isolation MIDI et PUNCH Shadow

Demandes AveyCole du25/10/2026 dans le chat de reprise. Livraison privee139,
experimental ; Adresses : VA OS1.13. Recette : `gen_governor_recovery_test.py
--midi-boundary --legacy-cart ... --legacy-classics ... --stage [--speak-adult]`.

## 1. Popup confirme sur la machine

[FAIT] Le handler encodeur natif peut appeler present avant son retour. Le menu
est temporairement suspendu pour deleguer les encodeurs ; cette suspension ne
doit pas annuler preview pendant parameter_edit. Le timer arme apres delegation
conserve le popup deux secondes. Les pixels du vrai dessinateur natif sont
conserves ; les evenements encodeur sans mouvement sont ignores. BACK conserve
press/repeat/release. Menu opaque et position des sous-pages conserves.

[FAIT sur machine,25/10/2026] AveyCole confirme v137 : « that worked for the popup ».
Ce retour ne valide pas les modifications MIDI ou Shadow ajoutees ensuite.

## 2. MIDI : restauration en fin d'operation

[FAIT] AveyCole signale que v137 modifie encore les controles en passant MIDI
et revenant dans le meme menu MACHINES.139 deplace la sauvegarde/restauration
des six valeurs autour de toute l'operation native, apres ses snapshots et
notifications. Banques distinctes synthese/Wizard/MIDI, par piste et session.
Hors menu, changements MIDI et resets explicites restent natifs. La publication
des valeurs restaurees reprend la notification virtuelle du setter natif.

[FAIT en emulation]30 trajets apparies : cinq points de depart sur six pistes,
avec/sans visite de MIDI et avec edition MIDI. Les100octets de chaque son au
retour sont identiques au trajet sans MIDI. Pas encore de confirmation physique139.

## 3. PUNCH Shadow

[FAIT] Option de compilation SHADOW_PUNCH_DISTORTION : drive x4 puis ecretage
symetrique32767 avant la conversion4096 et le VCA/gate natif. PUNCH Off conserve
le PCM et l'etat oscillateur ; PUNCH On conserve aussi le transitoire precedent.
Pas de modification de l'autre machine PUNCH, des IDs ou des controles affiches.
Les anciennes recettes restent sans cette option.

[FAIT en emulation]576 blocs du coeur compile verifies exactement,48 blocs
natifs sixvoix compares ; autres voix identiques, sorties bornees. Le code Shadow
et ses pointeurs relocalises seuls changent entre137 et138 ;139 ajoute ensuite
la restauration MIDI UI. Bootloader/updater inchanges et images re-extraites par
le constructeur. Pas de mesure CPU physique revendiquee.

## 4. Livraison

139 et139adult reconstruits avec --check, empreintes pinnees dans private-v139.
Principal non modifie. Sources/proofs fournis avec les fichiers directs.
Le signalement ulterieur des enveloppes PUNCH/TINY vers Decay100 reste une
investigation distincte, exclue de cette image a la demande explicite de l'utilisateur.

## 5. Retour materiel et correctif141 — 25/10/2026

[FAIT sur machine]139 et140 ne corrigent pas le retour MIDI. AveyCole precise :
Kick Sweep24 devient68. Il confirme que l'aller-retour jusqu'a PUNCH sans entrer
MIDI ne provoque pas son probleme.68 ne doit pas etre presente comme defaut Kick.

[FAIT] Le poll UI MIDI modernise initialise33mots avec un tag MIDI, puis sa sortie
appelle mm_audio_poll qui remplace les mots audio. Les anciennes preuves de scroll
omettaient ce poll entre deux rotations ; elles ne reproduisaient pas le materiel.

[FAIT en emulation] validate_midi_poll141.py appelle le vrai mx_poll entre chaque
rotation.140 reproduit Sweep24 vers68 ;141 conserve24 et les six dials sur sixpistes,
aller-retour des24machines. Les neuf controles CC non reserves restent OFF sans
assignation. Le correctif conserve/restaure les33mots audio et leur tag avant le poll,
en preservant le nouvel ID machine. Taille BSS sous la limite467ef000.

Recette141 : --midi-cleanup, options privees precedentes conservees. Le popup137
et la distortion Shadow commandee par PUNCH sont conserves. Pas de modification
des enveloppes PUNCH/TINY ni publication du principal. Validation materielle141
en attente. Les explications140 de bornes destructives ne suffisaient pas a
expliquer le symptome materiel ; le poll tardif est la regression reproduite ici.
