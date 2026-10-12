# MIDI LFO : destination défilante et clavier

Test 3 uniquement : six caractères maximum dans Dst, aller-retour à quatre
caractères/seconde, pause une seconde aux extrémités. Nouvelle destination :
retour au début. Invalidation UI limitée à quatre fois/seconde.

Les trigs 16–31, appui et relâchement, restent dans le clavier B sous le menu,
y compris avec REC actif. Aucun pas édité. Fermeture : annulation des notes
clavier encore tenues. Le pad sélectionne la lane MIDI B et son canal.

Vérifications : page placée, fenêtres et bornes, clavier Note On/Off avec
REC actif et pattern intact, boot complet, navigateur et transferts simulés.
Writer/périphériques simulés ; vérification matérielle de ces changements
encore attendue. Sauvegarde persistante non incluse.
