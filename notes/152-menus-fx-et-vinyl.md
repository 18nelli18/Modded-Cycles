# 152 — Menus FX, chorus/reverb et Vinyl prives

Demande AveyCole, chat du 23/10/2026 : conserver tout v54, differer les changements de type jusqu'au relachement TRACK, ajouter chorus+reverb et Vinyl, conserver les commandes natives des combinaisons et distinguer les ordres FUNC/TRACK. Ajouter le ralentissement MACHINES, les raccourcis de copie temporaire pendant retrig verrouille et le diagnostic physique seulement. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] v55/v55nf prives, reconstruits depuis l'image officielle par `tools/gen_governor_recovery_test.py --fx-menu [--profile no-filter]`. Aucun changement du principal2.23. Checklist anglaise utilisateur : `output/firmware/validation/v55-test-checklist.{md,html}`. Les nouveaux comportements restent experimentaux jusqu'au retour appareil.

## 1. Contrats et memoire

- Module original `tools/machines/fx_menu/`, GCC m68k-elf13.1.0, `-mcpu=54418 -O2`, entier Q20, aucun calcul flottant ni allocation/E/S dans le DSP.
- Code `0x46800000`, BSS `0x46808000`, fin inferieure `0x46810000`. Extension explicite apres l'ancienne reserve1Mo ; le bootstrap copie le tail entier, et le banc de boot conserve maintenant2Mo pour cette composition. Tampon Vinyl stereo2x2048samples ; aucune modification des tables sample/voix existantes.
- Detours gardes : encodeur `0x400775f8`, reverb `0x40056a2c`, postmix `0x40056b38`, vtable popup `0x401005bc`, query held `0x4007faf4`, increment machine `0x400148aa` ; getter commun br_key_hook, diagnostic gr_beat_key et relais de dessin existants.
- Trampolines rejouent les instructions entieres du query held et du getter. Le wrapper audio conserve le contrat MACSR/ACC du relais chorus et capte mix/a4/a5 pour les gains dry natifs.
- `/FxMix.cfg`,60octets : FX01,27valeurs,27complements,A5/5A. Lecture et ecriture UI a l'arret ; sauvegarde differee TRACK/menu. Modes et controles globaux, trois groupes de six sends par piste. Migration initiale depuis les anciennes preferences, sans les reecrire. Pas de nouvelles destinations p-lock/LFO.

## 2. Menus et controles

[FAIT en emulation] Les IDs sauvegardes Delay/Crush0..4 et Chorus0..2 sont preserves. Ordres visuels : Crush2,Crush1,Delay,CRU1+DEL,CRU2+DEL ; Vinyl+Rev,Vinyl,Reverb,Chorus1,Chorus2,Chor1+Rev,Chor2+Rev. Liste encadree, cinq lignes visibles, gauche monte/droite descend. Seul le curseur change pendant TRACK ; relachement applique, BACK annule. Deux evenements signes par position comme v54.

Combinaisons : Time/Size simple reste natif ; FUNC donne Rate/Speed ; FUNC puis TRACK donne Bits/Depth. FUNC+Send dose le send ajoute. Vinyl seul : Size Crackle,FUNC+Size WarbleAmount,FUNC puis TRACK+Size WarbleSpeed. Vinyl+Rev : Size ReverbSize,FUNC+Size Crackle,tripleSize WarbleAmount,tripleSend WarbleSpeed. TripleDelaySend donne Feedback natif. Les titres de send seuls refletent Crush/Chorus/Vinyl.

[FAIT en emulation] Le Vinyl retire du dry la portion envoyee puis ajoute sa version modulee/crackle au postmix. Send0 donne le dry exact. Reverb et chorus sont des retours paralleles ; les deux retours de correction directe Vinyl/crusher restent paralleles lorsqu'actifs ensemble. Saturation bornee, mais niveau et perception a confirmer sur appareil.

## 3. Touches et defilement

- FUNC puis TRACK est differe : tap court inutilise transmet le geste stock ; maintien/rotation consomme le TRACK sans ouvrir Track Setup. TRACK puis FUNC reste transmis au chemin de mute existant.
- Le verrou retrig transmet les evenements PATTERN/SETTINGS avec FUNC au chemin natif sans quitter le verrou. Les commandes d'edition transport restent protegees.
- Le diagnostic demande350ms de TRACK+RETRIG physiques, DX actif et aucune sequence de verrou. Les relachements synthetiques et BACK en verrou ne montrent rien.
- MACHINES borne chaque evenement a un voisin et espace les changements successifs de40ms, sans modifier les IDs ni l'ordre TINY/Shadow/MIDI.

## 4. Preuves et limites

[FAIT en emulation] Deux images independamment : `test_fx_menu_control.py` (24positions,annulation,matrice,6pistes,stockage,ordre touches,verrou et diagnostic), `test_fx_menu_popup.py` (26cycles popup natifs,5titres de send,12positions de liste), `test_fx_menu_machine.py` (140parcours du vrai scroller), `test_fx_menu_audio.py` (mixeur natif,Reverb PCM exact v54,Vinyl0 dry,aux0 reverb exacte,isolement,parametres/silence), `test_fx_menu_integration.py` (runtime voix et objets DSP v54 exacts,modifications declarees,sections hors MAIN exactes,decompression native sans ecrasement de source). Deux reconstructions `--check` requises avant livraison.

[À FAIRE sur appareil] Flasher, tester les deux ordres de touches et les vrais menus, la copie temporaire et sa restauration effective, la persistance disque, le niveau percu et la charge CPU sixvoix avec plusieurs FX. Les mesures d'instructions et la propagation d'un raccourci ne prouvent ni les cycles materiels ni le contenu effectivement sauvegarde.

## 5. Retour appareil et promotion2.24 (23/10/2026)

[FAIT, retour utilisateur] AveyCole : “Everything works great. Push v55 filter build to main as the .syx it serves.” L’image partagee exacte `ed59a947965aff8fc15369c61624baf1a564c6e07e42d837b6277ca6e1405c57` est approuvee. Promotion2.24 sans recompilation ; MAIN `8701f142868f862a916037039bcab824bde002b96cab9f511b235b20eb5f8c7a`. Les guides EN/FR et PDF expliquent explicitement Tone en mode REVERB standard puis retour au combine. La demande ulterieure SETTINGS+SIZE/TIME reste un test v56 separe ; utilisateur confirme publier v55 maintenant.
