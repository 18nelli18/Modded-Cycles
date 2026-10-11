# 54 — Générateur étendu et tirage du son

Demande d’AveyCole dans cette conversation, le 10/10/2026 : plages de variations, rythme/notes séparés, mutation, Euclid, tirage du son distinct, mutes dans la page et cartouche d’entrée. Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT en émulation] Variante séparée `experimental/advanced/49-scale-gen*.json`, produite par `tools/gen_seq_gen.py --advanced`. Le principal reste identique. La page de test utilise un catalogue autonome et les mêmes autres mods.

## 1. Séquence

24 lignes, quatre visibles. Minima/maxima velocity 1–127, decay et pan 0–127, pan 64 au centre. Les bornes croisées empêchent min > max. Both change notes et rythme ; Rhythm conserve les notes des anciens trigs encore actifs ; Notes conserve tous les drapeaux. Mutation choisit indépendamment les pas éligibles (0–100 %), sans garantir un nombre exact de changements. Une note tirée peut être identique à l’ancienne.

Euclid : `(((pas - rotation) mod longueur) * coups) mod longueur < coups`. Coups bornés à la longueur active. Le générateur ne touche pas les pas au-delà de cette longueur. Les pas non retenus par mutation utilisent la sentinelle 254 ; les repos 255. Snapshot intégral piste et pool de p-locks, contrôle d’identité avant Undo.

## 2. Son indépendant

SETTINGS + TRACK ouvre les réglages du son (pas de tirage automatique). Random sound applique les quatre contrôles machine (slots 11–14) et decay (18), selon les descripteurs de la machine active : `0x4005a692`, bornes `0x4005a65a`. Setter groupé stock `0x4001416c`. Amount interpole entre le son courant borné et un tirage dans les plages autorisées. Amount 0 ne touche rien. Sampler (machine 6) refusé. Snapshot indépendant de cinq valeurs ; Undo refuse une autre piste, un autre son ou une autre machine.

[FAIT en émulation] Les six machines stock passent le vrai setter et Undo exact, avec intensités 0/25/100. [À FAIRE] Extension aux descripteurs des machines ajoutées et essai hardware.

## 3. Mutes et entrée

FUNC capturé sans ouvrir QuickMuteMenu ; PadHandler privé (+16) route pads 1–6 vers le toggle stock `0x40013904`, une fois par pression. Le relâchement reste consommé même si FUNC a été relâché en premier. PLAY/STOP continuent vers la vue transport ; Undo reste disponible.

Cartouche « SEQ. » puis « GEN. », centré. Le wrapper LED UI lit `blk_clk` (1500 Hz) et efface le cartouche après 1500 blocs avec une seule demande de redraw. Aucune attente ni modification dans l’ISR audio. Le hook Model-TG reste chaîné. [FAIT en émulation] temporisation, débordement 32 bits, quatre marges et deux lignes ; [À FAIRE] contraste et lisibilité sur écran réel.

## 4. Allocation et compatibilité

6852 octets répartis dans 51 masques de sprites libérés ; allocation déterministe par sections, exclusion de tous les masques occupés par les tweaks canoniques. Les pointeurs de sprites doivent être uniques et alignés, leurs octets stock vérifiés. Les cinq vtables du handler LED Model-TG sont redirigées après vérification des écritures de base. Aucun octet du firmware officiel n’est ajouté au dépôt.

Le catalogue de test remplace seulement les deux variantes du générateur, conserve les 18 cartes et recalcule 767 images de référence avec tous les contrôles de conflits/caves et empreintes par mod.

## 5. Preuves et suite

`tools/emu/test_seq_gen_advanced.py` : longueurs 1/7/16/31/64, trois modes, mutation 0/25/100, plages, Euclid/rotation, restauration exacte, 24 lignes, preview/Undo, mutes sans répétition et cartouche temporisé. Les frontières allocation/dessin/observateurs restent simulées ; le getter, toggle et setter mute stock sont exécutés, bitmap vérifié en lecture active, observateur et frontières MIDI simulés. Ne pas assimiler ces preuves à un boot complet ou un essai matériel.

[FAIT en émulation] Lecteur de touches réel SETTINGS + TRACK/PAGE, idempotence et relâchements ; vrai chemin FUNC + pads, mute/unmute pendant la lecture. [FAIT] Audit avec origin/main upstream : aucun conflit nouveau (154 tweaks). Preuve navigateur : 18 cartes conservées, fichiers officiels, quatre builds dont la plus grande combinaison, empreintes intégrales/par mod et rejet volontaire d’une empreinte altérée. [À FAIRE] Essais des machines ajoutées et validation matérielle. La génération en lecture, avec application en début de boucle, relève d’un autre prototype et n’est pas activée ici.

## 6. Incident matériel signalé le 10/10/2026

AveyCole : « the random sound feature crashed my model cycles ». Le tirage du son
reste non validé ; les preuves précédentes interceptaient les observateurs et ne
couvraient pas l’environnement matériel complet. Cause non établie. Retrait
temporaire des extensions du flasher de test, remplacé par le catalogue principal
déjà testé. Aucun changement du principal. Les sources/JSON expérimentaux restent
disponibles pour l’investigation, sans nouveau résultat matériel positif.

Nouvelle demande : mod son indépendant, combo direct sans menu, cartouche
« SCRAMBLE ». Génération pendant la lecture conservée comme travail distinct.
