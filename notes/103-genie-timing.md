# 103 — Sequence Genie : retour du choix Loop/Page sur A et B

Demande AveyCole du 16/10/2026 : remplacer « Sound », valeurs 0/1, par le choix de frontiere de generation. Symptome confirme sur les deux cotes du candidat performance-feedback. Adresses : VA de l'OS 1.13.

## Reponse courte

[FAIT en emulation] La Banque MIDI raccorde au constructeur commun une copie historique de `stock_ui.s`. Les changements de Queue at existent dans le renderer audio courant, mais la copie conserve son etiquette Sound et sa voie numerique. Le probleme touche A et B puisque le callback est commun. Appeler directement le symbole audio `sg_render` ne reproduisait donc pas le defaut : il faut appeler celui de la Banque effectivement raccorde.

## 1. Correction test uniquement

`tools/machines/seq_gen/timing.js` compose apres la persistance MIDI et avant beat repeat. Le callback copie saute vers le renderer audio courant, qui utilise les tables et valeurs Loop/Page deja gardees. Intro, ABI, pointeurs de configuration, menu DATA, generation et Undo restent les memes. Sans Banque MIDI ou sans Genie, aucun changement de firmware.

Le debut desormais inaccessible de la copie accueille 42 octets propres de `timing_boundary.s`. Le hook de frontiere MIDI y saute : Loop autorise seulement le pas zero ; Page autorise aussi 16/32/48. D1 et pile preserves. Le reste du commit conserve ses gardes de piste/voie/snapshot/locks et sa copie atomique. Aucun nouveau payload, emplacement flash, allocation ou schema de sauvegarde. Le code propre remplace une portion inutilisee du payload existant ; taille decompressee identique. Empreintes et compression finales recalculees avant fixation de la source beat repeat.

Le mot Page signifie page de seize pas, comme le choix d'origine, et Loop boucle entiere de la piste selectionnee. Les longueurs non multiples de seize restent couvertes.

## 2. Preuves

`tools/emu/test_genie_timing_current.py` charge le vrai SYX, execute son bootstrap et le constructeur cache et exige les payloads exacts. Le callback reel avant correction affiche Sound 0/1 sur A et B ; apres correction Queue Loop/Page sur A et B. Le vrai encodeur DATA borne le choix. Frontieres MIDI testees sur tous les pas de pistes 16/20/32/48/64 : aucune publication precoce, D1 et pile preserves. Seuls les hooks de chance sont simules dans ce test cible ; leur logique n'est pas modifiee.

```
python3 tools/gen_genie_timing.py --check
python3 tools/gen_genie_timing_flasher.py --check
node tools/test_genie_timing_flasher.js
python3 tools/emu/test_genie_timing_current.py --case build/genie-timing/all
```

Profils navigateur signes : audio seul, Genie+MIDI, Wizard+Genie+MIDI, selection complete et MIDI sans Genie. Ce dernier et le profil audio seul sont identiques au principal. Les preuves existantes MIDI/LED, persistance et beat repeat sont relancees sur la selection complete.

## 3. Materiel

Experimental, non confirme sur machine. Verifier le choix Queue Loop/Page sur A puis B, Generate pendant lecture, application a la bonne frontiere et Undo. Le candidat inclut le filtre principal 1.75 deja confirme par AveyCole ; il ne modifie pas le principal. ChpHzrd reste un autre travail separe.

## 4. Teste sur la machine (16/10/2026)

AveyCole confirme : « sequence genie fix worked, push to main ». Promotion 1.76 avec memes octets que le candidat, seules descriptions/statuts modifies. Le filtre 1.75 reste inclus. Generateur principal `tools/gen_genie_timing_main.py --check` ; candidat historique epingle au principal 1.75. ChpHzrd exclu.
