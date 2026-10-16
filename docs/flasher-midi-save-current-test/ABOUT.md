# MIDI saving test — experimental

This separate test extends the hardware-tested independent MIDI Bank. Main remains RAM-only.

Stop playback, edit B, then use **Save Project**. **MIDI SAVED** means the MIDI files were written and read back successfully. An **MIDI SAVE E##** or **MIDI LOAD E##** popup is a failure; report the exact code. To test persistence, restart, load the same saved project and open B. Check another pattern and project too.

Includes notes/live timing, retrigger/chance/arp, CC assignments/locks and both MIDI CC LFOs. RETROSYN and TINY remain available; Sample Wizard is optional. Model-TG stays blocked. Two recovery copies per pattern live in ModdedCycles, outside standard Elektron backups and SysEx exports. Older saving formats are not imported. Saving requires Stop and does not run automatically at power-off. Physical durability has not been verified.

## Français

Page séparée : extension expérimentale de la Banque MIDI autonome testée. Le principal reste en RAM.

Arrêtez la lecture, éditez B et faites **Save Project**. **MIDI SAVED** confirme écriture et relecture. **MIDI SAVE E##** ou **MIDI LOAD E##** indique un échec : rapportez le code exact. Redémarrez, chargez le même projet sauvegardé et ouvrez B pour tester. Vérifiez aussi un autre pattern et un autre projet.

Notes/timing live, retrigger/chance/arp, assignations/locks CC et deux LFO CC inclus. RETROSYN/TINY disponibles, Sample Wizard facultatif, Model-TG interdit. Deux copies par pattern dans ModdedCycles, hors backups/SysEx Elektron. Anciens formats non importés. Stop requis, aucune sauvegarde automatique à extinction. Durabilité physique non vérifiée.
