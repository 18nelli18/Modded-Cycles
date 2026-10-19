#132 — Premiere sequence Genie variable

Le18/10/2026 Austin signale une premiere sequence toujours identique avec les memes reglages. La configuration sg_config demarre a0x6d2b79f5. Le PRNG xorshift et les regles musicales restent identiques.

Le helper propre de60octets intercepte uniquement le chargement de graine apres validation de sg_generate. Au premier passage valide, XOR du compteur DMA natif0xfc07000c avec la graine courante ; valeur nulle remplacee par la graine de secours. Ensuite aucune nouvelle lecture du timer, uniquement la graine avancee du generateur. Pas de travail periodique, nouveau timer ou hook audio. Une configuration invalide ne modifie ni seed ni flag.

Preuves : tools/emu/test_genie_entropy.py,128 horaires initiaux par profil USB. A reglages identiques les premieres sorties varient ; sorties/graines exactes par rapport au generateur original initialise avec la graine attendue. Appels suivants sans reseeding, refus invalide intact. Boot signe, catalogue18machines, stockage et MIDI verifies.

Austin confirme « genie fix worked, push that to main » le18/10/2026. Promotion principale1.99 demandee, sans diagnostic ni candidats audio1-3. L absence de repetition n est pas garantie lorsque les contraintes musicales forcent un resultat.
