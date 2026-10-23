# 156 - SCRAMBLE : vrai Decay, sans toucher Punch

Demande AveyCole du23/10/2026 dans Codex : la case Decay se coche mais n agit ni au geste bref ni sur pas marques,en machine Tone. Apres correction v66 : "Okay, that worked, publish 66". Publication exacte avec filtre partage comme principal2.28. Adresses : VA OS1.13.

## Reponse courte

[FAIT] Decay est slot18/CC80, Punch slot15/CC66. Le descripteur par machine du slot18 (50 pour Tone) ne correspond pas au descripteur commun24 retourne par le mapping inverse CC80. Le controle de coherence de plan() rejetait donc Decay en direct. Le constructeur de pas utilisait bien18 dans v64.

[FAIT] v65 a remplace18par15, erreur : cela ciblait Punch en direct et dans les locks. Le test initial appelait le champ15 "Decay" et ne validait pas l identite physique du parametre ; il reproduisait donc l erreur. Retour materiel v65 negatif confirme par AveyCole. Aucun v65 publie.

## Correction v66

[FAIT] Conserver18pour les locks ; resoudre le vrai descripteur commun par le mapping natif CC80 avant bornes,controle inverse et setter. Le meme plan alimente actions directes et pas marques. Aucun changement de cases,masques par piste,format /Scramble.cfg,defauts ni comportement des autres cases. Synthese,FX et audio compiles identiques au v64. Seul le module de masque change ; les references a son helper de bornes sont reliees aux nouveaux symboles.

Sources privees : tools/machines/scramble_mask/mask.c,tools/scramble_mask_assets.py,tools/gen_governor_recovery_test.py --scramble-decay-native. Construire depuis OS officiel,ne jamais superposer un candidat. Les macros separent v64,v65,v66 pour conserver les comparaisons.

## Preuves et limites

[FAIT en emulation] test_scramble_decay.py execute independamment Project::setParameter0x4000f2a2 avec CC80 puis CC66 pour identifier respectivement le champ18 et15. Sur19machines audio et6pistes :114cas par version ; v64 Decay inactif reproduit,v65 Punch modifie reproduit,v66 vrai Decay modifie et Punch conserve. Cases decochees inactives ; locks Decay18 seulement,sans modifier le son de base.

[FAIT en emulation] Vrai constructeur0x400548ce avec pattern serialise : Decay18dans le pool sur19machines,marque retiree avant moteur,base inchangee. Geste UI Tone : SETTINGS down,TRACK down,TRACK release,SETTINGS release via wf_key ; exactement un appel sx_run,vrai Decay modifie,Punch inchange.

[FAIT en emulation] test_scramble_mask.py :171actions et171evenements,menu DATA/BACK,sixmasques distincts,sauvegarde/reload,corruption de fichier,pool plein atomique,bornes. --check reproduit SysEx ; chargeur natif2 551 005octets exacts,garde733 539octets,aucune source compressee non lue ecrasee. Modules FX/chorus/crusher/latch/governor exacts v64. Ces tests simulent les observateurs du setter ; ce ne sont pas une mesure CPU physique ni un boot materiel complet.

## Test materiel et publication

[FAIT,retour utilisateur] AveyCole confirme v66 fonctionnel apres avoir precise Tone et les deux usages,puis autorise la publication. Le principal sert exactement ce fichier,avec guides EN/FR,PDF4pages et note de version2.28. Les autres corrections et effets2.27 restent.

SysEx : `f94a8f52b1832099e30df16fd48361eb2934a4fe08c7e2b56f864cae5132441a`.
MAIN : `e1cdefe371cf938d4d4aa2c84080a50dafc3514cccc3a476490f2d396be11a8e`.

Seul conteneur suivi modifie : `docs/flasher/all-features-usb-2ch-default.syx`,voie etablie autorisee. Preuve navigateur du telechargement exact et rejet checksum avant publication.
