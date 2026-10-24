# 159 — Ring, Phaser, DUCK et encodeurs live

Demande AveyCole : DUCK plus distinct, Ring Mod dans le slot reverb, Phaser dans le slot delay. Puis les valeurs FX continuent de tourner lors du jeu live sur triggers en v92. Adresses : VA OS1.13.

## Conception

DSP original commun stereo a48kHz, aucune boucle ajoutee par voix ni nouveau ring audio. Ring : sinus128 interpole, phase32bits et multiplication. Phaser : deux allpass par canal, coefficient sinus module, feedback borne. DUCK : DSP delay natif/feedback conserves, seul le wet est attenue, hold puis recovery ; Amount0 exact Delay sur1550blocs natifs (DMA modelise).

## Entree et charge

V94 ignore les replays exacts du meme stamp/delta EncoderEvent pour les nouveaux parametres FX ; nouveaux deltas acceptes, aucun faux mouvement sur delta0. La copie Application40006158 est executee dans la preuve ; peripheriques et calendrier audio/UI physiques ne sont pas simules. Allocations popup espacees de30ms, valeurs mises a jour a chaque nouvel evenement. Sauvegarde apres1s de repos et transport arrete. Phaser/Ring emploient des produits32bits directs bornes ; aucune modification des moteurs SPEAK ni du gouverneur. Le noyau Phaser conserve la quantification fixe v94 approuvee, les revisions suivantes ne sont pas publiees.

## Memoire et preuve

Code FX principal46800000..46807dc0, BSS46808000..46815d64 avant SPEAK46818000. DSP supplementaire dans la section chaude46830000 bornee46840000. Menus opaques et choix appliques uniquement au relachement TRACK. Fichiers historiques FxMix60octets intacts, Duck10 et ExtraFx16 controles avec complements/sentinelles. Contrats de registres/EMAC et mixeur natif conserves ; les comptes instructions ne sont pas des cycles appareil.

## Appareil et promotion

AveyCole rapporte “that worked” et approuve explicitement v94, SHA256 `f0663f703bb6d85e85dfcc2fa5c99ae1785ab696bd9fe750e532759d1878e46d`, principal2.33. Le lexique adulte reste prive. GATED et deplacement Ring apres Chorus1/2 ne concernent que le prochain test.
