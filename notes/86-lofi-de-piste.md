# 86 — Lo-fi de piste sur toutes les machines (Rate, Bits)

Demande du propriétaire (29/10/2026) : une expérience « lisse et homogène ». MACHINES + PITCH devient FINE TUNE sur
toutes les machines, MACRO compris ; le lo-fi devient un effet de piste de **toutes** les machines, **MACHINES +
COLOR = Rate** (fréquence d'échantillonnage), **MACHINES + SHAPE = Bits** (résolution), chacun destination des quatre
LFO, p-lockable, sauvé avec le son. Décisions : variante A (rien perdu), p-locks MULT et WAVE de LFO 2 indépendants.

Plan et relevés : `docs/2026-10-29-handoff-cycles-2.md` §9–§10 (dépôt Muslab), relevés de l'agent DSH
`docs/2026-10-29-lofi-inventory-dsh.md` et `docs/2026-10-29-plock-apply-dsh.md`.

## 1. Deux mots de paramètre libres

Chaque piste a 33 mots `k` (son + 20 + 2k ; miroir lissé de 66 o par piste, `0x8000100c`), taille fixée partout dans
l'OS. Dans l'OS 2.0 ils sont tous pris : 0..22 l'OS, 23..25 Attack/Filtre/Résonance (Model-TG), **26/27 l'état du
Sampler de Model-TG**, 28..32 LFO 2 (lfo-plus). Rate et Bits ont besoin de deux mots (p-lock, LFO, lissage,
sauvegarde passent tous par `k`) : k 27 et k 30.

## 2. k 27 : l'état du Sampler en k 26 + son+86 `[FAIT en émulation]`

Le Sampler range ses 14 réglages (mode, options, tranches, granulaire ; 28 bits, étiquette 0x7 en bits 28–31) dans un
long en son+72, donc sur k 26 **et** k 27. Le son en mémoire (100 o) a deux octets que personne ne touche :
**+86/+87**, entre le dernier mot k (+84/+85) et le long +88 de l'OS. Vérifié : aucun accès `@(86)` dans l'OS
(désassemblage complet), ni dans Model-TG, ni dans nos mods ; les copies de sons (100 o) les emportent.

`ST_SPLIT_PATCHES` (`tools/gen_model_tg.py`) : moitié haute (l'étiquette) sur k 26, moitié basse en son+86, aux six
endroits qui lisaient ou écrivaient le long (`state_store`, `st_apply_c`, `st_apply`, `snd_save_post`,
`snd_load_post`, `mc_commit_hook`). **Sur le disque rien ne change** : cases 28/29 de l'enregistrement (+84..+87) =
moitié haute puis basse, exactement le long d'avant ; tout projet se relit.

**Correctif au passage.** Au changement de machine, Model-TG testait `tstb +72 ; bmis` (« un état existe ») : seul le
bit 7 de l'ancienne étiquette 0xF passait, l'actuelle 0x7 était prise pour « pas d'état » et remplacée par le défaut.
Un Sampler quitté puis repris perdait ses modes, contrairement au commentaire de Model-TG. Le test est maintenant
`(octet & 0x70) == 0x70` (les deux étiquettes).

Effets de bord de la taille (+0x20 o avant `gflt_coef`, +0x34 sur les données d'après) :

- le build de Model-TG vérifie que chaque branchement 16 bits tombe sur une étiquette en désassemblant tout le bloc ;
  la table de pointeurs `rtg_names` n'était pas dans ses exceptions (`_DATA_LABELS`) et un pointeur 0x401b6d00 s'y
  lisait `bltw` : ajoutée par une retouche de son `build.py` ;
- `tools/sampler_mode_filter.py` : `GC_CONT` / `GC_STORE` +0x20 (son garde-fou l'a signalé) ;
- `tools/emu/test_sample_preview.py` : adresses du banc et empreinte de `sp_lock`, dont le code ne diffère que par
  sept adresses absolues (vérifié octet par octet). Ce contrôle échouait déjà avant (adresses restées d'avant le +4
  de owner-build) : le test passe maintenant entièrement.

**Preuve** `tools/emu/test_sampler_state.py` (vrai code de Model-TG, vraies fonctions de son de l'OS) :
sauvegarde/chargement de 64 états au hasard (cases 28/29 = le long d'avant, k 27 jamais écrit, laissé à 0 par
l'OS) ; `state_store` → `st_apply` de 48 réglages au hasard sur les 6 pistes, tous relus ; `st_apply_c` voit un
changement de la seule moitié basse ; changement de machine : étiquette 0x7 et 0xF gardées, sans état ou sans
étiquette le défaut en deux moitiés, k 27, d1 et la pile intacts. Régression : `test_model_tg`, `test_popup_view`,
`test_sample_preview`, `test_tempo_sync` (avec tout `os.json`) TOUT OK ; `test_lfo_plus` combiné : les mêmes 9
échecs qu'avant (préexistants, handoff §5).

## 3. k 30 : WAVE de LFO 2 dans le mot k 0 `[FAIT en émulation]`

**Pourquoi pas l'octet bas de k 29.** Le relevé de l'OS (rapport DSH §6) montre que des p-locks indépendants pour
MULT et WAVE dans un même mot demandent une douzaine d'accroches (pose, effacement, affichage, présence, application
dans la boucle des événements, écriture du son, bascule de pas) et trois tests de signe de l'OS à rendre exacts
(`0x4000dbcc`, `0x4000dcb2`, `0x4005b852` : un mot `0xFFxx` y passe pour « pas de lock »).

**Le mot k 0.** C'est le « None » de l'OS : aucun descripteur ne le règle (ni potard, ni CC), le chargement du son
y met la case 18 (inutilisée), une destination None vaut k 0. Il est déjà un vrai mot de paramètre partout : p-lock
(bornes 0..32 ; rangée `0x4010ee4c[0]` = 0, relue en k 0), lissage, copies. WAVE y est donc un paramètre à part
entière : **p-locks de MULT et de WAVE indépendants par la mécanique de l'OS**, sans accroche. Relevé (DSH §7) :

- LFO 1 (`0x40091d1c`) et la vélocité (`0x40056e88`) avec la destination None **ajoutent** leur modulation au mot
  k 0 de obj (le miroir lissé ; seule une destination > 32 est refusée). Le moteur de LFO 2 lit donc WAVE dans le
  mot k 0 des **cibles** (`(a3)` de la fonction audio, `0x800015a0`), où n'écrivent que la base et les p-locks ;
- le chargement du son écrit k 0 deux fois (case 0 puis case 18) : `lfo_tail` (`0x4005af3e`, après la boucle des
  cases) y replace WAVE, que `upk5` a déposé en k 30, et remet k 30 à 0.

Changements de lfo-plus : `lfo_id2k` (page 2 : WAVE → k 0), la table de LFO 2 construite sur la pile pour
`run_set` (SPD, MULT, DEST, DEP de obj ; WAVE des cibles), `lfo_pack` (WAVE pris en k 0, même format +88..+91,
compatible avec les sons de DavidCaruso), `lfo_tail`, p-locks : k 0 → rangée **29** (celle qu'avait WAVE : les
fichiers restent lisibles dans les deux sens), rangée 29 → k 0, k 30 non rangé (Lo-Fi Bits viendra). Place : un 13e
masque 34×34 (`0x4018ff64`, le dernier libre).

**Preuve** `tools/emu/test_lfo_plus.py` (mis à jour par l'agent DSH, relu) : id → k 28, 29, 0, 31, 32 ; sauvegarde
(WAVE pris en k 0, k 30 ignoré) ; chargement (WAVE en k 0, k 30 = 0) ; enregistrement de l'ancienne disposition
relu avec WAVE en k 0 ; aller-retour de 1 148 p-locks k 0..32 (WAVE par la rangée 29) ; p-lock WAVE ancien (rangée
29) relu sur k 0 ; sortie de LFO 2 inchangée par une valeur ajoutée au mot k 0 de obj ; les accroches gardent pile,
registres et mémoire. Seul : TOUT OK ; combiné avec tout `os.json` : les mêmes 9 échecs préexistants.

## 4. Les deux paramètres : descripteurs, rangement, p-locks `[FAIT en émulation]`

**Descripteurs.** Les ids 1 et 2 (emplacements « Error », groupe -1, libres dans l'OS 2.0) deviennent **Lo-Fi Rate**
/ `RATE` (k 27) et **Lo-Fi Bits** / `BITS` (k 30) : groupe 7 (communs à toutes les machines), 0..32512, défaut 0
(éteint), ni page ni potard ni CC, drapeaux 0x600 (destinations des LFO et de la vélocité), tri 38 / 39 après Attack,
Filtre, Résonance. Ils sont posés par le build.py de Model-TG à côté des siens (`TL_PATCHES` de `gen_model_tg.py`) :
les moteurs du Syntakt recopient la table de l'image (DESCN, `0x43034000`) avec les retouches de Model-TG, donc avec
les nôtres, sans rien de plus. La table k -> id communs de l'OS (`0x40a79394`, faite au démarrage par groupe) et
`paramIdFor` les donnent alors pour toutes les machines, Sampler compris (`sampler_com_gate` ne cache que 24/25).
Noms et code : `tools/track_lofi.py`, `tools/machines/track_lofi/track_lofi.S`, masque 48×22 `0x4015943c`, écrit avec
Model-TG comme `sampler_mode_filter`.

**Rangement.** Case 18 de l'enregistrement du son (+64/+65), que la sauvegarde de l'OS n'écrit jamais (sa table
k -> case saute 0x12) : un octet par réglage, l'octet fort du mot (0..127). La fin de `snd_save_post` /
`snd_load_post` de Model-TG saute dans `tl_save` / `tl_load` (même taille, aucun symbole ne bouge) ; le chargement
passe après `lfo_tail` de lfo-plus (qui remet WAVE en k 0 et vide k 30). Ancien enregistrement : 0, éteint ; un octet
au-dessus de 127 (jamais écrit) vaut 0. `dst_ours` de Model-TG garde aussi comme destination de LFO 1 / vélocité les
k 23..32 (avant : 23..25), Rate et Bits compris : sans cela la sauvegarde les renvoyait à None.

**p-locks.** Rangées de fichier : k 27 -> **32**, k 30 -> **18**, deux identifiants que l'OS n'écrit jamais (sa table
k -> rangée saute 0x12, son chargeur refuse au-delà de 32) ; `plk_id` / `lfo_plk_load` de lfo-plus. En mémoire, rien
à faire : ce sont des k <= 32.

**Preuves.** `test_sampler_state.py` : 64 sons au hasard, case 18 = octets forts de k 27 / 30 et relus ; ancienne case
à 0 et octet > 127 -> éteint ; destinations de LFO Rate, Bits, Attack gardées par la sauvegarde. `test_lfo_plus.py`
(attentes mises à jour par l'agent DSH, relues) : ids 1 / 2 -> k 27 / 30 et k -> id = 1 / 2 sur 24 machines, aucun
descripteur sur 28, 29, 31, 32 ; chargement avec et sans Model-TG ; rangées 18 et 24..32 ; aller-retour des p-locks
k 0..32 (1 225, seul k 26 laissé).

## 5. Le geste et l'affichage `[FAIT en émulation]`

`MACHINES` + COLOR / SHAPE règle Rate / Bits sur **toutes les machines**, comme `MACHINES` + DECAY / SWEEP / CONTOUR
règle Attack / Filtre / Résonance : positions 2 et 3 du descripteur sous `MACHINES` = ids 1 et 2.

- machines d'origine : `dh_pass` de Model-TG, `movel #other_descr,%d0` -> `jsr tl_dh` (même taille) ;
- Sampler : là où `sampler_pre` fait `sampler_descr_atk`, `moveq #0x0d ; movel d1,a0@(12)` -> `jsr tl_atk` (Attack
  puis Rate / Bits) ; `smf_descr` le rend ou le recopie selon le mode, positions 2 et 3 comprises ;
- machines des moteurs du Syntakt (MACRO comprise) : `tg_records` de `gen_syntakt_engines.py`, deux `move.l` de plus.

`[LFO]` + `MACHINES` + COLOR / SHAPE affecte donc Rate / Bits (lfo-plus `lfo_learn` lit l'enregistrement de KICK
changé par `dh_pass`), et la diode de la page LFO les montre sur COLOR (38) / SHAPE (39) (`lfo_led`, table `led_pos`
pour les ids 1..13).

Valeur : `OFF` à 0 ; Rate `46K` .. `4K` (pas r = (v + 1) / 2 = 1..64 du lo-fi de MACRO, 48 kHz × 2^(−86 r / 1536)) ;
Bits `12B` .. `2B` (12 − 10 (v − 1) / 126). Texte (+0x20) et dessin dans la fenêtre de valeur (+0x30) des objets
d'interface des ids 1 et 2 (`0x40a71754 + 100 id`), posés par `tl_ui` au geste et à chaque chargement de son ; la
fenêtre montre le texte en grande police, sans jauge, comme `lofi_draw` de MACRO.

## 6. Le son `[FAIT en émulation]`

`0x40059852` : `jsr 0x40056f58` (Volume + Dist) -> `jsr tl_post`, qui l'appelle puis traite les 6 pistes (Q31,
32 trames, `0x80001858 + 128 t`) : échantillonnage-blocage (phase Q16, avance 2^(−86 r / 1536) par trame, une nouvelle
valeur à chaque passage de 1), puis arrondi au plus proche de b bits forts (un demi-pas ajouté, borné au dernier pas,
32 − b bits faibles à 0, et la borne basse symétrique : −(dernier pas positif)) — l'algorithme de `lofi_apply` de
Model-TG, les pas du lo-fi de MACRO. Arrondi plutôt que troncature à la demande du propriétaire (os-lofi4, 30/10) : la
troncature vers −∞ ajoutait un décalage continu et faisait d'un signal sous le pas un créneau d'un pas entier, d'où un
volume qui montait avec Bits ; à 2 bits, la borne basse non symétrique (−2³¹ contre +2³⁰) déformait encore un sinus. Mots lus : les mots lissés (`0x8000100c + 14 + 66 t + 2 k`, p-locks, LFO,
vélocité compris), arrondis et bornés à 0..127. Une piste dont Rate et Bits sont à 0 n'est pas touchée (bit pour bit)
et sa phase est remise pour prendre la première trame. Une piste Sampler stéréo de Model-TG a son côté dans `sx_side`
(`0x401b9f30`), traité seulement quand `sx_on` (`0x401b9b24`) dit la piste stéréo dans ce bloc (deux adresses
vérifiées contre sa table de symboles) : même phase, même masque. Place : sept masques 48×22 (`0x4015943c`,
`0x4015f38c`, `0x40165fec`, `0x40168da4`, `0x4016dab8`, `0x4016fae8`, `0x40170c48`) ; état par piste dans un masque
(rechargé depuis la flash au démarrage).

Coût mesuré (`test_track_lofi.py`) : environ 400 instructions par piste mono en lo-fi et par bloc (≈ 0,4 % d'un bloc de
~108 000), un peu plus en stéréo ; une piste éteinte : une dizaine.

Conflit : le filtre par piste (`48-track-filter`, hors OS 2.0) prend le même site `0x40059852` et les ids 1..4 ; il
déclare déjà `conflicts` avec Model-TG.

**Preuve** `tools/emu/test_track_lofi.py` : descripteurs ; geste sur les machines 0..5 avec et sans `MACHINES` ;
`tl_atk` ; texte de 0 à 0x7f00 (et hors pas, hors bornes) ; fenêtre de valeur = le chemin texte de l'OS, sans sprite ;
`tl_post` contre un modèle Python, 6 pistes × 12 blocs (éteint, Rate seul, Bits seul, les deux au plus fort, mots hors
bornes, une piste éteinte un bloc puis rallumée) avec côté stéréo, bit pour bit ; registres et pile.

## 7. Pas tenu + MACHINES : le navigateur au relâchement `[FAIT en émulation]`

Sur l'appareil (os-lofi4) : pas tenu + `MACHINES` + COLOR pose bien le p-lock de Rate, mais l'OS ouvre le navigateur
des machines du pas dès l'appui de `MACHINES`. Décision du propriétaire : avec un pas tenu, l'ouvrir au **relâchement**
de `MACHINES`, et seulement si rien n'a servi pendant. Vaut pour tous les gestes `MACHINES` + potard (Attack, Filtre,
Résonance de Model-TG aussi).

Relevé (agent DSH, `docs/2026-10-30-trig-machines-dsh.md`) : `MainScreenView::consumeKeyEvent` (`0x4001c0d2`), cas 5
en `0x4001c252` : appui frais sans FUNC -> `0x4006b736` (UIStates +0x164, maintien) choisit PresetManager (1) ou
DrumSelect (0, le cas d'un appui de pas récent), ouverts à l'appui ; le relâchement arrive au même cas, sans effet. Le
masque des pas tenus est +0x15c/+0x160 (`0x4006b78e`).

`tools/trig_machines.py` + `tools/machines/trig_machines/` (masques 41×41 `0x4018d918` et 52×22 `0x4016ea78`, écrit
avec Model-TG), quatre accroches de prologue, aucune sur Model-TG :

- `0x4001c0d2` -> `mt_main` : appui frais de `MACHINES` sans FUNC, un pas tenu -> avalé (rend 1), le navigateur que
  l'appui aurait ouvert noté ; relâchement avec cette attente, le pas toujours tenu -> la fonction rejouée sur une
  copie de l'événement en appui frais ; le pas lâché d'abord : rien ; l'appui frais d'une autre touche annule ;
- `0x4001c27c` (`jsr 0x4006b736`) -> `mt_trig` : pendant le rejeu, le navigateur noté ;
- `0x4001f4f0` (`ParameterPageView::encoder`) -> `mt_knob` : un potard tourné (pas ≠ 0) annule ; un clic, non ;
- `0x4001f97e` (`ParameterPageView::consumeKeyEvent`) -> `mt_key` : l'appui frais d'une autre touche ([LFO]...) annule.

Sans pas tenu, ou avec FUNC : l'OS, à l'appui. Le modificateur n'est pas touché : Model-TG lit l'état physique de la
touche (`0x4007faf4` / KEY_BITS), pas l'événement avalé. Le premier jet de l'agent rejouait les prologues de
`encoder` et de la touche de page sans retirer l'adresse de retour du `jsr` (cadre décalé de 4) : corrigé, et le banc
le vérifie.

**Preuve** `tools/emu/test_trig_machines.py` (le vrai code de l'interface, constructeurs des navigateurs bouchés ;
référence : Model-TG sans ces écritures) : sans pas tenu ou avec FUNC, ouverture à l'appui comme avant ; pas tenu,
appui avalé et ouverture au relâchement, du navigateur de l'appui (DrumSelect, PresetManager en maintien) ; attente
annulée par un potard tourné, [LFO], une autre touche, gardée par un clic et un relâchement ; pas lâché avant : rien ;
les quatre fonctions dont le prologue est remplacé rendent la même chose et font les mêmes appels, deux fois
d'affilée sur une interface neuve.

Reste : MACRO (FINE redevient l'accord fin, `MACHINES` + PITCH = FTUNE comme partout), documentation, PR.
