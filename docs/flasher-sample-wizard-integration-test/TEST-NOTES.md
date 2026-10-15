# LFO clear / Genie quick-access test

Experimental; hardware verification pending. Main and the 909 edition are unchanged.

- FUNC + PLAY in grid recording: clear the selected track and both LFOs. Repeat to Undo.
- FUNC + PLAY outside grid recording: clear the pattern sequencers and both LFOs on all six tracks. Repeat to Undo.
- Sequence Genie: half-duration introduction; Generate is the first row and initial selection.
- The hardware-tested generated-note copy/paste condition fix is retained.

For this test's LFO clear integration, leave Model-TG unchecked, or enable Model-TG **and ChordKeys** together. Model-TG without ChordKeys does not yet carry the new clear integration.

Native ColdFire emulation verifies the actual track/pattern clear and Undo routines; getters, popup boundaries and notifications are simulated. Physical device behavior remains to be checked.

## Français

Expérimental ; validation matérielle en attente. Main et l’édition 909 restent inchangés.

- FUNC + PLAY en enregistrement grille : effacer la piste choisie et ses deux LFO. Répéter pour annuler.
- FUNC + PLAY hors grille : effacer les séquenceurs du pattern et les deux LFO des six pistes. Répéter pour annuler.
- Sequence Genie : intro deux fois plus courte ; Générer en première ligne, sélectionné à l’ouverture.
- Correctif copier/coller des notes générées, validé sur matériel, conservé.

Pour le nouveau clear LFO, laisser Model-TG décoché ou activer Model-TG **et ChordKeys** ensemble. L’intégration Model-TG sans ChordKeys reste à faire.

L’émulation ColdFire exécute les vrais clear et Undo piste/pattern ; getters, fenêtres et notifications sont simulés. Le matériel reste à vérifier.
