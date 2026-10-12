# Presse-papiers MIDI B

FUNC+REC copie la lane sélectionnée, FUNC+STOP colle, FUNC+PLAY efface.
Toujours limité à la lane B sélectionnée, même hors GRID RECORDING (demande
utilisateur). Pas de passage au presse-papiers pattern audio de l'OS.

Copie longueur/vitesse et64 pas. Le canal, port, activation et mute de la
cible sont conservés. Effacer conserve ces réglages et vide les64 pas ; les
valeurs par défaut restent C5/velocity100, sans trig actif. Un deuxième
clear/paste sur la même lane annule cette opération. Presse-papiers privé
indépendant, pas de transfert de données sonores A.

Avant mutation : clavier libéré, notes de la lane annulées. Copie mémoire
courte sous IPL7 pour que l'audio ne lise pas une lane partiellement copiée.
Appui long et relâchements ne répètent pas l'opération ni le transport stock.

Tests compilés : copie entre lanes,64pas, undo, autres lanes/audio/routage
intacts, releases après FUNC et transport ordinaire sans FUNC.
Sauvegarde persistante non incluse dans cette publication.
