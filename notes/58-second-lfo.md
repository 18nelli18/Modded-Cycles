# 58 — Second LFO indépendant

Demande d'AveyCole, conversation du 11/10/2026 : clone du premier LFO,
accessible au deuxième appui sur sa page. Adresses : VA de l'OS 1.13.

## 1. Réponse courte

[FAIT en émulation] La routine native peut faire évoluer deux banques de
six états indépendantes avec des paramètres distincts. Ce résultat ne fournit
pas encore le second LFO utilisable : mélange des destinations, interface,
sauvegarde et coût audio restent à établir. Aucun nouveau firmware livré.

## 2. État natif et preuve

[FAIT] `0x40091ab2` reçoit les paramètres des six pistes, le tempo et le masque
de retrigger. Deux références initiales chargent la banque `0x40fde838`
et les indicateurs à banque +28. Chaque état occupe 32 octets ; six états
occupent 192 octets. Les paramètres de piste occupent 66 octets.

[FAIT en émulation] `tools/emu/test_lfo_secondary_state.py` exécute la vraie
routine avec EMAC exacte, 128 doubles mises à jour à 120 BPM. Deux banques
et deux tableaux de paramètres sont utilisés alternativement. Chaque phase
est comparée à son modèle indépendant ; la banque non sélectionnée doit
rester entièrement identique. Les douze phases passent.

Cette preuve reloge les deux références uniquement dans l'émulateur ; elle
ne propose pas de modifier le code à chaque appel sur la machine. Les
adresses RAM choisies appartiennent à la fixture, pas à une réservation
validée sur le matériel. Destinations désactivées dans cette première preuve.

## 3. Prochaines validations

[À FAIRE] Wrapper réentrant avec banque propre sans modifier les instructions
pendant la lecture ; destinations différentes et identiques, modulation
additive sans accumulation ni écrasement de la première ; formes, modes,
fondu et retrigger indépendants ; budget audio maximal avec les moteurs.

[À FAIRE] Deuxième page LFO, état sélectionné, stockage persistant démontré
libre, copie/changement/sauvegarde du pattern. Ne pas prendre le raccourci
réservé à la seconde banque MIDI ou aux autres mods.

## 4. Entrée indépendante et mélange exécutés (11/10/2026)

[FAIT en émulation] `tools/machines/lfo_secondary/update.s` reproduit le
prologue de `0x40091ab2`, reçoit la banque en quatrième argument, puis rejoint
le corps natif à `0x40091aca`. L'épilogue natif restaure les registres et la
pile ; aucune instruction native n'est réécrite entre les appels. Les douze
phases restent indépendantes sur 128 doubles mises à jour.

[FAIT en émulation] `mix.s` reçoit sortie, base non modulée, taille en mots,
et les deux banques. Il rassemble au plus douze destinations, additionne
leurs deltas signés, puis sature une seule fois à 0..32 512. Aucun allocateur,
140 octets de pile. Le test assemble et exécute ce code ColdFire avec les
sorties natives, destinations machine identiques/distinctes (11/14), six
pistes, bases 0/16 384/32 512, 48 mises à jour. Il vérifie le bloc entier et
répète le mélange avec la même base pour exclure une accumulation.

[À FAIRE] Mesure des instructions/temps et intégration au caller
`0x4005979e` : celui-ci obtient le bloc via `0x40058474`, le prépare via
`0x40056e24`, puis appelle le LFO à `0x400597c6`. Le mélange doit conserver la
base avant cette modulation. Les destinations LFO elles-mêmes, toutes les
formes/modes, l'étendue exacte du bloc et les retriggers restent à couvrir.
Les buffers de preuve sont simulés ; aucun LFO 2 installé dans le flasher.

Dans les cas couverts, maximum observé : 930 instructions pour l'entrée LFO,
1 807 pour le mélange. Ce comptage n'est ni une mesure DDR/cache, ni une
validation de la marge audio. Le test couvre un cas où saturer après chaque
LFO donne un résultat différent de la saturation unique retenue.
