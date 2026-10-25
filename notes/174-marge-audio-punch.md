# 174 — Marge audio avec trois pistes PUNCH

Demande AveyCole, chat Codex du 25/10/2026 : SPEAK, PUNCH KIK, PUNCH GNG,
PUNCH ZAP, ACID et Kick, Sidechain, HALL et delay ping-pong ; P105 O3 N3,
charge encore accrue avec MACRO. Recette privee `--punch-fast` v143,
`tools/punch_fast143.py`, preuve `tools/emu/test_punch_fast143.py`.
Adresses : VA de l'OS 1.13.

## Reponse courte

[FAIT en emulation] Les tables deployees, le cache des controles et la fusion
de conversion Q31 economisent 5,00 % d'instructions sur le banc mixte de douze
blocs. Les substitutions MACRO sont mesurees separement. Le PCM teste est exact.
Ce ne sont pas des cycles ColdFire ni un pourcentage CPU physique. Le pic de
premiere initialisation reste identique. P<100 et O/N=0 restent a verifier.

## 1. Calcul conserve

[FAIT] La source MIT 100demons reste intacte et son garde SHA est conserve.
Le constructeur genere une copie : log-sinus 512 entrees au lieu du pliage
conditionnel, amplitudes 3 328 entrees au lieu du decalage de la table de puissance.
Le test de silence precede toujours l'acces a la table. Les resultats entiers sont
identiques. Conversion finale *2 puis <<15 / *4 puis <<15 fusionnee en <<16 / <<17,
avec les memes 32 bits de sortie. Aucun taux ou timbre MACRO/FX ne change.

[FAIT] Le cache par voix invalide sur note, ratio, Index, Env, Decay, PUNCH,
velocite, modele actif et compteur de clic MAR. Le rendu et les enveloppes
continuent chaque bloc ; LFO, Gate, retrigger et changements en direct restent actifs.
PUNCH bouton : MAR vibrato, GNG tremolo, autres modeles sans effet.

## 2. Placement et composition

[FAIT] Memes bornes : code PUNCH 0x468a0000 avant art 0x468ae000 ; BSS
0x468af000 avant 0x468b0000. Les assertions du linker restent actives. Pas de
nouveau hook IRQ ni d'allocation audio. Les recettes141/142 n'activent pas ce DSP.
La recette143 conserve QntM et corrige ses effacements de flags au-dela des deux
enregistrements de sous-menu ; elle ne change pas son timing musical.

## 3. Preuves

[FAIT en emulation] Les douze modeles sont compares a142 dans la vraie boucle
des voix avec changements de controles, ratios fractionnaires, modeles, retriggers
et Gate/release. Banc mixte avec vrai mixeur, HALL, delay et Sidechain : PCM exact,
puis quatre substitutions MACRO. Les nombres figurent dans manifest.json prive.
Le banc utilise des reglages representatifs, pas une copie du projet utilisateur.

[FAIT en emulation] Comparaison native du regulateur sous charges simulees50/95/70/
120/65 %, decisions et raccords de retrigger identiques ; registres/pile verifies.
P mesure le pic, O compte les blocs au-dela de90112ticks et N les nouveaux cuts.
Les compteurs et seuils ne sont pas modifies pour obtenir des zeros.

[FAIT en emulation] MIDI24 machines/six pistes avec poll reel, popups imbriques,
QntM cinq divisions/mute/solo/BACK/annulation/stop/changement pattern et IRQ passent.
Les deux variantes standard/adult reproduisent exactement avec --check ; reextraction
du conteneur et bootloader/updater identiques. Aucun principal publie.

## 4. Verification appareil restante

[A FAIRE] Comparer au meme tempo/projet et sur le meme intervalle de diagnostic.
Inclure le jeu etabli et les retriggers simultanes ; repeter avec MACRO.
Les enveloppes Decay PUNCH/TINY restent celles de142.

## 5. Retour143 et optimisation144 — 25/10/2026

[FAIT sur appareil, retour AveyCole] Meme pattern avec143 : P100 a101, O1 N2
(correction de son premier message100-100). Amelioration par rapport a105/3/3,
mais marge encore insuffisante.

[FAIT en emulation]144 compile seulement PUNCH avec GCC13.1.0 -O3, au lieu de
-Os. Les formules et tables143 sont conservees ; aucune baisse de qualite FX,
MACRO ou enveloppe. KIK/GNG/ZAP sont d'abord compares sous -O2 et -O3 ; -O3
gagne davantage. Le binaire PUNCH reste sous sa borne d'art0x468ae000.

[FAIT en emulation] Douze modeles avec controles live ; cas KIK/GNG/ZAP aux
extremes note0..127, Decay0..127, feedback, retrigger et Gate/release : PCM exact
face a143. Banc mixte six pistes :3,99 % d'instructions en moins que143 sur12
blocs ; substitutions MACRO0/20 :4,07 /3,57 %. Le pic d'initialisation reste
identique ; ce ne sont pas des mesures CPU appareil.

[FAIT] Audit binaire : seuls punch.bin et les adresses PUNCH dans tiny_metadata
et fundamentals changent. Les FX, Sidechain, SPEAK, retention MIDI, QntM et
regulateur sont identiques octet pour octet. Deux variantes standard/adult
reproductibles (--check), bootloader/updater inchanges. Preuve native :
tools/emu/test_punch_peak144.py. Comparaison appareil144 encore attendue.
