# Test Flasher 3

Upstream: [18nelli18/Modded-Cycles release 1.54](https://github.com/18nelli18/Modded-Cycles/commit/d89267af1e3ae9b54f54572a8401c4f8c2fe3e78). Fork baseline: aa9c9d5.

Includes ACID, MACRO lo-fi fix, Model:Samples installer support and optional upstream LFO 2/3/4. The upstream LFO mod is an alternative to Sequence Genie and the fork's Second LFO because their firmware hooks/storage overlap. Select All preserves Model-TG, Live MIDI OUT+THRU, Sequence Genie and Second LFO.

The MIDI bank candidate includes the simplified velocity display and uniform TR7–TR12 labels. Its combined boot, worker and browser-transfer checks pass emulation. This combined firmware requires hardware verification.

MIDI bank sequences and the fork's Second LFO settings remain RAM-only. Native persistence and B-side LFO-to-CC routing are not included. No firmware is supplied. Licenses and author credits accompany the page.

Whole-image reference hashes cover upstream's published sample and this exact MIDI-bank bundle; other fork combinations retain per-mod verification.
