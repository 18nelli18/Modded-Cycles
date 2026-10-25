# 80 — Le sample comme excitateur de MODAL

Demande de Maxime : dans le plan de MODAL (20/10/2026, [74 §8](74-machine-modal.md)), puis le 25/10/2026 : « code le
sample comme excitateur de modal ». Un sample choisi dans le menu des presets d'une piste MODAL est rejoué à chaque trig
comme l'entrée audio de Rings ; sans sample, l'excitateur interne, comme avant.

Fichiers : `tools/gen_model_tg.py` (trois retouches de `ST_PATCHES`), `tools/machines/modal/modal.c` (`exc_sample`),
`tools/gen_modal.py` (`tg_defines`), tweaks `30-model-tg-st.json` et
`31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json` ; preuves `tools/emu/test_modal.py`,
`tools/emu/test_modal_dsp.py`, `tools/emu/modal_machine_host.c`.

## En bref

| | État |
|---|---|
| Un sample sur une piste MODAL, depuis le menu des presets | `[FAIT]` trois tests « machine = 6 » de Model-TG acceptent aussi 14 (§2) |
| Le sample gardé avec le projet, rechargé avec lui | `[FAIT]` le jeton « SMP » du nom du son, comme le Sampler (§1, §2) |
| MODAL le joue à chaque trig comme entrée de Rings | `[FAIT]` `exc_sample` (§3) |
| Preuves | `[FAIT en émulation]` octet pour octet contre `modal.c` sur l'ordinateur, contre Rings en flottant, et les 256 machines pour les retouches de Model-TG (§4) |
| Coût | `[FAIT en émulation]` 0 à 4 % d'instructions de plus que l'excitateur interne (§3.4) |
| Sur la machine | à tester (§6) |

## 1. Comment Model-TG range le sample d'une piste `[FAIT, source Model-TG 70b39dd]`

- **Le navigateur** : `preset_fail_hook` enrobe la lecture d'un preset (`0x400a51fa`). Si ce n'est pas un preset, le
  fichier est pris pour un sample : `any_sampler` doit trouver une piste Sampler dans le projet (sinon « Select sample
  machine first! »), puis `track_hash[piste]` = l'empreinte, `track_slot` = −1 (muet pendant le chargement),
  `track_pend` = −1, `refresh_tracks` (`ensure_loaded` → la case dans `track_slot`), et `name_store` écrit le jeton
  dans le nom du son (son + 4..+19 : « SMP », 8 chiffres hexadécimaux, puis les octets de mode 11 à 13 du Sampler).
- **À chaque tick** (`tick_hook` → `name_probe`) : pour une piste Sampler, le jeton du nom du son donne `track_hash`
  (`np_adopt`, `pl_dirty`) ; pas de jeton → pas de sample (`np_notok`) ; une autre machine → empreinte 0
  (`np_nosmp`).
- **`load_pending`** : une empreinte voulue → `ensure_loaded` → `track_pend` = case | `PEND_NOFADE` ; plus
  d'empreinte alors qu'une case joue → `track_pend` = `PEND_SILENT` (0x1ffff : le mot bas vaut −1).
- **La voix du Sampler** (`sampler_pre`, `sp_pgo`) prend `track_pend` au bloc d'un nouveau trig, ou dès que la voix
  est muette : `track_slot` = le mot bas étendu (`extl`), `track_pend` = −1.
- **`tok_of`** (machine 6 et « SMP ») sert au préchargement des patterns (`pls_t`), à la protection des samples du
  projet quand la mémoire est pleine (`proj_has`), aux sons verrouillés par pas (`sp_lock`) et à `snd_tok`, `wfk_step`.
- Les cases : `slot_hash` (0 : vide), `slot_base` (l'en-tête de 64 o puis le PCM, 16 bits gros-boutistes),
  `slot_count` (échantillons du plan du milieu ; un fichier stéréo est rangé milieu (L+R)/2 puis côté (L−R)/2),
  `MAX_SLOT` = 64.

Model-TG teste « machine = 6 » à 13 endroits : `ap_done`, `sampler_amp_gate`, `gran_menu_open`, `mm_open`, `fh_ours`,
`tok_of`, `as_loop` (`any_sampler`), `np_l` (`name_probe`), `rp_arm`, `wp_id`, `mc_commit_hook`, `restore_hook`,
`pool_store_hook`. Seuls `any_sampler`, `name_probe` et `tok_of` concernent le sample d'une piste ; les dix autres sont
la voix, les menus et la réserve de sons du Sampler.

## 2. Les trois retouches de Model-TG `[FAIT]`

`ST_PATCHES` de `tools/gen_model_tg.py`, dans la version de Model-TG avec les moteurs du Syntakt (`30-model-tg-st.json`
seulement ; `30-model-tg.json` ne change pas) :

| Endroit (adresse dans le tweak) | Avant | Après |
|---|---|---|
| `as_loop` d'`any_sampler`, le navigateur (`0x401b3268`) | `andil #0xff,%d0` ; `cmpil #6,%d0` | `andil #0xf7,%d0` ; `cmpil #6,%d0` |
| `np_l` de `name_probe`, le jeton à chaque tick (`0x401b3750`) | `andil #0xff,%d0` ; `cmpil #6,%d0` | `andil #0xf7,%d0` ; `cmpil #6,%d0` |
| `tok_of`, préchargement et protection (`0x401b2da0`) | `cmpil #6,%d0` | `bclr #3,%d0` ; `subql #6,%d0` |

- `m & 0xf7 = 6` seulement pour `m` = 6 et 14 : MODAL est la machine 14 (la 15e à l'écran) du Modded Cycles OS. Dans
  les autres tweaks de la bibliothèque qui vont avec `30-model-tg-st.json`, la plus grande machine est 13 (ACID) : 14
  n'y existe pas.
- Même taille : aucune adresse de Model-TG ne bouge, ses symboles non plus ; le bloc de Model-TG change en 4 endroits
  (`0x401b2da4`, `0x401b2da7..a9`, `0x401b3271`, `0x401b3759`). Son MAIN OS seul : `8ad71e89…4dcc`.
- `d0` après le test : 6 dans les deux cas pour `any_sampler` et `name_probe` (`6 & 0xf7`, `14 & 0xf7`), comme
  avant ; 0 au lieu de 6 dans `tok_of`, que l'instruction suivante écrase (`mvzb %a0@(4),%d0`, ou `moveq #0` en
  `to_no`).
- Ce que `name_probe` fait de plus pour un son MODAL : `st_apply_c` lit l'état rangé du Sampler (son + 72, les mots
  26/27 que MODAL n'utilise pas) dans les tables par piste du Sampler, que MODAL ne lit pas ; les octets de mode 11 à
  13 du jeton sont ignorés par MODAL.
- `ST_SYMBOLS` exporte en plus `track_slot`, `track_pend`, `track_hash`, `slot_base`, `slot_count` (`slot_hash` l'était
  déjà) : `gen_modal.py` les passe à la compilation de `modal.c` (`-DTG_TRACK_SLOT=…`).

## 3. MODAL `[FAIT]`

### 3.1 `exc_sample` (`modal.c`), à chaque bloc de `modal_render`

1. **La case en attente** (`track_pend` ≥ 0) est prise au bloc du trig (`v+0x34` sans `v+0x38`) ou quand le sample ne
   joue pas : `track_slot` = le mot bas (signé), `track_pend` = −1, comme `sp_pgo`. Sans le fondu d'entrée du Sampler
   (`gv_gain`) : MODAL n'en a pas besoin, le sample repart du début au strum.
2. **La case** : 0 ≤ `track_slot` < 64, `slot_hash` ≠ 0, `slot_count` > 0 ; sinon l'excitateur interne
   (`internal_exciter` = 1), comme avant.
3. **Au strum** (le bloc après le trig, celui où Rings joue la note) : le sample repart du début ; MODAL retient sa
   case et son empreinte. Si l'une ou l'autre change sous la note (le navigateur pose `track_slot` directement, une
   case reprise par Model-TG), le sample se tait jusqu'au trig suivant.
4. **La lecture** : `slot_base` + 64, un échantillon par trame (48 kHz, pas de rééchantillonnage : le sample joue à sa
   vitesse, la note n'accorde que le résonateur), le plan du milieu pour un fichier stéréo, `<< 9` (pleine échelle =
   1,0), multiplié par le niveau de la frappe (la vélocité, comme l'excitateur interne), des zéros après la fin.
5. **Avec une case valide**, `internal_exciter` = 0 même quand le sample s'est tu : le filtre d'excitation reste celui
   de l'entrée, et le résonateur s'éteint de lui-même.

### 3.2 Ce que fait Rings de l'entrée `[FAIT, source eurorack 08460a6]`

`internal_exciter` = 0 dans `Part` : l'entrée passe par le filtre d'excitation, un passe-bas dont la coupure suit
BRIGHTNESS (`0.4 * SemitonesToRatio((cutoff - 1) * 108)`, Q 0,8 au lieu de 1,5) ; ni impulsion (modal) ni rafale de
bruit (`plucker_`, cordes) ; les cordes sympathiques reçoivent la même entrée. Le cœur de MODAL le faisait déjà
(`modal_dsp.h`, `rin_zero`) : rien n'y change.

### 3.3 Mémoire

MODAL lit les tables de cases et le PCM de Model-TG et n'écrit que `track_slot` et `track_pend` de ses pistes, au
moment où le Sampler le ferait (preuve de mémoire de `test_modal.py`, élargie à ces deux tableaux). Code de MODAL
+0,7 Ko, variables +0,2 Ko ; l'image va jusqu'à `0x401fd720`.

### 3.4 Coût `[FAIT en émulation]`

Instructions de MODAL par bloc, une voix, DECAY 100 (`cost` de `test_modal.py`) :

| SHAPE | Excitateur interne | Sample en entrée |
|---|---|---|
| 0 modal | 16 044 | 16 695 |
| 1 cordes sympathiques | 19 619 | 19 796 |
| 2 corde | 11 374 | 11 365 |
| 3 cordes en accord | 19 618 | 20 431 |

Au plus 800 instructions de plus par bloc, environ un demi-point de processeur au modèle de [77](77-cout-sur-la-machine.md).

## 4. Preuves `[FAIT en émulation]`

### 4.1 Le cœur contre Rings (`test_modal_dsp.py`)

16 cas de plus, `internal_exciter` = 0 et un sample en entrée rejoué depuis le début à chaque note, comme la machine :
une frappe de bruit (2 400 échantillons) et un sinus de 440 Hz qui s'éteint (9 000, relancé avant sa fin), les quatre
modèles, 1, 2 et 4 voix, et les quatre potards qui bougent. De 67,6 à 95,5 dB, sauf POSITION qui balaie toute sa course
en 0,13 s pendant que le sample excite encore : 34,4 dB avec le modèle modal (55 dB pour le même cas avec l'excitateur
interne). C'est l'écart connu des amplitudes interpolées sur le bloc ([74 §5.1](74-machine-modal.md)), plus visible
avec une entrée qui dure : seuil de 30 dB pour ce cas-là seulement. Tous les autres restent à 35 dB.

### 4.2 La machine dans l'OS (`test_modal.py`)

La preuve rejoue à `modal.c` compilé pour l'ordinateur (`modal_machine_host.c`) ce que la passerelle reçoit dans
l'émulation, avec les cases de samples posées comme Model-TG (empreinte, base, nombre, PCM) et `track_slot` /
`track_pend` avant chaque bloc ; elle compare la sortie et ces deux valeurs après chaque render, octet pour octet :

- les quatre modèles avec une frappe ; un sinus en 4 voix relancé avant sa fin ; un sample de 20 échantillons ; un
  sample à pleine échelle en vélocité 30 ;
- la case en attente au chargement d'un projet : prise dès la première note ; prise tout de suite quand le sample
  s'est tu ; prise au trig suivant quand il joue ;
- un autre sample posé par le navigateur sous la note : il part au trig suivant ;
- `PEND_SILENT` : retour à l'excitateur interne ; une case vide (empreinte 0) : l'excitateur interne ;
- avec un sample, le son change dès la note, et pas avant ;
- Model-TG : les trois tests modifiés, exécutés depuis le tweak pour les 256 valeurs de l'octet machine contre le code
  d'origine (les mêmes octets remis) : même branche et mêmes registres sauf pour 14, pris pour un Sampler avec 6 ;
- toute la preuve d'avant (sons, interface, les autres machines identiques, régulateur, mémoire, coût).

### 4.3 Model-TG et l'écoute des samples avec tout l'OS

`test_sample_preview.py --with` les tweaks de `os.json` : TOUT OK (la retouche de `tok_of` ne change rien pour le
Sampler). `test_model_tg_syntakt.py` avec les 5 moteurs (Model-TG retouché contre Model-TG seul, l'interface, le son,
le régulateur, les slide trigs, le mode mute) : TOUT OK, 36 vérifications.

## 5. Limites

- `[FAIT, source]` Un sample par piste : les sons verrouillés par pas (`sp_lock`) ne marchent que dans la voix du
  Sampler. Ce que fait un pas tenu pendant le choix d'un fichier sur une piste MODAL : `[À FAIRE]` sur la machine.
- `[FAIT, source]` Pas d'écoute dans le navigateur sur une piste MODAL : l'écoute des samples (notes/46) teste
  « machine = 6 » dans son propre code.
- `[FAIT, source]` Le nom du son devient le jeton « SMP » + 8 chiffres, comme sur une piste Sampler.
- `[FAIT, source]` Un preset de MODAL chargé sur la piste (un son sans jeton) : au tick suivant, `name_probe` n'y trouve
  plus de sample, `load_pending` pose `PEND_SILENT`, et MODAL reprend son excitateur interne au trig suivant.
- `[FAIT, source]` Le navigateur refuse toujours un sample (« Select sample machine first! ») quand le projet n'a
  aucune piste Sampler ni MODAL. Quand il en a une, `any_sampler` laisse le sample se poser sur n'importe quelle piste,
  comme Model-TG le fait déjà avec le Sampler ; sur une autre machine, le jeton est écrit dans le nom du son et
  `name_probe` l'oublie au tick suivant.
- `[FAIT]` Pendant qu'un sample se charge (`track_slot` = −1), l'excitateur interne joue.
- Le niveau du sample n'est pas réglable à part : la vélocité, et le volume du fichier.

## 6. À tester sur la machine `[À FAIRE]`

Avec quelques WAV à 48 kHz envoyés par Transfer (Device Config › Transfer sur SMP, notes/46) :

1. Une piste MODAL, FUNC + MACHINES, choisir un WAV court et percussif : « Sample loaded to track N » ; chaque trig
   fait sonner le résonateur avec le sample (une frappe qui sonne comme le sample, accordée par la note).
2. Les quatre modèles (SHAPE), COLOR en bas puis en haut (le sample filtré), DECAY, la vélocité.
3. Un sample long (une boucle) : il repart du début à chaque trig ; un sample stéréo.
4. Sauver le projet, l'éteindre, le rallumer et le recharger : la piste MODAL rejoue son sample dès la première note.
5. Changer de pattern et revenir ; deux pistes MODAL avec deux samples différents ; une piste Sampler à côté.
6. Charger un vrai preset de MODAL sur la piste : retour à l'excitateur interne au trig suivant.
7. Un projet sans piste Sampler ni MODAL : « Select sample machine first! », comme avant.
8. Tenir un pas et choisir un fichier sur la piste MODAL : noter ce qui se passe (§5).
9. La charge (page System de Model-TG) : à peu près la même qu'avec l'excitateur interne.

## 7. Chronologie

- 20/10/2026 : demandé avec MODAL, renvoyé à la suite ([74 §8](74-machine-modal.md)).
- 25/10/2026 : « code le sample comme excitateur de modal » (Maxime) : les trois retouches de Model-TG, `exc_sample`,
  les preuves.
