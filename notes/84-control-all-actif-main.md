# Control All Config : piste active sélectionnable, sur main

Recette de controls-control-all.json précédemment confirmée fonctionnelle sur matériel par AveyCole, avec active_track_excludable=true. Code identique ; seul statut du mod devient tested. Aucune copie LFO2 expérimentale n’est ajoutée.

TRACK + TRIG1–6 choisit les pistes audio incluses/exclues ; la piste active n’est pas forcée. TRACK + potentiomètre agit sur les pistes incluses. Trigs allumés = incluses. Choix en RAM, réinitialisés au démarrage.

Contrôle natif : 64 masques × six pistes actives × cinq boucles stock, LEDs et pile, press/release/repeat/long ; exécuté avec Chord TG sans Banque puis avec tout le bundle principal. Huit sélections navigateur avec références writes/payload strictes et conteneurs vérifiés : mod seul, Chord+TG sans machines, moteurs facultatifs, performance, Select All et Banque sans Chord.

Les travaux no-TG restent sur codex/independent-startup-20261014. Le main conserve les chemins TG, clear/Undo et LEDs nouveaux, sans sauvegarde MIDI.
