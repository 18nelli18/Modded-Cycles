# Test3 avec Model-TG : diagnostic Save

Build `2026-10-12-test-3-tg-save-diagnostics`. Demande utilisateur après gel du candidat autonome : remettre les nouveaux diagnostics sur Test3, avec Model-TG et toutes les anciennes sélections. Le principal reste inchangé. La cause du gel autonome n’est pas établie.

Base : assets du flasher principal au commit72b9f24b9e4556018896fed17def883f9c5bd58d. Catalogue tweaks.js identique au blobebcb77d89a4bda05fbe7a7f44c7046e6bf98bbaf. Le bundle MIDI est reconstruit avec Save MBK4, autosave WRK, LFO A2/B, live recording et diagnostics de note67. ACID et MACRO conservés, USB6 facultatif ; aucune sélection supprimée. Cache TG : neuf blocs réservés, sept natifs disponibles. Marge image :3850octets.

Vérifications : boot TG/Syntakt natif et décompression, cache, banque MIDI, routage DIN/USB, conditions, scheduler et séparation des données passent en émulation. Save/Load et tous les messages passent avec filesystem simulé. Navigateur : startup EN/FR, hashes exacts avec/sans USB6, transfert simulé684blocs et retour au moteur normal quand la banque est désactivée. Les scripts partagent un nouveau cachebuster.

Persistance matérielle non confirmée. Le quick assign LFO2 n’est pas encore intégré. Aucune modification de docs/flasher dans cette publication.
