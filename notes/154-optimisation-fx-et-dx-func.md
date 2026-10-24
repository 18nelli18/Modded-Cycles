# 154 — Optimisation FX et DX sur FUNC

Demande AveyCole du23/10/2026 : reduire les surcharges avec Shimmer1/2 sans perdre le son approuve, puis remplacer le geste DX TRACK+RETRIG par FUNC tap-maintien. Sources : `tools/gen_governor_recovery_test.py`, `tools/machines/fx_menu/`; preuves : `test_fx_cpu.py`, `test_dx_func.py` et `test_fx_menu_control.py` dans `tools/emu/`. Adresses : VA de l OS1.13.

## Reponse courte

[FAIT en emulation] Shimmer1/2 et PS1 donnent les memes PCM que v70 avec moins d instructions executees. Ce ne sont pas des cycles ou pourcentages CPU materiels. Principal2.29/v70 inchange ; CLOUD exclu ; filtre partage conserve. La marge materielle reste a mesurer.

## 1. DSP et construction

`--fx-cpu-opt` construit v71 ; `--dx-func-fix` construit v72 avec la reparation UI. Toujours depuis le conteneur officiel et les recettes epinglees, jamais par-dessus un SysEx precedent. GCC13.1, ColdFire54418. `delays.c`/`ps1.c` : O3 et deroulage ; autres objets FX : O2.

Shimmer1 : historique FIR32 duplique en64cases/canal, lectures contigues sans modulo par coefficient ; produit signe decoupe a16bits, mathematiquement exact avec les memes arrondis ; coefficients inchanges. Recherche d alignement separee O2 sans deroulage pour reduire les pics/spills. Shimmer2/PS1 : boucles simplifiees par compilation, frequences/niveaux/feedback inchanges. Code FX `0x46800000`, BSS `0x46808000`, bornes verifiees par generateur. Aucun nouvel appel audio pour DX.

| Noyau | Instructions echantillonnees en moins | Pic ancien / nouveau |
|---|---:|---:|
| Shimmer1 | 14,9% | 27 280 / 23 907 |
| Shimmer2 | 27,9% | 12 914 / 9 417 |
| PS1 | 45,5% | JSON de preuve |

[FAIT en emulation] Shimmer :600blocs aleatoires/silencieux par mode, PCM et historiques logiques exacts. PS1 :320blocs avec Decay/Tone changeants, PCM exacts. Delay natif PingPong/Shimmer1/Shimmer2 :320blocs par mode, wet/feedback exacts et EMAC restaure. Modules voice/filter/governor/chorus/crusher/latch inchanges.

## 2. Geste DX et echec materiel v71

Tap FUNC bref (<=250ms), second appui sous350ms, maintien>=500ms puis relachement. Toute autre touche/rotation annule. DX Off interdit popup et remise a zero des compteurs ; meme toggle sauvegarde que Mod Setup. TRACK+RETRIG ne montre plus DX ; retrig/latch/temp save restent disponibles. Le geste FUNC fonctionne en verrou retrig sans le quitter.

[FAIT materiel rapporte] AveyCole : « i tried v71, not working on hardware. function plus function hold does nothing » ; DX etait On. Ce retour ne valide pas le DSP optimise sur appareil.

[FAIT en emulation] La preuve initiale injectait les evenements et omettait le maintien long. Vraies fonctions anti-rebond `0x40059e64`, scan `0x4007fbde`, horloge120Hz `0x4007f914`, constructeur KeyEvent `0x4007238c` : evenement `0x2d` vers526ms apres le second press. Bit0x20 = maintien long, pas evenement synthetique. v71 le traitait comme annulation ; la trace native reproduit exactement le defaut.

v72 accepte ce bit. Meme trace native : popup unique au relachement ; maintiens550ms,750ms,1,5s et3s acceptes. DX Off, Off en cours de geste, autres touches/encodeurs, simples taps/holds, double tap bref, repeats et timer wrap verifies. Aucun retour au diagnostic TRACK+RETRIG.

## 3. Preuves et essais restants

```powershell
python tools/gen_governor_recovery_test.py --dx-func-fix --check
python tools/emu/test_dx_func.py
python tools/emu/test_fx_cpu.py validation/all-features-polivoks-cpu-trim-test-v72
python tools/emu/test_fx_menu_control.py validation/all-features-polivoks-cpu-trim-test-v72
python tools/emu/test_private_container_loader.py validation/all-features-polivoks-cpu-trim-test-v72
```

[FAIT en emulation] Bootstrap natif :2 588 249octets exacts sans ecraser la source compressee. Rebuild v70/v71/v72 exacts. v71 conserve pour reproduire le defaut. Objets DSP v71/v72 identiques.

[A FAIRE materiel] Comparer meme sequence, tempo/sends/feedback entre v70/v72 ; DX sur durees egales. Verifier geste avec DX On/Off, retrig/latch, temp save/reload et tous les FX. Checklist : `output/firmware/validation/v72-test-checklist.md`.

v71 SHA256 : `5cf97f701484bd526063964b2f8a8eafcf785eb006eb9303283101e85a7dfb73`.
v72 SHA256 : `9fdbc21ee242b141cc0bce47be9fe9d135611179037bb340a36ae6c35d456aab`.
