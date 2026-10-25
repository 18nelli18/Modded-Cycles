# 171 — Sidechain : suivre le mute de la source

Demande AveyCole du24/10/2026 : option On/Off dans S.Chn pour conserver ou interrompre le ducking lorsque la source est mutee. Variante privee128 reguliere/adulte au-dessus127. Adresses : VA OS1.13. Promotion du regulier128 demandee apres essai utilisateur ; variante adulte privee.

## 1. Masques natifs et enveloppes

[FAIT] IRQ40058ca6 charge mute800017ac et solo800017b0. Le masque de blocage est solo non nul ? complement solo : mute ; copie -84(a6) puis test par piste en40058e54. Lire ces deux mots directement en du_process, sans getter constructeur ni appel UI/disque. Option Off par defaut = comportement127. On : la source mutee ne contribue plus, enveloppe nettoyee ; le gain cible remonte avec la rampe32echantillons existante. Les autres sources restent actives et les trigs en amont ne sont jamais rejoues au demute.

## 2. UI et stockage

[FAIT implementation] Dixieme ligne Mute On/Off, DATA bascule. Bit64 libre du byte de cibles, six cibles dans bits0..5 ; etat72octets et allocations banques inchanges. du_enabled ignore le bit64, bypass sans routes conserve. Anciennes recettes gardees avec DU_MUTE/FXD_MUTE conditionnels. GCC13.1 ColdFire54418.

F2 initial387bits/392 : cinq bits libres ne suffisent pas aux six sources. F3 gagne un bit en codant le delay par index dense3bits (sept types actuels, garde<=8), puis ajoute six flags : exactement392bits, memes49octets et CRC24. Toute option Off emet encore F2 byte-identique. Lecteur128 accepte FXS1/F2/F3 ; les anciens firmwares ne lisent pas les patterns F3 avec une option active. Aucun octet natif additionnel ni agrandissement du projet. Garder une copie avant retour127.

## 3. Validation

[FAIT en emulation] Compilation, bornes, matrice mute/solo et six sources, patterns/copie/projet/fresh process, compatibilite F2/FXS1 et rendu des dix lignes : resultats detailles ci-dessous. Aucune mesure physique exhaustive revendiquee.

## 4. Resultats et promotion demandee

[FAIT en emulation] Code et BSS bornes et disjoints, ancienne recette127 exacte, candidat128 reproductible. Deux variantes : 48cas audio mute/solo, vrai filtre de notes sequence, deux sources avec politiques differentes, remontee rampee et aucun rejeu au demute. Codecs projet/pattern, copie/reset, blank et queue, redemarrage nouveau processus ; FXS1/F2 acceptes, F2 reemis exact ;64combinaisons flags, sept IDs delay, ID dense invalide avec CRC valide rejete. Bypass9instructions, pire cas teste7072instructions emulees, pas un pourcentage appareil. Rendu des dix lignes, toggle par source et largeurs. Valeur On/Off finale a119 pour rester dans la surbrillance ; la derniere modification source ne porte que sur cette coordonnee. Le compilateur reordonne le code de dessin : candidat final revalide en emulation.

[FAIT rapporte] AveyCole : «It worked, go ahead and push v128». Autorise publication du regulier128. Lexique adulte prive. Pas de mesure physique exhaustive revendiquee. Guide de reference : nouvelle commande Mute uniquement, pas de notes internes ajoutees.

Publication2.41 : SysEx `a3df9c7ca6e6f566e6747dab872223189e236a18567ba0163523b8b612a5ad0d`, MAIN `c7fcbbae50ac86ed190cb3d50eea4755137cc546dcc603e26a3f66d2b747b8e2`.

[FAIT publication locale] Livraison navigateur : SHA exacte128, telechargement Supermodel_2.41.syx, importeurs et guide bilingue verifies. PDF public et deux guides prives : six pages chacun, rendus et inspectes. Blurb fourni inchangé (SHA00da19e1...). Anciennes sorties gen_flasher_tweaks/registry deja obsoletes avant cette promotion ; entrees et sorties correspondantes inchangees, voir notes169/170.
