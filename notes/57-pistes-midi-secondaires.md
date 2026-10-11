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
