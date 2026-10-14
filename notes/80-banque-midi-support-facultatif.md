# 80 — Banque MIDI avec supports facultatifs

Demande d’AveyCole, 13/10/2026 : sélectionner la Banque MIDI sans imposer Model-TG, Sequence Genie, LFO2 audio, SCRAMBLE audio, Live MIDI OUT+THRU ou les machines supplémentaires. Une page de test distincte ; main conservé. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT en émulation] 32 backends sont compilés selon les cinq choix TG, Genie, LFO2 audio, SCRAMBLE audio et ChordKeys. Le noyau MIT de performance remplace le sampler lorsque TG est décoché. Les helpers partagés sont internes ; aucune case de support n’est forcée. La Banque reste en RAM, sans sauvegarde sur disque.

## 1. Chargement et réserve

- Noyau sans sampler à `0x401ab750`, Banque à `0x401ace40`.
- Avec TG : son code et ses symboles sont conservés ; Banque à `0x401bf8c0`.
- Callbacks de fusion MIDI, CC, conditions et clipboard dans le RAW privé, plutôt que dispersés dans des sprites. Seuls le chargeur et le décompresseur doivent exister avant le chargement.
- Chargeur à `0x401907a4`, source compressée fixe à `0x401f8f76` ; gap borné dans les builders JS/Python.
- Quatre à cinq blocs privés sans sampler ; huit à neuf avec TG. Les blocs disque restants sont vérifiés par le constructeur de cache natif.
- ChordKeys relogé derrière le RAW Banque ; thunk et vtable des pads passent par le wrapper qui conserve HARMONY lorsqu’un TRIG physique est tenu.
- Aucun hook de stockage installé. Aucun résultat de persistance revendiqué.

## 2. Dépendances remplacées

- Sans Genie : ses menus et adaptateurs ne sont pas assemblés ; SCRAMBLE CC utilise un xorshift privé, prouvé sur 4 096 sorties.
- Sans LFO2 audio : le callback revient au LFO natif. Les LFO CC internes de B restent dans la Banque.
- Genie/SCRAMBLE audio facultatifs : leurs références aux helpers TG sont relinkées vers le noyau partagé lorsqu’il n’y a pas de sampler.
- Les menus/actions Genie sélectionnent les données B, avec Undo et effacement des chances ; A est comparé avant/après.
- Les moteurs Syntakt/MACRO/ACID démarrent avant la décompression Banque. Les 4 064 variantes de reprises vérifient les anciens octets, sans effacer de conflit.
- Certains flux TG+MACRO+ACID utilisent l’encodeur cost512 existant. Le RAW décompressé doit être identique ; seuls les paramètres d’encodage et les empreintes sont publiés, jamais le firmware ni les moteurs extraits.

## 3. Preuves

`gen_midi_optional_support.py`, `gen_midi_independent_candidate.py`, `gen_midi_optional_chord.py`, `gen_midi_optional_matrix.py`, `gen_midi_independent_flasher.py`.

- `emu/test_midi_optional_matrix.py` : 32 boot/clear/cache natifs, entrée par le hook de touche réel, 96 notes et releases par backend, scheduler natif wait/post et pile dédiée. Avec Chord : deux interfaces de pads et captures HARMONY.
- `test_midi_independent_flasher.js` : cases réelles, aucun support forcé, hashes de mods et conteneurs, machines facultatives, TG/Chord seuls, Select All, EN/FR.
- `emu/test_midi_independent_browser.py` : images JS/Python identiques, bootstrap/cache des images réellement sélectionnées.
- Les allocations UI, la présentation et les writers physiques sont des fixtures ; MOVEC cache observé mais non modélisé. TRAP/RTE adaptés au format ColdFire.

## 4. Garde conservée

[FAIT] LFO Plus utilise un autre dispatcher audio ; la Banque refuse encore cette association. Ce test découple les supports nommés ci-dessus, sans supprimer une incompatibilité réelle par simple changement de case. La compatibilité LFO Plus reste à intégrer séparément.

## 5. À vérifier sur la machine

Page expérimentale seulement. Vérifier transfert MIDI/USB, passage A/B, notes/releases, CC/slide/retrigger, menus, puis associations choisies avec les machines. Aucun gain CPU matériel annoncé. Le dépassement CPU signalé précédemment reste un sujet distinct.

Après cette publication : intégrer clear/Undo du LFO2 A/B, selon l’ordre demandé. Les prototypes de sauvegarde restent désactivés.
