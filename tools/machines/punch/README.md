# PUNCH — integration Supermodel v131

Moteur MIT de100demons, version0.5, commit2b61d3947110bf87826ceffbc0d5e39bc6cc30eb de https://github.com/100demons/cycles-engines.

Les quatre fichiers C/H enregistres dans UPSTREAM.json restent intacts. Compilation selon le manifeste upstream ; pas de changement DSP. Le profil des statistiques utilise le dessinateur Supermodel ; icone droite upstream. ID23 ajoute, MIDI17 toujours dernier ; aucune renumerotation.

Code468a0000, art468ae000, BSS468af000..468b0000. Tout reste au-dessus de Legacy46898630 et sous RETROSYN468b0000. Table24machines,161descripteurs,24rangees ; bornes UI/voix/CC et retention adaptees. Ratio156+2, formatteurs et fine via les objets upstream ; edition normale via bf_edit.

Recette : gen_governor_recovery_test.py --punch --legacy-cart ... --legacy-classics ... --stage [--speak-adult] [--check].
Preuve : tools/emu/test_punch131.py v131 (ou v131adult). L'objet du sous-dossier reference est exclusivement un oracle audio pour les tests.

Les deux variantes sont privees et experimentales. Le paquet upstream contient12modeles, sans snare dediee. Pas de resultat hardware revendique.
