# 172 — Mod Setup vers MACHINES

Demande AveyCole du24/10/2026 apres publication128 : MACHINES apparait mais sa molette ne change plus les machines jusqu au retour BACK. Adresses : VA OS1.13. Correction privee129 reguliere et adulte ; principal128 conserve.

## 1. Reproduction

[FAIT en emulation128] Appui bref SETTINGS13 + TRACK2 ouvre menu=1. MACHINES5 est transmis (retour0), mais menu reste1 ; sx_encoder consomme DATA et change la ligne Mod Setup au lieu de deleguer au selecteur. Meme proprietaire global dans Scramble et S.Chn.

## 2. Correction

[FAIT implementation] WM_MACHINE_EXIT, active seulement avec --menu-handoff, ferme wm_menu/wm_editing/wm_pending sur le nouvel appui MACHINES. Evenement intact, retour0 natif ; sx/du nettoient leurs sous-pages en remontant leurs wrappers existants. Aucun changement audio ou format de sauvegarde, ancienne recette128 conservee.

## 3. Preuves

[FAIT en emulation] Deux lexiques :12cas racine/edition/Scramble/Sidechain/Mute, hook encodeur de menu reel et delegation native, evenement physique intact, reouverture/BACK et releases des modificateurs. Vrai DrumSelect EncoderEvent400a28b4 vers setMachine :23machines et retour inverse, MIDI Out dernier. Tests de gestes123 conserves (tap/hold/marqueur de pas), anciennes recettes128 exactes,129 reproductible. Toute la memoire runtime et le code natif resident sont identiques128 hors region UI4684d000..4684f000. Aucun changement audio ou stockage. Test appareil attendu.

## 4. Fin du son precedent

[FAIT en emulation stock] Question AveyCole : ancienne machine audible apres changement jusqu a la prochaine note ou fin Decay. Le vrai moteur OS1.13 garde Tone4 apres selection Kick0 sans trig. La prochaine note change bien la voix en Kick0 au bloc suivant de son pipeline. Le choix du type et reset sont conditionnes par le trig precedent en400a7dac..400a7dde. Comportement natif conserve dans129 ; aucun ajout de coupure des queues.

## 5. Promotion demandee

AveyCole : «Go ahead and push that» apres livraison129. Publication2.42 reguliere exacte ; aucune validation physique exhaustive revendiquee. Adulte prive ; blurb fourni identique. Guide2.41 conserve, commandes inchangees.

SysEx `71697a12c13b38e9ec30efde7f91c378390b6a909b950389e5e8b534bc9cd55b`, MAIN `4ab1f623db445f10d58d131b8178ea40c9afb049e46af3e5e5da3e75586d38fe`.

[FAIT publication locale] Vrai navigateur : image129 exacte, nom Supermodel_2.42.syx, importeurs WAV/DX7, guide EN/FR et layout mobile verifies ; aucun MIDI reel. Blurb SHA00da19e1... identique. check_overlaps :171tweaks et139ensembles valides. Sorties gen_flasher_tweaks/registry deja obsoletes avant promotion, inchangees (notes169/170).
