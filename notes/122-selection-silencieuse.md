# 122 — Selection de piste silencieuse facultative

Demande AveyCole, conversation du18/10/2026 : integrer dans le prochain test une contribution communautaire fournie en JSON. Contexte : https://discord.com/channels/1556268411947057252/1557839199971975261 . Auteur non identifie dans l’extrait fourni ; ne pas attribuer sa creation a AveyCole. Adresses : VA de OS1.13.

## Reponse courte

Module experimental `invert-track`, non coche par defaut, uniquement dans `flasher-invert-track-test`, base principal1.90. Le principal et909 restent identiques a la release LFO approuvee. Diagnostics disponibles dans le test, avec Beat Repeat et moteur SY ; pas de lecture CPU/CUT inventee sans compteurs.

## 1. Octet et comportement

[FAIT] A0x4001d374, offset MAIN118644, `67 d8` (beq) devient `66 d8` (bne). Le deplacement reste identique, la condition sur TRACK est inversee. Aucun payload, aucune memoire reservee, aucun changement de donnees sauvegardees. Le generateur verifie le firmware officiel et les deux octets, puis produit49-invert-track.json ; --check compare exactement la recette. Le flasheur garde son propre old67 et refuse un mismatch.

[FAIT en emulation] PadsView0x4001d180 et le vrai constructeur PadEvent : six pistes, vitesses, TRACK, RETRIG, appui/relachement, changement des modificateurs avant relachement et double relachement. Hors navigateur : pad simple selectionne sans note ; TRACK + pad selectionne et transmet exactement les arguments du relais note/live record natif. La note memorisee est relachee correctement. Les touches de pas ne sont pas modifiees.

Avec navigateur preset identifie par le RTTI du controleur : l’appui simple garde l’apercu sans imposer une selection ; TRACK + pad selectionne et joue. Le banc fournit le resultat du RTTI, mais execute les branches natives et leurs relais. La sortie sonore physique et l’horloge live record ne sont pas simulees : les arguments du relais note-on sont compares au chemin stock, pas un nouvel enregistrement audio revendique.

## 2. Integration et preuves

`tools/gen_invert_track_test.py` produit une copie complete du principal1.90, ajoute la ligne facultative en/fr et le diagnostic. `tools/test_invert_track_flasher.js` compare module absent/present dans quatre configurations : Arp minimal, ensemble complet avec/sans MIDI et Wizard avec Attack/filtre/LFO2. Chaque firmware est signe et verifie ; les MAIN OS depaquetes ne different que par l’octet118644. La preuve native execute aussi le bootstrap des fichiers construits ; les relais deja modifies par les autres modules sont observes a leur entree, leurs corps et le lecteur d’arp sont ramenes au chemin stock dans cette preuve de routage uniquement.

`tools/check_overlaps.py` : aucune nouvelle collision dans171 recettes. Le registre des points de patch est regenere. La recette est disponible en JSON dans le depot, mais aucune carte ajoutee au principal. Module non teste sur appareil ; attendre la verification du proprietaire avant promotion.


[FAIT en emulation] La comparaison module off/on ne change qu’un octet dans les quatre MAIN OS construits, avec et sans MIDI/diagnostic. Le module seul est aussi signe, sans payload. Une ancienne couche de composition mettait en cache les selections connues ; le module est maintenant retire de son input puis ajoute en dernier a la composition finale avec sa reference propre, pour que son activation soit toujours prise en compte. Le JSON garde ordre49 ; aucun autre mod ni cache principal n’est modifie.

Le controle global historique gen_flasher_tweaks --check signale une difference preexistante du catalogue statique. Son rendu est identique avec/sans49-invert-track.json et le fichier principal tweaks.js est identique au commit release ; ce catalogue n’est pas regenere dans ce test. Les generateurs propres au nouveau module et a la page, le registre et les chevauchements passent.
