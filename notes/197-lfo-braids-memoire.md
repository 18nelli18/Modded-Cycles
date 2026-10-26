# 197 - LFO au choix, gammes BRAIDS et memoire

AveyCole,26/10/2026 : «that worked. Let's push that to main and work on copy persistence». Generateur `gen_governor_recovery_test.py --lfo-compact-ram`, source v175 exacte. Adresses : VA OS1.13.

[FAIT] LFO count1/2/3/4, defaut2, Global > LFOs. LFO3/4 dans fichiers internes par projet/pattern/piste ; hors SysEx de sons et locks natifs. Pol. primaire/secondaire reste globale par piste, copie a corriger separement. Uni = onde/2+fade_gain sans overflow ; Mode conserve FRE/TRG/HLD/ONE/HLF.

[FAIT] BRAIDS quantizer d Emilie Gillet, MIT ; dix-neuf gammes par demi-tons. Off/ORGN/BRDS ; plus proche avec egalite vers le bas. Lock Off ne construit pas de table ; service differe apres readiness, pas d ecriture des defauts.

[FAIT en emulation] Public v164 : FUNC+SIZE en GATED active le pre-delay, puis le ring468c0000 ecrase Attack. v175 ring46940000..46980000. WAVE ancien46900000 chevauchait les LFO ; six nouvelles fenetres46a00000..47c00000. LFO code468f4000..468f5358, BSS468fc000..468fca58 ; gros buffer36928o alloue en UI seulement quand LFO3/4 demandes.

[FAIT en emulation] Bootstrap, menus, stockage, waveform/depth,57 912 mappings, releases,4 120blocs GATED et lectures WAVE six pistes. Les anciens175 tests/journaux prives accompagnent la session. SHA `99d392585a03a0f94cab0eb76fd1c16def0cc690230e909e821a09e01fa69bee`.

## Teste sur la machine (26/10/2026)

L utilisateur signale que v175 fonctionne puis autorise sa promotion exacte. v170/v171/v174 bloques au logo ; v172 fonctionne. Le test materiel valide le candidat ; il n identifie pas a lui seul laquelle des modifications memoire a resolu le logo. Aucune nouvelle mesure CPU revendiquee.
