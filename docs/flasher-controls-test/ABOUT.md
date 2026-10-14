# Supermodel controls test — 13 October 2026

Includes the published ChordKeys/roterodamus integration, with its original pad
behavior, all existing choices and MIDI protocols. New experimental changes:

- Control All Config: TRACK + TRIG 1–6 excludes/includes audio tracks; lit trigs follow. The selected track always follows. TRACK + knob applies Control All; choices reset at startup.
- MIDI Bank selected: removing an A-side grid trig clears all native locks and
  SCRAMBLE/slide markers. B-side deletion verified to clear all twelve CC locks,
  chance/retrig/arp/nudge and slide data; fresh note C5, velocity 100, length1.
- Second LFO: equivalent frame-copy code uses 476 fewer executed instructions
  per audio block. CPU percentage and complete overload recovery are not claimed.
- MIDI Bank remains RAM-only. Track clear + LFO Undo is still in development.

Test on hardware: delete/recreate locked trigs on A/B; play the same Syntakt/ACID
pattern used to reproduce timing trouble. Check notes, MIDI and active LFOs.

Inclut ChordKeys/roterodamus publié, avec ses gestes de pads d’origine, tous les
choix et protocoles MIDI. Nouveautés expérimentales :

- Control All Config : TRACK + TRIG 1–6 exclut/inclut les pistes audio ; trigs allumés = incluses. Piste active toujours incluse. TRACK + potentiomètre applique Control All ; choix réinitialisés au démarrage.
- Banque MIDI cochée : effacer un trig grille A supprime ses locks natifs et
  marques SCRAMBLE/slide. En B, suppression des 12 locks CC, chance/retrig/arp/nudge
  et slide vérifiée ; nouveau pas C5, vélocité100, longueur1.
- Second LFO : copies identiques avec 476 instructions exécutées en moins par
  bloc audio. Aucun pourcentage CPU ni correction complète de surcharge annoncé.
- Banque MIDI en RAM. Clear piste + Undo LFO encore en développement.
