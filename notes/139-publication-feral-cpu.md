# 139 — Publication Feral et CPU, principal 2.16

Demande explicite AveyCole dans Codex le 22/10/2026 : promouvoir le fichier
v33 avec filtre partage et lier les notes des changements depuis main 2.15.
Credit Feral demande explicitement : **Glycinate**.
Adresses : VA de l’OS 1.13.

## Reponse courte

[FAIT] Le principal distribue la copie exacte du candidat partage v33,
sans recompilation ni modification des octets approuves. Le toggle DX reste
sauvegarde, Off par defaut, conformement a cette promotion explicite.
Les pages de comparaison privees et leurs fichiers restent fixes.

## 1. Identite de livraison

- Release : 2.16 ; stamp `2026-10-22-feral-cpu-main-216`.
- Source : `all-features-polivoks-cpu-trim-test-v33.syx`.
- SHA256 SysEx : `77f97ede90973a7a5de1b40b5bdb19ab4b7165b56141b0d7b2f4c44ed41d16f7`.
- SHA256 MAIN : `a9ccfa81d460f421a42d0a98ecb7d7999a762539a25e9f4915ab76bc57eb36a5`.
- Flasheur : `docs/flasher/`, image fixe et hashes concordants dans BUILD.json.
- Notes publiques EN/FR : `docs/flasher/release-notes-2.16.html`.

## 2. Contenu et preuves du candidat

[FAIT en emulation] Chord/ChordKeys : 735 cas d’harmonie par variante,
PCM/etats exacts ; rendu allege d’environ17,9% instructions sur le trajet teste.
SD Vintage, Clap Vintage et SY Toy : oscillateur partage en SRAM, 256 cas
directs et 288 blocs mixtes, audio/etat/EMAC exacts. Ampli neutre et repeat
(fondus, plateau, copie historique) optimises sans changer les sorties testees.
Sept modes Wizard conserves, dont Wavetable. Les filtres partage et Wizard
sont maintenant des passe-bas deux poles inspires du Polivoks ; leur son change.
Deadline reelle du gouverneur, reprise avec raccord32samples et scan de silence
alleger ; seuils/protection sampler conserves. Les surcharges restent possibles.

[FAIT en emulation] Feral remplace TINY (52modeles) par dixmodeles0–9.
416rendus relocalises par variante, sixpistes, controles/notes aux limites,
audio/etat/EMAC exacts a la source utilisateur.160blocs de boucle native puis
32blocs mixtes ; autres voix identiques aux versions optimisees precedentes.
Decompresseur natif :2315991octets exacts pour cette variante partagee, aucune
source non lue ecrasee. Sections hors MAIN, bootloader et updater inchanges.

Aucun pourcentage CPU global ni resultat materiel supplementaire deduit.
L’approbation de publication est explicite ; `hardware_verified` reste false.

## 3. Verification de publication

`tools/test_fixed_main_delivery.js` execute la vraie page Chromium : fichiers
Cycles/Syntakt fournis, SHA complet et MAIN exacts, paquets valides,
telechargement identique ; image corrompue refusee sans fallback.
Aucun acces MIDI ni transfert physique automatique.
Les notes et credits citent Glycinate, les liens et versions EN/FR sont verifies.
## 4. Controles generaux de publication

[FAIT] Build synthetique Python/JS identique, verificateur SysEx bon/corrompu
concordant, compilation Python482fichiers et controle overlaps171tweaks passent.
La page Chromium verifie l’image exacte, son telechargement, le rejet d’une
corruption, le lien des notes, le retour principal, EN/FR et le credit Glycinate.

[CONSTATE] Trois checks historiques restent rouges : catalogue tweaks.js,
REGISTRY.md et recette11-6ch-usbup juges non a jour par leurs generateurs.
Ces fichiers/generateurs sont inchanges par cette publication. Aucune
regeneration de ces anciennes compositions n’est appliquee a l’image fixe.
Le smoke generique jsdom ne demarre pas (module absent de l’environnement) ;
la vraie page est testee dans Chromium a la place. Ne pas annoncer ces checks
historiques comme passes. Aucun nouveau test materiel revendique.
