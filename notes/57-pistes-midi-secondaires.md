# 57 — Une seconde séquence MIDI par piste

Demande d'AveyCole dans cette conversation, le 11/10/2026 : ajouter à chacune des six pistes une seconde séquence, indépendante du son interne et destinée uniquement à la sortie MIDI. Adresses : VA de l'OS 1.13.

## Réponse courte

[FAIT en émulation] Six voies MIDI indépendantes sont intégrées au bundle expérimental avec Model-TG et Live MIDI Out+Thru. Le test dédié est `docs/flasher-midi-test/` ; voir §19 pour les preuves et les limites. La banque reste en RAM, partagée entre patterns, sans sauvegarde projet. La charge et les sorties physiques restent à vérifier sur machine.

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


## 12. Raccourci de banque et contexte audio/UI (11/10/2026)

Demande AveyCole : FUNC + SETTINGS + PAGE bascule pads 1..6 entre les pistes
sonores existantes et six voies MIDI privées sur canaux 7..12, sans interrompre
la lecture de l'autre banque. Le raccourci simple SETTINGS + PAGE reste réservé
à Sequence Genie.

[FAIT en émulation] `key.s` adapte le getter avant la chaîne existante :
les événements SETTINGS restent transmis, afin de ne pas bloquer l'état
maintenu Model-TG. PAGE avec FUNC et SETTINGS ouvre/ferme la vue privée,
les lectures multiples, répétitions et relâchements ne doublent pas la bascule.
La vue ne se ferme plus dès l'appui FUNC+SETTINGS. `ml_key_next` et les
symboles TG sont fournis explicitement par le futur générateur ; la preuve
utilise le vrai getter natif comme cible suivante et des états TG en fixture.
La chaîne complète SCRAMBLE/Sequence Genie/Model-TG reste à prouver.

`integration.s` lit uniquement le contexte publié : `ml_audio_tick(now,playing)`
appelle l'ordonnanceur sans accéder aux ports ; `ml_ui_drain()` refuse IPL>0
et transmet au plus huit messages via le service natif. SR et registres
préservés restent intacts. La preuve ferme la vue puis enchaîne horloge IPL5,
file six canaux 7..12, drain UI et Stop avec six note-off. Les six données
sonores et la sélection audio native restent inchangées. Le routeur physique
est simulé ici, ses chemins natifs étant couverts par la preuve service.

## 13. LED des pas par callback natif (11/10/2026)

[FAIT en émulation] `led.s`, vtable LedHandler privée au sous-objet +8,
remplace uniquement le callback +8, sans écrire les LED des pads/transport.
Mapping `0x4000608c` (table `0x404a8bdc`), singleton `0x400cfaf4`, writer
first-wins `0x40005f86` et masque de revendication 64 bits. Les seize pas
courants reçoivent état 1 (éteint) ou 2 (actif), les autres LED sont intactes.
`test_midi_lane_led.py` couvre six voies × quatre pages, données de pattern
inchangées et conservation d'un état LED déjà attribué par le gestionnaire.
Getter/mapping/writer natifs exécutés ; périphérique LED et gestionnaire
complet simulés. Aucun MIDI, allocation ou appel audio depuis ce callback.

[À FAIRE] Raccordement global touches, service UI et horloge au transport
réel, synchronisation audible, placement compatible, persistance et catalogue
expérimental. Aucun flasher MIDI livré ni test matériel revendiqué.


## 14. Service UI indépendant du dessin (11/10/2026)

[FAIT en émulation] Prototype `ui_hook.s` pour l'entrée du gestionnaire
`0x40006a4a`, avant le test de vue sale `0x40076bfa`. Il sauvegarde
les registres volatils/SR, appelle le drain privé puis rejoue les huit
octets déplacés et reprend à `0x40006a52`. Le chemin sans dessin
continue donc à transmettre la file même lorsque la vue MIDI est fermée.

`test_midi_lane_ui_hook.py` applique le detour en mémoire, exécute les
branches natives propre/sale, vérifie huit puis quatre paquets (six
note-on, six note-off), argument du gestionnaire et registres conservés.
Sans contexte, registres/SR/pile et callbacks correspondent au stock pour
IPL0/IPL5. Routeur physique et callbacks LED simulés ; la présence de ce
point d'appel dans chaque cycle UI réel reste à confirmer. Aucun hook
audio/transport ou placement flashable n'est déduit de cette seule preuve.

## 15. Pause et reprise des voies privées (11/10/2026)

[FAIT en émulation] `ml_clock` accepte maintenant les trois modes du
transport natif : arrêt 0, lecture 1, pause 2. La première pause relâche
les six notes et transforme chaque échéance en délai restant, sans changer
le prochain pas. Les appels suivants en pause ne changent rien. La reprise
reconstitue les échéances depuis l'heure fournie ; un arrêt réinitialise
la lecture au pas 1, même après une pause. Aucune allocation ni sortie
physique n'est ajoutée, la structure reste de 52 octets.

La preuve horloge couvre six vitesses distinctes, délais restants,
relâchements uniques, Stop après pause et rebouclage 32 bits, en plus
de l'avance musicale OS à quatre tempos. Les modes sont encore fournis
par la fixture : cela ne prouve pas le raccordement au transport réel.

[À FAIRE] Armer le premier pas à l'échéance audible native, traiter une
première ouverture pendant la lecture, vérifier Start/Continue MIDI et
les redémarrages rapides. Le point `0x40054686` copie l'échéance native
vers `0x80001848` dans le chemin Play ; c'est un candidat à étudier,
pas un hook installé. Le budget du drain UI et la charge audio combinée
restent à mesurer avant tout flasher MIDI.

## 16. Prototypes aux sites natifs Start et audio (11/10/2026)

[FAIT en émulation] `transport.s` détourne en mémoire les six octets de
`0x40054686` : il capture échéance, contexte présent et indicateur Continue
`d6`, puis rejoue le move vers `0x80001848`. Un numéro d'armement distingue
les nouveaux Start, même si le Stop intermédiaire tombe entre deux ticks.
Le prototype d'appel `0x400594a8` conserve d'abord le vrai `0x40053330`,
puis appelle l'horloge privée en conservant ses résultats et SR. Aucun
routeur MIDI ni allocation depuis ce chemin audio.

`test_midi_lane_transport.py` vérifie le contrat des deux sites, l'attente
avant échéance, l'ancrage des échéances suivantes malgré 100 unités de
retard, six canaux, Pause/Continue, redémarrage, Stop et rebouclage 32 bits.
Les modes/heure/d6 sont des fixtures ; seul le move et la branche inactive
du vrai appel audio sont exécutés. Ce n'est pas une preuve du chemin Play
complet, ni de l'alignement audible matériel, ni de la charge audio totale.

La preuve invalide explicitement le cache de traduction après chaque
réécriture d'instruction et vérifie l'incrément d'armement : sans cette
invalidation, Unicorn peut continuer à exécuter l'ancien code. Même
correction appliquée aux comparaisons stock/detour de la preuve UI.
Les flags sont observés par branches avant la sortie d'émulation.

Le premier service UI prépare désormais le contexte, sans ouvrir la vue.
Les voies vides peuvent tourner avant la première ouverture de l'éditeur.
Échec d'allocation réessayé au prochain service ; aucune allocation IPL>0.
Si Play arrive avant toute préparation, le prototype reste fermé jusqu'au
prochain Play : la synchronisation d'une allocation tardive reste à finir.

[FAIT, note 45 §2] Le gestionnaire UI retenu tourne à 30 Hz. Huit messages
par service représentent donc seulement 240 messages/s, avec jusqu'à une
image UI de latence : ce drain est un prototype, pas un service final
assez précis pour un séquenceur MIDI. [À FAIRE] Choisir un service plus
rapide sans attente depuis l'audio, éprouver saturation et jitter USB/DIN,
puis le placement, la chaîne complète de touches et la persistance.
Aucun flasher MIDI publié par ces preuves.

## 17. MIDI OUT par voie et service dédié (11/10/2026)

Demande AveyCole : FUNC + pad active/coupe MIDI OUT plutôt que le mute audio.
La page propose « MIDI OUT » sur enabled (+0), sans toucher le mute privé
réservé (+1) ni les pistes sonores. Couper appelle `ml_quiet` : au plus 64
paquets inspectés sous IPL7, les note-ons en file sur le canal fixe sont
remplacés par leurs note-offs, puis la note tenue est libérée sur son ancien
port. Autres canaux/ports conservés. Réactiver conserve la phase du séquenceur.
Répétitions et releases des pads ne basculent pas à nouveau.
`test_midi_lane_page.py` couvre commande, menu, note livrée et encore en file,
autre canal, mute réservé et données audio intactes. `[FAIT en émulation]`.

Le service actuel UI est limité à 30 Hz × huit messages = 240 messages/s et
une latence maximale d'une image. Monter le budget ne retire pas les attentes
physiques de la tâche UI. `worker.s` propose un consommateur dédié : contexte
privé 16 octets, sémaphore natif 8 octets, réveil coalescé, runtime. Le post
`0x40001bb0`, également appelé par l'IRQ native `0x400020d4`, est borné et
arme un pend logiciel (`fc050014`, bit 13) si une tâche attend. Il ne bloque
pas et ne fait pas de trap, contrairement à l'attente `0x40001aca`.
`ml_worker_once` refuse IPL non nul, draine huit messages puis réarme
atomiquement si la file reste non vide. Les writers restent hors IRQ et
hors verrou privé.

`[FAIT en émulation]` : vrai post natif sans waiter, cent notifications IRQ
coalescées en un signal, huit puis quatre messages, réarmement et refus IPL ;
routeur OS réel, sorties physiques simulées. Post natif avec waiter rejoué : listes prêtes vide/occupée et bit de pend logiciel exact, sans exécution du scheduler. `[À FAIRE]` : création de tâche,
publication du contexte, scheduling réel, IRQ pendant le service et
coupure pendant un paquet en vol. Prototype pas encore branché dans le
firmware ; aucun gain UI mesuré. Ne pas drainer simultanément depuis UI et
tâche dédiée. Sauvegarde et placement du mod restent à intégrer.

## 18. Création native du consommateur et première mesure de place (11/10/2026)

[FAIT en émulation] La variante `ML_WORKER` crée maintenant le consommateur
depuis le service UI, avant publication : allocation réessayable de 16 484
octets (contexte 16, TCB natif 84, pile 16 KiB), initialisation native
`0x400019ec`, ajout aux listes prêtes par `0x40001a38`. Priorité 5, sous
l'UI à 6. L'IRQ audio poste seulement le sémaphore ; la tâche attend
`0x40001aca` puis consomme huit paquets au plus avant de réarmer ou dormir.
Dans cette variante, l'UI ne consomme aucun paquet. La coupure MIDI OUT
réveille également le consommateur pour les note-offs en attente.

`test_midi_lane_worker.py` exécute les initialiseurs TCB/listes et le chemin
d'attente non bloquant natifs. Il vérifie allocation unique, refus IPL,
réessai après échec, publication, pile, priorité, réveil depuis IRQ,
absence de consommation UI et sortie des douze messages en deux passages.
Quand le singleton MIDI est absent, la file reste intacte et le consommateur
ne se réarme pas en boucle ; les producteurs et le service UI réessaient
le réveil après publication du singleton. Les writers et l'allocation
restent simulés, le changement de contexte scheduler complet n'est pas
exécuté et aucun gain de durée matériel n'est encore mesuré.

[FAIT] Une liaison contiguë du prototype avec consommateur dédié occupait
5 904 octets avant l'ajout du garde singleton. La variante
Model-TG ST réserve déjà six blocs cache de 16 KiB : ses pointeurs natifs
de premier élément et de fin de boucle sont `0x401eb7c8` et `0x401eb7ec`,
soit six entrées de 20 octets retirées depuis `0x401eb750`. Le bloc TG
finit à `0x401bf8c0` ; la limite des six blocs est `0x401c3750`, laissant
16 016 octets candidats. Ce constat de taille ne prouve pas un placement
exécutable : la remise à zéro TG s'arrête actuellement à son propre bloc.

[FAIT] Le bundle Select All compatible, LFO 2 inclus, finit à `0x401fa98d`
après ajout du flux Syntakt compressé, soit 22 131 octets sous la limite
d'image `0x40200000`. Les six voies semblent donc pouvoir tenir avec TG,
sans réduire davantage le cache. [HYP] Copier leur code après la
décompression Syntakt dans la fin des blocs déjà retirés et étendre la
plage préservée au démarrage. Ne jamais occuper le tampon disque nul
`0x401a7750..0x401ab750` ; ne jamais écraser le flux Syntakt avant sa
décompression. Aucune adresse candidate n'est encore utilisée par un
firmware publié. Le retrait de TG fournirait une autre réserve de code,
mais exigerait de remplacer les hooks partagés avec TG.

[À FAIRE] Prouver boot/cache et chaîne complète, scheduler/préemption,
transport réel et première ouverture pendant lecture, puis stockage
persistant par pattern/projet. Pas de flasher MIDI nouveau à ce stade.


## 19. Bundle TG et installateur expérimental (11/10/2026)

[FAIT en émulation] `gen_midi_bank_bundle.py` lie 6 016 octets à
`0x401bf8c0..0x401c1040`, sous la limite des six blocs cache déjà retirés
par TG (`0x401c3750`). Le tampon disque nul reste intact. Le chargeur dans
un masque libre copie le code après décompression Syntakt, invalide les
caches instruction/branchement et étend la plage préservée par le boot TG.
Le payload TG reste identique ; aucune réduction supplémentaire du cache.
L'image finale finit à `0x401fc10d`, sous `0x40200000`.

Le JSON reste isolé sous `experimental/midi-bank/`, hors du catalogue
principal. Ses dépendances imposent exactement le Select All compatible :
Model-TG, Live MIDI Out+Thru (prioritaire sur MIDI Out en THRU), moteurs
Syntakt/MACRO, Sequence Generator avec génération différée, SCRAMBLE par
pas, LFO 2 et les autres mods compatibles. SHA-256 MAIN OS :
`eea78b8b67025e29f59e622fb09ad495f0f8ef5d99057c858d39be6368157f0e`.

`test_midi_bank_bundle.py` exécute le démarrage avec vraie décompression
Syntakt, copie de banque, remise à zéro et conservation TG. Il vérifie
les hooks placés, la chaîne de touches complète, le service UI, les appels
Start/audio et douze sorties USB/DIN en OUT puis THRU. Le bootstrap relit
également à l'identique le MAIN OS repaqueté et agrandi.

`test_midi_lane_scheduler.py` exécute les listes natives et le handler de
changement de contexte : UI priorité 6, consommateur 5, idle 0. Vingt
réveils depuis IRQ donnent quarante messages depuis la pile propre du
consommateur, IPL 0, puis attente sans boucle active. TRAP/RTE ColdFire
sont adaptés par le banc Unicorn ; les writers physiques et l'allocation
restent simulés. Le cache est modélisé, pas mesuré matériellement.
Le chemin Play complet, la préemption physique et le débit réel ne sont
pas validés par ces preuves.

`gen_midi_test_flasher.py` produit un installateur fixe séparé, avec les
uploaders OS Cycles/Syntakt, sélection MIDI et transfert rapide uniquement.
`test_midi_flasher.js` charge les vrais scripts et les deux OS officiels :
hashes de chaque mod, hash MAIN OS et signature du conteneur vérifiés.
Le sélecteur de mods est masqué ; les limites RAM sont visibles en EN/FR.

Commandes : FUNC + SETTINGS + PAGE bascule l'éditeur ; FUNC + pad active
ou coupe MIDI OUT de la voie. Les canaux 7–12 sont fixes. DATA choisit un
réglage, clic DATA édite ; les seize trigs et PAGE éditent les pas.
Les deux banques jouent ensemble. Arrêter avant la première ouverture
après démarrage ; le contexte créé après Play attend le prochain Start.

[À FAIRE] Essai matériel avec TG et Select All, charge UI et absence de
notes bloquées ; sauvegarde par pattern/projet et première ouverture en
lecture. La banque RAM unique persiste entre changements de pattern,
mais disparaît au redémarrage. Si la vérification matérielle avec TG
échoue, AveyCole autorise une variante sans TG ; aucun retrait préventif.


## 20. Transfert interrompu et choix restaurés (11/10/2026)

AveyCole signale un arrêt de progression après environ deux secondes :
le Cycles reste sur sa barre de mise à jour arrêtée. Aucun message de refus
ni dernier bloc reçu n'est disponible. [HYP] Blocage transport ; la cause
matérielle précise n'est pas établie. Ne pas déclarer la panne corrigée
sur machine avant son nouvel essai.

Le flasher d'essai restaure tous les choix, méthodes rapide/classique et
le téléchargement pour Elektron Transfer. La banque MIDI devient une case
indépendante : l'activer sélectionne son bundle TG validé ; modifier cette
combinaison la désactive explicitement. Les autres sélections construisent
réellement leur propre firmware, avec les références du flasher principal.
Le payload firmware de la banque est inchangé.

Le cœur de transfert est une copie générée propre à cette page : pauses
100 ms après départ et entre blocs (au lieu de 50 ms), journal du bloc en
cours, réponse trop courte et fin prématurée refusées. Une erreur conserve
la progression et donne bloc/offset pour les timeouts. Aucun renvoi de bloc
sans acquittement ni reprise automatique d'une mise à jour partielle.
Redémarrer le Cycles après un blocage avant une nouvelle tentative.

`test_midi_transfer.js` simule succès intégral, fin prématurée, réponse
courte, timeout, refus, annulation et chemin classique. Le test navigateur
vérifie les vrais builds avec/sans banque et LFO 2, activation du bundle,
désactivation incompatible, références, téléchargements et choix de méthode.
[À FAIRE] Vérifier matériellement le transfert et identifier le dernier
bloc en cas de récidive ; aucune réussite matérielle revendiquée.


## 21. Retour au transfert principal exact (11/10/2026)

AveyCole signale que la variante temporisée ne dépasse plus 0 %. À sa
demande, tous les changements de transport du §20 sont retirés : le test
charge directement `../flasher/flasher.js`, le même script que main.
Les fonctions UI de connexion, flash, erreurs, choix de méthode et upload
restent celles de main sans modification. La copie de transfert et son
test spécifique sont supprimés. Aucun correctif de transport hypothétique
n'est conservé ; l'essai matériel reste à refaire.

La seule extension visible est la carte expérimentale « MIDI OUT Bank »
dans Sequencer, avec détails EN/FR, initialement décochée. Aucun bandeau,
case externe, sélection forcée au chargement ni méthode masquée. Cocher
la carte sélectionne son bundle validé ; changer cette combinaison retire
la carte et rafraîchit le picker. Les limites RAM et commandes figurent
dans ses détails. Les références de build sont conservées avec l'ajout
banque, sans modifier le MAIN OS de cette dernière.

`test_midi_flasher.js` vérifie l'identité textuelle des fonctions de flash
avec main et l'URL du script de transport partagé, ainsi que les vrais
builds avec/sans banque, l'état initial et les choix. Le test ne prouve pas
un transfert physique réussi. LFO 2 reste dans main, testé par AveyCole.


## 22. Arrêt également sans banque MIDI (11/10/2026)

AveyCole confirme que le transfert bloque avec et sans la carte banque MIDI.
Ce constat exclut son payload comme seule cause, sans établir la cause
réelle. La comparaison matérielle avec main, même sélection après
redémarrage, reste demandée ; aucun nouveau correctif spéculatif publié.

Le test navigateur exécute maintenant aussi le bouton Flash réel avec le
récepteur indépendant du test principal : handshake, départ, CRC et
positions des blocs, réception complète comparée octet pour octet.
Résultats simulés : banque 1 371 040 octets / 670 blocs ; contrôle sans
banque 1 365 280 octets / 667 blocs. Pauses supprimées uniquement dans le
banc de test. Les fichiers du navigateur passent aussi les vérifications
Python des paquets, checksum conteneur et HMAC ; les sections autres que
MAIN OS sont identiques à l'officiel. Ces preuves ne valent pas essai
physique et ne justifient pas de déclarer le problème résolu.


## 23. Main fonctionne ; application entièrement partagée (11/10/2026)

AveyCole confirme « Main just worked » après le signalement d'échec avec
et sans banque sur le test. La cause physique précise reste inconnue.
Pour supprimer toute divergence de l'application, le test charge
maintenant directement les quatre scripts main : builder, catalogue,
flasher et app. La copie générée `flasher-midi-test/app.js` est supprimée.
Aucun fichier ni comportement de l'application principale n'est modifié.

Seul `bundle.js`, chargé après app et avant DOMContentLoaded, ajoute la
recette, une carte bilingue et ses deux références aux objets exportés.
Cocher la banque utilise le vrai bouton Select all pour sélectionner ses
dépendances ; le builder natif refuse une combinaison incomplète. Aucun
remplacement des fonctions de sélection, upload, ports, erreurs ou flash.

Le test ouvre deux DOM indépendants : vrai main et test avec banque retirée.
Même sélection, fichiers officiels, application et sortie `.syx` identiques
octet pour octet. L'envoi UI complet des deux fichiers vers le récepteur
simulé passe encore : 670 et 667 blocs, CRC, positions et contenu vérifiés.
[À FAIRE] Nouveau transfert physique ; pas de réussite matérielle affirmée.

## 24. Trig tenu + DATA et vue musicale (11/10/2026)

AveyCole rapporte « it works », puis demande la saisie des notes comme sur
le séquenceur natif. Il précise « Hold trig + DATA ». Pour le centre de
l'écran, il choisit « Show note velocity as volume », sans nouveaux CC de
panoramique ou volume. Ce retour porte sur le test précédent, pas sur cette
nouvelle interface.

[FAIT en émulation] Un appui bref ajoute/retire un trig. Sur un trig existant,
la suppression attend le relâchement ; un mouvement de DATA annule cette
suppression et édite directement la note. Plusieurs trigs tenus reçoivent
ensemble le même déplacement, borné à 0..127. Les répétitions sont ignorées.
PAGE et le changement de voie sont bloqués tant qu'un trig est tenu, pour
ne pas appliquer le relâchement à une autre page/piste.

La vue principale affiche la note chromatique dans un rectangle inversé
à gauche, Vol/vélocité au centre, canal et pas à droite, MIDI OUT en bas.
Sans trig tenu, DATA sélectionne le pas. Un clic DATA ouvre le menu existant ;
EXIT revient à la vue principale. Les réglages de routage, longueur, vitesse,
vélocité et gate restent dans ce menu. Aucun réglage de son audio n'est touché.

Preuve : `test_midi_lane_page.py`, six voies × quatre pages, appuis/relâchements,
édition multiple, conservation des pistes audio, noms C-1/C4/C#4/G9, cadre
inversé et accès/retour au menu. Présentation et dessin interceptés : le rendu
physique et le confort de l'interface restent à vérifier sur machine.

Le bundle reste expérimental, en RAM partagée entre patterns. Seul le test
MIDI est mis à jour ; aucun changement au transfert principal.

## 25. LED reconnues par le vrai gestionnaire (11/10/2026)

AveyCole demande que la grille bascule vers les trigs de la banque MIDI,
comme les pistes audio. [FAIT en émulation] Le précédent callback placé dans
le sous-objet +8 n'était jamais reconnu : `DrumSelect` hérite de `View` et
`Observer`, pas de `LedHandler`. Le cast natif `0x400f4cec(obj, View,
LedHandler, -2)` rendait zéro. La preuve précédente appelait le slot
directement et ne détectait pas ce défaut ; +8 appartient à `MidiHandler`.

La page réserve maintenant 0x510 octets et ajoute une vraie base LedHandler
à +0x500, avec RTTI privée et destructeurs ajustant le pointeur. MidiHandler
reste intact. Le masque de revendication est corrigé au format big-endian
64 bits (IDs 0..31 dans le second long). Le trig actif reçoit l'état natif 3,
et non 2. La position de lecture vient du dernier pas de la voie MIDI et
utilise l'overlay natif mode 6 ; aucun curseur hors page ou à l'arrêt.

Les actions d'édition signalent désormais aussi la saleté LED par
`0x400760ba`. Le service UI compare le curseur et ne réveille le gestionnaire
qu'en cas de changement ; 100 polls identiques n'entraînent aucun redessin.
Aucun writer MIDI ni allocation dans le callback LED.

`test_midi_lane_led.py` reproduit le cast nul de l'ancien RTTI, puis exécute
le vrai dispatcher `0x40076ca2` et le writer natif sur six voies × quatre
pages. Il couvre revendication, priorité MIDI, pose/retrait de trigs et
retour à une vue audio sous-jacente simulée après retrait de la vue MIDI.
Le périphérique LED et le backend de la vue audio sont simulés ; essai
physique de cette correction encore nécessaire.

## 26. Sauvegarde avec les patterns : recherche (11/10/2026)

AveyCole demande aussi de sauvegarder les séquences MIDI supplémentaires
avec les patterns. Les données actuelles représentent 1 584 octets par
pattern ; avec LFO 2, 1 680 octets. Pour 96 patterns : 161 280 octets,
hors en-têtes/identités/contrôles d'intégrité. Le runtime, la file de sortie,
les notes tenues et les deadlines ne doivent pas être sérialisés.

[FAIT dans l'OS officiel] Le routage des ressources utilise `/projects/` (référence
`0x4012ad53`). `0x40064128` compose ce préfixe avec une chaîne passée en
argument, puis résout la ressource associée. L'énumération des métadonnées
utilise `/projects/*/.metadata` en `0x400649b6`. Ces points sont des pistes
pour retrouver l'identité durable ; ils ne constituent pas encore des
hooks de sauvegarde vérifiés. Les chaînes voisines `RouteTypeHandler` et
`ProjectHandler` indiquent un routage virtuel : aucun répertoire physique
`/projects/` n'est démontré, et ces chemins ne doivent pas être utilisés
directement pour écrire un fichier annexe.

[HYP] Un fichier annexe versionné, rattaché à l'identité native du projet
et contenant des entrées par pattern, éviterait d'écraser les structures
stock. Les primitives de petits fichiers déjà utilisées par Model-TG sont
identifiées (note 57 §9). L'index ne doit pas être le nom affiché seulement :
renommage, suppression/réutilisation d'un slot et Save As doivent être traités.
L'export projet SysEx devra transporter ces données explicitement ; un
fichier annexe seul ne ferait pas partie du backup stock.

[À FAIRE] Identité, notification de changement/copie/effacement, sauvegarde
et rechargement de pattern, Save/Save As projet, écritures atomiques et
erreurs disque, puis preuve de round-trip avec LFO 2 et compatibilité TG.
Aucune nouvelle écriture disque ni persistance livrée dans le test LED.

## 27. Affichage stock avec indicateur B (11/10/2026)

[DEMANDE] Pendant l'édition des voies MIDI, conserver l'affichage du
séquenceur stock ; seul un `B` doit distinguer la banque. Cette demande
remplace la vue personnalisée de la section 24. La vélocité reste la valeur
de volume des notes MIDI ; ne pas ajouter de CC de volume/pan implicite.

[FAIT] La vue actuelle `mlp_overview` dessine encore une disposition privée.
Le rendu natif `MainScreenView::draw` commence en `0x4001b22a` et lit le
projet, la piste sélectionnée et les paramètres du kit via des singletons.
L'appeler directement afficherait les données audio, pas les données MIDI.

[À FAIRE] Réutiliser les primitives et la disposition natives avec les
données MIDI, y compris la vue de note pendant maintien d'un trig, puis
ajouter le B et comparer les images rendues. Ne pas remplacer temporairement
les pointeurs globaux du projet/kit : le moteur audio pourrait les lire.
Ce changement visuel n'est pas encore implémenté ni publié.

## 28. Banques par pattern : premier prototype (11/10/2026)

[DEMANDE] Les six voies MIDI doivent changer avec le pattern et retrouver
leurs notes/réglages lorsqu'on revient au pattern précédent.

[FAIT en émulation] `banks.s` résout 96 blocs indépendants de 1 584 octets
(152 064 octets), refuse les indices invalides et relit l'identité audio
native à `(*0x40a7887c)+30706`. `test_midi_lane_banks.py` exécute ce code
ColdFire et les vrais setters `ml_init/ml_edit` : notes, vélocités et trigs
distincts pour les patterns 0, 1 et 95, puis retours répétés sans mélange.
Les objets actifs sont synthétiques ; le changement natif complet n'est
pas encore exécuté. Le prototype n'est pas inclus dans le générateur.

[À FAIRE] Séparer pointeurs d'édition et lecture, raccorder le changement
effectif (pas la simple demande de prochain pattern), supprimer les note-on
en attente de l'ancien pattern et garantir ses note-off avant le nouveau,
réinitialiser l'horloge au bon temps, gérer projet/copie/effacement puis
sauvegarde disque. Une table RAM par index ne suffit pas pour la persistance
et ne doit pas réutiliser les données d'un autre projet.

[FAIT en émulation, suite] `ml_bank_activate(slot,runtime,clock,bank)`
utilise un slot de lecture indépendant de l'édition. Sous IPL7, un seul
parcours borné à 64 paquets convertit les note-on des canaux 7..12 en
note-off, puis les six notes tenues sont libérées, les 52 octets d'horloge
sont remis à zéro et le pointeur de lecture est publié. Aucun writer
physique n'est appelé. La preuve couvre 58 paquets en file et six places
réservées, conservation des données des patterns, banque inchangée/nulle
sans effet, et les note-off précédant les six notes du nouveau pattern.
La remise à zéro prépare un départ au prochain appel `ml_clock` ; son
alignement sur le véritable changement natif reste à raccorder et prouver.
Le prototype reste hors du flasher.

## 29. Rendu stock et banques par pattern — 11/10/2026

[FAIT en émulation] Le générateur propose deux variantes privées,
`--pattern-banks` et `--stock-display`, avec sortie explicite hors du JSON
publié. Sans ces options, les nouvelles branches restent absentes.
Le bundle composé TG-ST/LFO 2/MIDI passe boot, décompression, ordonnanceur,
writers DIN/USB simulés et basculement A/B au site audio natif. Une demande
de prochain pattern ne bascule pas prématurément ; l'identité active le fait.
Les banques des patterns 0, 1 et 95 sont distinctes et retenues en RAM.
L'allocation est paresseuse côté UI, jamais depuis le hook audio.

[FAIT en émulation] `stock_display.s` réutilise les corps natifs de
MainScreenView et NoteVelocityView sur un objet privé de pile. Les trois
getters de dessin sont détournés à leurs seuls sites d'appel : index de
voie MIDI, vélocité et pan centré. Aucun projet ni kit sonore n'est remplacé.
Le libellé TR reçoit le canal MIDI fixe 7..12 sans modifier l'index interne
0..5 utilisé par les getters. Un B marque la banque. Le menu de réglages
reste disponible séparément. `test_midi_lane_stock_display.py` exécute les
polices/sprites/primitives natifs, au repos et trig tenu sur six voies,
vérifie TR7..TR12 et l'absence de modification des données musicales.
L'utilisateur a approuvé l'aperçu ; cela n'est pas un test matériel.

[FAIT en émulation] `audit_midi_project_identity.py` confirme que le getter
Project lit raw+8, le convertisseur sauvegarde en v6+24 et le préfixe de
chargement restaure raw+8. L'identité nulle est générée une seule fois par
`0x4000eb72`. `0x4000eb12` la renouvelle explicitement avec notification
0x20. Des chemins natifs de chargement/remplacement appellent ce dernier :
un nom de fichier fondé seulement sur cette identité ne doit donc pas être
considéré stable sans raccordement au slot et au cycle de chargement.

[À FAIRE] Persistance disque, séparation entre projets, copie/effacement,
validation complète du rendu placé et coût matériel. Les variantes privées
ne sont pas encore publiées dans le flasher et ne sont pas marquées testées.

## 30. Candidat public sans sauvegarde — 12/10/2026

L'utilisateur demande de publier le candidat complet sans sauvegarde disque.
`flasher-midi-test` utilise maintenant les variantes RAM par pattern et rendu
stock de la section 29. L'intitulé est TR7..TR12 selon le canal, avec B.
Le catalogue et le transport du flasher principal restent identiques.

[FAIT en émulation/navigateur] Boot/scheduler du bundle composé validés ;
dessin natif repos et trig tenu sur les six voies ; basculement de pattern
sans allocation IRQ ; transferts UI simulés intégraux avec et sans banque,
CRC/positions et conteneur signé vérifiés. Sans banque, le firmware produit
est identique octet pour octet au build de la sélection dans main.

[À FAIRE sur matériel] Nouveau rendu, LED et basculement par pattern.
Aucune sauvegarde disque ajoutée. Les données disparaissent au redémarrage.
L'isolation entre projets est inachevée : la carte EN/FR demande de tester
sur un seul projet et de redémarrer avant d'en changer. Cette restriction
reste à lever avec le stockage et le raccordement des chargements.

## 31. Testé sur la machine (12/10/2026)

AveyCole confirme dans cette conversation : « MIDI Out Bank is hardware tested btw ».
Le retour concerne le build RAM courant : rendu stock B/TR7..TR12, édition et
banques par pattern. La carte et le tweak passent à tested. Aucun octet
firmware ne change ; SHA MAIN OS b803b3b2c4b48bbd5d10173846a715f9060af444dc7f14f014ed459fb068551f.
La sauvegarde et l'isolation entre projets restent inachevées et ne sont pas
couvertes par ce statut. Redémarrer avant de changer de projet reste requis.
