# 173 — Sidechain des retours Rev. et Del.

Demande AveyCole du 25/10/2026 : ajouter Rev. et Del. aux cibles Sidechain. Puis «130 worked, push to main». Publication reguliere130 en2.43 ; adulte prive. Adresses : VA OS1.13.

## 1. Routage et audio

[FAIT] Six sources conservant leurs cinq cibles pistes et leur option Mute. Deux nouvelles cases par source dans `du_fx[6]` : bit0 Rev., bit1 Del. Meme Dpt/Atk/Hld/Rel ; le gain minimal des sources actives gagne, sans multiplication cumulative. Les pistes non choisies restent intactes. Rampe32echantillons stereo, produits entiers signes fractionnes, aucun float ni allocation.

Le mixeur appelle deja `du_process` via le relais beat-repeat. Cette fonction publie les deux gains wet souhaites ; chaque callback applique le gain precedent vers le gain courant au moment natif de son retour. Les phases du pipeline sont conservees, sans supposer que le pulse et le retour se trouvent dans le meme point du bloc.

API fixe `0x46835ff0` : saut vers `du_return`. Appel a la fin de `fx_reverb` et `fx_delay`, apres les calculs de feedback. Pour Vinyl, traiter la correction wet/dry ajoutee au postmix, pas la piste seche. Del. cible le retour wet ; le traitement direct du crusher reste sur le chemin des pistes. Les buffers internes de feedback ne sont jamais modifies par ce gain.

## 2. UI et bornes

Douze lignes natives : cinq autres pistes, Rev., Del., Dpt, Atk, Hld, Rel, Mute. DATA bascule les sept cases et Mute ; edition numerique seulement pour les quatre temps/niveaux. MACHINES ferme encore Mod Setup et rend les encodeurs au selecteur.

Code DU dans0x46833000..0x46835800, BSS jusqu'avant0x46835ff0 ; banque FXP a0x46836000 jusqu'avant0x46840000. Region des gestes deplacee a0x4684f000..0x46850000 pour laisser davantage de place au codec F4 ; LEGACY commence ensuite. Sources130 dans `sidechain/returns.c`, incluse uniquement avec DU_RETURNS ; ancien controleur conserve dans `duck.c` pour reconstruire129 exactement. GCC13.1 ColdFire54418.

## 3. Sauvegarde compacte

Etat runtime78octets :72 precedents plus six masques de retours. Memes zones natives reservees :48octets a0x39d0 et six octets de padding du header (29,30,31,36,37,39 a partir de0x3990). Aucun champ natif supplementaire, aucun agrandissement du projet.

Sans cible FX : F2/F3 byte-identiques. Avec cible FX : F4,404bits de payload + tag4bits0xA + CRC24 =432bits, soit exactement54octets. La premiere demi-octet de payload partage le premier octet avec le tag ; le reste est decale de quatre bits. CRC sur51octets de payload, quatre bits hauts finaux nuls. Lecteur FXS1/F2/F3/F4 ; anciennes versions ne restaurent pas les reglages ajoutes des patterns F4. Garder une copie anterieure avant downgrade. Desactiver les deux cibles de chaque source remet le format F2/F3.

## 4. Preuves

[FAIT en emulation] Codecs projet/pattern natifs, Save Project/cache Load, clipboard/copie/reset, activation differee, blanc et reouverture dans un nouveau processus.78valeurs independantes ; metadata native et ChordKeys preserves.4096combinaisons de cases Rev./Del., tous les types FX, flags Mute, limites des controles, CRC et rejection des54octets corrompus un par un. Anciennes sauvegardes121/127/128 et reemission F2/F3 exactes.

144cas audio manuels : six sources, retours seuls ou doubles, politiques Mute/solo, rampes stereo exactes y compris bornes int32, sources independantes et aucun rejeu au demute. Les pistes seches sont inchangees pour des cibles FX seules. Bypass du traitement de pistes :9instructions emulees. Avec six sources/pistes stereo :7122instructions emulees, aucune deduction de pourcentage CPU physique.

Mixeur natif :15compositions conservent les PCM129 quand les cases FX sont Off. Neuf types du retour Rev., dont Vinyl/correction, appliquent le gain seulement au retour ; entrees/queue interne et Delay inchangees. Sept chemins du retour Del. : sortie attenuee, feedback natif identique avec DMA modelise, MACSR/ACC restores. Le test capture les gains au vrai callback, afin de respecter l'ordre des blocs audio.

Douze transitions de menu,23machines, gestes tap/hold et p-lock Scramble verifies. Rendus128x64 Rev./Del./Mute et controle des largeurs. Recettes129 et130 reproductibles exactement. PDF public et guides prives : six pages rendues et inspectees ; navigateur reel : image130 exacte, nom Supermodel_2.43.syx, guide bilingue, importeurs et blurb fourni inchanges.

## 5. Publication

Rapport utilisateur : «130 worked, push to main». Aucun chiffre CPU materiel revendique. SysEx regulier `881099ad7b7d8505f1850f13ffb17eb5688ffa5e69e0038d9cf1e2ae5be22fb3`, MAIN `176faf7748d706a15f65652383a7e5cc495817ff78bfad830dd6de71f288fe18`. Le lexique adulte reste hors Git public. Sorties gen_flasher_tweaks/registry deja obsoletes avant promotion, inchangees : voir notes169/170.
