# 228 — Restaurer les noms du menu delay

Signalement utilisateur du6novembre2026 : fenetre de selection delay vide.

[FAIT] Le retrait384 effacait RX_C jusqu au tableau des pointeurs de noms. Les chaines des sept autres delays etaient placees juste AVANT ce tableau et ont ete effacees avec les tables DSP. Le test ne cherchait que l absence du nom retire ; il acceptait donc des chaines vides.

Correction : restaurer uniquement les sept chaines DELAY, CRUSH1/2, PING PONG, DUB, DUCK, PHASER a leurs pointeurs existants. Le generateur384 arrete maintenant l effacement au premier pointeur de texte. Aucun DSP ni choix retire ne revient. Test renforce : trois vrais labels attendus pour chaque curseur, deux voies de rendu, quatre editions ; ancienne image refusee au premier curseur, images corrigees acceptees. Les tests de navigation, stockage et20raccords live sont conserves. Version3.06. Aucun resultat appareil revendique.
