# 176 — Marge PUNCH et Sidechain

Demande du 25/10/2026 : poursuivre les optimisations apres validation de 145. Generateur : `tools/gen_governor_recovery_test.py --voice-headroom`. Preuve : `tools/emu/test_voice_headroom146.py`. Adresses : VA de l'OS 1.13.

## Reponse courte

[FAIT en emulation] 146 conserve les echantillons testes et reduit les instructions interpretees du banc mixte de 0,75 a 0,86 %. Ce ne sont pas des pourcentages CPU mesures sur appareil. La publication reste sur 145 (main 2.46).

## 1. Calcul PUNCH

`punch_hot146.py` incorpore l'attenuation fixe dans les compteurs Q16 de l'enveloppe au debut du bloc, puis la retire a la sortie. Deux additions par echantillon disparaissent. Les etats atteignables restent dans la plage 32 bits. Les douze modeles, parametres dynamiques, retriggers, relachements et cas extremes KIK/GNG/ZAP donnent le meme PCM. Source originale preservee ; transformation uniquement dans la copie de compilation.

## 2. Sidechain

Compilation du C a -O3 avec m68k-elf GCC 13.1.0, sans changer les formules ni l'assembleur. Code : 0x46833000 a 0x46835558, avant BSS 0x46835800 ; fin de l'etat 0x468358c4 avant pont 0x46835ff0. PUNCH finit a 0x468a4fac avant HALL 0x468a6000. La variante -funroll-loops est rejetee car elle chevauche la BSS.

[FAIT en emulation] Le banc Sidechain isole baisse de 3 342 813 a 2 977 116 instructions, environ 11 %, avec PCM exact et retours d'effets. Le gain global du banc six pistes est nettement plus faible, environ 0,8 %. Le pic initial de ce banc ne change pas.

## 3. Verification et limites

Reproduction exacte des images standard et adulte ; noyaux HALL/MACRO, regulateur et seuils inchanges. Tests MIDI 24 machines sur six pistes, popup, QntM, interface Sidechain et integration native des retours reverb/delay passes. Aucune modification des controles ou du guide.

[A FAIRE] Comparer la meme sequence sur appareil. Aucun resultat physique 146 n'est encore disponible.
