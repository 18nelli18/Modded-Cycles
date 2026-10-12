# 63 — Reprise automatique des séquences MIDI et LFO ajoutés

Demande d’AveyCole dans la conversation du 12/10/2026 : retrouver les éditions
B-side et LFO après redémarrage sans Save Project explicite. Adresses : VA OS1.13.

## Réponse courte

Candidat expérimental `--audio-lfo --working`, distinct du build manuel MBK3.
Les checkpoints WRK sont séparés des copies SEQ du Save Project. Le redémarrage
working96 lit WRK ; Reload Project explicite lit SEQ. Aucun firmware distribué.

## 1. Chemins et identité

`storage_path.s` type2 produit `/ModdedCycles/SS-XXXXXXXX/WRK-PP-A` et B.
Les 5 184 combinaisons de chemins du test restent uniques ; indices invalides
refusés sans modification de sortie. Le codec et la sélection A/B CRC restent MBK3.
Working96 n’est associé à SS que si slot/type/identité natifs sont cohérents.
Une absence vérifiée de WRK permet le fallback SEQ ; une corruption ne le permet pas.

## 2. Déclenchement

[FAIT en émulation] Le callback natif `0x4000fa26` transmet working96 à
`0x4000f762`, avec double indirection self et propagation des échecs.
Sa cadence automatique native n’est pas prouvée. Le candidat ne dépend donc pas
uniquement de ce callback : `storage_autosave.s` scrute une banque par150 blocs
audio (~100ms), dans le service UI, et attend au moins3000 blocs de stabilité.
Avec96 patterns, attendre environ20s après la dernière édition avant extinction ;
la cadence matérielle et les latences disque restent à mesurer.

Un contexte heap1536 conserve CRC, date de changement et état écrit pour96 patterns.
Les états identiques ne sont pas réécrits. Le changement d’identité ou serial Load
réinitialise le suivi. Les configurations LFO2 audio sont capturées avant le CRC ;
les phases ne sont ni sauvegardées ni incluses dans le suivi.

IRQ, Load incomplet, contexte disque occupé ou empoisonné interdisent les écritures.
L’échec sans poison conserve le checkpoint en attente ; erreur physique empoisonnée
interdit toute autre écriture jusqu’au redémarrage. Save96 natif écrit WRK sans
popup MIDI SAVED ; Save0..95 garde SEQ et son retour utilisateur.

## 3. Place

Lecture MBK2 conservée, fonctions d’encodage/sélection MBK2 inutilisées retirées
uniquement dans ce candidat. Les deux moteurs ACID et MACRO restent sélectionnables.
Réserve TG8 blocs inchangée ; marge image4706 octets au build vérifié.
La réserve RAM du payload reste très serrée : aucune marge implicite revendiquée.

## 4. Validation et limites

- `test_midi_working_autosave.py` : cadence, allocation unique, stabilité, états
  inchangés, échec/réessai, association refusée, IRQ/Load/busy/poison.
- `test_midi_storage_session.py --extended --working` : WRK/SEQ indépendants,
  redémarrage working96, Reload explicite, identité et récupération A/B.
- `test_midi_bank_bundle.py --audio-storage --working-storage` : vrai boot
  TG/Syntakt, décompression, caches, piles, contexte, travail MIDI et réserve.
- `test_midi_saving_flasher.js` : démarrage EN/FR, références exactes USB6/non-USB6,
  transfert simulé683 blocs, compression normale quand banque désactivée.

[À FAIRE matériel] Editer B et les LFO A/B, attendre le checkpoint, redémarrer sans
Save Project, puis vérifier Reload Project. Tester la charge UI en lecture et avec
plusieurs patterns. L’interruption d’une écriture physique, Save As à identité
renouvelée et backup Elektron/SysEx des sidecars ne sont pas garantis.
