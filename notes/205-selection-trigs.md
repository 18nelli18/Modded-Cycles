# 205 — Selection de trigs avec TRACK + PAGE

Demande AveyCole,30/10/2026, apres Direct Jump : porter aussi la selection de
trigs PPPCCC. Le geste amont SETTINGS + PAGE appartient deja a Sequence Genie.
AveyCole choisit explicitement « TRACK + PAGE (recommended) ». Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] TRACK + PAGE active/desactive ; les taps selectionnent
les trigs notes, lock-trigs ou pas avec p-locks sans les creer/supprimer.
FUNC + PAGE selectionne tous/aucun uniquement dans ce mode ; PAGE conserve
la selection en changeant de page. Les pas selectionnes clignotent a4Hz.
Le masque de steps tenus de l'OS fournit les memes commandes d'edition ;
sortir efface ce masque. Mode OFF apres boot, aucune preference persistante.

## 1. Provenance

`gialloinfuso/PPPCCC-M-S-Mods`, revision
`43b894bd14f55313cef6381af9a008acec3ed0f1`, MIT, copyright2026
PPPCCC/gialloinfuso. Licence jointe. Le generateur amont est conserve avec
imports locaux ; seuls ses noyaux `build_a` et `build_s` sont installes.
Le patch distinct Control Mode Absolute n'est pas active : l'edition relative
existante reste native. Aucun firmware ni octet ROM ajoute au depot.

## 2. Integration et espace

`tools/gen_trig_select.py` prend les cinq candidats Direct Jump epingles.
Code a `0x46924000` ; pointeurs/texte/wrappers a partir de `0x46925000`, avant
`0x46930000`. BSS `0x46930100`, apres la BSS de JUMP et avant GATED.
Un petit chargeur sparse chaine les chargeurs JUMP et MD existants.

Trois hooks : vtable GRID `0x40100af0`, aiguillage FUNC+PAGE `0x4001c4a6`,
LED `0x40021f56`. Le dernier est deja modifie par Supermodel pour les slides :
les pas non selectionnes appellent son helper existant, les selectionnes
dessinent le clignotement. Ce contrat conserve pile et registres non-volatils.
Les pas caches par Page Len sont exclus de TOG/ALL, avec portee PTN ou TRK.
Genie, les p-locks, nudge et Note/Velocity/Length ne sont pas reecrits.
La fenetre Absolute et ses hooks ne sont pas importes.

## 3. Preuves et limites

`tools/emu/test_trig_select.py` : bootstrap natif, vrais KeyEvent et methodes
UIStates de masque/hold/focus ; selection/deselection, taps/hold/release,
trigs vides exclus, masque64pas, longueurs16/64 et borne200, pages,
all/none, toggleOFF et gestes transport delegues a l'OS. Les peripheriques
et objets projet/track sont simules. TestsLED contre le helper existant,
avec/sans slide : OFF exact, pas non selectionnes exacts, selection4Hz et pile.
Page Len4 et Page Len par piste2 excluent les pas caches. RAM runtime hors
nouveau module byte-identique : DSP et handlers existants conserves.

Les cinq editions sont couvertes : main Full/Lite, Optional Full/Lite et
Optional MD all22. Direct Jump et son menu/persistance sont reverifies sur
le candidat combine. Packaging : HMAC, capacite, recovery conserve et vrai
bootstrap/verificateurs Samples. Rapports : `../trig-select-test/`.

[A FAIRE sur appareil] Verifier le geste avec TRACK physiquement tenu,
l'edition des locks sur plusieurs pas, notes/velocity/length, nudge,
REC/copie, STOP/collage et PLAY/clear-locks. Les preuves du masque natif et
de la delegation ne remplacent pas cet essai des commandes de bout en bout.
Verifier aussi changement de piste/pattern et fermeture des autres fenetres.
Aucun resultat materiel ni mesure CPU revendique ; pas de popup CPU/CUT dans
ces images. Les flasheurs restent inchanges, pas de publication.
