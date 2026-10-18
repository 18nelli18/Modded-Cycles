# 123 - Source ChordKeys apres recompression Swarm

Demande AveyCole le18/10/2026, capture du rapport Amb055 : preparation refusee avec « l'image ne finit pas ou le tweak l'attend ». Liste : preview/removal/arp/dim/LFO2, ACID, cinq moteurs Syntakt, WAVE, Wizard, Attack, filtre, USB6, raccourcis performance, preview samples, noms longs et animation Supermodel. Demande explicite : ne pas changer Select All ni les autres combinaisons qui fonctionnent. Adresses : VA OS1.13.

## Reponse courte

[FAIT] Reproduit avec le firmware officiel : Wizard finit a0x401c0d60 ; moteurs wizard-machines-223 compresses finissent a0x401e77bf, mais ChordKeys attend0x401e77c6. Sept octets de difference apres remplacement Swarm LITE. Le builder refuse correctement ; ne pas contourner sa garde par du padding arbitraire.

## 1. Cause

composeWizard calcule la source ChordKeys a partir de la taille du catalogue avant Swarm LITE. La couche Swarm change les octets du moteur puis le recomprime. La source ChordKeys et son lea41f9 dans chord_boot restent anciens. Le corps ChordKeys n'a pas change. Le beat repeat est prepare ensuite d'apres cette source perimee.

## 2. Reparation ciblee

La copie test appelle tools/web/swarm-chord-layout.js depuis Swarm, avant les couches MIDI/repeat. Seulement si Wizard et un ChordKeys append se trouvent directement apres un moteur compresse modifie : verifier les references, verifier que l'ancienne source etait exactement l'ancienne fin du moteur, calculer la nouvelle fin et verifier lea(source)/lea(destination) au debut du vrai chord_boot. Modifier seulement append.at et l'immediat source du chargeur ; actualiser la reference des writes. Le contenu des payloads reste identique. Si la source est deja correcte, retour identique sans mutation. ChordKeys embarque dans une banque et Select All suivent leur composition existante.

Les references originales sont restaurees par la couche Swarm avant chaque nouvelle resolution de selection. Pas de nouvelle reserve memoire, pas de DSP ou parametre change, garde du builder conservee. Les autres problemes minimaux observes lors du diagnostic (chargeurs natifs ACID/MACRO sans support) ne sont pas modifies par cette correction.

## 3. Validation et statut

tools/test_swarm_chord_layout.js reproduit le refus avant reparation, signe/verifie le resultat, compare les contenus de tous les payloads, et compare les compositions/references des selections deja valides. Comparaison du fichier Select All signe avant/apres. tools/emu/test_swarm_chord_layout.py execute le vrai bootstrap, compare ChordKeys charge, execute le hook stockage401c4b44 et l'initialisation cache disque. Code propre, aucun firmware publie.

Page test separee avec diagnostic CPU/CUT facultatif conserve ; principal et909 inchanges. Verification sur appareil encore attendue.

[FAIT en emulation] Huit builds signes : liste rapportee avec/sans invert-track, liste etendue Genie/SCRAMBLE, variante sans Swarm, sans ChordKeys, Select All, complet sans MIDI, diagnostic. La variante sans Swarm portait aussi une ancienne source de six octets : meme recompression de regions communes, refus original reproduit puis repare sans changement des payloads. Select All est compare fichier signe entier, strictement identique. Compositions et references sans Chord et complet sans MIDI identiques. Bootstrap/hook stockage/cache verifies pour rapportee, etendue, sans Swarm, diagnostic, Select All et complet sans MIDI.

La variante de la liste avec Banque MIDI ajoutee echoue deja avant correction avec MIDI Bank: unknown machine startup et garde exactement ce refus apres correction. Ce probleme distinct, ainsi que les erreurs minimales ACID/MACRO observees precedemment, sont hors scope ; aucune garantie toutes combinaisons n est revendiquee. Les compositions fonctionnelles controlees ne changent pas. Aucun fichier principal ou909 ne fait partie de la publication.
