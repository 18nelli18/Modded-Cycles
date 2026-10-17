# 111 — Diagnostic CPU/CUT du repeat sur copie principale

Demande AveyCole du 17/10/2026 : remettre le diagnostic utilise pendant les tests repeat/SY sur une copie de la checklist principale. Les essais repeat MIDI et filtre MIDI sont abandonnes. Adresses : VA OS 1.13.

## Reponse courte

`flasher-beat-diagnostic-test` ajoute une carte Diagnostic charge audio. Choisir cette carte, le beat repeat et au moins un moteur SY (qui fournit les compteurs natifs existants). Maintenir TRACK+RETRIG pendant le probleme, avec ou sans division, puis relacher un bouton : CPU moyenne/pic et CUT. CUT compte les pistes distinctes observees en fondu/suspension pendant le geste, y compris celles deja suspendues. Aucun flag du regulateur modifie ; diagnostic seulement, aucune correction des clicks annoncee.

## Construction

`gen_beat_diagnostic.py` compile une copie du repeat principal actuel avec uniquement les sondes de l ancien test SY. Les calculs DSP repeat, Swarm LITE, filtres et autres mods gardent les versions principales. Le chargeur ROM et sa reservation sont ceux du principal courant. `gen_beat_repeat.generate` accepte un dossier source facultatif ; sans argument le comportement du generateur principal reste identique.

Le wrapper de composition ne change le module repeat que lorsque la carte diagnostic est cochee. Il lie gov_load, gov_avg, gov_fading et gov_stolen du vrai catalogue avec gardes des pointeurs initiaux, puis recalcule les references. Aucun firmware ni dump exporte dans git. Nouvelle combinaison experimentale ; principal publie inchange.

## Preuves

[FAIT en emulation] Vrai boot/cache du SYX navigateur, module exact, gestes/16 divisions/64 masques/exclusions et fondus, stereo Wizard, annulation Stop/projet, ABI et allocations. Le test --meter verifie valeurs Q8, pic, CUT cumulatif/reset, flags regulateur intacts et popup UI. Navigateur : checklist complete avec/sans banque, sans Wizard et diagnostic decoche. Parite Python/navigateur pour les builds prepares. Peripheriques simules ; charge et clicks physiques a mesurer par AveyCole.
