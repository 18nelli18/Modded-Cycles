# 126 - Machine MIDI selectable sur les six pistes principales

Demande directe AveyCole,18/10/2026 : remplacer la banque B par une machine MIDI sans audio, assignable par projet aux pistes A, avec fonctions MIDI B conservees (CC assignables, locks, LFO, arpege, etc.). Priorite confirmee : « work on the seperate midi out machine ». Une nouvelle integration experimentale est requise ; principal1.93 et Banque actuelle restent disponibles.

## Reponse courte

[FAIT en emulation] Le noyau d'une machine silencieuse, son entree dans le catalogue complet et les helpers MIDI natifs sont verifies. [A FAIRE] Ce n'est PAS une machine MIDI complete : interface CC, locks, ordonnanceur choisi, sauvegarde et integration au flasher non termines. Aucune page incomplete publiee.

## 1. Noyau et integration machine

tools/machines/midi_machine/core.c fournit mm_update sans DSP, mm_render qui ecrit32samples nuls et mm_mask qui reconnait les six choix de machine dans les parametres natifs (66octets par piste). Pas de writer MIDI, allocation ou acces disque dans ces callbacks.

tools/gen_midi_machine_core.py reutilise l'ABI generateur MACRO avec une machine nouvelle index6, sans remplacer une machine stock. Recette locale build/midi-machine/core.json ; --check compare la regeneration. Le noyau existe aussi dans le catalogue complet via tools/gen_midi_machine_catalogue.py, argument extra facultatif de gen_machine_combinations.generate. Sans cet argument, le chemin de generation existant reste identique.

## 2. Limite de descripteurs a pleine selection

[FAIT] Le catalogue complet Wizard+10ajouts a17machines et126descripteurs. Ajouter MIDI donne18machines et131descripteurs. Les MOVEQ de bornage signes8bits ne peuvent charger131. wide_bounds remplace les gardes concernees par des detours propres chargeant la borne sur32bits, rejouant les instructions deplacees et les petites branches conditionnelles. Les detours existants ne sont pas ecrases. Code MIDI a PAY+0x8c000, gardes a PAY+0x8d000, reservation jusqu'a PAY+0x8e000 ; descripteurs jusqu'a PAY+0x8b0a8. Recettes et octets firmware restent sous build ignore.

[A FAIRE] Verifier toutes les gardes et entrees de branchement avant publication, puis profils partiels, sans Wizard et seul. Les seuls profils prouves ici sont le noyau stock+MIDI et les menus du catalogue complet ; ne pas annoncer toutes les combinaisons.

## 3. Preuves executees

- test_midi_machine_core.py : vrai boot du nouveau slot, donnees et ABI preserves ; huit blocs de chacun des six moteurs stock avec sorties exactement identiques ; six machines MIDI,32blocs y compris retriggers sans audio ;64masques de selection et entrees invalides ; constructeur natif a sept machines.
- test_midi_machine_notes.py : helpers natifs de notes live, routeur et appels DIN/USB reels, drivers physiques/getters du projet instrumentes ;96paires note-on/off, six pistes x16canaux. Pas de preuve de sequence complete ou sortie materielle.
- test_midi_machine_catalogue.py : constructeur18machines, noms, indices de parametres propres pour les onze ajouts ; nouveaux descripteurs126..130 accessibles ; acces hors bornes131,132,255,256,INT_MAX etUINT_MAX rejetes comme stock. Pas encore de preuve de boot complet avec tous les moteurs et la Banque.

## 4. Decision d'edition et suite

[DECISION AveyCole,18/10/2026] « Keep the A-side notes and normal grid ». Changer une piste en MIDI conserve ses notes, trigs et editeur A natifs. Ne pas embarquer l'editeur ni l'horloge privee des six pistes B dans cette machine.

Architecture retenue : reutiliser transport/phase/notes/longueurs A ; adapter CC assignations/locks/LFO et stockage sans garder les six voies B actives. Les notes et locks natifs restent dans la sauvegarde du pattern A. Les metadonnees MIDI supplementaires demandent encore un format et des preuves de sauvegarde.

Toute nouvelle page test conserve le diagnostic ; aucun outil de diagnostic n'est ajoute au principal. L'ancien format de sauvegarde B ne sera ni efface ni converti silencieusement.

## 5. Raccordement des notes natives,18/10/2026

[FAIT en emulation] Detour du getter MOut a0x40016e90 : retourne1 pour une piste du pattern actif dont le son est MIDI Out ; sinon rejoue le prologue stock et reprend a0x40016e96. Aucun changement permanent du reglage MOut dans les donnees sauvegardees. Indice MIDI compile suivant le catalogue (6 seul,17 complet). Aucun nouveau calcul dans la boucle audio.

Le getter recoit un objet piste du pattern ; celui-ci n'est PAS un objet son. On resout sa position dans le pattern actif, puis le getter machine natif0x4001e318(0,piste), dont le second argument est le numero de piste. Les retours de pointeurs natifs sont dansD0 ; les declarations C utilisent des retours entiers pour eviter l'ABI pointeur A0 de GCC m68k-linux. La fixture distingue maintenant donnees des sons et des pistes et six sons differents : les premiers essais avec un seul son partage masquaient cette distinction.

test_midi_machine_notes.py : getter MOut stock compare sur quatre valeurs, six moteurs stock ; les64masques mixtes MIDI/audio donnent des sorties independantes ;192paires clavier/pads sur6pistes x16canaux, DIN etUSB. Ces controles passent dans les deux catalogues (7 et18machines), avec les vrais getters machine et MOut. Les singletons/proprietes peripheriques et pilotes restent instrumentes. Aucune preuve d'un cycle complet de sequence, arp, locks ou sauvegarde n'en decoule.

[A FAIRE, bloquant publication] Changer de machine pendant une note live MIDI demande un relachement capture. Dans une sonde locale, MIDI note-on puis changement du son en stock avec MOut0 avant note-off supprime le relachement natif. Il faut capturer notes/canal/port aux attaques et garantir la fermeture aux transitions, sans couper une autre piste partageant le canal. Ne pas publier ce noyau comme une machine terminee.

## 6. Relachement capture,18/10/2026

[FAIT en emulation] Correction du relachement perdu ci-dessus : core.c conserve une capture16bits par note et piste (1536octets BSS) avec validite, canal et port de l'attaque. live.S relaie les chemins clavier/pads apres l'appel natif audio/enregistrement ; seules les attaques de la nouvelle machine et leurs relachements captures remplacent le relais MIDI. Pas de fichier, allocation, nouvel ordonnanceur ou etat global de pile. Les autres machines reprennent leurs instructions stock.

Les12cas clavier/pads x6pistes changent simultanement machine, canal et port avant relachement : le note-off part bien vers l'ancien canal/port. Les24cas stock clavier/pads x6pistes xMOut ON/OFF restent identiques. Les registres callee-saved et la pile sont verifies a chaque appel. refs_into ne trouve aucun pointeur ni branchement vers l'interieur des cinq accroches (getter et quatre relais live).

[A FAIRE] Cette capture ferme la note au relachement ; un changement de machine ou STOP sans evenement de relachement doit encore fermer immediatement les captures. Le chemin sequence, ses durees et son nettoyage STOP doivent etre verifies a part. Les quatre relais live recouvrent ceux de Chord Keys : le futur composeur doit chainer explicitement les deux comportements, pas ecraser un detour. L'integration avec Chord Keys n'est pas encore faite ; ces recettes locales ne sont pas offertes dans le flasher.

## 7. Premier test isole demande par AveyCole

Demande « alright, let me try it » : tools/gen_midi_machine_test.py prepare docs/flasher-midi-machine-test uniquement, six machines stock plus MIDI Out, sans autres modules ni banque B. Pas une copie fonctionnelle complete du principal. Une seule case, empreintes ecritures et charge utile, fichier OS officiel fourni par l'utilisateur. Notes live uniquement annoncees ; CC non raccordes et sequence/sauvegarde encore non verifies. Relacher les notes avant changement de machine/projet.

Diagnostic CPU/CUT indisponible : ce petit profil n'embarque pas les compteurs SY ni Beat Repeat. Cette limite est affichee sur la page ; aucun relevé invente. Principal et909 inchanges. Les generateurs de catalogue complet precedemment notes restent du travail local ; seule la variante sept machines est proposee ici.

Validation : gen_midi_machine_core.py --check, gen_midi_machine_test.py --check, emu/test_midi_machine_core.py (boot reel et audio stock exact), emu/test_midi_machine_notes.py (notes live, capture, ABI), test_midi_machine_test.js (vraie page jsdom et fichier signe, empreintes ecritures/charge utile). --catalogue ajoute le controle facultatif du catalogue local complet.

## 8. Retour du premier test et interface MIDI complete demandee

AveyCole confirme le18/10 : « it does send midi notes ». SETTINGS + potard modifie encore le parametre de base du prototype ; l'assignation CC n'y etait pas raccordee. Nouvelle exigence explicite : toutes les fonctions de configuration B dans la machine, selection avec les autres modules, aucune banque B, aucun parametre de synthese visible quand MIDI Out est choisi. Ne pas presenter le prototype live comme repondant a cette demande complete.

[FAIT en emulation, local seulement] controls.c separe numero CC et valeur dans un mot16bits, OFF compris, et prepare12controles par piste. ui.c utilise le vrai setter par lot0x4001416c et sa notification, une copie UI des parametres, puis envoi CC depuis l'UI seulement. SETTINGS modifie le numero et conserve la valeur sans transmission. Le mouvement normal modifie la valeur sans retargeter le CC. Les slots11..22 portent les controles ; marqueur provisoire en32, sauvegarde native de ce format encore a prouver avant integration.

ui.S consomme les gestes avant le dispatch vers les parametres stock ; le dessin principal et le popup ne montrent que MIDI/CC. Une release SETTINGS apres assignation est consommee dans le profil autonome. Une API de pointeurs est prevue pour le drapeau mod-used du support commun afin de conserver ses releases dans les combinaisons.

gen_midi_machine_controls.py --ui et --ui --check passent. test_midi_machine_controls.py verifie codec et saturation sans E/S, six pistes x12controles, preservation des autres champs. test_midi_machine_ui.py execute les trois wrappers UI et le setter OS : six pistes x12potards, CC d'assignation non transmis, valeurs CC transmises, noms MIDI seulement, aucune allocation/vue synthese dans le geste, release SETTINGS consommee ; ABI/pile controles. Les primitives LCD et le popup sont instrumentes, pas une capture d'ecran materielle.

[A FAIRE] Raccorder ce module au nouveau composeur complet, supprimer la banque B de ce profil, chainer ChordKeys et les autres detours, locks/recorder/lecture CC, sauvegarde/rechargement du format (marqueur32 compris), menus MIDI/LFO et commandes DATA sans fuite de parametres audio. Le test public1 reste identique ; aucun test2 incomplet publie.

## 9. Locks, sauvegarde et tache MIDI ; travail local puis pause18/10

[FAIT en emulation] `ui.c` ecrit maintenant les locks par les vrais setters OS : grille64pas, depart depuis la valeur de chaque lock, saturation0..127, aucun changement de base ni emission pendant une edition de TRIG tenu. Une reassignation de base ne retargete pas les anciens locks. Les pas vides deviennent lock-only. Le recorder CC utilise le pas natif quand l'enregistrement live est actif.

`test_midi_machine_locks.py` execute six pistes x12CC x4pages :288locks. Sauvegarde0x4005ba0a, chargement0x4005b894 et copie0x4008f1f0 conservent les mots CC exactement. Le format natif des locks ne necessite donc aucun fichier annexe.

[FAIT] Le codec son stock conserve11..22 sauf17 (FINE normalise), et ignore32. `storage.c/.S` execute d'abord le codec natif puis, uniquement pour MIDI, stocke le mot17 dans l'emplacement fichier30(+88) et le tag0x4d49 dans31(+90). Ces emplacements du filtre audio restent inchanges pour les machines audio. Un chargement refuse ne touche pas aux reglages precedents. `test_midi_machine_storage.py` compare les six sons audio aux deux codecs stock, prouve les12CC et le tag au format2 courant et neutralise proprement les anciens sons sans tag. Pas de revendication de round-trip du format1 : le chargeur courant le refuse sur un buffer destination vierge.

[FAIT en emulation] `worker.c/.S` ajoute72cases CC coalescentes et un token unique dans la mailbox native. Producteur IRQ borne, sans writer, malloc ou attente ; consommateur natif IPL0, huit CC par passage de token. Si un message de note MIDI precede le token, les12CC en attente de cette piste sont transmis avant son attaque. Le traitement natif note/duree/STOP reste en place. `test_midi_machine_worker.py` verifie288changements ->72CC finaux, IPL, ports, bornes, rearmement et CC avant note.

Les deux retours audio (attaque0x4005919e, lock-only0x40058f3c) capturent les mots apres application native des locks et avant lissage audio. `test_midi_machine_sequence.py` execute la vraie file audio, extraction et application des locks sur six pistes, puis le worker ; lock-only transmet sans nouvelle attaque, note-off ne transmet pas de CC.

Le generateur `--controls` compile maintenant les modules ensemble dans le catalogue18machines. Code a PAY+0x8e000, reservation jusqu'a PAY+0x92000 ; les gardes131descripteurs restent a PAY+0x8d000. La version sans `--controls` reste le prototype publie et `gen_midi_machine_core.py --check` reste identique. Le chargeur Wizard existant est explicitement chaine via `mm_storage_api`, jamais ecrase. `test_midi_machine_catalogue.py --controls` verifie les18entrees, indices hors limites, vrais dispatchs UI/CC et save/load des six sons MIDI avec Wizard.

[A FAIRE] Ceci n'est toujours pas la composition de toutes les options : menus MIDI/LFO, politique DATA et autres vues, fermeture immediate des captures live aux transitions, chainage ChordKeys/filtre et autres detours, tous profils partiels, boot/audio/signature de la composition finale et test materiel. Aucune nouvelle page publiee, principal/909 inchanges par ce travail. Pause explicite demandee par AveyCole pour examiner Sample Wizard : « slice end just changes between a0and1.0value ».

## 10. Preset complet MIDI sans banque B (18/10/2026)

Demande AveyCole apres confirmation End909 : finir une page de test Select All, sauf la banque MIDI B. `gen_midi_machine_all_test.py` construit une copie separee du principal. Ce premier essai est un preset fixe, pas une annonce de compatibilite de tous les profils partiels. Principal et909 publies restent inchanges par ce travail. Le prototype live1 reste disponible sans modification.

[FAIT en emulation] Machine MIDI index17 dans le catalogue18,131descripteurs proteges sur32bits. Code complet a4678e000, reservation46792000 ; gardes4678d000. Le composeur installe les detours seulement apres les autres modules et chaine explicitement ChordKeys live/sequence, le stockage Wizard/filtre, les dispatchs UI preexistants et le second LFO audio. Le code reprend les contrats de pile d'origine. Si ChordKeys differe la note native, la machine MIDI emet exactement une note apres ses locks, sans doublement. Les lock-only ne produisent pas de note.

SETTINGS+potard : assignation CC sans modifier la valeur ni envoyer ; potard seul : valeur CC. SETTINGS seul : canal/port ; DATA choisit puis clic active edition. Les deux premiers potards editent aussi canal/port. LFO parcourt deux pages MIDI puis CC ; BACK revient aux CC. Aucun controle de synthese dans ces panneaux. MainScreenView est identifie par sa vraie vtable400ffe20, pas un offset errone. Changements de page/selection utilisent le vrai drapeau redraw40076bee du manager applicatif.

Format son courant : les33mots MIDI sont conserves exactement dans le record100octets, zone28..93 et tag0x4d32en94. Nom/header, position du byte machine et sentinelle restent natifs. Tag memoire0x4d4a :12CC en11..22, LFO1en1..8, LFO2en23..30, routage31. Les sons audio restent strictement identiques aux codecs OS. Le format CC seul provisoire precedent est remplace ; le chargeur conserve sa compatibilite avec celui-ci.

Deux LFO MIDI utilisent les vrais calculs/temps LFO natifs avec phases privees par piste. Les cibles MIDI sont masquees pendant les LFO audio et la tranche MIDI restauree entierement. Pas d'horloge B ni de writer depuis IRQ. Le producteur utilise84cases fixes (12CC+2LFO par piste), coalescence et un token ; la tache MIDI consomme au plus8CC par passage. Les LFO publient au plus un CC modifie par3blocs. Les CC des locks sont transmis avant l'attaque de leur piste. Notes sequencees et live respectent canal/port sauvegardes ; les fins de notes gardent le port de l'attaque apres changement de reglage. STOP ferme aussi les captures live, meme apres changement de machine.

Preuves : controles/menus natifs six pistes, DATA non editant avant clic,288locks et copies/pattern save-load natifs,33mots son exacts, worker IPL0 et bornage/coalescence, deux LFO sur vrai moteur OS avec resultats audio seuls identiques, catalogue18 et indices invalides, boot du vrai preset signe, hooks partages et UI/save-load/notes des six pistes dans ce preset. La vraie file audio avec ChordKeys produit une seule note MIDI par evenement accepte et conserve le CC verrouille. CPU/CUT dans le test uniquement. Aucun resultat materiel annonce avant retour AveyCole.

[A FAIRE sur appareil] Verifier projet apres extinction/rechargement, menus/labels, deux ports, notes/arpege/conditions et locks/recording, deux LFO, STOP et six pistes mixtes avec diagnostic. Les profils d'installation partiels ne sont pas proposes dans ce preset. Ne pas promouvoir cette integration vers principal sans confirmation.


## 11. Retour materiel : entree des encodeurs et ecran principal (18/10/2026)

AveyCole : SETTINGS+PITCH change encore Pitch ; autres boutons CC3/CC4 sans assignation, FUNC+PAGE masque, panneau MIDI permanent. Il demande les valeurs CC uniquement pendant le geste, aucun parametre audio, retour au principal.

[FAIT] La premiere preuve appelait directement40077532 : ce n'est pas le chemin utilise par les encodeurs physiques. L'entree Application40006158 copie un EncoderEvent avec vtable400fbebc puis appelle400775f8. Le detour est deplace vers400775f8 ; prologue8octets identique, reprise40077600. Les preuves passent maintenant par40006158, sans contourner cette conversion native. La preuve precedente ne demontrait pas le routage physique et son affirmation trop large est retiree.

[FAIT en emulation] Six pistes x12potards : SETTINGS assigne sans transmettre, mouvement normal transmet la valeur seulement, aucun Pitch ni handler audio. Les deux pointeurs SETTINGS-held/mod-used du support commun sont effectivement raccordes par le composeur ; le getter natif seul ne suffit pas quand les listeners absorbent SETTINGS. Le flag commun est prioritaire sur le fallback autonome, afin de ne pas garder une ancienne touche tenue. Potards non assignes consommes sans action.

Le dessin principal est delegue a l'OS quand aucun menu MIDI explicite n'est ouvert. PAGE ferme ces menus et passe au stock ; DATA est delegue hors menu MIDI, ce qui rend FUNC+PAGE et l'edition native de longueur accessibles. Les popups CC sont transitoires. Les menus LFO/canal/port restent explicites. Test2 uniquement ; aucune modification des flashers principal/909 et aucune validation materielle revendiquee.


## 12. Test3 : appui SETTINGS brut, Track Setup et notes sequencees (18/10/2026)

Retour AveyCole test2 : potards ordinaires inactifs, SETTINGS+potard inactif, notes live seules transmises. Il demande le geste Track Setup de B, ses options KbT/Pad Note et le canal en plus.

[FAIT] Le detour key precede le getter qui met set_held a jour ; consommer SETTINGS avant ce getter laissait le flag commun nul. La preuve test2 prechargeait ce flag et ratait le defaut. Le nouveau code publie le veritable appui/release brut dans ce flag, passe le down au natif et consomme la release apres assignation. Test_midi_machine_ui execute maintenant les hooks key et entree applicative encoder avec flag initial nul, sur six pistes, sans precharger held. Aucun menu MIDI ne s'ouvre sur le simple relachement SETTINGS.

FUNC+TRACK ouvre Track Setup MIDI, DATA navigue et un clic active edition : Channel/Output/KbT/Pad Note. Les deux derniers utilisent les vrais getters/setters A : KbT40016da6/40016dd6, Pad40015a34/40015a64 ; notification et stockage pattern restent natifs. Le getter Pad rend seulement un octet ABI, explicitement declare u8. Rien n'est stocke dans une nouvelle zone. Les potards gris restent CC dans ce setup ; les pages LFO explicites gardent leurs huit controles. FUNC+PAGE passe au Scale Setup natif. QuickMute40100c3c est ferme par40076126 avant le setup ; les flags latch, si installes, sont effaces afin d'eviter un FUNC verrouille. Preuve menu six pistes : quatre champs, bornes, note C5, clic DATA, fermeture native QuickMute, BACK et delegation Scale Setup.

[FAIT] L'emission MIDI propre etait conditionnee par event+20, le bit MOut audio. Une machine MIDI doit emettre meme si ce bit de la piste audio precedente reste nul. La condition est supprimee seulement pour la machine MIDI, sur le chemin note accepte ; lock-only reste sans note. La preuve complete cree ces evenements avec MOut=0 et ne s'arrete plus au comptage des messages : chaque vrai message produit est donne a la vraie tache MIDI, puis les envois DIN et USB sont controles sur six canaux. Les pilotes physiques seuls sont instrumentes. Les autres machines gardent leur ancien chemin.

Test3 seulement, principal/909 inchanges ; verification materielle encore attendue.


## 13. Test4 : vrai MenuView et retour a une machine audio (18/10/2026)

Retour materiel test3 : notes sequencees et CC fonctionnent ; FUNC+TRACK reste un texte qui disparait en tournant DATA. Quitter MIDI Out laisse la nouvelle machine silencieuse, live et sequence.

[FAIT en emulation] Track Setup utilise maintenant le vrai MenuView400423e4, ses polices, bordures et surbrillances. Quatre lignes Ch/Out/KbT/Pad ; Glob abrege Global. DATA navigue, un clic entre en edition, BACK ferme. Le flag edition est dans l'octet+80 du MenuItem84octets, distinct de son identifiant bas. Une vue Pads/transitoire au-dessus du principal ne fait plus perdre le menu explicite ; les autres touches de menu deleguent normalement. Captures Bitmap/polices OS reelles navigation et edition distinctes sous build/midi-machine/menu-*.png.

[FAIT en emulation] Les mots CC/LFO MIDI partagent les emplacements audio : notamment Fine17, Decay18 et destination LFO4. Les reutiliser apres changement de machine peut rendre le moteur silencieux. mm_audio_poll suit les six machines et, uniquement apres sortie MIDI avec marqueur4d49/4d4a, remplace les reglages par les defauts du moteur cible. Le mapping4005a692 et les bornes/defaults4005a65a sont executes, pas une table inventee. La publication4001416c conserve notifications natives. Machine9, Pitch10, notes/grille et pattern sont preserves ; le son cible repart de ses valeurs par defaut. La verification tourne apres delegation encodeur et au dessin, jamais dans l'IRQ audio. Aucun reset repete ni changement des sons audio sans marqueur MIDI.

Preuves : test_midi_machine_transition execute le detour encodeur apres delegation, six transitions et le vrai VOICE_LOOP des six moteurs stock avec sorties non nulles. test_midi_machine_all controle les17destinations audio du vrai preset signe avec leurs propres descripteurs. test_midi_machine_menu_render execute le vrai MenuView avec fonts/Bitmap OS ; test_midi_machine_menus couvre DATA sous vue transitoire. Tests CC, stockage, notes sequencees, ports et LFO conserves. Test4 uniquement, aucun changement des flashers principal/909 ; validation materielle attendue.
