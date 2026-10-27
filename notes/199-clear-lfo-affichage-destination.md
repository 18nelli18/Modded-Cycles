# 199 - Clear des LFO et destination native

AveyCole27/10/2026 confirme v189 : "Perfect, push it." Adresses : VA OS1.13.

[FAIT] Apres la commande complete400149fa, remettre quatre banques a zero et publier les cinq champs LFO2 ; le sync audio40183408 ne recharge plus des valeurs precedentes. Undo son couvert ; Undo pattern des fichiers LFO3/4 non etabli.

[FAIT]4000a830 termine en4005a692 en reecrivant sa pile context/destination vers destination/machine. Le callback4002650e recoit donc context/descripteur/destination/machine. Lire argument4 affichait toujours FLT sur ESTUS ID24 ; argument3 corrige le rendu. Le test complet echoue en v188 puis passe2592cas en v189.

[FAIT] Les controles ESTUS SETTINGS n exigent plus transport arrete. Retour appareil positif sur les trois corrections. Copie/Undo/stockage et ESTUS controles verifies en emulation ; aucune mesure CPU appareil nouvelle.

Preuves : tools/emu/test_lfo_clear189_native.py et test_lfo_destination189_renderer.py ; candidat v189 local requis. Empreinte exacte : 6a729fbf198b50768ec1bfade96d6627ab11f08cea210f452586927d207a3282.
