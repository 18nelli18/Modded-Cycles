# 165 — WAVE : precharge et BACK dans les dossiers (v115 prive)

Suite au retour AveyCole du24/10/2026 : v114 reste silencieux meme SWEEP ouvert ; les tables importees avaient fonctionne. BACK quitte la selection au lieu de remonter. Recette `wave_starter_assets.py --wave-starter`, sources `wave_starter/`, preuves `test_wave_starter115.py` et `test_wave_browser115.py`. Adresses : VA OS1.13.

## 1. Chargement

La cause materielle exacte du silence114 n'est pas encore confirmee. Sa preuve couvrait le tableau de dispatch mais pas un appel direct a46779000 avec un etat de table vide.115 elimine cette dependance : COUNT4677b2a0 et BASE4677b2b8 sont initialises pour les six pistes dans le runtime, et le prologue original46779000 est detourne vers le fallback. Le trampoline rejoue exactement `lea -64(sp),sp;movem d2-d7/a2-a6,(sp)` puis reprend46779008. Tous les pointeurs caches vers l'entree originale passent donc par le fallback. Le tableau de dispatch conserve son pointeur original.

[FAIT en emulation] Un demarrage dont les4Mo de RAM runtime sont pre-remplis deA5 retrouve les six COUNT68608 et BASE46860000, ainsi que le SHA PCM d33d2706ae0f6bbfb0bd2b5f539c0eb8e502719e7522ce7c5c053e43d7af5fe7. Le meme test114 retrouve des pointeurs nuls : le banc vide n'inventait pas les octets du PCM, mais ne prouvait pas l'activation dans tous les chemins. Aucun resultat materiel pretendu.

Le code WAVE est a46849000, sous4684a000 ; le seul nouvel etat du navigateur est back_owner a4684a000, dans le padding avant LEGACY46850000. Assertions sur le trou et les fins. Le PCM et les six tampons restent comme la disposition ci-dessous, sans reservation audio supplementaire.

## 2. BACK

Le key handler natif400a6d5c a plusieurs chemins selon le mode courant.115 intercepte seulement BACK physique12, premier appui, wt_lock actif et machine14. Si le dossier courant du FileSystemDirectory (`PM+640`, getter4007cf72) differe de wt_root4677ab6e, il appelle directement le chemin parent natif400a6f8c avec le meme cadre de pile et les registres attendus. La release et les repetitions du meme appui sont consommees pour empecher une fermeture consecutive. A la racine, sans verrou WAVE ou sur une autre machine, delegation native.

Les trampolines rejouent le prologue8octets `link fp,#-116;movem d2-d7/a2-a5,(sp)` ; la sortie native restaure la pile. Le chemin parent charge A2=PM et D2=event ; D3=1 indique un evenement traite. Aucun acces fichier dans l'IRQ, aucune modification globale de BACK.

## 3. Validation

[FAIT en emulation] Key native et navigation native, seules API de stockage et destinations UI factices : dossier300 ->200 ->100, modes fichier/preset0 et1, appui1, repetition21, release20. Aucun close avant la racine, puis un close natif a la racine. Une autre machine garde son changement de mode natif. Pile equilibree. Les preuves audio/import WAVE de la revision114 restent valides, plus recuperation par l'entree originale des six pistes.

[A FAIRE] Nouvelle verification physique du silence, du sequenceur sans navigateur, du retour dans deux sous-dossiers et d'un import connu. Pas de promotion publique avant ce retour. Regular et adult fournis separement.


## Publication et resultat materiel (24/10/2026)

AveyCole : "115 worked, go ahead and push that." Approuve la promotion exacte reguliere en2.37. SHA SysEx `9305c3ae7727fde21bd63fec305a7cdb89ab0bf6f77332bf372f92848fdb476a`, MAIN `6bbae768295095d82d106606af79b24f76ff868f34e35b2fc5c85b7128bfaff4`. Adult non publie. Table16trames,68608echantillons s16BE (137216octets) a46860000..46881800 ; six tampons de3Mo a46900000..47b00000. Source originale AV-WAVE-Morph.wav et convertisseur WAVE existant de Kevin-Shallvari/Modded-Cycles, revision5b6108ee57cdee4767f91bfb894ccefaadf4210d, MIT. Aucun changement du DSP WAVE. Preuves natives audio/import/boot/navigation et validation navigateur du chemin de livraison fixe.
