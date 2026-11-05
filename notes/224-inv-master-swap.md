# 224 — GOV INV, effets master et corrections Swap (05/11/2026)

## En bref

Demande de l'utilisateur dans ce chat : GOV INV comme TRK mais dans l'ordre
6 vers1 ; seulement des FX master, toujours memorises par pattern. Il signale
ensuite des retours du curseur avant Swap, des niveaux nuls apres permutation,
et un A01 d'usine apparaissant remplace par un pattern personnel jusqu'au
rechargement du projet. Adresses : VA de l'OS 1.13.

Images privees 3.81, Main/Optional Full/Lite, sur les bases FX Save 3.05.
Le correctif de sauvegarde precedent a ete confirme par « Okay, that worked » ;
l'edition exacte et le protocole appareil n'ont pas ete precises.
Les nouveaux changements restent experimentaux, sans resultat appareil.

## 1. GOV INV

`gov-policy372.c` accepte les valeurs0/1/2 : Lod, Trk, INV. Le fichier
`/Governor.cfg` conserve son format et les anciennes valeurs0/1. Les valeurs
hors domaine et les fichiers incomplets restent refuses ; les E/S restent
differees a l'arret. `gov-inv380.S` conserve D0 et rend seulement la cle D2 :
Lod appelle le noyau existant, Trk rend t, INV rend5-t. Seuils, eligibilite,
protections et fondus ne changent pas.

Le stub est assemble a la fin de la reserve SRAM du calcul de cle. `nm`
donne l'entree reelle apres alignement, au lieu de supposer que le premier
octet du binaire est une instruction. Le binaire occupe30o, padding compris,
dans les38o disponibles. Le module UI/service additionnel occupe
`467a5000..467a5800`, avant le BSS du filtre LUT. Generateur :
`tools/gov_inv_master380.py`, option `rebuild300_pack.py --gov-inv-master380`.

## 2. Effets master seulement

`master-only380.c` force le mode MST avant le service historique, empeche le
chargement d'une ancienne preference TRK et neutralise le setter du mode.
La ligne FX reste a sa place, affiche MST et n'est plus editable ; DATA est
consomme sur cette ligne. Les banques et les reglages FX par pattern sont
conserves, ainsi que le correctif de sauvegarde confirme par l'utilisateur.
La chaine de navigation GOV/Swap reste explicite, sans casser les trampolines.

## 3. Niveaux : cause reproduite

[FAIT] Le getter natif `40009c5a` lit l'octet fort a RawKit+16+2*t ; le setter
`4000a3ae` ecrit une valeur8.8 sur16bits. Swap utilisait stride1/taille1,
echangeant parfois l'octet fort d'un niveau avec l'octet faible nul d'un autre.
Le correctif utilise stride2/taille2 et conserve aussi la partie fractionnaire.
Le test precedent reprenait la meme mauvaise hypothese de stockage ; il a ete
corrige et verifie maintenant les valeurs par le vrai getter natif. Le test
corrige echoue sur l'ancien firmware et passe sur3.81.

## 4. Navigation et propriete du pattern

Le navigateur Track gere lui-meme les quatre lignes lorsqu'aucune valeur
historique n'est en edition. Il ne delegue plus les lignes intermediaires au
compteur historique de trois lignes.40mouvements alternant pas lents/rapides
verifient les positions, DATA et BACK restent testes.

[FAIT] Comparer seulement les IDs UI/audio ne prouvait pas leur appartenance
au meme projet. Les verifications exigent maintenant :

- RawPattern UI = RawProject+28+ID*30710 ;
- RawKit UI = RawProject+2cfc5c+ID*7094 ;
- pattern audio =406fa040+ID*30710 ;
- UUID de projet identique entre UI+8 et la banque audio406fa02c ;
- proprietaire, pointeur actif, generation et UUID encore identiques sous
  masque IRQ, juste avant la premiere permutation.

Le plan de permutation porte ces attentes. Un changement de projet ou de
pattern pendant le preflight refuse la transaction avant toute ecriture.
`track_swap381.py` reconstruit le module Swap et ses trampolines, en conservant
la delegation vers le nouvel encodeur GOV. Option `--track-swap381`.

[HYP] Ces controles couvrent une famille de causes possibles du remplacement
apparent d'A01. L'incident exact n'est pas reproduit : ne pas annoncer que sa
cause materielle a ete identifiee. Un refus de Swap est preferable a une
permutation sur un contexte incoherent ; recharger/reselectionner le pattern
si le contexte ne correspond plus.

## 5. Preuves et livraison

Les quatre images atteignent la continuation native40000542 apres leur vrai
bootstrap. `test_gov_policy372.py` verifie les120cles Lod, les deux ordres
complets, les pistes protegees/jeunes/deja volees, le menu, la persistance INV
et le rejet des fichiers invalides. `test_fx_mst_save379.py` verifie les menus
FX installes, l'ancien fichier TRK ignore, Save/Load Project natifs et une
nouvelle instance froide.

`test_track_swap_ui377.py` verifie les niveaux16bits par getter natif,
les autres95patterns et95kits inchanges, le refus du mauvais proprietaire
et de l'UUID audio, quatre changements de contexte injectes avant l'ecriture,
les caches LFO/ACID/Wizard et ChordKeys Optional. `test_track_swap377.py`
verifie les15paires,9216cas de masques, les refus atomiques et les codecs
natifs pattern. Les notifications/disques/UI sont simules dans ces preuves.

Livraison hors depot : `../inv-master381/delivery`. Les fichiers restent
prives ; aucun envoi MIDI ni publication. [A FAIRE appareil] Retour du curseur,
niveaux des patterns d'usine, conservation A01 et projet voisin, INV sous
charge, et sauvegarde des FX master apres extinction.

## 6. Retrait de la ligne FX et push source (05/11/2026)

L'utilisateur confirme « That works » puis demande de supprimer completement
la ligne FX/MST du menu Mod et de pousser les sources. L'edition testee reste
non precisee. La3.82 conserve les effets master, les sauvegardes par pattern,
INV et les protections Swap de3.81.

`hide_master_fx382.py` produit une vue Global compacte en omettant le record
FX ; les indices logiques des controles historiques sont conserves. Le
curseur visible et le scrolling sont remappes, et la navigation passe
directement de LFOs a ACID (Full) ou JUMP (Lite), dans les deux sens. La ligne
GOV demeure accessible et editable. Le module est reserve dans
`467a0800..467a0f00`, avant le BSS deep-idle. Option `--hide-master-fx382`,
a utiliser avec `--gov-inv-master380 --track-swap381`.

La livraison des images reste hors depot ; le push ne versionne aucun octet
de firmware Elektron. La publication des flasheurs publics n'est pas modifiee
par ce push source.
