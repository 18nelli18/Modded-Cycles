# 188 — Marge SPEAK, ACID et retrig maitre

Demande AveyCole25/10/2026 : optimiser encore SPEAK/ACID, peut-etre masterretrig. Generateur --speech-acid-headroom, base154 et banques151/LEGACY154 conserves. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] SPEAK 5.782% instructions en moins sur128mots/4096blocs phonemiques actifs ; ACID 4.512% sur huitbancs sixpistes. Retrig actif3,2% sur l ensemble du banc avec transitions, environ18% sur certains blocs etablis, gros pic de transition identique. Mix sixpistes avec SPEAK audible/HALL/PingPong/Sidechain :0,96–1,09% instructions en moins, pics du banc un peu plus bas. Aucun pourcentage CPU physique deduit. Aucun sample ni octet d etat DSP change.

## 1. SPEAK

Trois resonateurs deroules explicitement, neuf lissages et trois filtres conserves dans le meme ordre. Etats/entree/sortie distincts dans le contrat bridge, qualifies restrict sans nouveau champ ni cache. Tous les phonemes, tables, niveau, saturation, excitation/bruit, RNG, pitch, vitesse et sixphases d interpolation sont conserves. La division par6 par sample48kHz devient un produit borne exact : x=(next-last)*upsample, |x|<=40950 car level produit |next|<4096 et upsample<=5. ((x*43691)>>18)+((uint32)x>>31) egale troncature(x/6) sur toute la plage, verifiee exhaustivement sur81901cas natifs.32divisions par bloc supprimees ; ne pas compter une division comme un cycle ni convertir les instructions en P.

128mots standard et128adulte,4096blocs par lexique, PCM et State complets exacts ; choix de phonemes actifs explicite pour ne pas mesurer seulement le silence initial. Controles live, Punch et tous decalages d interpolation. Les deux banques passent separement.

## 2. ACID

Meme corps et arithmetique de32samples, quatre choix constants waveform/attaque faits avant la boucle. Aucun pole, produit EMAC, drive, polyBLEP, accent ou enveloppe supprime. Disposition constatee apres compilation, code reste avant BSS46848000. Huitcas sixpistes : notes extremes, cutoff/resonance/env/drive, scie/carre, controls live, retriggers et release ; PCM et BSS fondamental complet exacts.

## 3. Retrig

Chemin plateau rr_native_plain deroule explicitement par4. Ordre lire live, capturer history, relire history, ecrire audio conserve meme si read/write se recouvrent. Residuel9bits et saturation asymetrique-32767..32767 exacts. Le pragma GCC a ete ignore en-Os ; il ne fait pas partie du gain final. Un essai-O3 global depassait le trou jusqu au Scramble et a ete rejete par la garde ; le candidat livre garde-Os et ne deroule que ce chemin. Module final4892octets finit467c831c avant Scramble467c9000 ; SRAM unity36octets exacte.

Banc natif154/155 : Off, arme, captures, restes de fade, playback/arret, mono/stereo,12pistes mid/side, toutes valeurs limites de quantification, masques d exclusion ;96blocs actifs et110frontieres par mode stereo, wraps32bits et tampons, samples/historique/etat exacts. Les gros blocs fade restent identiques, seul plateau change.

## 4. Portee et livraison

Seuls objets speak.o, fund-acid-c.o et8.o (repeat_fades) changent, plus trampolineUI a pointeur reloge. Autres objets audio exacts, LEGACY154 conserve. Audit normalise seulement les adresses UI deplacees. Bootloader/updater et autres sections horsMAIN exactes, bounds verifiees, DSP standard/adulte exacts sauf lexique. Bankqueue151, factoryWAVE, MIDI24machines, popup/BACK et QntM passes. Standard/adulte --check et154 --check byte-identiques. Recettes147/149 toujours exclues. Principal2.47 et guide public non publies/modifies par cet essai. Appareil155 attendu.

Suite utilisateur : apres155, integrer Groove et Chord Strum depuis gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods (lien corrige), puis montrer un concept original Sample Wizard titre/waveform avant toute modification de sa vue ; navigateur de fichiers conserve. Question Linux traitee, utilisateur demande de laisser ce sujet de cote.
