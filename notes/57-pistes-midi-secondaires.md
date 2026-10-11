# 57 — Une seconde séquence MIDI par piste

Demande d'AveyCole dans cette conversation, le 11/10/2026 : ajouter à chacune des six pistes une seconde séquence, indépendante du son interne et destinée uniquement à la sortie MIDI. Adresses : VA de l'OS 1.13.

## Réponse courte

[HYP] Le moteur peut probablement cadencer six séquences supplémentaires et transmettre leurs notes. La faisabilité complète reste à établir : données persistantes, édition, messages de sortie et charge doivent être prouvés ensemble. Aucun tweak ni firmware de cette fonction n'est encore proposé.

## 1. Points d'appui existants

- [FAIT] La note 32 décrit le lecteur, les événements de notes et la file protégée `0x40001fba`. L'arpégiateur utilise cette file avec ses propres tampons pour envoyer des messages à l'interface. Ce chemin ne constitue pas encore une preuve d'émission MIDI indépendante.
- [FAIT] La banque de lecture native commence à `0x406fa040`, avec 30 710 octets par pattern. La génération différée suit le pointeur actif `0x40a7887c` et les compteurs propres à chaque piste ; voir note 56 et `tools/emu/test_seq_gen_queue.py`.
- [FAIT] Les portes `0x4000154a`, `0x4000156a` et `0x40001590` gouvernent l'émission générée en mode THRU. Le nouveau chemin devra respecter le choix OUT/THRU et le mod `midi-live-both` (note 50).
- [FAIT] Le format courant des pistes et des pools de locks est déjà utilisé par l'OS. Aucun emplacement persistant pour six nouvelles séquences n'a été démontré libre.

## 2. Premier prototype envisagé

[HYP] Une voie monophonique MIDI par piste, avec note, vélocité, durée et activation des pas ; canal de sortie propre à cette voie. Au début, longueur et vitesse suivent la piste correspondante. Le déclenchement doit utiliser un chemin MIDI dédié, sans appeler le constructeur de voix interne.

[À FAIRE] Vérifier le chemin natif d'émission note-on/note-off jusqu'aux sorties DIN/USB. Gérer Stop, changement de pattern, mute, désactivation et changement de canal : aucune note ne doit rester tenue. Définir explicitement le comportement des notes simultanées identiques sur un même canal.

[À FAIRE] Concevoir une bascule d'édition sans collision avec FUNC + pad (mute), SETTINGS + TRACK (SCRAMBLE), les pas tenus et le second appui LFO demandé. Aucun raccourci n'est réservé à ce stade.

Précision d'AveyCole : une seconde page de six pistes, exclusivement MIDI,
avec leurs propres réglages de sortie. [HYP] Le premier écran de cette page
proposera un canal et une activation pour chaque voie, puis note, vélocité,
durée et pas. La sélection de page doit changer seulement la cible d'édition ;
les six pistes internes continuent leur lecture. Les canaux peuvent être
indépendants ; DIN/USB devront respecter aussi les réglages globaux du port.

## 3. Stockage, coût et preuves nécessaires

[À FAIRE] Rechercher du stockage réellement inutilisé dans le projet et prouver sauvegarde, chargement, copie et changement de pattern. Une allocation RAM seule ne fournit pas de persistance.

[À FAIRE] Mesurer le coût et la saturation des files avec six voies actives ; éviter allocations et appels UI dans l'interruption. Comparer au stock : son interne et séquence primaire identiques, MIDI secondaire séparé, arrêt/reprise et changement de pattern sans notes bloquées. Refaire la preuve avec tous les mods compatibles.

Cette recherche s'ajoute à la génération différée, au SCRAMBLE par pas et au second LFO. Elle ne change pas le statut matériel de ces fonctions et ne modifie pas le flasher principal.

## 4. Routage indépendant établi en émulation (11/10/2026)

[FAIT] `0x400826b0(longueur, octets, destination)` accepte un port par message :
1 = réglage global, 2 = USB, 3 = DIN, 4 = DIN + USB. Le global passe par
`0x40082686` et le getter `0x40044e6c`. L'état MIDI actif `0x40fe4228`
reste nécessaire. La branche DIN appelle `0x40001584`, donc respecte aussi
OUT/THRU et son mod combiné. La branche USB utilise les verrous natifs puis
`0x40003396`. Les canaux font partie des octets du message, sans sélectionner
ni modifier une piste sonore.

[FAIT en émulation] `tools/emu/test_midi_lane_output.py` couvre 2 048 cas :
16 canaux, note-on/off, destinations global/USB/DIN/both, quatre réglages
globaux et OUT/THRU, stock puis mod combiné. Les octets sortants et les
verrous USB sont vérifiés ; aucun constructeur de note sonore n'est appelé.
Les files physiques sont simulées : pas de preuve du fil MIDI réel.

[FAIT] Le chemin DIN bas niveau `0x40001100` peut attendre de la place dans
son tampon de 4 096 octets. Il ne faut donc pas appeler ce writer sans borne
depuis l'interruption audio. [À FAIRE] Une file privée bornée entre l'horloge
des voies et le service MIDI côté UI, avec réservation pour les note-off,
doit être conçue et éprouvée avant intégration.

Les réglages par voie pourront ainsi proposer canal et port sans modifier
les réglages des six pistes internes. L'ordonnanceur, la seconde page de
pistes et leur stockage persistant restent à implémenter ; aucun de ces
éléments n'est inclus dans le test 2 publié.

## 5. Prototype d'ordonnanceur et file (11/10/2026)

[FAIT en émulation] `tools/machines/midi_lanes/runtime.s` fournit une banque
RAM de 320 octets : file de 64 messages, compteurs, six états note/gate.
`ml_step` reçoit l'index, un paquet note-on et une durée en pas (1..64) ;
0 comme paquet représente un pas silencieux. `ml_stop` libère une voie ;
`ml_take` retire le prochain message pour un futur service MIDI. Aucune API
sonore, sortie physique ou attente. Les sections atomiques sont bornées et
restaurent SR ; aucun emplacement RAM matériel n'est encore réservé.

Une note-on acceptée réserve un emplacement pour son note-off ; si la file
sature, les nouveaux note-on sont refusés, les notes déjà acceptées peuvent
toutes être arrêtées. Canal, note et port du note-off sont ceux du note-on.
Les ports du prototype sont déjà résolus (2 USB, 3 DIN, 4 both) : un éventuel
choix global doit être résolu avant d'accepter la note, pour éviter un
changement de sortie avant son note-off. Les doublons actifs canal/note entre
voies sont refusés dans ce premier prototype, même si les ports diffèrent.
Cette politique pourra évoluer avec une gestion explicite des propriétaires.

[FAIT en émulation] `tools/emu/test_midi_lane_runtime.py` assemble et exécute
ce code sur ColdFire : 16 canaux × trois ports, gates, six voies et Stop,
messages invalides et collisions, saturation avec appariement exact de tous
les note-on/off acceptés, puis 150 cycles traversant le ring. Registres
sauvegardés, pile et SR contrôlés. L'horloge native, les données des 64 pas,
l'édition de la banque, les mutes, la persistance et le service de sortie
restent à intégrer ; aucune nouvelle voie dans le firmware publié.

Maximum observé dans cette preuve : 157 instructions pour `ml_step`, 37 pour
`ml_stop`, 18 pour `ml_take`. Ce sont des comptages d'émulation, pas des mesures
de durée matérielle ni de charge de l'interruption complète.

## 6. Données de pas et canaux fixes (11/10/2026)

Nouvelle consigne d'AveyCole : six voies MIDI Out seulement, canaux 7..12
immuables pour pads 1..6. Le prototype `pattern.s` dérive le canal de l'index
de voie ; le setter refuse tout changement de canal. Les pistes sonores ne
sont jamais consultées pour ce choix. Port USB/DIN/both reste indépendant.

[FAIT en émulation] Six blocs de 264 octets : configuration de 8 octets puis
64 pas note/velocity/gate/enabled. `ml_edit`/`ml_config` valident les bornes et
écrivent un octet ; `ml_pattern_tick` relie ce modèle au runtime réservé aux
notes MIDI. Init : voies actives, canaux fixes 7..12, 16 pas, notes désactivées.
Mute/désactivation libèrent les anciennes notes sur leur ancien canal/port.
Les six voies × 64 pas, champs invalides, intégrité des autres champs et
notes off sont éprouvés en assembleur ; SR/pile/registres conservés.

[À FAIRE] Horloge native, bascule/édition physique, sortie physique bornée,
changement/copie/sauvegarde de pattern. Ces 1584 octets sont une structure
privée du prototype, pas un emplacement persistant libre revendiqué.

## 7. Service vers le routeur natif (11/10/2026)

[FAIT en émulation] `service.s` relie `ml_take` au routeur OS `0x400826b0`
(trois octets et port résolu). Il refuse tout IPL non nul et un singleton
MIDI absent (`0x40fe4228`) sans retirer de paquet. Budget plafonné à huit
messages ; aucun verrou privé conservé pendant l'appel natif. La sortie DIN
peut attendre : cette fonction est réservée au contexte UI, jamais audio.
Le plafond borne le nombre de messages, pas leur durée physique.

`test_midi_lane_service.py` exécute l'assembleur et le vrai routeur, ses portes
OUT/THRU stock puis modifiées. Seuls writers physiques et verrous USB sont
simulés. Canaux 7..12, ports USB/DIN/both, messages on/off exacts, budgets
0/1/7/8/9/0xffffffff, refus IPL 1/3/5/7, singleton absent, file restante,
pile/SR/registres vérifiés. Le test interdit les chemins de voix internes.

[À FAIRE] Installer le service dans une boucle UI adaptée, raccorder
l'horloge exacte (pas le lecteur anticipé de patterns), interface physique,
persistance et vérification matérielle. Aucune nouvelle banque flashable livrée.

## 8. Ordonnanceur indépendant et heure audio native (11/10/2026)

[FAIT] L'heure musicale `0x8000184c` avance de deux fois le tempo (en 1/120
de BPM) par bloc audio. Une noire vaut 21 600 000 unités ; un pas de double
croche vaut 5 400 000 (note 38). `0x400593ec..0x40059490` est le chemin natif
qui avance cette heure ; ce n'est pas le prélecteur `0x400550da`.

[FAIT en émulation] `clock.s` reçoit explicitement now et playing, six
configurations privées et un état de 52 octets (running, six couples
deadline/next-step). Il appelle `ml_pattern_tick` au maximum une fois par
voie/bloc et ne transmet jamais directement au MIDI. Sept vitesses privées
sont définies : 1/4, 1/2, 1, 3/2, 2, 3, 4 (index 2 = 1×). Elles ne lisent ni
ne modifient longueur/vitesse des six pistes sonores. Six longueurs séparées,
rebouclage 32 bits, mute immédiat gardant la phase, changement de longueur
sans répétition du premier pas, Stop appariant les notes actives. Un appel
tardif resynchronise l'échéance sans rafale de rattrapage non bornée.

`test_midi_lane_clock.py` assemble et exécute ce code, vérifie six vitesses
et longueurs simultanément, puis exécute la vraie avance horaire native à
30/120/300/546 BPM. Seize pas par mesure, décalage de déclenchement inférieur
à un bloc audio ; registres, pile et SR conservés. Maximum observé 1608
instructions pour les six pas, pas une mesure de charge matérielle.

[À FAIRE] Identifier le point exact de démarrage/arrêt audible et installer
le hook après l'avance audio ; ne pas confondre transport anticipé et première
note audible. Budget audio combiné aux moteurs/LFO, service UI, page et
sauvegarde restent à intégrer. Ces résultats ne prouvent pas encore la synchro
physique d'un firmware de banque MIDI.

## 9. Piste de persistance à vérifier

[FAIT dans la source Model-TG] Les slices manuelles utilisent des fichiers
annexes `/Slices/<hash>` via les petites API natives : open `0x4007bc5e`,
read `0x4007baaa`, write `0x4007bb0a`, close `0x4007bc1c`. Leur écriture est
différée dans un message de tâche UI (`mk_post/mk_sv_run`), car écrire depuis
le callback LED a déjà gelé l'audio. Source pinned `70b39dd`, `model_tg.s`,
section manual slices. Cela ouvre une piste sans occuper les données natives
des patterns, mais ne prouve ni un format, ni un emplacement libre pour nous.

[À FAIRE] Identité stable projet/pattern, copie/Save As, namespace réservé,
vérification des erreurs et écriture atomique avant toute intégration de
fichiers annexes. Aucun fichier utilisateur écrit par ces prototypes.

## 10. Page d'édition privée (11/10/2026)

[FAIT en émulation] `midi_lanes/page.s` construit une vue avec le vrai
constructeur MACHINES et un groupe de vtables privé. Les six pads choisissent
la voie MIDI sans jouer ni modifier la sélection sonore native. FUNC+pad
bascule le mute une seule fois par pression ; une note active reçoit son
note-off sur son ancien port. Les canaux affichés 7..12 ne sont pas éditables.

DATA choisit/édite sortie USB/DIN/both, longueur, vitesse, pas, trig, note,
vélocité, gate et mute. Les seize touches de grille basculent les pas de la
page courante ; PAGE parcourt les quatre pages. Les bornes d'un paramètre
ne provoquent pas de coupure de note quand la valeur reste identique.

`test_midi_lane_page.py` vérifie 132 rendus, huit champs sur six voies,
64 pas, répétitions/releases, canaux immuables, mute et changement de port,
transport simple, destruction native et réouverture conservant les données
RAM. Gardes IPL, contextes absents et gestionnaire absent : aucune allocation
ni modification. Refus d'allocation de page/détenteur nettoyés. Les writers de
dessin, allocations et présentation sont simulés ; constructeur, destructeur
et lecteurs de sélection exécutent le code OS. Les données sonores restent
identiques et les points d'entrée de voix internes sont interdits au test.

[À FAIRE] Raccourci global, LED de grille, persistance, allocation des
contextes et hooks firmware réels. Une réouverture conservant la RAM ne
constitue pas une sauvegarde de projet/pattern. Cette page n'est pas encore
disponible dans un firmware flashable.

## 11. Préparation du contexte de banque (11/10/2026)

[FAIT en émulation] `prepare.s`, `ml_prepare()`, alloue un seul bloc de
1956 octets dans la tâche UI : pattern 1584, file/gates 320, ordonnanceur 52.
Le pattern reçoit `ml_init` ; file et horloge sont entièrement remises à zéro.
Les pointeurs UI sont établis, puis `ml_context` est publié en dernier.
Le futur hook audio doit lire cette publication unique et dériver les trois
sous-structures ; les pointeurs UI intermédiaires ne prouvent pas readiness.

La preuve de page observe l'initialisation avant publication, vérifie chaque
octet et les offsets, conserve les modifications lors d'un second appel,
refuse IPL non nul/réentrance, puis retente après un échec d'allocation.
Cette préparation n'installe toujours aucun hook de transport ou de sortie.
Allocation persistante en RAM seulement ; sauvegarde sur disque à faire.
