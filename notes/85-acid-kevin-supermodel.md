# 85 — Fondu ACID de Kevin sur Supermodel

Demande d’AveyCole du 14/10/2026 : remplacer ACID par le correctif de Kevin,
puis intégrer WAVE séparément. Source MIT : Kevin-Shallvari/Modded-Cycles,
wave-acid-preview, commit 5b6108ee57cdee4767f91bfb894ccefaadf4210d.
Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT] Nouveau trig : rampe sur 32 échantillons (~0,67 ms). Aucun fondu
supplémentaire sur un slide. Quatre corps liés, partagés par 128 recettes,
augmentent de 72 octets ; aucun moteur stock remplacé.

Le flasher de test reprend le main TG, les recettes RAM de Banque et ChordKeys.
Le moteur complet comprimé avec profondeur 512 augmente de 20 octets.
La source flash Banque/ChordKeys et son unique immédiat dans le crochet
0x401907a4 passent de 0x401f8f76 à 0x401f8f8a. Les destinations RAM,
réservations cache et routines Banque ne changent pas. Pas de sauvegarde MIDI.
Références des écritures et charges utiles recalculées pour chaque recette.

## Preuves

Navigateur : ACID seule, TG, MACRO, MACRO+TG, Select All et Banque sans ChordKeys.
Chaque image est construite depuis l’OS officiel ; références strictes, conteneur
et signature vérifiés. ACID reste expérimental : pas de test matériel d’AveyCole.

Émulation : tools/emu/test_kevin_acid_fade.py utilise la boucle audio native et
compare au DSP C de référence. tools/emu/test_kevin_acid_browser_boot.py compare
l’image Python/navigateur et contrôle démarrage/cache de la Banque.
MOVEC observé : la cohérence physique du cache n’est pas simulée.

## Reproduction

Le générateur tools/gen_kevin_acid_test.py prend le catalogue main exporté,
le dossier main et tools/machines/acid/kevin-fade-map.json comme --upstream.
Le map conserve les quatre anciens/nouveaux corps compilés de Kevin et les
courtes modifications PACK ; aucun firmware Syntakt extrait n’y est stocké.
Le code source du DSP et la licence de Kevin accompagnent le test.

WAVE et Model909 sont des intégrations distinctes encore en investigation.
