# 129 — Accordage fin MACRO sans perdre le Lo-Fi

Demande AveyCole du18/10/2026 : verifier le partage de FUNC+PITCH entre le Lo-Fi MACRO et l'accordage fin, puis fournir un autre geste si necessaire. Sources `tools/machines/macro/fine.c`, `fine.S`, `fine_draw.S` ; generateur `tools/gen_macro_fine_test.py` ; preuves `tools/emu/test_macro_fine.py` et `tools/test_macro_fine.js`. Adresses : VA de l'OS1.13.

## Reponse courte

[FAIT] MACRO utilise le parametre FINE17 pour sa reduction de frequence/bits. Son controle FUNC+PITCH ne peut donc pas simultanement regler cet accordage. La hauteur native PITCH10 contient deja une fraction8.8 ; le calcul Braids de MACRO en conserve une resolution de deux unites, soit1/128demi-ton (0,78125cent). Le test ajoute SETTINGS+PITCH pour cette fraction. FUNC+PITCH garde exactement le Lo-Fi. Aucun changement du DSP ou du format de sauvegarde.

## Interface et composition

Le relais de recherche du potard4001e8da appelle toujours le precedent relais Lo-Fi et ne remplace pas le descripteur43. Uniquement pour PITCH42 sur MACRO, les callbacks d'edition/format/dessin sont enveloppes ; les originaux sont gardes et executes sur les autres machines. Les fractions sont conservees quand PITCH est ensuite tourne normalement. Les bornes viennent de l'OS,40<<8..88<<8 ; aucune extension arbitraire0..127. Affichage signe a trois decimales, par exemple+0.008.

SETTINGS vient du drapeau partage du support commun quand disponible, sinon du getter natif. Le drapeau mod_used evite CONFIG apres le geste ; le fallback autonome intercepte sa release via40077720. FUNC prend priorite sur le geste fin. Compilation GCC15.2.0, -mcpu=54418. Code UI1116octets, appende apres le dernier payload ; references32bits relocalisees et gardees, taille du chargeur mise a jour. Pas de stockage dans une structure projet inconnue.

Le dessin derive du relais de valeur Lo-Fi existant du projet, sous sa licence MIT ; le code de synthese Braids/Mutable Instruments et ses credits restent inchanges.

## Verification et limites

[FAIT en emulation] Deux vrais profils construits/signes, Select All avec et sans banque B. Boot du firmware avant/apres ; lookup natif et vrai setter4000b7d6,72editions fines aux limites ;128valeurs Lo-Fi identiques ; popup decimal rendu avec les primitives OS ; autres machines gardent edition/texte ; vrai codec son conserve fractions2/126/128/254. Les fonctions de calcul DSP ne sont pas modifiees. Aucun resultat materiel revendique.

Le diagnostic CPU/CUT reste propose dans ce test quand Syntakt et beat repeat sont installes. Le profil MACRO seule rencontre deja un refus du chargeur Lo-Fi dans le principal ; ce travail ne le modifie pas et ne revendique pas sa validation. La page de test utilise donc le preset complet prouve, seule la banque B reste selectionnable. Les flashers principal et909 restent inchanges. Verification materielle des gestes, sauvegarde projet et rendu sonore attendue avant toute promotion.
