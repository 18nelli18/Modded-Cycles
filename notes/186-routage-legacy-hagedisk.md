# 186 — Routage LEGACY Hagedisk

AveyCole25/10/2026 :153 ACID semble mieux, P environ100 ; LEGACY depasse100 meme sans SPEAK sur cinqpistes. Correction du patch : Hagedisk (Legowelt), pas Swissynth. Demande poursuivre les gains. Generateur --legacy-routing, sur153 ; preuves exactes ci-dessous. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation]154 economise 5.196% instructions de moteur sur24cas Hagedisk original, PCM et tous octets des sixDxTrack exacts. Mix natif : environ0,55–0,60%, pic maximum mesure encore identique. Ne pas convertir ces chiffres en P physique ou promettre moins de100. Aucun principal change. Tests appareil154 attendus.

## 1. Routage fixe, memes operateurs

Hagedisk original est slot9, algorithme12 (index11), feedback7. Ne pas profiler seulement la banque par defaut : notre composition remplace Hagedisk par une voix ROM. La preuve lit directement le patch original et le banc mixte charge les32voix d origine dans banks.

Le chemin algorithm==11 deroule les sixflags constants 01,05,05,14,c1,14 avec les memes seuils1120, Exp2, noyaux152, has_contents, phases et feedback. Toute autre topologie garde le chemin generique. Un operateur inactif peut invalider son bus : aucune suppression de cette semantique. Aucun cache, nouvelle allocation ou changement de DxTrack. FmCore compile avec le meme GCC13.1.0/O3/funroll que153.

## 2. Produit pitch exact

Le produit (uint32 pmd * int32 sens)>>39 utilisait le helper64bits. EMAC signe produit q=floor(signed(pmd)*sens/2^31), puis q>>8. Si pmd a son bit31, correction sens*2^32 : ajouter sens>>7 puis la retenue de (q&255)+2*(sens&127). Sensibilite reelle bornee par +/-255*2^23 ; le q signe tient donc toujours dans32bits. Le cas abstrait pmd=sens=0x80000000 ne respecte pas cette borne et n est pas le contrat. MACSR20 et ACC0 vide sont garantis par wrap.S ; sauvegarde48bits et autresACC inchanges.

## 3. Preuves et disposition

94cas de moteur dont24Hagedisk original,32algorithmes, notes/velocites/brightness/EGtime/feedback et relache, PCM/etat complet exacts.128cas FmCore supplementaires :64masques d operateurs actifs/inactifs, seuils1119/1120/1121, feedback0..16, PCM/tampons/parametres/feedback/EMAC exacts.8288produits natifs compares aux entiers exacts, sens dans ses bornes reelles et pmd sur toute la plage uint32. Deux mixes32blocs avec vraie banque Hagedisk, PUNCH/PUNCH/KICK/ACID et SPEAK ou MIDI silencieux, HALL/PingPong/Sidechain : PCMvoix et FX exacts. Le gros bloc froid ne prouve pas le cout du LEGACY etabli ; ne pas le presenter comme un pire retrigger LEGACY.

Seuls objets dx7_fm_core.cc.o et dx7_port.cc.o changent ; noyaux152 et tousautresobjets exacts, queue151 et factoryWAVE exacts. Standard/adulte DSP exacts, bootloader/updater et sections horsMAIN exacts, bornes code verifiees.154standard/adulte --check et153 --check passent. Banque burst/overflow/retry/STOP/DIN+USB passent.

## 4. Retour utilisateur et suite

153 : utilisateur signale ACID environ100P et LEGACY au-dessus100 sur cinqpistes ; pas de nouveau chiffre112–114 attribue a153.154 appareil attendu. Ensuite auditer les plages/valeurs affichees des machines ajoutees, en particulier TINY/PUNCH/ELDER, et documenter seulement les comportements verifies ; ne pas remapper les controles sans diagnostic.
