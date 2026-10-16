# 96 — RETROSYN parmi les machines existantes

Demande d’AveyCole du 16/10/2026, archive locale `retrosyn-core.tar.gz`, pour
[AveyCole/Modded-Cycles](https://github.com/AveyCole/Modded-Cycles). Demandes
complementaires : conserver TINY ; Sample Wizard independant facultatif ;
interdire Model-TG dans le flasheur principal. Adresses : VA de l’OS 1.13.

## En bref

[FAIT en emulation] RETROSYN fournit six formes : PULSE, TRI, WAVE, NOISE-L,
NOISE-S et boucle de style SNES. Quatre recettes experimentales : seule,
avec Sample Wizard, avec toutes les machines ajoutees, et toutes avec Wizard.
Les combinaisons completes conservent WAVE et TINY, sans Model-TG.

[À FAIRE] Ecoute et mesure de charge sur le materiel. L’aperçu ne propose pas
encore les sous-ensembles partiels de machines ni ChordKeys avec RETROSYN.

## 1. Contrat audio

`tools/machines/retrosyn/retrosyn.c` reprend le contrat MACRO : update puis
render, 32 echantillons a 48 kHz, note Q16, parametres 8.8. Etat individuel
pour les six pistes, initialise au changement de machine. La chaine d’ampli
TONE assure DECAY/GATE ; PUNCH quantifie ici l’oscillateur a quatre bits.
FINE reste un accord fin (environ un demi-ton de chaque cote du centre).
Le niveau du coeur est celui fourni dans l’archive, sans normalisation nouvelle.

Le generateur MACRO accepte maintenant un moteur externe sans changer son
chemin historique. Les generateurs RETROSYN n’importent aucune recette Model-TG.
Le contexte de passerelle de Wizard vient exclusivement de `sample-wizard`.
Les fonctions communes de ce depot gardent leurs anciens noms internes.

## 2. Memoire et interface

Seule : charge utile a `0x43000000`, BSS a `0x43036000`.
Combinaisons completes : moteurs existants a `0x46700000`, leurs corps et
leurs etats restent en place ; RETROSYN a `0x46785000`, BSS a `0x46787000`.
Les 126 descripteurs vont a `0x46733c00`, rangees a `0x46784000`, rangees CC
a `0x46784400`, enregistrements a `0x46784800`. Les dix ajouts tiennent sous
l’indice 128 des descripteurs. Les reperes de selection sont repartis sur
neuf colonnes, entre x=64 et x=124, pour tenir dans l’ecran.

Sans Wizard : 16 machines. Avec Wizard : 17, Sampler reste en septieme
position et RETROSYN vient apres TINY. Compression aPLib avec le compresseur
existant ; aucun changement du format du builder. Les corps compiles
MACRO/ACID/WAVE/TINY sont repris du catalogue actuel, sans recompilation.

## 3. Preuves

- Tests du coeur fourni : hauteur, quatre rapports, tables, periodes LFSR,
  arpeges, balayages, interpolation, PUNCH, retrig et niveau : tous passent.
- UBSan : 450 000 blocs sans acces hors table ni debordement signe.
- ColdFire contre reference C hote : six pistes, six formes, trois jeux de
  controles et retrig, sortie oscillateur identique bit pour bit.
- Boot reel, decompresseur aPLib et invalidation du cache ; menus, bornes,
  descripteurs et selection ; toutes les machines precedentes conservent
  leur audio bit pour bit dans les combinaisons completes, dont TINY/WAVE.
- Version Wizard : 17 rangees, RETROSYN apres TINY, aucun acces hors memoire.
- Flasheur reel sous jsdom : quatre chemins, references strictes et SysEx
  signes verifies, ainsi que Tout selectionner puis RETROSYN. Les fichiers d’OS restent exclusivement locaux et ignores.

Le compteur indicatif varie de 14 762 a 22 634 instructions par bloc de six
pistes selon la forme (COLOR maximum), pas une mesure de cycles ni une
garantie de charge audio. La charge
reelle avec bruit rapide et six pistes doit etre mesuree sur le Cycles.

## 4. Model-TG interdit au main

`main-policy.js`, charge apres les extensions du main, retire la carte,
refuse sa reintroduction dans le tableau des cartes et verrouille l’entree
`MCBuilder.build` pour rejeter ses recettes et dependances. Le resolveur
verifie aussi sa sortie. Le test de regression couvre les identifiants et
les ajouts directs de carte. Sample Wizard independant reste autorise.
Il s’agit d’une regle de code et de tests : une modification intentionnelle
du depot peut toujours changer le code, ce qui doit faire echouer ces tests.

Un retour a la ligne manquant apres le commentaire initial de `wizard.js`
commentait toute son initialisation. Le correctif active effectivement
l’extension Sample Wizard independante deja presente dans le depot.

## 5. Sources et essais materiels

Le coeur fourni ne contenait aucune declaration de licence ni nom d’auteur.
Son attribution est conservee comme source fournie par AveyCole, sans lui
inventer une licence ou une autre provenance. Les licences et credits des
moteurs existants restent inchanges, notamment @Glycinate pour TINY.

Sur machine : sauvegarder les projets, installer une des quatre recettes,
choisir RETROSYN, parcourir les six SHAPE, tourner COLOR/SWEEP/CONTOUR,
verifier PUNCH, FINE, DECAY/GATE, retrigs et six pistes ensemble ; dans la
version complete, ecouter aussi TINY/WAVE et le Sampler. Le statut reste
experimental jusqu’au retour explicite du proprietaire.

## 6. Limites des anciens controles globaux

Le controle historique `gen_flasher_tweaks.py --check` differe deja du
`docs/flasher/tweaks.js` du main : le resultat est strictement identique
avec ou sans les cinq nouvelles recettes. Ce fichier historique n’est pas
reecrit par ce travail. Les recettes RETROSYN ont leur propre generateur
et `--check`. Le vieux smoke UI attend encore une carte Model-TG et tombe
sur son absence voulue ; le test du main sans Model-TG et celui des cinq
chemins RETROSYN couvrent la nouvelle selection. Le builder synthetique,
les references strictes, les chevauchements et le registre memoire passent.

## 7. ChordKeys et selection complete — 16/10/2026

AveyCole demande RETROSYN + ChordKeys avec tous les autres choix. Apres
identification des conflits historiques du pack LFO 2/3/4 avec Genie,
Attack et Filter, il demande explicitement son retrait de cette page.
Second LFO reste disponible ; les deux animations restent exclusives entre elles.

[FAIT en emulation] Six configurations navigateur reelles : RETROSYN seul
et banque complete, sans/avec Wizard, puis Select All avec chacune des
animations. Toutes gardent ChordKeys et Second LFO ; Select All garde toutes
les autres cartes. Ecritures, charges utiles, signature et boot verifies.

La banque Wizard etait trop grande avec deux flux comprimes independants.
Le code propre ChordKeys est donc inclus au runtime RETROSYN +0x2e900,
dans une reservation controlee disjointe de toutes les parties et tables.
Le chargeur Chord copie 2 405 longs depuis la SDRAM decompressee ; ses
adresses et corps fonctionnels restent identiques. Le meme format aPLib
utilise compress_margin=0 (defaut historique 9 conserve), identique en
Python et JavaScript. Flux complet Wizard : 258 705 octets ; fin
0x401ffff1, soit 15 octets sous END_LIMIT. Sans Wizard : 258 461 octets.

Les chemins seuls gardent leur support independant : retour du chargeur
RETROSYN chaine vers le support, restauration des LEDs et protection du
cache disque. Wizard seul avec Chord range son flux Chord a 0x401f8f76
pour eviter de decompresser sur une source qui chevauche sa destination.

Preuves : tools/test_retrosyn_chord_flasher.js et
emu/test_retrosyn_chord.py (six boot/clear/cache ; corps Chord et callbacks
RETROSYN exacts). Pas de verification materielle annoncee.

## 8. Teste sur la machine (16/10/2026)

AveyCole demande explicitement : « push retrosyn to main as hardware tested ».
Cette confirmation du proprietaire autorise le passage de RETROSYN a tested
et sa publication au principal. Aucun detail supplementaire de protocole
materiel ou de mesure CPU n’a ete fourni ; aucun n’est invente.

Le code DSP, les ecritures et les charges utiles restent ceux du test
precedent. Seuls statut, documentation, version et retrait de l’ancien
pack LFO 2/3/4 de la selection principale changent. Sample Wizard reste
facultatif et Model-TG demeure bloque.
