# 187 — Valeurs de depart des machines ajoutees

AveyCole25/10/2026 transmet une remarque : les zeros sembleraient etre au centre64, notamment TINY/PUNCH/ELDER ; recommande de verifier puis documenter. L utilisateur demande d ignorer sa derniere phrase sur le «mod jank». Aucun changement des controles autorise par simple supposition.

## Reponse courte

[FAIT en emulation] Les85popups des17machines ajoutees, pour les cinqparametres specifiques, affichent leurs minima/milieux/maxima propres. Les commandes numeriques0..127 affichees0 correspondent au minimum0, pas64. PITCH42 et FINE43 sont differents : le formateur natif affiche0 pour raw64, comportement centre normal. La remarque n etablit donc pas une erreur generale de conversion0->64.

TINY : valeurs par defaut64/0/64/32/60 ; Elder0/0/0/0/50 ; PUNCH64/KIK/4:1/40/50, ordreCOLOR/SHAPE/SWEEP/CONTOUR/DECAY. Les descripteurs et les popups natifs sont executes sur154 ; le DSP/controlUI horsLEGACY est identique153 et148. Lecture du bridge natifTINY4677c000 : les octets COLOR/SWEEP/CONTOUR sont transmis sans ajout64 ; PITCH/FINE retranchent leur centre. Les bridges sources PUNCH et Elder passent egalement les commandes de timbre0..127 sans ajout64. Cela ne prouve pas que chaque modele sonne neutre a0 ; aucun neutre universel n est affirme. Le modele Stretch du sampler a seulement ete rapporte, pas reproduit : pas de procedure de remise a zero ajoutee sans preuve.

## Guide

Source canonique publish-v105/tools/shortcut_guide_content.json, generation HTML/Markdown EN/FR et PDF ; paragraphe ajoute aussi a docs/guide/index.html. Valeurs initiales et distinction commandescentrees/unipolaires, pas de remappage ni nouveau firmware. Generateur PDF corrige son sous-titre obsolete2.45 vers2.47. Sixpages rendues ; controle visuel du contact de touteslespages et de la page modifiee, aucun chevauchement/coupure. Publication non effectuee, guide local seulement. Les images de firmware et donnees privees ne font pas partie de la modification du guide.
