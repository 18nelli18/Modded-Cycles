# 189 — Groove, Humanize et CHORD Strum

Demande AveyCole25/10/2026 : porter Groove et CHORD Strum depuis https://github.com/gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods ; revision61c7432076e49b3050c7e076a5b602747d36fb8c, MIT, copyright2026 PPPCCC/gialloinfuso. Generateur --groove-strum, candidat156. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] Sept tables Groove, Swing natif, Humanize temps/velocity par piste et CHORD Strum bidirectionnel. UI originale Mod Setup > Grv ; aucune gesture/chaine FX tierce importee. Mode, Trk1..6/All, Tim0..100, Vel0..100 et Str-80..80ms entre notes. Le Swing natif dose les tables. Defaut Swing/Humanize0/Strum0 : PCM exact155 sur192blocs sixpistes (CHORD, SPEAK/MACRO/PUNCH/KICK/ACID et LEGACY).

## 1. Integration et memoire

Noyaux G/Humanize468b2000, table dispatch468b2200, pointeurs468b2300, sept tables128octets468b2400, ST/G0F468b2800, UI468b3000. Code finit avant468ba000 ; BSS468ba000..468bb000. Padding du porteur RETROSYN garde zero avant ecriture, apres code_end et avant art468bb000. Aucun buffer audio emprunte. Hook sequencer40054af8, epilogue CHORD400ab240 et gain400ab2d2 gardes individuellement. Detours UI key/encoder/draw/frame gardes et prologues rejoues.

## 2. Conflit de sauvegarde resolu

[FAIT] Le Humanize amont emploie les octets40..51 de l en-tete. Chord Keys emploie deja40..63 : premiere composition rejetee par le test d initialisation. Aucun hook ni octet de pattern de Humanize dans le candidat livre. Douze valeurs globales par piste dans /Groove.cfg20octets, avec mode/strum, version2, complements et bornes ; ecriture UI seulement, lecture une fois et sauvegarde arretee. Les amounts suivent les pistes entre patterns. Configuration independante de Chord Keys et de ses signatures ; aucun nouveau schema de pattern.

## 3. Preuves et livraison

test_groove_strum156.py : sept tables/64pas/Swing0,7,30/velocity1,40,100,127, flags81/91 ;800cas Humanize sixpistes, RNG et valeurs invalides ;6000blocs CHORD reference entiere, deux directions,0 et bornes ; contrat epilogue D2-D5/A2-A4 et D6/D7/pile. Native voice loop CHORD atteint le hook et produit un render audible. Menus cinq lignes/BACK/All/clamps et fichier sauvegarde. test_groove_audio156.py : PCM exact155 quand les nouvelles options sont neutres. Tous objets audio precedents et bins exacts155 ; banque151, WAVE, QntM, isolation MIDI, bootloader/updater et autres sections preserves. --check standard/adulte exacts. Pas de resultat appareil revendique. Principal2.47 inchange.

UI abbreviations : Swng, BBap, Disc, Regg, Bong, Caix, High, Kudu. Tables completes Swing, Boom Bap, Disco, Reggae, Bongo, Caixixi, Highlife, Kuduro. Str indique des millisecondes entre notes ; amplitude80 peut etaler quatre notes sur240ms. Candidat experimental prive.
