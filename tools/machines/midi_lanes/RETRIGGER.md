# Retrigger/arp B — état du prototype au 12 octobre 2026

Option locale `gen_midi_bank_bundle.py --lfo-cc --retrigger` ; flasher publié
inchangé. Aucun résultat matériel revendiqué.

- `retrigger.s` : armement, répétition bornée, annulation ; la file existante
  réserve les Note Off avant d'accepter les Note On. Vitesses natives 0..16.
  Len fini converti via table OS réelle ; INF127 utilise active=2 et ne compare
  aucune échéance artificielle. Stop/mute/changement de pattern restent requis.
- `retrigger_service.s` : six états privés de 20 octets ; service infra-pas,
  arrêt sur mute, stop/pause, canal/port ou configuration invalide. Changement
  de pointeur de pattern : annulation avant le service. Aucun I/O physique.
- `integration.s` : raccordement audio conditionnel `ML_REPEAT`, avant
  `ml_clock`. Le générateur définit cette option seulement avec `--retrigger`.
- `retrigger_locks.s` : 64 enregistrements privés de 8 octets par voie.
  Champs enabled/rate/length/curve/mode/octaves ; octet6 = masque des champs
  verrouillés. Le résolveur combine les défauts de voie et les locks sous IPL7,
  valide tout avant de copier le résultat. Zéro explicite ≠ héritage.
- `arp.s` : état privé de notes tenues (12 maximum), six modes et quatre
  octaves. Portage de l'algorithme MIT `tools/machines/arp/arp.c`, sans ses
  pointeurs audio. Comparaison de 9600 sélections avec la référence Python :
  notes non triées, doublons, limites MIDI, unisson et accords de 12 notes.
- `arp_tick.s` : sélection sur une copie de l'état arp, puis vrai retrigger et
  vraie file privée. Progression/seed publiées seulement après Note On accepté.
  Une file pleine ne consomme pas de note d'arp ; OFF conserve le paquet courant.
- Le service six voies appelle maintenant `arp_tick` avec mode/Oct/état propres
  à chaque voie. `ml_repeat_service_with_arp` reçoit une banque explicite : un
  contexte live peut rester distinct du séquenceur sans échanger de global.
  Les données de notes sont réinitialisées au changement de pattern, tout en
  conservant mode/Oct. Raccordement physique du clavier encore absent.
- `retrigger_patterns.s` : allocation UI de 3120 octets par pattern, table de
  96 couples banque/réglages. Échec/retry et locks isolés prouvés. Pointeurs
  d'édition et lecture publiés séparément ; lookup audio au changement seulement.
- `retrigger_step.s` : raccordement réel depuis `ml_pattern_tick`. Résolution
  des locks, Len natif, armement, note source d'arp, réglages mode/Oct par voie.
  Repos préserve Len ; lock OFF termine le retrigger et rejoue le chemin normal.
- `retrigger_menu.s` : FUNC+RETRIG ouvre un modèle MenuView privé rendu par le
  stock ; Rte/Len/V.Crv/A.On/Arp/Oct, trois lignes visibles avec défilement.
  DATA édite défauts ou lock du pas maintenu. BACK conserve B. Clavier direct
  actif derrière le menu même REC actif. V.Crv affiche --- et reste non éditable dans le candidat publié.

Preuves d'intégration : `test_midi_retrigger_menu.py` et
`test_midi_bank_bundle.py --pattern-banks --stock-display --lfo-cc --retrigger`.
Boot TG/Syntakt, décompression exacte, réserves/cache, getters, worker/merger,
banques et scheduler passent. Candidat après clipboard : marge image946 octets. Les tampons de clipboard
retrig (1040 octets) sont alloués dans le heap UI, hors IPL7, pour conserver
la réserve de sept blocs TG. Un échec refuse le raccourci sans mutation.
La preuve audio du wrapper emploie encore un témoin `ml_clock` pour l'ordre
d'appel ; les preuves de bundle et de pas sont distinctes.

`audit_midi_retrigger_length.py` exécute l'armement stock 384 fois : les128 Len
et trois horloges/latences, dont wrap. Allocation/copie/On sonore sont témoins,
mais le calcul temporel est natif. Len127 donne -1 ; Len fini donne la moitié
du gate restant + table native Len - latence. Conversion en unités B testée
séparément, y compris limites et INF avec arp.

Preuve : `tools/emu/test_midi_lane_retrigger.py --cycles firmware/model-cycles_OS1.13.syx`.
Le service, les locks, le wrapper audio et la file MIDI sont assemblés et
exécutés. Dans le test du wrapper, `ml_clock` est un témoin d'ordre d'appel,
pas une preuve du déroulement complet du séquenceur natif. Les 64 combinaisons
de masques, les six voies simultanées, le wrap temporel, la saturation de file
et les changements de propriétaire/canal sont vérifiés.

À raccorder avant publication :

1. Sauvegarde des extensions par projet à raccorder ; Load remet les réglages à zéro.
2. Live retrig et accords depuis le clavier : contexte/file distincts prouvés,
   mais hook des touches/RETRIG et service live restent à raccorder.
3. Courbe de vélocité native : ligne réservée non éditable (---), effet non raccordé.
4. Mesure de charge IRQ, preuve du parcours combiné menu->pas dans le bundle,
   tests navigateur et publication expérimentale.
5. Extension du format de sauvegarde : le sidecar MBK1 actuel ne transporte que
   les 1584 octets des séquences B et ne sauvegarde pas encore ces locks.

La preuve `test_midi_storage_session.py` valide Save/Load avec backend FS simulé.
Elle ne prouve ni le stockage physique, ni le cycle boot/working96/Save As sur
matériel. Ne pas annoncer la sauvegarde disponible sur cette seule base.

## Clipboard et suppression

La suppression UI d'un trig retire ses huit octets de locks et annule le
repeat actif de la voie via le chemin Note Off réservé. Les défauts restent
intacts. Copie/colle transporte les 520 octets de réglages et locks de la voie ;
clear conserve les huit défauts et initialise les 64 locks. Undo restaure
l'extension avec les notes, sans toucher canal/port/mute ni les pistes audio.
Les modifications de clipboard annulent le repeat avant publication.

Preuves : `test_midi_retrigger_menu.py` (vraie suppression par appui/release),
`test_midi_lane_clipboard.py --retrigger` (copie/colle/clear/Undo et isolation).
Aucune validation matérielle de ces nouveaux chemins pour le moment.

## Test3 retrigger séquencé

Load natif réussi (y compris working96) bloque immédiatement les pointeurs
retrig et réserve les Off. La prochaine visite UI retire et libère les
extensions hors IPL7, puis initialise de nouveaux défauts. Un Load échoué
ne change rien. `test_midi_retrigger_project.py` exécute le vrai chargeur,
avec cache/convertisseur simulés. Cela ne prouve pas la sauvegarde physique.

Le générateur `gen_midi_retrigger_test.py` part de la page Test3 du commit
7abbe84a9fae9c57a44128e4ed4dcbb0a48f0aa4, conserve son transport et ajoute la
recette retrig ainsi que le décodage/contrôle du flux précompressé côté navigateur.
La sauvegarde, le retrig live et V.Crv restent explicitement inachevés.

## Correction du raccourci de pas

REC actif : maintenir un trig et appuyer deux fois sur RETRIG. Le premier
appui ouvre le menu ; le second bascule uniquement le lock enabled du pas.
Les éditions suivantes ciblent ce pas tant que le trig reste maintenu.
FUNC+RETRIG conserve son accès au menu de voie. La preuve des événements
clavier vérifie le défaut inchangé, le rate privé et la conservation du trig
au relâchement. Correction expérimentale, non testée sur matériel.
