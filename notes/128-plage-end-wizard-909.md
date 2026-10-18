# 128 - Plage End de Sample Wizard dans909

Demande AveyCole18/10/2026 : interrompre la machine MIDI et corriger Sample End qui ne passe que de0a1, observe dans909, en particulier avec Slice. La presence du meme probleme dans le principal n'est pas confirmee.

## Reponse courte

[FAIT en emulation] Le profil909 remplace le descripteur62 (slot12) par RC Type, borne0..256 pour ses deux positions. Wizard emprunte le meme descripteur pour End, donc son edition est limitee a1/127du sample au lieu de la plage complete. Le test redirige uniquement les references Wizard vers52, autre descripteur du meme slot12, deja continu0..32512. Les81descripteurs909 et les corps DSP restent identiques ; aucun elargissement global du Type.

## Composition

`tools/gen_909_wizard_end_test.py` construit `docs/flasher-909-wizard-end-test` depuis909.7 et un cas de reference produit par `tools/test_909_current.js`. Le composeur final retrouve les copies Wizard dans la table de boot `midi_current_copies`, verifie chaque ancien octet, modifie les references propres et recalcule empreinte/compression et source du chargeur Beat Repeat.

References : ID du descripteur prive dans sampler_pre ; table des cibles LFO ; comparaison fine_hook ; comparaison wf_popup ; sept jeux de noms (normal/granular/stretch/pluck/wave/lofi/tape-vinyl) ; six operandes vers les records UI du formatter/dessin decimal. Les noms52 restaures sont les vrais noms909. Slot12, notes, locks, marqueurs, samples, plages et DSP909 ne changent pas.

Le test inclut CPU/CUT et n'est pas marque confirme sur appareil. Les flasheurs publies principal et909 ne changent pas. La machine MIDI reste en pause jusqu'a publication de ce test, puis reprend selon la demande explicite AveyCole.

## Preuves

- Navigateur reel jsdom : quatre WAV locaux synthetiques, preparation/signee, remplacement et retrait invalidant le cache, refus d'un OS deja modifie, aucun transfert automatique. Les samples et images restent sous build ignore.
- `test_909_wizard_end.py` : vrais bootstraps, constructeur de tables OS, construction privee Wizard avec gabarit de page fourni ; End passe du lookup62/borne256 a52/borne32512. Tous81descripteurs909 restent identiques. Fine_hook ancien ramene toutes les valeurs teste es a256 ; nouveau conserve les fractions exactes autour de10000. Formatter/dessin fin installe puis restaure sur52, record62 intact. Corps des fonctions voix909 verifies identiques, diagnostic present dans le test seulement.
- Preuves crossover et preecoute existantes avec option explicite `--diagnostics` pour un test ; leur controle sans diagnostic reste obligatoire par defaut pour les releases.

[A FAIRE sur appareil] Verifier End en One-shot et Slice, l'edition des marqueurs dans Slice editor, affichage decimal pendant le geste et retour aux controles909 avec RC Type toujours a deux positions. Aucun resultat materiel annonce avant ce retour.

## Teste sur la machine (18/10/2026)

AveyCole confirme : « sample end fix worked ». Promotion autorisee vers909 principal. Le generateur gen_909_wizard_end_release.py reprend exactement les references confirmees, retire la dependance diagnostic et publie909.8. Tests natifs release : End, crossover et preecoute ; preparation navigateur et signature. Aucun fichier du flasheur principal ordinaire ne change.

