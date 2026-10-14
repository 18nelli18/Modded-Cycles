# 78 — Machines facultatives avec Banque MIDI

13/10/2026, demande d’aveycole : pouvoir décocher Syntakt, MACRO et ACID
avec Banque MIDI. Le build de test avait un lien réel à leur loader,
en plus du raccourci UI qui sélectionnait tout. Adresses VA OS 1.13.

## Sélection

Banque MIDI sélectionne seulement ses supports nécessaires : Model-TG,
Sequence Generator, Second LFO, SCRAMBLE et MIDI Live OUT+THRU.
Les machines Syntakt/MACRO/ACID, ChordKeys, USB6 et les options visuelles
ne sont plus imposés. Décocher un support requis désactive la Banque.
Le format musical RAM, les CC, les slides et le transport restent identiques.
Aucune sauvegarde MIDI réintroduite. Le flasher principal reste inchangé.

Limite : ChordKeys conserve son intégration complète existante, qui prépare
ses données de synthèse au démarrage. Le sélectionner coche encore le bundle
compatible ; retirer une de ses trois options de machines le décoche.
Il reste facultatif et doit rester décoché pour la sélection sans moteurs.

## Bootstrap

Avec un moteur, son bootstrap termine vers `boot_extra_hook=0x401bf3d8`.
Selon la variante, cette fin est en `0x4016cb1a`, `0x4016cb44` ou `0x4016cb96`.
Les trois JMP vérifiés sont détournés vers le même loader MIDI `0x401907a4`.
Sans moteur, l’opérande de l’appel natif en `0x40000532` passe directement de
`0x401bf3d8` au loader MIDI. Model-TG utilise sa variante de compatibilité ST,
sans installer de moteur Syntakt et sans demander son fichier OS.

La source compressée MIDI demeure `0x401f8f76`, au-dessus de sa destination
RAM `0x401bf8c0..0x401cdca0`. Déplacer sa source à la fin du seul TG aurait
créé une décompression en place dangereuse. Une réserve flash remplie de
zéros comble donc le manque de moteurs : `append.zero_pad_from=0x401bf8c0`.
Le builder Python et navigateur l’acceptent exclusivement pour Banque MIDI,
dans la plage bornée entre la fin déjà construite et sa source fixe, sous
`END_LIMIT`. Le payload et le loader musicaux restent byte-identiques.

## Vérifications

`gen_optional_midi_machines.py` produit les quatre variantes d’écritures et
leurs hashes indépendants. Le catalogue ne contient plus le moteur complet
comme dépendance de Banque MIDI. Les références payload restent celles du
RAW/compressé original ; le trou de zéros appartient à la réserve explicite.

`test_optional_midi_machines.js` utilise les vrais contrôles de la page :
Banque seule sans OS Syntakt, MACRO, ACID, MACRO+ACID, Syntakt et sélections
complètes avec/sans ChordKeys. Hashes des mods, conteneurs et EN/FR vérifiés.
`test_optional_midi_boot.py` compare les images Python/navigateur et exécute
les vraies chaînes de démarrage, jusqu’au flush cache final du loader :
le RAW MIDI doit être intégralement identique. Les registres MOVEC/cache
sont ignorés par la simulation, les RAM DSP/OS sont simulées, sans matériel.
`test_optional_midi_transfer.js` vérifie la construction sans fichier Syntakt
et le transfert UI intégral vers un récepteur simulé, CRC et contenu exacts.

L’utilisateur a confirmé le correctif Control All de la note77 sur matériel.
Sur le test précédent, l’audio est redevenu normal après retrait des copies,
mais le CPU affiche encore des pointes au-dessus de108 % avec les machines
stock. Ce changement de sélection ne prétend pas résoudre cette mesure.

Build : `2026-10-13-midi-bank-optional-machines`, sur `flasher-controls-test`.
Après publication : LEDs B visibles en mode REC seulement, puis sélection
de piste par pad ChordKeys quand aucun TRIG physique n’est tenu.
