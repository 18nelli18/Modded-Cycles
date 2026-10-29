# POTS — provenance

DSP de durchgemacht/model27, revision epinglee
`5badf6ad27d956e86d32ff331c480a84ef74db92` :
https://github.com/durchgemacht/model27/tree/5badf6ad27d956e86d32ff331c480a84ef74db92/tools/machines/pots

`pots.c`, `pots_tables.h`, `LICENSE` et `manifest.json` sont conserves tels quels.
Licence MIT, copyright 2026 durchgemacht and Claude. Les commentaires anglais
du DSP sont ceux de l'amont. Le manifest decrit l'integration model27 ; son ID
de slot ne doit pas etre utilise comme ID Supermodel.

L'adaptateur Supermodel est `../track_fx/pots-slot.c`. Il utilise ID12,
une ligne privee de 262144 octets, et le DSP amont POTS_RATE=4 (12 kHz).
Compilation ColdFire : `-O2 -fwrapv -fno-tree-loop-distribute-patterns`.
Preuve : `tools/emu/test_pots_delay.py`. Voir note202.
