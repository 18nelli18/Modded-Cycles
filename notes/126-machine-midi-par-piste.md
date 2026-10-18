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
