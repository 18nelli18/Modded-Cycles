# 179 — DUB sur les deux canaux

Demande AveyCole le25/10/2026 apres le diagnostic178 : «Alright lets make dub not only go right». Generateur prive `--dub-stereo`, source `tools/machines/fx_menu/ping.c`, preuve `tools/emu/test_dub_stereo148.py`. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] DUB utilise maintenant l'entree stereo du delay natif, sans permutation des retours. Une source mono centree donne les deux canaux des le premier echo, meme avec feedback0. Le filtre HP/LP DUB, Time, Feedback et Send sont conserves. PingPong garde sa route alternee et ses samples exacts. Base146, aucune optimisation147.

## 1. Cause et correction

Avec FX_DUB_DISTINCT, DUB9 partageait le chemin PingPong5 : somme mono dans nd_feed gauche, silence droit, puis permutation du retour avant feedback. Premier echo a droite ; la gauche dependait du feedback et devenait plus faible apres filtrage.

La nouvelle definition de compilation FX_DUB_STEREO retire9 de la permutation dans fx_delay_return et envoie directement in a la routine native0x40057488 dans fx_delay. dub.S reste byte-identique, avec ses coefficients0x7b000000/0x7d000000. Aucun buffer, etat, gain correcteur ou cadence ajoute. Les recettes anterieures sans ce flag restent exactes ;146 --check reconstruit l'empreinte archivee.

## 2. Preuve native

Bootstrap et code148 reels, seule la file DMA modelisee (8blocs). Rafale32samples,192blocs, feedback interne0/12000. Comparaison146/148 : Delay0, PingPong5 et Duck10 strictement identiques pour chaque sample dans les deux reglages. Ancien DUB146 a feedback0 reproduit avec canal gauche exactement nul.

DUB148 mono centre : L/R identiques sans feedback ; energies0,1226546932488896 par canal. Avec feedback : energies0,14435638339628207 et0,1443563834048556, ecart maximal2LSB Q31. Le delay natif ordinaire presente deja14LSB d'ecart dans ce banc de feedback ; la preuve de balance admet16LSB, sans modifier l'arithmetique. Les autres comparaisons restent strictes. Sources gauche seule, droite seule et opposees preservees : aucune sommation mono ni annulation de phase imposee.

## 3. Integrite et regressions

Seul l'objet FX ping.c change ; autres objets FX, dont dub.S, exacts. PUNCH, Sidechain, HALL rapide, filtre MACRO, gouverneur, MIDI et QntM conserves. Pointeurs des relais UI/FX regeneres. Standard/adulte : meme FX binaire ; images reproductibles depuis le conteneur officiel, autres sections dont bootloader/updater identiques.

Tests popup/BACK, MIDI24machines/sixpistes, QntM et integration native des retours reverb/delay avec Sidechain passes. Aucune promotion du principal, aucun changement de controles. Le retour stereo est volontairement audible ; le fichier prive README le decrit. [A FAIRE appareil] Verifier DUB feedback0 puis repeats, mono centre puis pistes pannees, et comparer P/O/N a146 sur le meme pattern. Aucun gain CPU physique revendique.

## 4. Promotion2.47 (25/10/2026)

AveyCole autorise : «Okay, push that. then work on more optimization in test». Publier le standard148 exact SHA `442c1720818c7c5e6798cadbebbd29e37288eae09d9a80c3ce3b7b743f2397d4`. Autorisation de publication, sans inventer un resultat hardware ou P/O/N. Les recherches suivantes restent dans des builds de test.
