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
