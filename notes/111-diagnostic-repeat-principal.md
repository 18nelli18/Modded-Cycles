# 111 — Diagnostic CPU/CUT du repeat sur copie principale

Demande AveyCole du 17/10/2026 : remettre le diagnostic utilise pendant les tests repeat/SY sur une copie de la checklist principale. Les essais repeat MIDI et filtre MIDI sont abandonnes. Adresses : VA OS 1.13.

## Reponse courte

`flasher-beat-diagnostic-test` ajoute une carte Diagnostic charge audio. Choisir cette carte, le beat repeat et au moins un moteur SY (qui fournit les compteurs natifs existants). Maintenir TRACK+RETRIG pendant le probleme, avec ou sans division, puis relacher un bouton : CPU moyenne/pic et CUT. CUT compte les pistes distinctes observees en fondu/suspension pendant le geste, y compris celles deja suspendues. Aucun flag du regulateur modifie ; diagnostic seulement, aucune correction des clicks annoncee.

## Construction

`gen_beat_diagnostic.py` compile une copie du repeat principal actuel avec uniquement les sondes de l ancien test SY. Les calculs DSP repeat, Swarm LITE, filtres et autres mods gardent les versions principales. Le chargeur ROM et sa reservation sont ceux du principal courant. `gen_beat_repeat.generate` accepte un dossier source facultatif ; sans argument le comportement du generateur principal reste identique.

Le wrapper de composition ne change le module repeat que lorsque la carte diagnostic est cochee. Il lie gov_load, gov_avg, gov_fading et gov_stolen du vrai catalogue avec gardes des pointeurs initiaux, puis recalcule les references. Aucun firmware ni dump exporte dans git. Nouvelle combinaison experimentale ; principal publie inchange.

## Preuves

[FAIT en emulation] Vrai boot/cache du SYX navigateur, module exact, gestes/16 divisions/64 masques/exclusions et fondus, stereo Wizard, annulation Stop/projet, ABI et allocations. Le test --meter verifie valeurs Q8, pic, CUT cumulatif/reset, flags regulateur intacts et popup UI. Navigateur : checklist complete avec/sans banque, sans Wizard et diagnostic decoche. Parite Python/navigateur pour les builds prepares. Peripheriques simules ; charge et clicks physiques a mesurer par AveyCole.


## Test 2 et retour AveyCole (17/10/2026)

AveyCole rapporte CPU 73/101 et CUT 4 avec Kick, Snare, Metal, Perc, Tone et SD Vintage, filtres et beat repeat actifs : moins de clicks mais clicks persistants. Ces mesures indiquent des pointes au-dessus du budget ; elles ne prouvent pas que chaque click vient du regulateur.

Le candidat 2 specialise le plateau plein du repeat : phases contigues, enveloppe a un, capture uniforme, six fades deja etablis. Plus de trajectoire intermediaire dans ce cas. Conversion et bits bas conserves exactement : sortie = historique*32768 + residu signe des neuf bits bas du live. Si enveloppe/fondu/bord/historique impose le chemin general, celui-ci reste actif. Aucun filtre ni moteur sonore modifie.

[FAIT en emulation] Audio, historiques complets et fades identiques au principal : mono/stereo, divisions et masques variables, 110 frontieres par cote (longueurs courtes, enveloppe, wrap circulaire et temps32). Instructions propres : -10,7 % sur la sequence mixte et -28,0 % sur la repetition etablie longue. Ce ne sont ni des cycles materiels ni une garantie de disparition des clicks. Diagnostic CPU/CUT conserve dans le test 2.

Consigne explicite AveyCole : garder le diagnostic dans tous les futurs tests, jamais dans le principal publie. Regle ajoutee a AGENTS.md. Demande suivante : optimiser aussi l ensemble du chemin audio apres livraison du candidat repeat ; travail de profilage distinct, aucune reduction sonore implicite.
