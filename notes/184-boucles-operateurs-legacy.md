# 184 — Boucles operateurs LEGACY plus rapides

Demande AveyCole25/10/2026 : «work on optimizing legacy as much as possible», apres correction de la comparaison113P (MACRO remplace par LEGACY).151 confirme sur appareil pour banques : BANK RECEIVING puis LEGACY BANK SAVED. Pattern SPEAK/MACRO/PUNCH/PUNCH/KICK/ACID rapporte101P. Generateur prive --legacy-fast, kernels152.S ; preuves test_legacy_kernels152.py/test_legacy_exact152.py/test_legacy_mix152.py. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation]152 conserve151 et remplace seulement les trois boucles operateurs de MSFA. Gain moyen11,506% instructions dans70cas LEGACY,6,654–14,499% parmi les32patches de la banque. Les sixcas d'operateurs desactives peuvent economiser moins, voire rien quand aucun operateur ne rend de sample. Banc aleatoire des noyaux :18,894% instructions en moins. Banc sixmachines avec uneLEGACY :1,31–1,64% total, PCM exact. Sans LEGACY, PCM et instructions exacts151. Aucun gain CPU physique152 mesure ; ses limites/controles et la synthese restent exacts.

## 1. Chemin optimise

MSFA/Dexed Apache2.0, Google2012 et PascalGauthier ; provenance/revision du moteur conservees. fm_op_kernel.cc garde ses implementations originales pour toutes les recettes sans DX7_LEGACY_FAST.152 utilise les memes symboles ABI C++ statiques en assembleur ColdFire. compute, compute_pure et compute_fb,32samples, boucles par4. Les constantes de decalage13/14 restent en registres dans les boucles sans feedback ; progression de phase/gain et adressage de table simplifies. Feedback conserve y0/y dans leur ordre exact, yprecedent avant calcul du prochain. Aucun tableau, cache, LFO, enveloppe, normalisation, seuil ou precision reduit. Arrondis et debordements32bits identiques. ACC0 seulement, vide apres chaque produit ; MACSR/48bits physiques geres par le wrapper151 inchangé.

L'essai initial de compilation-O3/-funroll-loops seul donnait moins de1% ; abandonne. La livraison utilise les boucles explicites et les autres objets restent-O2.

## 2. Contrat et memoire

d2-d7/a2-a4 sauves/restaures dans36octets de pile ; d0/d1/a0/a1 et CCR caller-saved. a5/a6 intacts. Arguments int32 et bool empiles avec ABI originale ; retour32samples et historique feedback exacts. Aucun nouvel etat persistant ou BSS. Code dans moduleDX7 existant0x46850000, fin avant factoryWAVE0x46860000. Queue151 conservee0x468a8000..0x468acd74, hors HALL/artPUNCH et hors WAVE. Les gardes151 et les octets zero sont conserves.147 et149 exclus. Bootloader/updater et toutes sections horsMAIN exactes.

## 3. Preuves

192cas aleatoires : trois noyaux, add/remplacement,32phases/frequences/gains/entrees/historiquesfeedback par chemin ; PCM et feedback exacts, canaris, d2-d7/a2-a6, MACSR, ACC0 et ACC1..3 nonzero preserves.70cas moteur natif :32patches fournis,32algorithmes avec modulation/LFO,6masques d'operateurs ;8blocs chacun, notes0..127, velocites1/64/100/127, brillance/temps/feedback0/64/127, pitchlive, relache. Comparaison de TOUS les octets des sixDxTrack, pas seulement de la sortie. Invocations note_on/controls et enveloppes/pitch/phase/feedback exactes.

Mixeur natif HALL/PingPong/Sidechain : SPEAK, MACRO36 ouLEGACY0/15/31, deuxPUNCH, KICK, ACID. Sorties voix/post/wet/rev_wet/send exactes. Totaux avec LEGACY0 :554421->545335 ;15 :547060->539888 ;31 :548662->541149. SansLEGACY :591789exact. Plus gros blocs du banc inchanges61281/61345/61409 ; ne pas promettre une baisse deP. Profil complementaire : beaucoup d'instructions dans le traitement natif partage0x400a8204 et environs, hors operateurs LEGACY. L'expression initiale «worst trigger block» et l'attribution a la seule initialisation etaient trop precises ; les comptes seuls ne localisent pas une regression physique. La mesure P est un temps reel, pas ce compteur d'instructions.

Banques :32bursts,16slots,overflow/retry,DIN/USBsimultanes,WAVE exact passes. Popup/QntM/retentionMIDI24machines/sixpistes passes. Builds standard/adulte reproductibles --check. Audit : seul ancien objet fm_op_kernel.cc change et nouvel objet kernels152.S ; FX/Fundamentals ne changent que leurs relocations de relaisDX7, tous autres objets exacts151. Modules LEGACY/DSP standard-adulte exacts.

## 4. Appareil

[A FAIRE appareil152] Meme pattern, meme patchLEGACY, memes FX/Sidechain et reglages, comparer151/152 A/P/O/N apres stabilisation. Conserver151 pour comparaison. Le succes banque sur151 est confirme, celui de152 est herite et prouve en emulation mais encore a confirmer physiquement. Aucun principal modifie, aucun guide public a changer car aucun controle/son change.152 exclut l'optimisation149Harmonics et le mixeur/SPEAK147.

## 5. Retour appareil et correction du banc25/10/2026

AveyCole :152 toujours112–114P avec LEGACY a la place deMACRO. Pas de gain physique de pic etabli. Banque151 deja confirmee. Le decodeur de toutes les copies ACID/HALL manquait dans le banc mixte184 ; voir185 pour la couverture corrigee et les nouveaux chiffres. Les preuves directes des noyaux LEGACY restent distinctes.
