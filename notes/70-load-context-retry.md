# Test3 : reprise après contexte absent

Le matériel affiche MIDI: CONTEXT au Save et bloque B-side après Load d'un projet déjà enregistré. La cause matérielle exacte reste inconnue.

Le service abandonnait définitivement le serial Load lorsqu'une allocation du contexte échouait. Il conserve maintenant ce Load en attente et retente sur un prochain cycle UI, sans publier de banque appartenant à un autre projet. Les autres erreurs de Load ont des messages distincts (ID, SLOT, TABLE, READ, APPLY).

Validation : simulation du contexte absent, allocation refusée une fois, puis restauration sur le même serial sans nouvelle notification native. Backend fichiers simulé ; persistance matérielle à vérifier. Model-TG et le catalogue existant conservés. Flasher principal inchangé.
