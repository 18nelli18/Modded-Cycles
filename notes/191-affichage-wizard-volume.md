# 191 — Sample Wizard, Groove On/Off et volume segmente

Demande AveyCole du25/10/2026 : disposition Wide waveform approuvee, activation Groove separee du Type, maintien des notes et navigateur, volume horizontal par rectangles et labels des previews. Generateurs --wizard-display158 et --wizard-volume159. Adresses : VA de l OS1.13.

## Reponse courte

[FAIT en emulation]159 ajoute titre, waveform122colonnes, piste/duree et onze rectangles de volume ; Groove On/Off et Type distincts sans Swing dans Type ; Off conserve le Swing natif. Les labels opaques des six previews sont restaures. Navigateur et entree des notes preserves. Statut experimental prive ; appareil attendu.

## 1. Ecran et bornes

Source display158.c, reserve code468b8000..468ba000 et BSS468ba800..468bb000, apres Groove et avant art RETRO. Detour mm_draw4678f6a0 garde/rejoue le prologue. MainScreenView400ffe20 seulement ; exclusions natives popup, trig tenu, navigation notes et vues secondaires avant acces PCM. Les getters UI retournent un octet avec bits hauts non definis : masque255 obligatoire.

PCM16BE, en-tete64octets, bornes slot/count/size/side validees ; min/max sur122colonnes, au plus32positions par colonne et canal. Cache invalide par slot/base/count/size/hash/side ; zero lecture PCM au redraw en cache. Reconstruction L/R du mid/side ; aucun calcul dans le chemin audio. Marqueur Start/Position fixe, sans faux curseur de lecture. Volume lit le getter natif40009c5a pour la piste selectionnee, masque255/clamp127. Rectangles4x5, espace2px, onze segments au format normal ; nombre adapte a la place restante avant duree. Zero : contours ;127 : tous pleins.

## 2. Preferences et labels

control158.c : Groove Off/On distinct, Type1..7 seulement ; choix retenu lorsque Off, Strum independant. Groove.cfg21octets version3, migration20octets version2 ; sauvegarde arretee et aucun nouvel octet de pattern. mod-overlay159.c capture le nom via le callback du parent natif, le redessine avant inversion de la fenetre opaque. Valeur/graphique/labels gardes ensemble ; cache2secondes et BACK conserves. Les menus FX gardent leur dessinateur.

## 3. Preuves

Rendu natif et oracle min/max/cache/stereo/bornes ; volume0/64/127, contours/espaces/remplissage exacts et autres pixels invariants. Vrais getters UI et priorite des notes/popups. Setters Pitch/Fine et six notes36..84 en step-record : donnees pattern30710octets exactes157. On/Off, sept Types, retention et migration des preferences verifies. Six previews avec texte, present imbrique, duree et BACK verifies. Scope159 : tous objets DSP, Groove/Strum, navigateur, entrees et banques exacts158 ; seules exceptions dessin Wizard/labels et relocalisation pointeurs du trampoline QntM. Reservations non chevauchantes et sections horsMAIN identiques. Builds standard/adulte reproduits avec --check, GCC13.1.0 -mcpu54418. Aucun pourcentage CPU ni succes appareil revendique ; principal2.47 inchange.

## 4. Promotion2.48 (25/10/2026)

AveyCole : «but goahead and push159 as well». Publier le standard159 exact SHA `fb0d1b480d21910e6c0c63f300b6383f802a1cbbf490eb7e55f6932951a6047f`, MAIN `e743c142835072c4050c60d42d9b86f7c89e3fb209a416ff6d7b1e97416a9ec4`. Autorisation de publication, aucun nouveau resultat hardware revendique. Engines VA/LXR recherches ensuite dans un test separe.
