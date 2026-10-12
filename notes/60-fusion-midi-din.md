# 60 — Fusion DIN OUT/THRU par messages

Demande d'AveyCole le12/10/2026 : notes bloquées en lecture B, clavier MIDI envoyant
un CC cutoff en mode OUT/THRU combiné. Stop deux fois ne libérait pas la note.
Adresses : VA OS1.13. Complément à notes/53 §7.

## Réponse courte

[FAIT en émulation] Le relais octet peut couper un note-off généré ou corrompre le
running status entrant. Le candidat groupe les messages avant le writer DIN natif.
[HYP] C'est la cause du défaut matériel signalé ; la correction reste à tester.

## Chemins et placement

- Hook `400012cc`, six octets stock vérifiés `2f02242f0008`, vers `mm_rx`.
- OUT0 ne relaie rien, THRU1 garde `40001232`. Mode2 utilise `mm_feed` ; realtime
  F8–FF utilise toujours le writer octet. Tous les octets atteignent aussi le
  gestionnaire suivant `*422fee70`, argument et registres préservés.
- `mm_feed` reconstruit les statuts canal, suit F1/F2/F3, F6/F7 et les SysEx.
- `mm_service` appelle `40001100` uniquement IPL0, dans le worker MIDI existant.
  Le writer natif groupe le message sous exclusion IRQ dans son anneau4096.
- Contexte heap8256 octets publié après zéro : en-tête32, huit cases1028.
  Sept messages prêts au plus, une case producteur. Le consommateur ne libère la
  case qu'après copie native. Aucun writer/allocation/attente depuis RX IRQ.
- SysEx maximum1024 octets. Surcharge ou message trop long : rejet entier,
  compteur contexte+20. Pas de garantie pour une entrée saturant durablement la
  sortie DIN ; le candidat doit être testé avec le clavier réel.
- Aucun masque libre assez grand : le générateur fragmente le code avec sauts
  absolus dans les seuls masques libres de tous les tweaks du catalogue. Chaque
  masque est redirigé vers sa copie intacte. Les sections sont mesurées par
  objdump avant placement. Le contexte n'occupe pas la réserve TG.
- La banque passe de15792 à15872 octets ; Model-TG reste disponible. Le bundle
  MIDI doit être sélectionné pour installer cette correction. Pas de changement
  de la carte MIDI OUT/THRU seule dans cette version expérimentale.

## Preuves

`tools/emu/test_midi_merge_stream.py` montre la corruption protocolaire.
`test_midi_merge.py` exécute le parser ColdFire :112 statuts canal, running status,
commun système, realtime, SysEx1024, débordement, plusieurs tours, exclusion IRQ.
`test_midi_merge_native.py` exécute les fragments placés, RX, portes et writer/DMA
OS : quatre découpages CC/note-off, running status restauré, modes0/1 inchangés,
SysEx entière, pile/registres/SR. UART/DMA modélisés, pas de cadence physique.
`test_midi_bank_bundle.py` : boot/décompression TG/ST réels, allocation zéro,
réveil du worker par CC seul, scheduler natif avec adaptation TRAP/RTE.

Le candidat conserve deux corrections séparées, vérifiées par
`test_midi_lane_runtime.py` : le tick lit le canal édité ; une nouvelle note
refusée pour collision n'empêche plus l'expiration du gate précédent.
Sauvegarde et LFO CC côté B ne sont pas raccordés.

## Test matériel demandé

Même clavier/cutoff CC en OUT/THRU combiné, six voies B en lecture DIN, puis Stop.
Vérifier absence de notes bloquées et fonctionnement du CC, puis comparer OUT et
THRU pur. Ne pas marquer cette correction testée avant retour d'AveyCole.

## Test matériel du12/10/2026

AveyCole : « Publish cc fix to main as hardware tested, it worked. »
La fusion DIN CC/note-off est donc testée sur sa machine et promue au flasher
principal à sa demande. Cette confirmation ne concerne pas sauvegarde ou LFO CC.
