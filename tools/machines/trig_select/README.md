# Trig selection

Selection cores from PPPCCC/gialloinfuso (MIT), revision
[`43b894bd14f55313cef6381af9a008acec3ed0f1`](https://github.com/gialloinfuso/PPPCCC-M-S-Mods/tree/43b894bd14f55313cef6381af9a008acec3ed0f1).
The vendored generator has local imports and no dependency on PPPCCC's core.
Supermodel supplies the popup, TRACK + PAGE gesture, Page Len checks and a
chained LED handler. The separate Absolute Control Mode patch is not enabled;
existing relative held-step editing stays intact.

TRACK + PAGE toggles selection. Tap existing trigs to select/deselect them.
FUNC + PAGE selects all/none in selection mode. PAGE changes pages while
preserving selection. Selected trigs use the OS's held-step mask and blink.
The mode is OFF after boot; exiting clears the selection. SETTINGS + PAGE
keeps opening Sequence Genie. See note205 and `test_trig_select.py`.
