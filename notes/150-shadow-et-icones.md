# 150 — Shadow et icones de machines

Demande AveyCole, conversation du22/10/2026 : ajouter une machine inspiree d’Opal sans retirer de moteur ; nom Shadow, apres TINY et avant MIDI Out. Adresses : VA OS1.13. Sources privees `shadow_assets.py`, `tools/machines/shadow/`, `tiny_extra_assets.py`, reconstructeur `--shadow`/`--machine-icons`. Preuves `test_shadow.py`, `machine-icons-proof-v50.json`.

## Reponse courte

[FAIT] Le site officiel Fors decrit Gem(FM),Mass(modal),Dust(pulsar/bruit) et Slate(granulaire). Voir https://fors.fm/opal et https://api.fors.fm/storage/v1/object/public/manuals/opal-guide.pdf . Opal est un appareil Max for Live, pas un binaire ColdFire importable. Shadow est une implementation originale du principe pulsar, pas une extraction ni un port complet ; pas de donnees/presets/code Fors copies. Les trois oscillateurs, les fenetres triangulaires et les tables mathematiques originales limitent le cout. FM/Blur complets d’Opal ne sont pas inclus.

## 1. DSP et bornes

- Code `0x4678b200`,2752octets ; BSS `0x4678ca00`,552octets. Ancien padding des metadonnees, verifie nul et separe des descripteurs precedents finissant `0x4678b0a8`, et des trampolines `0x4678d000`. Aucun agrandissement de la reservation1Mo ni allocation audio.
- Trois trains de grains fenetres, phases et aleatoire independants par piste. Spread0 saute deux oscillateurs ; bornes entieres Q31 et tables48kHz. Etat de92octets/piste.
- Color=Grain,Shape=Density,Sweep=Spread,Contour=Chaos ; PUNCH ajoute une attaque repetee. Pitch/Fine,Decay/Gate et VCA natifs conserves. Etats remis a zero au changement de moteur et au trigger.
- Les metadonnees sont regenerees pour20machines et141descripteurs. DATA `0x467e9800`,DESC `0x467e9a00`,code metadata `0x467ec000`. Anciennes references relocalisees par sites verifies ; IDs conserves0..18,Shadow19 ajoute. Ordre0..16,18,19,17.
- Le helper de retention accepte maintenant19. Le SCRAMBLE utilise les descripteurs natifs de Shadow. Les banques Wizard/synth restent limitees au menu, sans cout dans l’audio.

## 2. Icônes

Dessins originaux34x34,272octets colonne-major par bitmap, JSON editable et BIN sous `tools/machines/shadow/artwork/`.

- Shadow : personnage avec grande ombre derriere ; WAVE : formes d’onde superposees ; TINY : loupe.
- MIDI Out : prise/cable DIN cinq broches ; ACID : panneau sixknobs/clavier303 ; Feral : guepard tachete.
- v49 integre les trois premiers ; v50 ajoute les trois suivants. Cartes stock et chapeau Wizard conserves. Les sixautres icones lettres restent inchangees dans v50.

## 3. Preuves

[FAIT en emulation] Les deux compositions v49 passent140cas du selecteur natif,20reperes dans l’ecran,descripteurs/nom et bootstrap. Les18anciens moteurs audio produisent le meme PCM quev48 sur144blocs sixvoix. Dixcommandes de Shadow affectent l’audio. Coeur :942..3281instructions dans les cas usuels,4473maximum sur128blocs d’extremes avec notes0/24/60/96/127 ; pas de pourcentage CPU physique revendique. Pic Q31 borne203956224 dans ce balayage.

Preuves complementaires : sixsessions d’isolation Wizard,171cas SCRAMBLE live et171locks par composition. Le v50 differe du v49 uniquement dans les trois nouveaux bitmaps ; code/audio/etats identiques. Rendu natif des cartes et chargeur natif exact, aucun ecrasement de source compressee.

## 4. Retour utilisateur et publication

AveyCole : « they looked great in new v49 on my machine », puis approuve le v50 exact avec « push this to main ». Publier2.22, SHA256 `78a0a39695cc7bf9824cd71f4f2ac0874f327046240b94028daa51db50a4a39f`. Pas de declaration d’essai audio materiel exhaustif. Variante sans filtre partage privee, filtre interne Wizard conserve. Guides EN/FR/PDF actualises, credits Glycinate/Fors/PPPCCC/18nelli18 conserves.

Demandes suivantes : icones SD Vintage,Clap Vintage,SY Toy,SY Bits,Swarm et MACRO(DNA), puis sends crusher/delay independants dans Both1/Both2, aveccrusher0=delay propre. Ces changements ne font pas partie des octets v50 approuves.
