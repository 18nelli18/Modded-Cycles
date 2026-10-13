# Diagnostic Save isolé

Page `flasher-save-test`, build `2026-10-12-save-diagnostics`. Principal, Test3 et page noyau existante inchangés. Pack MIDI autonome, six machines natives uniquement ; aucun moteur Syntakt, ACID, MACRO ni sampler Model-TG.

La comparaison après écriture utilisait encore 1616 octets pour les enregistrements de 4928/5024 octets. Le compteur suit désormais ML_RECORD_BYTES. Tests : corruption après l’ancienne limite et au dernier octet refusée ; source inchangée et chevauchement refusé. Cela corrige une couverture de vérification, sans prouver la cause de MIDI SAVE ERR sur matériel.

Les erreurs Save indiquent INIT, OWNER, SYNC, PATH, ROOT, DIR, SNAP, COMMIT, CREATE, DATA, OPEN, ALLOC, WRITE, FLUSH, CLOSE ou DISK. Le succès reste MIDI SAVED. Une erreur disque détectée garde la protection persistante jusqu’au redémarrage. Les tests couvrent les messages et la chaîne Save/Load avec backend simulé. La persistance physique reste à confirmer.

Choisir Standalone MIDI performance bundle, charger un projet sauvegardé dans un slot normal, éditer la face B puis Save Project. Rapporter le texte exact si échec. Les fichiers annexes restent hors export SysEx/backup projet Elektron standard. Le quick assign LFO2 reste à intégrer.

Génération : tools/gen_save_diagnostics_flasher.py --cycles OS1.13.syx --model-tg CLONE. Aucune donnée officielle dans cette note ni dans les sources publiées.
