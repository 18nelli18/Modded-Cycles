# 203 — TRX-B2, TRX-SD et TRX-CH dans Machine Optional

Demande AveyCole,29/10/2026 : ajouter les moteurs du site Talachan12 au flasheur
Optional. Source epinglee : `Talachan12/Elektron-Model-Machinedrum`, commit
`70e1483535c5a6919ff170ce3b79ba4a10c066ac`. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] Trois moteurs ColdFire, IDs25/26/27 ; les IDs0..24 sont
conserves. Le catalogue compte28machines et181descripteurs. Optional presente
22choix, garde ses19choix coches par defaut et conserve Legacy/ChordKeys/Vinyl.
Les moteurs TRX exigent le fichier Machinedrum UW1.63 de l'utilisateur. Le
navigateur accepte le SYX officiel ou le BIN de reference epingle.

## 1. Provenance et autorisation

Les noyaux sont ceux du port Talachan12, construit sur Modded-Cycles de18nelli18.
Le depot amont ne specifie pas de licence generale pour ce port. AveyCole a
ensuite explicitement confirme « Great news: I got permission! » en reponse a
la question sur sa reutilisation et redistribution dans Supermodel Optional.
Cette confirmation est enregistree dans `tools/machines/md/README.md` ; aucun
label MIT n'est invente pour ces sources.

Les tables, coefficients et attaque sont extraits de l'OS utilisateur.
La recette publique remplace ces zones par des zeros ; les descripteurs natifs
sont clones au build, pas distribues dans cette recette. Le sinus est calcule
par l'algorithme DSP amont. Aucun nouvel asset firmware MD n'est publie.

## 2. Memoire et boot

Code/constantes :469c0000..469f8000,186480octets dans ce compilateur.
BSS :469f8000,1752octets. Pas de chevauchement avec GATED, POTS ou WAVE.
Le code ne prend pas la SRAM deja utilisee par les moteurs Supermodel.

Le sinus32768x32bits est transporte en deltas16bits et reconstruit exactement.
Une copie separee, chainee par40195adc avant l'ancien bootstrap, evite un grand
padding dans le MAIN. Tous les registres utilises par cette copie sont conserves.
Le MAIN est recomprime depuis les operations du Cycles officiel, puis protege
contre le chevauchement d'entree du bootstrap. En all22 :1751008octets flash,
limite1835008, marge84000. Bootloader/updater inchanges.

## 3. Selection et controles

Masque22bits ; MIDI Out reste en dernier. Les anciennes gardes Optional de
services MIDI/WAVE/Legacy sont conservees ; le dispatch MD respecte le masque
complet et met les sorties des voix desactivees a zero.

| Controle | TRX-B2 | TRX-SD | TRX-CH |
|---|---|---|---|
| PITCH | PTCH | PTCH | LPF |
| COLOR | Distortion | Snap | Metal |
| SHAPE | Dirt | Tone | High Pass |
| SWEEP | Ramp | Bump | Resonance |
| CONTOUR | Hold | Bump Env | Gap |
| DECAY | Decay | Decay | Decay |
| PUNCH | Tick0/64 | Clip0/64 | sans fonction |

TRX-CH Resonance70 correspond au reglage du Machinedrum. Le noyau travaille
a44,1kHz et le pont polyphase le convertit a48kHz. Le signal passe dans les
fonctions de piste et FX du Cycles ; ce n'est pas un port du mixeur MD entier.

## 4. Reproduction et preuves

`tools/gen_optional_machinedrum.py --cycles officiel.syx --md MD1.63.syx
--cross <prefixe> --check` recompile la recette et refuse un socle non epingle.
Le BIN1.63 epingle est egalement accepte pour les tests locaux. Les produits
contenant les tables utilisateur restent dans le dossier de travail ignore.

[FAIT en emulation]

- Noyaux dans six positions :96blocs par moteur/piste, signal non nul et PCM
  identique entre positions equivalentes.
- Boucle complete : sixcopies de chaque MD et deux mixages stock/MACRO/ACID/ESTUS,
 48blocs par scenario ; toutes les voix MD audibles, aucun acces non mappe.
- Constructeur28rangees,181descripteurs,15libelles MD et5850choix de selecteur.
- Cinq images navigateur : boot, code/tables et32768sinus exacts, BSS nul,
 30dispatches chacune ; voix desactivees muettes, ABI conservee.
- Python/navigateur : image all22 identique, SHA
 `c803ffb0fec8e13cc437a5cb16a46266adcc54ada2bff8fb3f5622ee0ad1c4a6`.
- Navigateur reel :22cases,19initiales, fichierMD requis, All/None/TRX-B2 seul,
  fichier invalide refuse, controles verrouilles pendant l'envoi.
- Regression POTS : menus, projet/reload, DSP, doubleSTOP et1050blocs de
  transitions natives passes dans l'image all22.

## 5. Limites

Integration experimentale2.62, non poussee pendant cette investigation.
Confirmation appareil et mesures CPU physiques encore attendues ; les preuves
ne transferent aucun resultat materiel du port amont a Supermodel.
Le manuel public2.61 reste le manuel de la release publiee.
