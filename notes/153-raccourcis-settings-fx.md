# 153 — Raccourcis SETTINGS des effets (main2.25)

Demande AveyCole, chat du 23/10/2026 : le v57 joint doit etre le .syx servi par le flasher principal. Le guide fourni (4 pages, 2.25) decrit la difference avec main2.24.

## Reponse courte

Main2.25 sert le v57 exact : SHA-256 `35370f22a4d6423bb3c66f290da8e45c0fd02fe5083942fe02980bc765cce045`, MAIN OS `3f9dd0211da1321e4f504bc6f0bc87306f740a4d8e1318aaf33771c8daed8b2b`. Le v55 precedent avait MAIN `8701f142…8c7a` ; les deux MAIN OS ont la meme taille (2476069 o).

## Ce que le guide 2.25 ajoute

- En CHOR1+REV, CHOR2+REV, VINYL+REV : SETTINGS + REVERB SIZE regle Reverb Tone ; relacher SETTINGS revient a Reverb Size. Mode REVERB standard : FUNC + SIZE inchange.
- En CRU1+DEL, CRU2+DEL : SETTINGS + DELAY TIME regle Delay Feedback ; TIME simple reste Time natif. FUNC puis TRACK + DELAY SEND regle toujours Feedback.
- Menus et popups FX opaques par-dessus l’ecran normal.

[HYP] Le guide ne decrit pas tout changement de code entre v55 et v57 ; seules ses differences visibles sont documentees ici et dans les notes de version. Aucun test materiel ni emulation n’est consigne par cette note.

## Livraison

`tools/gen_midi_machine_main.py` (STAMP `2026-10-23-fx-settings-main-225`), `tools/gen_shortcut_guide.py`, `tools/gen_print_shortcut_guide.py`, `docs/flasher/release-notes-2.25.html`. `tools/test_fixed_main_delivery.js` attend les nouveaux hashes (necessite les fichiers officiels).
