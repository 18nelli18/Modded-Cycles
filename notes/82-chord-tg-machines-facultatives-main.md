# ChordKeys : TG conservé, machines facultatives

Le flasher ne simule plus Select All en cochant ChordKeys. Model-TG reste requis ; ChordKeys n’impose plus Banque MIDI, Syntakt, MACRO ou ACID. Les sélections Banque gardent leurs dépendances et leur firmware principal existants. Aucun noyau sans TG n’est intégré.

Sans Banque, le chargeur TG/Chord déjà établi charge 9620 octets à 401c383c. Les chaînes de démarrage de chaque moteur facultatif sont explicitement adaptées, avec références writes/payload strictes. Le padding navigateur est limité au tweak Chord TG, source401f8f76 et base401aa140 ; tous les autres gaps restent refusés.

Sept choix réels navigateur : Chord+TG seul ; chacun des trois groupes machines ; Genie/LFO2/SCRAMBLE ; Select All ; Banque sans Chord. Images Python identiques, boot/depack et cache natifs. Les deux choix Banque conservent exactement les hashes de la release clear/Undo. Les nouveaux choix Chord+TG sans Banque restent à vérifier sur matériel.
