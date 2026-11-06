# 227 — Sample Wizard : pan pendant FUNC et valeurs numeriques

Demande utilisateur du6novembre2026 : remplacer le toggle DATA par un affichage pan pendant FUNC ; niveau et pan doivent suivre Num. Version conservee3.06, quatre editions.

[FAIT] La vue lit la touche FUNC courante au redraw : niveau sinon, pan pendant le maintien. Les trois voies clavier deleguent DATA sans capture ni etat persistant. FUNC demande un redraw a la pression et au relachement. Num lit le meme octet inverse4018fddf que Mod Setup ; Num On affiche LVL/PAN0..127, Num Off garde les rectangles. Le pan utilise le parametre22 de base a l arret, la frame audio courante en lecture pour les p-locks.

[FAIT en emulation] Chaque edition demarre et passe les six pistes, valeurs0/1/63/64/65/126/127, maintien/relachement FUNC, Num On/Off, priorite des vues natives et delegation DATA aux trois niveaux. Comparaison complete des captures : seules les plages Wizard UI et leurs detours changent ; SRAM et chemins DSP restent identiques. Aucun nouveau resultat appareil.

Sources : wizard_pan371.py, machines/wizard_display/display158.c. Preuve : emu/test_wizard_func385.py. Guides EN/FR et PDF36/9pages regeneres et controles.
