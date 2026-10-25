# 170 — Gestes Mod Setup/Scramble et niveau Shadow

Demandes AveyCole du24/10/2026 : inverser les gestes, appui bref Mod Setup, maintien Scramble ; bref avec trig tenu conserve marque par pas. Retirer boost Elder, ajouter boost Shadow, puis encore6dB. Renommer entree Sidechain en S.Chain puis S.Chn, alignement gauche et fleche >. Recette privee --sidechain-label ; principal122 inchange. Adresses : VA OS1.13.

## 1. Implementation

[FAIT] Module UI a4684d000..4684f000, apres code FXP et avant Legacy46850000. Detour sur sx_previous_key, pas sur la chaine externe : tous les wrappers SX/S.Chain/retention restent actifs. Reutilise globals et wm_api du controleur original. Appui bref differe au premier relachement : sc_steps_toggle seulement ;0 signifie aucun pas tenu et ouvre alors menu. Maintien appelle sc_key original par API6 avec press/release synthetiques et garde SETTINGS temporaire. Etat owned interdit de rearmer pending sur flags33 repetes. SETTINGS release continue vers les autres handlers ; menu_used/mod_used empechent CONFIG et touches collees.

[FAIT] Routage render Elder16 vers original avant boost. Meme wrapper de gain sature retargete Shadow19 : deux doublements satures apres rendu/enveloppe, avant mixage, x4=12,0412dB. Pas de changement des algorithmes, VCA, filtres ni autres voix. Sources et compileflags conditionnels conservent122 et123 byte-identiques. 125 reprend124 avec label S.Chn et coordonnee gauche72 identique aux autres labels ; fleche utilise la coordonnee native x+24. Police et fleche verifiees dans le dessin natif128x64.

## 2. Validation et limites

[FAIT en emulation] Tap/hold, deux ordres de relachement, repetitions flags9/33/34 sans double Scramble, DATA/BACK, marque pas native on/off avec longueur64 et neutralisation release ; controles S.Chn, largeurs et absence chevauchement. Suite72champs pattern/FX/Sidechain, codecs natifs, copies/reset, metadata et ChordKeys, requete queuee, reload nouveau processus. PCM natif144paires de blocs six voix : Elder exact avant boost ; Shadow x4 apres fondu natif de changement de machine, arrondi final3unites au plus ; cinq autres voix exactes. Pic du corpus Shadow252067840, pas une garantie absence clipping avec tous les patches. Gains satures, aucun wrap entier. Emulateur doit etre en mode superviseur pour le wrapper voix qui preserve SR, comme sur appareil.

[FAIT rapporte] AveyCole a indique «Worked great» sur123 avant la demande d alignement. Cela ne constitue pas test physique125 realise par l agent.125 est prive, experimental ; variantes reguliere/adulte, modules geste/gain/menu identiques. Principal2.39/122 et blurb inchanges. Check --sidechain-label exact et ancien --sidechain122 exact passes.

## 3. Variante privee126 - cibles abregees

[FAIT] Recette --track-abbrev conserve125 et ajoute DU_TRK : chaque cible dessine une seule chaine Trk. N a x72. Ancien label Track et numero separes desactives seulement pour les cinq cibles ; cases a119..126 et controles inchanges. Libelle principal S.Chn > conserve. Variantes reguliere/adulte generees depuis la recette officielle, jamais par modification du syx existant.

[FAIT en emulation] Deux variantes : chaine native touches/encodeur, cinq cibles pour six sources, limites des quatre controles, DATA/BACK, dessin natif128x64 et largeurs verifiees ; capture inspectee. Binaires fundamentals et gesture123 identiques a125. Aucun test physique126 revendique ; principal2.39/122 et blurb inchanges.

## 4. Variante privee127 - controles dans la surbrillance

[FAIT] AveyCole demande Dpt, Atk, Hld, Rel et de placer les labels dans la selection. --compact-controls ajoute DU_CONTROLS ; quatre labels a x72 au lieu de65, valeurs a126 inchangees. Anciennes recettes conservees. Aucun changement audio, stockage ou gestes ; binaires fundamentals et gesture123 identiques126. GCC13.1 ColdFire54418, meme emplacement reserve et gardes du module Sidechain.

[FAIT en emulation] Deux variantes : touches/encodeur, limites, DATA/BACK, police et absence chevauchement. Quatre selections rendues en128x64 puis inspectees : premieres lettres dans la surbrillance. Pas de revendication de test physique127. Principal et blurb inchanges.

## 5. Promotion publique 2.40

[FAIT rapporte] AveyCole : «Perfect, push v127 to main». Publication reguliere exacte SHA `cb19d4d68c2a341bf92a2d26c73c1f042d7f7ff335ae3fcf06d0a615439b72bb`, MAIN `04905a7ad1f75d5fd3b0a6c14e7c7e0c9c220a45c88ecd99b96fa9ec671da6e2`. Guide EN/FR/PDF actualise ; adulte prive et blurb fourni identique.

[FAIT validation publication] Recette --compact-controls --stage --check reproduit127 exact. Preuves test_gesture123 et rendu UI passes ; controle Chromium reel du flasher et de sa construction exacte, importateurs, EN/FR/mobile, blurb byte-identique. Guide imprime neuf pages rendu et inspecte. check_overlaps passe. gen_flasher_tweaks --check et registry --check signalent les sorties deja perimees avant cette promotion (notes169) ; leurs generateurs, entrees de tweaks et sorties n ont pas change ici. Une ancienne attente de preuve codait le gain12dB pour124/125 seulement ; corrigee en revision>=124, sans modifier le firmware. Les guides prives regulier/adulte restent hors depot public.

## 6. Guide de reference sans historique

[FAIT] AveyCole demande de retirer les changements tels que les voix LEGACY ameliorees du guide de raccourcis. Suppression des sections New in, notes de gain, remplacement de voix et correctifs ; commandes utiles regroupees dans Machines, LEGACY, Effets et Mod Setup. Notes de version conservees ailleurs. Trois PDF regeneres sur huit pages, rendus et inspectes ; lexiques prives128mots exacts. HTML/Markdown EN/FR issus de la meme source, controle Chromium/mobile et --check passes. Firmware127 et blurb strictement inchanges. Guides adultes et prives hors depot public.

## 7. Impression condensee et retrait des details internes

[FAIT] Demande AveyCole : reduire le blanc initial et retirer notamment la phrase sur les quatre commandes Wizard gardees dans MACHINES. Suppression des notes de preservation de valeurs, implementation et ancien comportement ; commandes et usages conserves en EN/FR. Flux PDF continu, tableaux divisibles par ligne avec en-tete repete, moins de padding des listes. Police inchangee. Guides public/regulier/adulte de huit a six pages, premiere page remplie par les controles, tous les rendus inspectes et index128mots verifies. Test navigateur attend maintenant la fin de lecture asynchrone du fichier banque avant de compter les32voix. Firmware127 et blurb byte-identiques ; guides prives hors depot.

## 8. Nom du telechargement avec version

[FAIT] AveyCole demande Supermodel_2.40.syx pour le firmware genere. Le chemin fixe principal prend la version de MC_RELEASES[0], meme source que la version affichee ; version ajoutee a la cle de cache du build. Le lien download utilise ce nom. Pas de changement des octets du firmware, restauration ni fichiers importes. Controle Chromium : vrai evenement download, suggestedFilename Supermodel_2.40.syx et SHA des octets identique au127 approuve. EN/FR/mobile et blurb proteges par la meme suite. Stamp du site actualise pour charger le nouveau script.

## 9. Ponctuation du blurb : substitution de police

[FAIT] Capture AveyCole : fin de phrase visible en !!1. Le HTML et le DOM contiennent pourtant trois points d exclamation. Reproduction Chromium avec Familjen Grotesk : substitution contextuelle calt affiche le dernier comme1. Capture avant/apres : font-feature-settings calt0 retablit !!!. Regle limitee a fixed-features, en dehors du texte fourni ; SHA du bloc blurb strictement identique. Verification CSS calculee et capture de la vraie page locale, suite livraison exacte/download/ENFR/mobile reussie. Aucun octet firmware ni mot du blurb modifie.
