# 112 — Premiere passe transversale de charge audio

AveyCole demande le 17/10/2026 une optimisation generale apres un candidat repeat, sans diagnostic dans le principal. Cette passe conserve le son, le nombre de voix, les divisions, les filtres, les fondus et les priorites MIDI. Adresses : VA OS 1.13.

## Reponse courte

Copie separee `flasher-audio-load-test`, derivee du diagnostic repeat test 2. Elle garde ce diagnostic et ajoute trois reductions de travail : fondu repeat commun entre voies identiques ; filtre sans resonance, boucle de deux samples ; banque MIDI, eviter le balayage des 72 slots CC quand aucune slide n est active. Principal et test repeat 2 inchanges.

Retour machine du test repeat 2 : 71 % moyenne / 104 % pic / CUT 4, meme Kick/Snare/Metal/Perc/Tone/SDVtg, filtre presque ferme et repeat actif. La pointe reste au-dessus du budget ; moyenne un peu plus faible ne prouve pas la resolution. Les positions filtre differentes limitent la comparaison au premier 73/101. Ces optimisations sont des candidats, pas une garantie de suppression des clicks.

## Filtre

`tools/machines/track_filter/fast.s` garde les memes instructions EMAC et saturations. Seule la boucle sans feedback traite deux samples avant son test de fin. Noyau610o dans reservation678o ; aucune nouvelle region audio. Registres, MACSR et accumulateurs gardent le contrat existant. Le chemin resonance est identique en nombre d instructions.

`test_filter_load_equivalence.py` accepte deux noyaux explicites ; 2 048 blocs extremes/aleatoires : samples et quatre etats identiques, six pistes, resonance/bornes. Sans resonance -3,2 % d instructions du noyau ; avec resonance 0,0 %. Mesures d instructions et non de CPU physique.

## Banque MIDI

Le tick slides ordinaire peut inspecter 72 slots tous les trois blocs meme sans slide. Le wrapper propre `ao_tick` valide transport, pattern/proprietaire, cadence et curseur. Si aucune des six voies de ce pattern n a de bit actif, il conserve la meme cadence et retourne. Sinon le trampoline rejoint le tick original avec son prologue exact. Aucun port physique, allocation ni reduction de priorite des Note Off.

`gen_audio_load.py` exporte le module relogeable et filtre avec gardes SHA/ABI. Le compositeur lie six pointeurs du vrai catalogue, puis recalcule charges/references et source/longueur du chargeur repeat. Sans banque, retour de composition original intact. Les deux optimisations restent dans la copie test.

[FAIT en emulation] Vrai boot/cache du navigateur, module exact. `test_audio_load_slides.py` : 512 cas comparatifs, queue868o et states384o, cadence/curseur, stop/mute/owner/wrap identiques. Balayage vide : 220 664 vers 13 894 instructions, -93,7 %. Ce pourcentage concerne uniquement cette routine quand aucune slide n est active, pas la charge globale du Cycles.

## Validation et suite

Builds navigateur avec/sans banque/Wizard et diagnostic decoche, signature et references. Regressions filtre precision, repeat/diagnostic, clavier/mutes/slides/Genie et ordonnanceur MIDI. Comparaison de la chaine des six machines indiquees avec filtre et repeat dans `test_audio_load_mixed.py` ; les objets/peripheriques sont fixtures et aucune deadline physique n est simulee. Parite Python/navigateur et generateurs --check avant publication.

Le profilage d autres voies reste une recherche de gains prouves ; aucune baisse implicite de qualite, de voix ou de cadence. Le probleme de premiere entree B est reporte a la demande utilisateur pendant les clicks/diagnostics.


## Fades repeat partages

Les six voies ont souvent le meme etat de fondu pendant le geste Control All. Le candidat ne recalcule la table32 que si l etat initial ou l inclusion differe du dernier calcul ; les memes samples et etats finaux sont reutilises pour les autres voies equivalentes. Cache local a l appel, aucun etat partage avec UI/IRQ, voie stereo garde le meme fondu. La sequence mixte passe de -10,7 % a -15,0 % d instructions repeat face au principal. Les 110 frontieres mono/stereo, changements de masques et releases restent bit exacts. Les 28 % du test etabli sont une mesure separee ; ne pas additionner les pourcentages.

AveyCole precise que Banque MIDI etait installee mais B jamais ouvert pour le releve71/104/CUT4. La garde de boot interdit alors tout runtime MIDI : optimisation slides sans effet sur ce cas. La priorite de ce cas reste le chemin audio commun et les pointes, pas une accusation de la banque inactive.


## Resultats de la combinaison six machines

[FAIT en emulation] Kick/Snare/Metal/Perc/Tone/SDVtg : 48 blocs off/arme/repeat (premiere iteration filtre/slides) et 16 blocs repeat avec le cache de fades final ; samples identiques. Sur cette derniere fixture : instructions filtre+repeat152 472 vers147 812 face au diagnostic2, soit environ3,1 % pour ces seuls modules. Trace du chemin couvert : aucun appel gflt dans la boucle voix,96 appels pendant les16 passes post de six pistes. Pas de double filtrage dans ce chemin observe ; les peripheriques, autres chemins UI et deadlines physiques restent hors preuve.

Le candidat final conserve la precision filtre, la voix SD Vintage, les cinq voix stock, stereo Wizard, masques et fades. Slides : vraie extension et cache,512 cas aussi dans le profil banque sans beat repeat. Banque native : scheduler, clavier, locks/slides, Genie et LEDs passent. Cinq builds navigateur (avec/sans banque/Wizard, diagnostic decoche, banque sans repeat) et parites passent ; verification materielle requise.


## Test 2 : chemins partages natifs et historique (17/10/2026)

AveyCole rapporte79 % moyenne /96 % pic /CUT1 dans le test1, avec encore des ticks a l ajout de SDVtg en sixieme piste. Le seuil de100 % n est pas le seul seuil du regulateur, et le compteur observe aussi les suspensions deja en cours. Pas de modification des seuils ni des fades du regulateur dans ce test.

Profilage du meme type de six voix sur4 blocs :188 505 instructions voix, dont36 915 en SRAM. Les zones les plus frequentes incluent les deux oscillateurs stock0x400a80e6 et0x400a8204. Candidat : leurs indices de tables sont simplifies sans changer interpolation/EMAC.

-0x400a8204 : `(phase & 0xffffff) >>16` devient SWAP + masque255. Le moveq16 devenu inutile est retire ; d3 est recharge avant son prochain usage.
-0x400a80e6 : `(phase >>14) &1020` devient SWAP + masque255, et les deux adresses indexees prennent l echelle4. Le moveq14 est retire. Le moveb15 suivant fixe les6 bits de compteur utilises avant que d6 entier soit recharge.

Les corps restent a leurs adresses, la branche arriere est corrigee de2 octets ; remplissage NOP uniquement apres RTS. Deux regions et leurs instructions sont gardees par SHA et controles de chevauchement. Aucun corps officiel exporte dans les assets : transformation uniquement depuis le fichier utilisateur. `native_index.s` valide le fragment propre au build.

[FAIT en emulation] Deux fonctions completes,512 etats extremes/aleatoires chacune : samples, etat persistant, MACSR et accumulateurs identiques ; registres callee-saved et pile preserves.32 instructions gagnees par appel de32 samples, soit environ3,4 % et2,4 % de ces fonctions, pas du CPU total. Boucle des17 machines comparee separement.

Le repeat partage maintenant l addition `br_start+phase` et le masque circulaire une seule fois par sample au lieu de les refaire pour chaque voie. La sequence mixte passe de-15,0 a-16,7 % d instructions repeat face au principal ;110 frontieres mono/stereo restent bit exactes. Le plateau rapide et les conversions ne changent pas. Diagnostic conserve uniquement en test ; son, nombre de voix et timing inchanges en emulation.


Validation finale test2 : aucune branche externe ni pointeur absolu vers les regions natives decalees dans l image officielle.17 machines comparees,6 pistes de chaque type,4 blocs chacune : sorties exactes. Le cas Kick/Snare/Metal/Perc/Tone/SDVtg repete/filtre passe16 blocs : instructions des seuls modules filtre+repeat152 472 vers146 013 face au diagnostic2, sans compter les economies des fonctions voix. Registres preserves verifies explicitement dans les1 024 appels natifs aleatoires. Cinq builds navigateur/signature et parites Python passent. Publication test uniquement, sans resultat physique affirme.


## Test 3 : isoler la regression machine (17/10/2026)

AveyCole rapporte80 % moyenne /101 % pic /CUT3 pour le test2, contre79/96/CUT1 au test1. Regression observee ; les gains en instructions ne garantissent pas un gain physique. Test3 retire entierement le tweak natif oscillateurs du compositeur. Il garde la base filtre/slides/fades du test1 et uniquement le nouvel index historique repeat du test2, pour isoler les deux variables. Aucune conclusion causale avant comparaison machine. Les recettes et preuves natives restent disponibles pour recherche, mais aucune ecriture native correspondante n est appliquee. Diagnostic uniquement en test ; principal inchange.


## Test 4 : ordonnancement EMAC du filtre (17/10/2026)

Test3 a ete prepare dans la branche puis ouvert localement dans DigiEmu ; pas publie sur Pages. Le test4 repart du repeat test1 : retrait des indices natifs et de l index historique partage du test2. Seul nouveau changement DSP face au test1 : preparer le deuxieme sample de la paire pendant deux latences MAC du premier sample. D7 est temporaire, deja sauve/restaure par le contrat. Aucun acces hors des32 samples : chaque premiere position paire precharge sa voisine.

Noyau614o sur678. 2 048 blocs extremes/aleatoires : samples, etats et EMAC identiques au test3 ; resonance inchangee. Compteur instructions sans resonance +1,6 %, mais estimation statique+stalls des tables DigiEmu -6,0 % (1 361 458 vers1 279 538), resonance0,0 %. Cette estimation exclut branches dynamiques, caches/bus et deadlines ; ne pas annoncer6 % de CPU global.

DigiEmu0.4.1 officiel : stock run passe, marge estimee39,6 % ; verification candidate standard echoue a reconnaitre le display detourne par Chord Keys. Adaptateur local uniquement, garde du detour, corps et trampoline, restaure la resolution panel_diff/fb_front/fb_back sans toucher le firmware ; le vrai UI candidat atteint120 frames stables et ouvre le panneau interactif. Le check standard signale aussi deux MOVEC dans le payload appendu hors de la zone qu il sait intercepter : limite de compatibilite, pas preuve d erreur hardware. Aucun PASS global ou timing six machines revendique pour ce run. GUI test3 ouverte ; firmware test4 reste a verifier sur appareil.


## Test 5 : ordonnancement filtre complet (17/10/2026)

Retour hardware AveyCole test4 :77 % moyenne /101 % pic /CUT4, clicks les moins perceptibles a ce jour. Il ajoute ensuite des pics a107 %. Le101 initial n etait pas le pire observe : ne pas marquer le probleme comme resolu. Pas de preuve que chaque click correspond au pic ; CUT observe aussi des voies deja suspendues. Principal/909 inchanges, diagnostic conserve en test.

Base test4. Sans resonance : le troisieme MAC du premier sample prepare dans D7 la difference du prochain sample avec le premier pole deja mis a jour. Le quatrieme MAC avance A1 ; sortie du premier sample a -4(A1). Le deuxieme sample reutilise la difference. Chaque paire ne precharge que sa voisine : aucune lecture hors des32 samples.

Avec resonance : charge de la voie feedback pendant le MAC d entree ; constantes de clamp et avance du pointeur preparees dans les six gaps MAC/resultat. D7/A5 reutilises seulement apres leurs usages precedents ; ils sont sauvegardes/restaures. Saturations, ordre des calculs et cadence restent identiques. Le chargement feedback est deplace vers D7 et le MAC le consomme directement. Noyau618o sur678.

2 048 blocs extremes/aleatoires, samples/quatre etats/EMAC exacts. Estimation statique+stalls DigiEmu sans resonance :1 279 538 vers1 197 618 (-6,4 % face au test4) ; avec resonance2 050 623 vers1 624 639 (-20,8 %). Instructions +1,6 %/+10,0 % car le travail prepare pendant les stalls est explicite. Ces estimations excluent branches dynamiques, caches/bus et deadlines : aucun pourcentage CPU global ni resultat physique annonce. Hardware a verifier.
