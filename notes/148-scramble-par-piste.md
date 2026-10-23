# 148 — SCRAMBLE par piste et principal2.20

AveyCole demande une liste dans Mod Setup et sixparametres : Pitch,Decay,Color,Shape,Sweep,Contour. DATA ouvre et coche ; BACK remonte d’un niveau. Preferences par piste. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] v46/v46nf ajoutent un septieme item Mod Setup et un sous-menu natif a sixcases. Masque initial60 : Pitch/Decay Off, quatreparametres originaux On. Sixmasques globaux par numero de piste, conserves entre projets et extinctions dans /Scramble.cfg, SC01 avec valeurs/complements et garde finale. E/S uniquement UI, transport arrete et stockage pret ; BACK programme la sauvegarde, corruption conserve les defauts. Ce ne sont pas des champs de pattern.

Code propre tools/machines/scramble_mask, assembleur MenuView reutilise du mod DX. Zone nulle467c9000..467cf000, BSS467cf000 avant Feral467d0000 ; aucune reserve sample agrandie. Generateur tools/scramble_mask_assets.py integre apres v45 dans gen_governor_recovery_test.py --scramble-mask. Source officielle reconstruite, attentes avant chaque detour.

sc_run est remplace par un plan de sixslots10,18,11..14, bornes et mappingCC natifs valides avant les ecritures Project. Wizard ne tire que Pitch/Decay facultatifs, jamais sample/mode. L’action MIDI Out conserve sa delegation preexistante. Les pas marques lisent event+8 pour la piste ; masques identiques, locks dans l’evenement seulement. Un pool plein est laisse intact si les nouveaux locks ne tiennent pas. Aucun getter UI ou E/S dans le constructeur de pas.

[FAIT en emulation]162cas live et162cas de locks par variante,18machines,6pistes independantes ; autresoctets intacts, masques0/1/2/4/8/16/32/60/63, sauvegarde/reload, fichiers invalides, DATA/BACK, vrai hook avec pile/registres/SR. Bootstrap natif exact et aucune source nonlue ecrasee. Tous octets DSP v45 conserves ;16blocs mixtes Feral/ChordKeys/Wizard exacts. Rendu natif128x64 inspecte : certains noms longs sont tronques par les champs natifs ; la correction des labels sera un suivi prive distinct.

## Publication approuvee

AveyCole : « v46 worked, make that the main push ». Principal2.20 = exact shared v46, SHA2db3be51ad7f7e44bfbd7919cd4babb583a38746672728bca2ef8c87d093627e, MAINce57c8033da13ef7f575e4a087e418f3973ba3497c1f565cd28bf9799df54d77. Les fonctions v43 et creditsPPPCCC/18nelli18/Glycinate restent. Variante sansfiltre et comparaisons privees conservees. Ni travail prive MD ni iconeF mentionnes dans les notes publiques.
