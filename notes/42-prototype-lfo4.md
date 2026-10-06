<!-- SPDX-License-Identifier: MIT -->
# Prototype de quatre LFO natifs

Cette proposition conserve le code original existant : trois banques supplémentaires par piste, publication séquentielle, menus natifs, sélection, affichage et invalidation, protection des lecteurs et de la durée de vie, ajout vérifié du sélecteur, destinations sûres, RANDOM, SPEED et persistance Sound/Project. Elle ne constitue pas une fonction installée ni une preuve matérielle.

Les fichiers sous `tools/machines/lfo4/source/` sont des sources expérimentales pour revue. Certains sont des extraits : les prologues d'origine, les valeurs par défaut et les fixtures privées ne sont pas distribués. Les références non résolues restent explicites dans `DEPENDENCIES.json`. Aucune intégration manquante n'est inventée et aucun outil de firmware n'est exécuté.

Les tests host réutilisent les assertions originales de publication, d'admission, de géométrie, d'énumération et des trois/quatre lignes du menu. Ils utilisent une mémoire synthétique. Les tests du codec portable restent un composant de soutien, décrit dans la note 41. Aucun de ces tests n'est une preuve de DSP, d'affichage physique ou de sauvegarde durable.

Le résultat accepté reste quatre LFO complets par piste : toutes les formes et destinations natives, sync/reset/Fade/Start Phase, édition et persistance. Les preuves CPU historiques sont limitées et séparées ; les 176 contrôles généraux ne sont pas 176 tests LFO complets. Les vérifications de concurrence, de transport/MIDI, de changement de profil/Project, de média/cache/DMA, d'amorçage, de mémoire/pile/délai et du matériel restent ouvertes.

La série proposée réunit d'abord runtime, édition et destinations sûres ; ajoute les contrôles/RANDOM ; persiste les identités Sound ; joint Project/BANK/média ; puis qualifie l'ensemble. Le correctif indépendant du validateur est facultatif. Aucun tweak de flasher, release, annonce ou image de firmware n'est ajouté.

Le MIT s'applique uniquement aux fichiers originaux explicitement énumérés dans la licence de contribution. Les octets/données du firmware officiel et les dépendances tierces conservent leurs propres conditions.
