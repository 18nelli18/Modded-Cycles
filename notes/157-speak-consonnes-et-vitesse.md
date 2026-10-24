# 157 — SPEAK : consonnes et lecture lente

AveyCole signale des consonnes rapeuses puis un silence sous Speed60 meme avec Decay127. Enregistrement utilisateur fourni : analyser les transitions consonantiques, pas seulement la fin du mot. Aucun enregistrement utilisateur ni lexique prive ajoute au depot. Adresses : VA OS1.13.

## 1. Consonnes

[FAIT emulation] Bruit S/Z reduit de0,7 a0,35 du prototype, SH/ZH0,4 et autres0,5 au lieu0,8 ; resonances bruitees elargies, poids aigu reduit, transitions coefficients ralentis d un cran. Aucun gain de voyelle retire, aucune nouvelle boucle DSP. Comparaison AH/US ~0,07157->0,07125FS RMS ; S ~0,2528->0,11546 ; K dans la phrase ~0,15113->0,09944. Durees conservees. Ce sont des mesures, pas un verdict perceptif.

## 2. Vitesse

[FAIT reproduit] Speed0, Decay127 : silence initial long, compteur idle a son seuil ; index phoneme fige0 avant la premiere consonne. La lecture native ne rappelle plus le moteur. Dans speak_render, seulement tant que le mot est inacheve et que son enveloppe autorise le rendu, remettre son compteur quiet a0 (`0x4673205e + piste`). Ne jamais modifier FREE, STOLEN, FADING ni PRESSURE. Mot termine/enveloppe eteinte : comportement idle habituel. Nouveau banc natif180blocs Speed0 : progression vers phoneme1, RMS0,02896 au lieu0,00013.

## 3. Validation et publication

[FAIT emulation]128mots complets, bornes, hauteur/vitesse independantes, popups et carte21machines ; six pistes220blocs avec24changements de mot ; bootstrap2623158octets exact sans ecrasement source. v85 reste fige et reproductible sans les options nouvelles. [FAIT approbation] AveyCole demande explicitement la publication reguliere v87 comme principal2.31 ; cette demande ne constitue pas une mesure exhaustive de charge sur appareil. SHA256 `97d4c95a3ab7c7e5b8e5a8bb9eb10d6d004bb03a52a3937d2d6ff03ba71570bf`, MAIN `4f2800f2d7218118788a4fbd284b5486487836253649215e9fe047eb845f5b61`.
