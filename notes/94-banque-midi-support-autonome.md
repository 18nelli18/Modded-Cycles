# 94 — Banque MIDI sur support autonome Supermodel

Le 14/10/2026, A.V. confirme le test du support autonome sans Banque et demande
sa promotion vers main, puis la réintégration de la Banque dans la même page test.
Adresses : VA de l’OS 1.13.

## Portée

Main reçoit exactement le support testé, sans Banque. La page
`flasher-own-support-test` ajoute la Banque facultative, sans sampler obligatoire.
Les sélections TG/Genie/LFO2/SCRAMBLE/Chord restent indépendantes. Les recettes
sont recompilées à partir du catalogue main actuel ; le support MIT local conserve
sa provenance de notes/93. Aucun stockage projet ou fichier audio utilisateur.
La Banque est RAM seule ; l’édition909 reste inchangée.

## Validation

[FAIT en émulation] Le candidat sans TG avec Genie/LFO2/SCRAMBLE/Chord passe
bootstrap/décompression/clear/cache natifs, combo B, 96 notes/releases ch7–12,
génération B isolée/Undo et scheduler natif. Les périphériques physiques sont
simulés ; coût CPU et stabilité matérielle ne sont pas déduits de ces résultats.

[À FAIRE] Test matériel de la Banque réintégrée. Le résultat utilisateur porte
seulement sur la version sans Banque, qui est marquée testée dans main.
