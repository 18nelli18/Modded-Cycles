# Clear/Undo LFO et clavier MIDI sur le main TG

La Banque reste en RAM uniquement, avec le démarrage et les dépendances TG du main fonctionnel. Les tests indépendants sans TG ont échoué sur matériel : écran blanc et appareil figé après le logo. Ils ne sont pas intégrés ici.

Avec la Banque sélectionnée, FUNC + PLAY efface la piste A ou B et ses deux LFO ; répéter restaure séquence et LFO. Les autres pistes restent intactes. Sans la Banque, les anciennes recettes sont conservées.

Hors REC, les pas enregistrés B sont masqués ; les touches physiques tenues sont éclairées. Le curseur de lecture reste inchangé. Avec REC, notes, locks et slides restent visibles. ChordKeys garde son clavier lorsqu’un TRIG physique est tenu ; sinon les pads sélectionnent la piste.

Preuves : clear/Undo A et B sur six pistes, notifications et invalidation des snapshots, purges MIDI, clavier/pads et seize touches ; cinq sélections réelles navigateur avec image Python identique et démarrage/cache natifs. Marge flash minimale 1016 octets. Ces nouveaux comportements ne sont pas encore vérifiés sur matériel ; statut expérimental de la Banque.
