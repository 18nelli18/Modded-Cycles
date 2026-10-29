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
