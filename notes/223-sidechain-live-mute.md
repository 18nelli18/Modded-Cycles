# 223 — Sidechain live sur source mutee

Signalement fourni par AveyCole le 01/11/2026 : Machine Optional2.99,
Model:Cycles, Mute On, sequence en lecture, source T5 mutee et cible T6.
Les pads/trigs live ne declenchaient plus le ducking. Adresses : VA de l'OS1.13.
Generateur : `tools/gen_sidechain_manual301_comparison.py`.
Preuve : `tools/emu/test_sidechain_manual301.py`.

## En bref

[FAIT en emulation] Le meme defaut est reproduit sur Optional Full3.00.
La politique Mute On annulait toute enveloppe de source mutee, sans distinguer
sequence et jeu live. Les quatre variantes privees3.01 corrigent cette distinction.
Aucune publication ni confirmation materielle du correctif.

## 1. Chemins et cause

[FAIT] `du_note` recoit les notes dues avant le masque mute natif ; type1
represente la sequence. Le hook voix `0x400a7d4a` recoit les trigs effectivement
rendus apres filtrage mute/solo de la sequence. Le masque mute est `0x800017ac`,
le solo `0x800017b0` et conserve sa priorite native.

[FAIT] `du_process` annulait niveau, stage et compteurs des sources mutees.
Un pad live pouvait donc notifier le pulse mais perdre son enveloppe au bloc suivant.

## 2. Correction

Deux masques6bits separent les pulses live et les enveloppes live en cours.
Mute On filtre les pulses sequence des sources mutees ; un pulse live arme
l'enveloppe et la laisse parcourir attaque, maintien et relachement.
Les pulses sequence suivants ne la relancent pas. `du_reset` efface les masques
au changement/reset de pattern. Mute Off garde le comportement anterieur.
Les rampes mid/side et les retours reverbe/delay reutilisent les etats existants.
Aucune allocation, aucun acces fichier ou changement du mute/solo natif.

Les sources generales `duck.c` et `returns.c` portent aussi la correction.
Le module prive `manual301.c` reemploie les symboles de3.00 pour conserver
les adresses attendues par les autres modules. Compilation ColdFire54418, GCC16.2,
-O3 comme le chemin sidechain rapide existant.

## 3. Memoire et coexistence

Code : `0x469a0000..0x469a0934` (2356octets).
BSS : `0x469a2000..0x469a2008` (deux masques).
Le generateur verifie les plages code/BSS declarees et les SHA des entrees.
Quatre detours tardifs remplacent reset, notification note, notification voix
et traitement. Le chargeur est chaine apres Transfer3.00 et avant la continuation
existante ; les donnees/routages du projet restent inchanges.
La zone MD commence `0x469c0000`, hors correctif.

## 4. Preuves et cout

[FAIT en emulation] Demarrage natif et installation des quatre detours verifies
sur Main Full/Lite et Optional Full/Lite. Par variante :288cas couvrent six
sources, Mute Off/On, mute/solo, transport arrete/en lecture, sequence/pad/note live.
Le hook voix assemble reel est utilise ; son noyau de synthese aval est remplace
par un retour de test. Les vrais traitements DSP mid/side et retour sont executes.
Tests complementaires : queue live complete sous sequence mutee, absence de
retrigger fantome, reset, notes invalides et bypass PCM intact.

| Chemin |3.00 |3.01 |
|---|---:|---:|
| Desactive |9 |12 |
| Six sources actives, stereo et retours |6412 |6462 |

Comptages d'instructions emulees incluant appel/retour, pas cycles ni pourcentages
CPU materiels. Preuve : `profile_sidechain_manual301.py`.

## 5. A verifier sur appareil

[À FAIRE] Flasher le test Optional Full3.01 et rejouer le cas T5 vers T6,
avec source mutee, sequence en lecture et Mute On. Pads et trigs doivent produire
le ducking ; sans jeu live, la sequence mutee doit rester sans effet.
Tester ensuite maintien/relachement audibles et Mute Off. Aucun resultat
materiel n'est revendique.

## 6. Confirme sur appareil et publication3.00 (01/11/2026)

AveyCole repond « Fixed, push without changing version number from 3.00 anywhere ».
Le test prive Optional Full est confirme sur Model:Cycles. Publication autorisee
des quatre variantes, avec startup/flasher3.00 et nouveaux SHA/cache stamps.
Le code DSP reste identique au test prive ; seule la version startup redevient3.00.
Les autres variantes et conversions Samples sont validees logiciellement ;
aucune confirmation materielle supplementaire n est revendiquee.
