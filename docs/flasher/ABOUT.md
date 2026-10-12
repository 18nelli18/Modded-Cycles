# Test Flasher 3

Upstream: [18nelli18/Modded-Cycles release 1.54](https://github.com/18nelli18/Modded-Cycles/commit/d89267af1e3ae9b54f54572a8401c4f8c2fe3e78). Fork baseline: aa9c9d5.

Includes ACID, MACRO lo-fi fix, Model:Samples installer support and optional upstream LFO 2/3/4. The upstream LFO mod is an alternative to Sequence Genie and the fork's Second LFO because their firmware hooks/storage overlap. Select All preserves Model-TG, Live MIDI OUT+THRU, Sequence Genie and Second LFO.

The MIDI bank candidate includes the simplified velocity display and uniform TR7–TR12 labels. Its combined boot, worker and browser-transfer checks pass emulation. This combined firmware requires hardware verification.

MIDI bank sequences and the fork's Second LFO settings remain RAM-only. Native persistence and B-side LFO-to-CC routing are not included. No firmware is supplied. Licenses and author credits accompany the page.

Whole-image reference hashes cover upstream's published sample and this exact MIDI-bank bundle; other fork combinations retain per-mod verification.


2026-10-12 update: MIDI Bank no longer requires 6-channel USB audio. Select
All still selects it; uncheck that card to build without it. Both choices
have full MAIN-OS references and pass browser build checks.

Sequence Genie now captures its B-side bank/track when opening, preserving
that target even if the underlying B-side UI object disappears. Generate
and Undo isolation passes emulation; this candidate still needs hardware
confirmation of the reported A-side targeting failure.

Mise à jour : audio USB6 facultatif (décocher après Tout sélectionner).
Genie conserve explicitement sa destination B ; isolation Generate/Undo
prouvée en émulation, confirmation matérielle encore nécessaire.

2026-10-12: AveyCole confirmed B-side Genie targeting works on hardware.
New candidate: centered M1–M6 labels, no duplicate velocity slider, and MIDI
channel 1–16 editable in FUNC + PAGE Scale Setup, defaulting to 7–12.
Display/editing/codec checks pass emulation; this layout/channel change still
needs hardware verification. Saving and B-side LFO CC remain uninstalled.

AveyCole confirme le ciblage Genie B sur matériel. Nouveau candidat :
M1–M6 centré, sans curseur de vélocité dupliqué ; canal 1–16 dans Scale Setup,
défaut 7–12. Sauvegarde et LFO CC non raccordés.

New manual MIDI-bank steps, including steps re-added after deletion, now
start at C5 (MIDI72). Existing active notes and hold-trig + DATA editing
are preserved. Six-lane/four-page editing checks pass emulation.

Les nouveaux trigs MIDI manuels repartent de C5 (MIDI72), même après
suppression. Notes actives et édition trig tenu + DATA conservées.

B-side pad pulse isolation: audio-track pulses are filtered while the
B-side sequencer is open. MIDI-note pulses and selected-pad indication
remain. A-side pulses return when B closes. Emulation passed; hardware
verification needed. / Pulses audio filtrés dans B ; pulses MIDI et pad
sélectionné conservés, retour A natif à la fermeture. À tester sur matériel.

Channel readout: smaller CH1–16 below M1–M6 follows the Scale Setup setting.
Native rendering tested on all six lanes and sixteen channels. / Petit
indicateur CH1–16 sous M1–M6, lié au canal choisi dans Scale Setup.
Saving and LFO CC remain unfinished and are not included in this build.


2026-10-12: Experimental DIN OUT/THRU message merger. Incoming channel messages
are queued whole, with explicit running status restored. Realtime bytes remain
immediate. Only combined mode2 changes; OUT and pure THRU keep their native paths.
Requires the MIDI OUT Bank — Test3 selection. Buffer: seven completed messages,
SysEx maximum1024 bytes; overflow drops a whole incoming message and increments
a counter. This candidate needs the keyboard-cutoff-CC + B-side playback hardware
test. It also fixes edited playback channels and rejected-note gate aging.
Saving and B-side LFO-to-CC are not installed.

Fusion DIN OUT/THRU expérimentale par messages complets, running status restauré,
realtime immédiat ; uniquement le mode combiné2. Nécessite la sélection Banque
MIDI OUT — Test3. Sept messages en attente, SysEx1024 octets maximum ; surcharge
jetée entière et comptée. Test clavier cutoff CC + lecture B requis.
Sauvegarde et LFO CC non inclus. Voir [note technique](../../notes/60-fusion-midi-din.md).

Hardware result, 12 October 2026: AveyCole reports the CC/note-off merger worked and authorizes main publication. This confirmation concerns the merger; saving and B-side LFO CC remain uninstalled.
Résultat matériel du12/10/2026 : AveyCole confirme la fusion CC/note-off et demande la publication principale. Sauvegarde et LFO CC non raccordés.

## 2026-10-12-main-stock-chance

Chance popup and conditions promoted from the hardware-tested Test3 build. Musical writes and MAIN OS references are unchanged. Settings remain RAM only; saving is unfinished.

Fenêtre et conditions Chance promues depuis Test3 validé sur matériel. Écritures et références MAIN OS identiques ; réglages en RAM, sauvegarde inachevée.

## 2026-10-12-step-copy-popup

B-side held-trig + RECORD/STOP copies/pastes one step and its locks, with native COPY/PASTE confirmations. Emulation verified; new addition awaits hardware confirmation. Saving remains unfinished.

TRIG B maintenu + RECORD/STOP copie/colle un pas et ses locks, avec confirmations natives COPY/PASTE. Émulation vérifiée ; confirmation matérielle attendue. Sauvegarde inachevée.
