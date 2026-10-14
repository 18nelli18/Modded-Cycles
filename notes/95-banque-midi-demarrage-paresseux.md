# 95 — Banque MIDI : allocation différée après le logo

Le14/10/2026, A.V. signale un blocage sur le logo avec Select All sans TG,
après validation du support sans Banque. Adresses : VA de l’OS1.13.

[FAIT] Le service UI appelait ml_prepare au premier passage, avant toute entrée B.
Cette voie construit ensuite les contextes CC/pattern et la tâche MIDI.
[HYP] L’ordre d’initialisation matérielle pourrait ne pas tolérer ce travail si tôt.
Il ne s’agit pas d’une cause démontrée du blocage.

Le candidat remplace cet appel unique par trois NOP dans les16 profils sans TG.
Le combo B conserve ml_prepare ; après publication du contexte, le service normal
reprend. Aucun service de sauvegarde ajouté. Les profils TG restent inchangés.
Le flux compressé utilise64 octets supplémentaires de son propre padding flash ;
les limites0x40200000, les blocs RAM/cache et les symboles musicaux restent fixes.
Les références w/p sont régénérées depuis les recettes et gardées strictes.

[À FAIRE] Validation matérielle du démarrage puis première entrée B et lecture.
Main et l’édition909 inchangés ; sampler séparé toujours en attente.

[FAIT en émulation] Comparaison des16 profils : heap dans l’ancien premier UI,
aucune allocation/tâche dans le nouveau. Bootstrap/cache, première entrée B,
96 notes/releases, Genie B et scheduler natif passent sur le profil complet.
