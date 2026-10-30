# 83 — Filtre et Résonance de piste pour le Sampler (Model-TG)

Décision propriétaire (27/10/2026) : en modes Granular (3), Stretch (4), Pluck (5) et Wave (6) de la machine Sampler
(selon `loop_mode` de la piste), les combinaisons `MACHINES + SWEEP` et `MACHINES + CONTOUR` doivent régler le filtre
de piste de Model-TG : Filtre et Résonance de piste (identifiants 0x0c et 0x0b, `trackData +48 / +50`, calculés par
`gflt_coef` et exécutés par `gflt_run`), exactement comme sur toutes les autres machines de l'appareil.

Auparavant, `gflt_coef` désactivait systématiquement le filtre de piste pour le Sampler (`cmpil #6,%d1 ; beqs gc_store`),
et le descripteur du Sampler sous `MACHINES` (`dh_atk -> sampler_descr_atk`) ne remplaçait que la position Decay par
Attack (0x0d). Les modes One shot (0), Loop (1) et Slice (2) doivent rester strictement dans leur comportement initial
(le filtre propre du Sampler sur 0x49 / 0x4a, sans double filtrage). Dans les modes 3..6, le filtre interne du Sampler est
déjà sauté et ses deux potentiomètres servent de paramètres de mode.

Code : `tools/sampler_mode_filter.py`, `tools/machines/sampler_mode_filter/`, entrées de `MC_PATCHES` dans `tools/gen_model_tg.py`.
Preuve : `tools/emu/test_sampler_mode_filter.py`. Adresses : VA de l'OS 1.13.

## 1. Conception et intégration

1. **Calcul des coefficients (`gflt_coef`)** :
   Dans `model_tg.s` (ligne 18810), le test `cmpil #6,%d1 ; beqs gc_store` (8 octets) est remplacé par un saut de même
   taille (`jmp 0x4016bd42 ; nop`) vers `smf_gflt`. Si la machine n'est pas le Sampler (`d1 != 6`), le filtre reste
   actif comme auparavant. Si la machine est le Sampler (`d1 == 6`), `smf_gflt` lit `loop_mode[track]` :
   - si `loop_mode < 3` (One shot 0, Loop 1, Slice 2) : saut vers `gc_store` (`0x401bac78`), `gflt_f` reste à 0 (bypass) ;
   - si `loop_mode >= 3` (Granular 3, Stretch 4, Pluck 5, Wave 6) : saut vers `0x401bac0a` pour calculer les coefficients
     à partir de `trackData +48` (Cutoff) et `+50` (Resonance), `d0` remis à 0.
   Le filtre 4 pôles en échelle (`gflt_run`) s'exécute ensuite normalement dans `amp_hook` sur la sortie audio.

2. **Descripteurs sous `MACHINES` (`dh_atk` et `dbh_atk`)** :
   Dans `model_tg.s` (lignes 4057 et 9631), `movel #sampler_descr_atk,%d0 ; rts` (8 octets) est remplacé par
   `jmp 0x4016bcd8 ; nop` (8 octets) vers `smf_descr`. La fonction détermine la piste active via les accesseurs
   officiels de l'OS (`0x40012412(0x4000eb90(0x400cf866()))`) :
   - si `loop_mode < 3` (ou piste invalide) : rend `sampler_descr_atk` (`0x401abee6`), où positions 4 et 5 sont 0x49 et 0x4a ;
   - si `loop_mode >= 3` : recopie les 19 mots longs (76 octets) de `sampler_descr_atk` dans `other_descr` (`0x401abf32`),
     force la position 4 (SWEEP) à 0x0c (Track Filter) et la position 5 (CONTOUR) à 0x0b (Track Res), et rend `other_descr`.
   Sans `MACHINES` (`mod_held == 0`), le code d'origine de `descr_hook` rend `sampler_descr` sans passer par `dh_atk`.

3. **Préservation absolue des tailles et des symboles** :
   Le code assembleur est logé dans le masque de sprite 48×22 libéré `0x4016bcd8` (192 octets réservés, `tools/sprites.py`).
   Le binaire généré fait 148 octets (< 192 o). Les trois retouches dans `model_tg.s` font exactement 8 octets pour
   8 octets : aucun symbole de Model-TG ne bouge d'un seul octet, préservant l'intégrité de toute la chaîne des
   moteurs Syntakt (`31-*`, `32-*`).

4. **Sauvegarde, p-locks et LFO** :
   `trackData +48 / +50` (slots de sound +68 / +70) sont déjà sérialisés par `snd_save_post` et `snd_load_post` dans les
   slots d'enregistrement 25 et 26 pour toutes les pistes sans distinction de machine. Les p-locks et les destinations
   LFO s'adressent directement aux identifiants 0x0c et 0x0b portés par le descripteur sous `MACHINES`.

## 2. Preuves en émulation `[FAIT]`

Le banc `tools/emu/test_sampler_mode_filter.py` valide rigoureusement les 4 points :

| Test | Comportement attendu | Résultat |
|---|---|---|
| Audio modes 0..2 | Sortie bit à bit identique avec filtre fermé vs ouvert | TOUT OK (diff = 0) |
| Audio modes 3..6 | Sortie atténuée par le filtre 4 pôles quand +48 est réduit | TOUT OK (énergie réduite de 99.9 % à 100 %) |
| Descripteur mod_held=1 (modes 0..2) | Positions 1/4/5 = 0x0d, 0x49, 0x4a | TOUT OK |
| Descripteur mod_held=1 (modes 3..6) | Positions 1/4/5 = 0x0d, 0x0c, 0x0b | TOUT OK |
| Descripteur mod_held=0 (modes 0..6) | Positions 4/5 = 0x49, 0x4a | TOUT OK |
| Charge processeur | 6 pistes Granular + 6 filtres en échelle actifs simultanément | 37 614 instructions (22.6 % du budget à 250 MHz) |

Validation globale de la chaîne de build :
- `tools/gen_model_tg.py --check` : TOUT OK (`30-model-tg.json` et `30-model-tg-st.json` à jour) ;
- `tools/gen_syntakt_engines.py --all --tg --check` : les 31 combinaisons de moteurs Syntakt validées à jour ;
- `tools/gen_flasher_tweaks.py --check` : TOUT OK (`tweaks.js` à jour) ;
- `tools/registry.py --check` : TOUT OK (`REGISTRY.md` à jour) ;
- `tools/ref_mainos.py --check` : TOUT OK (`app.js` à jour) ;
- `tools/check_overlaps.py` : TOUT OK (aucun conflit de masque ni d'écriture) ;
- `tools/relocate_6ch.py --check` : TOUT OK ;
- `tools/emu/test_popup_view.py` : TOUT OK.

## Revue (27/10/2026)

- `smf_descr` remplace `movel #sampler_descr_atk,%d0 ; rts` dans `descr_hook`, lui-même à la place de la fonction
  feuille `0x4004df5c`, qui ne touche que d0 et d1 : l'appelant compte sur a0/a1 (voir le commentaire de
  `descr_hook`, un plantage déjà payé par Model-TG). La première version rendait a0 (et a1 en modes 3..6) modifiés ;
  d1, d2, a0 et a1 sont maintenant sauvés et rendus. Le banc le vérifie (valeurs témoins dans d2/a0/a1 avant
  l'appel par le vrai `descr_hook`) : 7 échecs sur l'ancienne version, aucun sur la nouvelle.
- Les adresses de Model-TG écrites en dur dans `tools/sampler_mode_filter.py` sont comparées à la table de symboles
  de chaque construction (`check_syms`, appelé par `gen_model_tg.py`) : si une retouche de Model-TG les déplace,
  la génération s'arrête.
- Reste connu : le mode lu est celui de la piste sélectionnée (comme `wf_popup`), pas forcément celle dont l'OS
  demande le descripteur.

## 3. `[LFO]` + `MACHINES` + SWEEP / CONTOUR sur le Sampler `[FAIT en émulation]` (30/10/2026)

Signalé par le propriétaire : sur le Sampler, `[LFO]` + `MACHINES` + SWEEP / CONTOUR ne donnait pas Filtre / Résonance
comme destination (DST None), alors que DECAY donnait bien Attack. Relevé (agent DSH, identique sur `merge-retro`, donc
antérieur au lo-fi de piste) :

- l'affectation par potard (`0x4001eaa2`) lit l'identifiant dans l'enregistrement de **KICK** (`0x4004df5c(1)`), que
  `dh_pass` de Model-TG change sous `MACHINES` (positions 1/4/5 = 0x0d/0x0c/0x0b) : sur le Sampler on obtenait donc
  toujours k 24/25 (filtre de piste), jamais son filtre (0x49/0x4a, k 13/14), ce que règlent pourtant les potards en
  modes 0..2 ; et en modes 0..2 le filtre de piste est sauté : affectation muette ;
- `sampler_com_gate` (Model-TG) retire k 24/25 de la liste DEST du Sampler (`paramIdFor`, `0x4005a692`) : la page LFO
  nommait None et la diode retombait sur PITCH, même en modes 3..6 où ce filtre joue.

Correctifs :

1. `lfo_learn` (`tools/machines/lfo_plus/lfo_plus.S`) : pour 0x0c/0x0b sur une piste Sampler (`0x40014042`),
   l'identifiant est relu dans le descripteur du Sampler sous `MACHINES` (`0x4004df5c(7)` : `descr_hook`, puis
   `smf_descr`), positions 4 et 5 : 0x49/0x4a en modes 0..2, 0x0c/0x0b en modes 3..6. lfo-plus ne lit aucune adresse
   de Model-TG ; tant que `sampler_pre` n'a pas construit le descripteur (`descr_done`), on retombe sur l'ancien
   résultat.
2. `smf_com` (`sampler_mode_filter.S`) à la place du `jmp 0x4005a6ac` (« aucun identifiant ») de `sampler_com_gate`,
   même taille : en modes 3..6 la réponse commune (0x0c/0x0b). DST affiche le Filtre / la Résonance de piste et
   `lfo_led` allume SWEEP / CONTOUR. En modes 0..2, rien ne change. (La molette DEST n'est pas vérifiée.)
   Place : la recherche du mode (`smf_mode`) est mise en commun avec `smf_descr` ; le code tient en 192 o.

**Preuve** `tools/emu/test_lfo_plus.py` §9 (vrai code de l'OS, de Model-TG et de lfo-plus) : Sampler, modes 0..6,
LFO 1..4 : `[LFO]` + `MACHINES` + SWEEP / CONTOUR → k 13/14 en modes 0..2, k 24/25 en modes 3..6, k 13/14 sans
`MACHINES` ; `paramIdFor` nomme 24/25 0x0c/0x0b en modes 3..6 seulement, 13/14 toujours 0x49/0x4a ; diode SWEEP (40) /
CONTOUR (41). Seul avec Model-TG : TOUT OK ; avec tout `os.json` : les 9 échecs préexistants (handoff §5), le nouveau
contrôle passe. `test_sampler_mode_filter.py` : TOUT OK (ses adresses `track_hash` / `track_slot` sont maintenant
tirées de `slot_hash`, elles dataient d'avant le +0x34 de notes/86).

## 4. Retour à la machine d'origine sur l'écran des machines (30/10/2026)

Signalé par le propriétaire : un Sampler réglé, passé sur une autre machine puis repris, sonnait autrement. L'OS
photographie les réglages de chaque piste à l'ouverture de l'écran des machines ; revenir sur la machine d'origine
sans le quitter les remet (`0x4001416c`). Model-TG sautait ce retour pour le Sampler (`restore_hook`), qui retombait
donc sur les défauts de page de l'OS et ceux de `mc_commit_hook` (Start 0, End au maximum, Filtre ouvert, Résonance
0) : seuls ses modes et son échantillon survivaient.

Retouche de `MC_PATCHES` (même taille, `beqs rs_skip` → `nop`) : le Sampler est rendu comme toute machine. Un vrai
changement de machine (sortie de l'écran puis retour plus tard) remet toujours les défauts, comme le stock pour toutes
les machines. **Preuve** `tools/emu/test_sampler_state.py` §5 : `restore_hook` (vrai code, puis `0x4001416c` de l'OS)
remet les cinq réglages du cliché (k 11..14 et k 5) et envoie la notification, Sampler (6) comme Metal (2).
