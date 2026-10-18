# Notes de développement : mod USB multipiste Model:Cycles

Notes de travail tirées de l'analyse de dépôts GitHub (analysés le 25/09/2026). Elles complètent
[`../dossier-technique.md`](../dossier-technique.md), tiré du fil Elektronauts.

> **Conventions**
> - **`[FAIT]`** : lu dans le code ou la doc d'un dépôt, ou décodé à l'octet près.
> - **`[HYP]`** : hypothèse ou interprétation de ma part, à confirmer sur l'image firmware.
> - **`[À FAIRE]`** : action à mener.
> - Toutes les adresses sont des adresses virtuelles ColdFire (VA) de l'OS **1.13**, sauf mention contraire.

---

## ⚡ Ce qu'il faut retenir en premier

1. **Le mod existe déjà en grande partie.** Le dépôt `scottmetoyer/ms-multi-output` fournit une cible
   `--target cycles` qui envoie **les 6 pistes du Model:Cycles sur 6 canaux USB** (48 kHz, 32 bits, High Speed).
   Le mixage stéréo n'est alors plus envoyé en USB.
   - Le **code patché est vérifié sur du matériel**, mais sur un Model:Samples qui fait tourner l'OS Cycles (« cross-flash »).
   - **Validé sur un vrai Model:Cycles le 29/09/2026** (variante `6ch-usbup`, flashée par USB), avec SD VINTAGE ([14](14-machine-sd-vintage.md)).
2. **La chaîne d'outils est connue et scriptable.** On extrait la section 3 (MAIN OS) avec `elektron-firmware-tool`,
   on applique une table de patchs octet par octet, puis on reconditionne et re-signe (HMAC recalculé).
   Aucune signature cryptographique n'empêche le flash.
3. **Filet de sécurité.** Le bootloader se trouve dans un secteur que les mises à jour d'OS n'écrivent jamais.
   On revient toujours à l'OS officiel par l'**entrée MIDI IN** de l'appareil, une prise jack TRS 3,5 mm (le menu de démarrage ignore l'USB).
   **Une interface MIDI reliée à ce MIDI IN est obligatoire avant tout flash** : sortie TRS + simple câble jack stéréo,
   ou sortie DIN + adaptateur fourni ([12](12-flash-par-jack-trs.md)).
4. **Limites du mod actuel** :
   - pistes mono (pan non appliqué) ;
   - delay et reverb absents ;
   - plus de mix stéréo en USB ;
   - `CONFIG → UPGRADE` par USB cassé avec `6ch-multiout`. La variante `6ch-usbup` ([13](13-6ch-upgrade-usb.md)) le garde : **testé sur un vrai Model:Cycles le 29/09/2026** ;
   - hôte USB High Speed obligatoire ;
   - le LEVEL de piste est-il appliqué avant le point de prélèvement ? Inconnu sur le Cycles.

## Sources analysées

| Dépôt | Statut | Commit analysé | Rôle |
|---|---|---|---|
| [scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output) | ✅ lu en entier | `3edf617` (19/09/2026) | Le mod 6 canaux (M:S et **M:C**) |
| [mischa85/elektron-firmware-tool](https://github.com/mischa85/elektron-firmware-tool) | ✅ lu en entier | `a5bce9a` (08/09/2026) | Dépaquetage / repaquetage / re-signature des `.syx` |
| `bryantysinger/elektron-models-teardown` | ❌ **supprimé** par l'auteur (confirmé par l'utilisateur) | n/a | Analyse du firmware des Models ; perdu, rien n'en dépend |
| **Image officielle OS 1.13** | ✅ **téléchargée et analysée** le 25/09/2026 | 1.13 (dernière) | Voir [09](09-analyse-firmware-1.13.md). Fichiers dans `firmware/` (non versionné) |
| [bryantysinger/octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt) | ➕ bonus (seul dépôt public du même auteur) | `e970dd0` | Patch de valeurs du firmware Octatrack : méthode registre, vérification, hashs |
| [mxldyn/octamax](https://github.com/mxldyn/octamax) | ➕ bonus (crédité par ms-multi-output) | `7d9debc` | Rétro-ingénierie complète de l'OS Octatrack : technique code cave + détour, Ghidra, émulateur, pièges |
| [drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks) | ✅ lu et **adopté** (mtlib versé dans `tools/`) | `6e0b4df` (19/09/2026) | Outillage Python pur (SysEx/aPLib/ELE3/HMAC), format de tweak JSON, 3 tweaks QoL pour le M:C 1.13 |

## Plan des notes

| Fichier | Contenu |
|---|---|
| [01-ms-multi-output.md](01-ms-multi-output.md) | Fonctionnement du mod 6 canaux, **table de patchs Cycles décodée**, stubs, historique et leçons |
| [02-format-os-syx.md](02-format-os-syx.md) | Format `.syx` → conteneur ELE3 → sections aPLib → MAIN OS ; checksums, HMAC, CLI de l'outil |
| [03-plateforme-coldfire.md](03-plateforme-coldfire.md) | CPU MCF5441x, carte mémoire connue, pièges de l'ISA ColdFire, outils de rétro-ingénierie |
| [04-usb-audio.md](04-usb-audio.md) | Pilote USB (dQH/dTD), descripteurs UAC2, table de modes USB, ring, bande passante, compatibilité OS |
| [05-methode-patch.md](05-methode-patch.md) | Technique code cave + détour, règles de sûreté, build reproductible, leçons des crashs |
| [06-flash-et-recuperation.md](06-flash-et-recuperation.md) | Procédures de build, de flash et de récupération ; pièges de `flash.py` avec le Cycles |
| [07-snippets.md](07-snippets.md) | Code prêt à l'emploi : stubs ASM relogés Cycles, helpers Python, commandes shell |
| [08-feuille-de-route.md](08-feuille-de-route.md) | Étapes du projet, extensions (8 / 12 / 14 canaux, FX), questions ouvertes, risques |
| [09-analyse-firmware-1.13.md](09-analyse-firmware-1.13.md) | **Vérifié sur l'image officielle** : structure ELE3, menu de démarrage, réglages USB, réécriture des descripteurs, mixeur |
| [10-faisabilite-fonctionnalites.md](10-faisabilite-fonctionnalites.md) | **Faisabilité des 10 fonctionnalités souhaitées**, par priorité, avec effort et inconnues matérielles |
| [11-conception-8-canaux.md](11-conception-8-canaux.md) | **Conception du mode 8 canaux** (6 pistes + mix) : stubs `tracks8`/`prime8` vérifiés, éditions, rings à finaliser |
| [12-flash-par-jack-trs.md](12-flash-par-jack-trs.md) | **Flasher avec un simple câble jack stéréo** : entrée MIDI TRS (types A et B), interfaces à sortie TRS, piste « sortie casque » simulée |
| [13-6ch-upgrade-usb.md](13-6ch-upgrade-usb.md) | **Variante `6ch-usbup`** : stubs déplacés dans une cave, descripteurs et table des modes USB d'origine, pour garder l'upgrade USB. Vérifications (émulation) et protocole de test |
| [14-machine-sd-vintage.md](14-machine-sd-vintage.md) | **Machine SD VINTAGE** (caisse claire vintage, d'après le Syntakt) : architecture des machines du M:C décodée, moteur en C, banc d'émulation du moteur audio (EMAC corrigée), masques de sprites libérables, étape 1 **validée sur le matériel** (29/09/2026), plan de la 7ᵉ machine |
| [17-portage-exact-syntakt.md](17-portage-exact-syntakt.md) | **Le vrai SD VINTAGE du Syntakt dans le Cycles** : extrait au build de ton `.syx`, relocalisé en SDRAM à `0x43000000`, crochet de démarrage, passerelle, démarrage sûr ; **même sortie échantillon par échantillon** en émulation ; décompression vérifiée avec le vrai bootstrap ; **testé sur la machine le 30/09**, dans le flasher web |
| [18-septieme-machine.md](18-septieme-machine.md) | **SD VINTAGE en 7ᵉ machine « SDVtg », à côté de SNARE** : tout ce qui dépend du nombre de machines (moteur, paramètre ALG, écran MACHINES, icônes, recherche potard → descripteur, état par descripteur) ; 5 descripteurs propres (noms et défauts du Syntakt) ; 20 vérifications en émulation sur le vrai code de l'OS ; dans le flasher web |
| [19-cp-vintage-8e-machine.md](19-cp-vintage-8e-machine.md) | **CP VINTAGE en 8ᵉ machine « CPVtg », avec SDVtg** : moteur 7 du Syntakt (30 fonctions, tables), OS à 8 machines, champ machine 7 = « toutes » contourné ; 26 vérifications en émulation, CPVtg identique à CP VINTAGE ; **testé sur la machine le 30/09** |
| [20-moteurs-syntakt-a-cocher.md](20-moteurs-syntakt-a-cocher.md) | **Moteurs du Syntakt à cocher, et SY TOY « SYToy »** : générateur pour n'importe quel choix de moteurs, SY TOY identique au Syntakt en émulation, flasher avec une case par moteur, option « à la place de SNARE » retirée de la page ; gel dû à une piste restée sur une machine disparue, corrigé ; **SYToy seul et les trois moteurs testés sur la machine le 30/09** |
| [21-sy-bits.md](21-sy-bits.md) | **SY BITS en machine « SYBit »** : Detune de 40 à 88, PUNCH = Bit Redux, fonction appelée par pointeur à relocaliser ; identique au Syntakt en émulation (16 cas) ; les firmwares déjà testés restent identiques à l'octet près ; **SYBit seul testé sur la machine le 30/09** |
| [22-sy-swarm.md](22-sy-swarm.md) | **SY SWARM en machine « SYSwm »** : supersaw, PUNCH = sous-octave (Fundamental Sub) ; identique au Syntakt en émulation (13 cas, 16 combinaisons) ; flasher à 5 cases (511 empreintes) ; **SYSwm seul testé sur la machine le 30/09** |
| [23-optimisation-charge.md](23-optimisation-charge.md) | **Ralentissements avec plusieurs moteurs du Syntakt** : compteur de charge sur la machine (le Cycles d'origine prend déjà 77 % pour l'audio, même à l'arrêt ; une voix du Syntakt ≈ 2 voix d'origine) ; **arrêt des voix muettes** (−77 % d'instructions quand les voix se taisent, son identique) |
| [24-moteurs-restants.md](24-moteurs-restants.md) | **Moteurs du Syntakt restants** : SP TWINSHOT impossible (ses 64 échantillons ne sont pas dans le fichier d'OS, et trop gros) ; toutes les autres machines sont analogiques (circuits pilotés par le processeur) : le portage exact est terminé |
| [25-regulateur-de-charge.md](25-regulateur-de-charge.md) | **Régulateur de charge** : mesure de chaque bloc audio ; sous forte charge, fins de notes coupées plus tôt (−66 dB) ; en surcharge, la voix la plus faible (Syntakt d'abord) s'éteint par un fondu de 5 ms, une à la fois ; vérifié en émulation |
| [31-model-tg.md](31-model-tg.md) | **Model-TG (TinyGregAudio, MIT)** : machine Sampler, rééchantillonnage, retrig et effets master ; proposé seul dans le flasher (même empreinte que son propre build), avec ou sans audio USB 6 canaux ; conflits avec les moteurs du Syntakt analysés ; **version combinée** (Sampler 7e machine, moteurs du Syntakt ensuite) : une retouche de sa source, détours chaînés, charge utile à 0x46700000 rangée en morceaux, prouvée en émulation ; **passage à sa v1.1.0** (slide trigs, aussi sur nos moteurs du Syntakt, prouvé en émulation) |
| [32-arpegiateur.md](32-arpegiateur.md) | **Arpégiateur à la place du retrig** : menu Retrig Setup et répétitions de l'OS analysés ; réglages dans l'octet +512 de la piste (inutilisé, sauvegardé) ; code dans des masques de sprites libérés ; prouvé en émulation jusqu'à la vraie boucle d'événements de l'interruption audio ; en live rec, l'arpège enregistre les notes qu'il joue (§11) |
| [33-effacer-un-trig.md](33-effacer-un-trig.md) | **Effacer un trig (défaut de l'OS d'origine)** : un appui de plus de 200 ms sur un trig compte comme un maintien et le trig reste ; chaîne des touches décodée (anti-rebond à 1 kHz, horloge de maintien à 120 Hz, mode grille et `UIStates`) ; correctif : 500 ms pour les pas qui ont un trig, décidé aussi au relâchement ; prouvé en émulation sur la vraie chaîne de l'OS, avec tous les autres tweaks ; **testé sur la machine le 03/10/2026** |
| [34-ecoute-en-pause.md](34-ecoute-en-pause.md) | **Écoute d'un pas : PAGE tourne la page après un Stop MIDI** : le tweak `trig-preview` (aussi dans Model-TG) refusait le séquenceur en pause, où le met un Stop MIDI reçu même à l'arrêt ; correctif de 3 octets (`lsr.l #1,d0 ; bcs.w`), aussi appliqué à la copie de Model-TG ; prouvé en émulation avec le vrai gestionnaire du Stop MIDI ; **testé sur la machine le 04/10/2026** |
| [35-glitches-usb-multipiste.md](35-glitches-usb-multipiste.md) | **Glitches de l'audio USB avec Model-TG (Reddit)** : l'OS envoie chaque bloc à l'USB juste après l'avoir calculé, et la file du mod 6 canaux ne tolère que 0,2 ms d'écart, alors que Model-TG et nos moteurs font varier la charge de 20 à 95 % ; pilote USB décodé (remplissage, démarrage, mesure du débit) et simulé avec le vrai code ; correctif : envoi au début de l'interruption suivante, file alignée au démarrage, ring de 9 cases, copie des pistes déroulée (6ch-usbup, Model-TG, moteurs) ; pistes USB coupées au mute avec Model-TG (`voice_quiet`), retouche prouvée sur la vraie boucle des voix ; simulé : de milliers de trames abîmées à aucune ; **testé sur la machine le 04/10/2026** |
| [36-regulateur-sans-coupures-inutiles.md](36-regulateur-sans-coupures-inutiles.md) | **Moins de notes coupées, plus léger** (« avec 6 pistes actives, la dernière est souvent coupée ») : le régulateur réagissait à des blocs isolés déjà passés et choisissait la voix la plus faible avant le mixeur ; sa règle de charge soutenue n'agissait jamais (arrondi de la moyenne lente) ; nouvelle règle (pic qui dure deux blocs, charge soutenue = la plus basse des deux moyennes, voix qui viennent de partir comptées, voix la moins audible dans le mix, la plus ancienne à égalité), réécrite en assembleur à la place du code compilé (sans GCC 16.2) ; suivi des voix plus léger avec Model-TG, division des pistes par 2 plus courte dans la boucle des voix de l'OS ; profil de la boucle des voix en émulation |
| [37-flash-rapide-usb.md](37-flash-rapide-usb.md) | **Flash rapide en USB** (remarque Reddit, Elektroid) : le protocole de mise à jour d'Elektron Transfer dans le flasher web (trame `F0 00 20 3C 10 00`, empaquetage 7 bits, départ `50`, blocs `51` de 2 Ko avec CRC, chaque bloc acquitté) ; environ une minute au lieu de 5 à 10 ; la page demande qui répond et refuse une machine qui répond Model:Samples ; méthode classique en secours, `.syx` à glisser dans Transfer ; vérifié octet pour octet contre le C d'Elektroid et face à un faux Model:Cycles ; **testé sur la machine le 04/10/2026 (33 s, confirmation YES/NO)** |
| [38-tempo-546-bpm.md](38-tempo-546-bpm.md) | **Tempo au-delà de 300 BPM** : tempo en 1/120 de BPM, enregistré sur 16 bits dans le projet, d'où le plafond de **546 BPM** sans changer le format ; heure musicale du séquenceur sur 32 bits (jusqu'à 3 750 BPM) ; les six bornes et les deux contrôles au chargement (qui remettent 120 BPM) relevés ; le LFO synchronisé sortait de son cycle au-delà de 351,6 BPM, remise dans le cycle en boucle ; tweak `tempo-max` sans place libre, prouvé en émulation sur le vrai code ; **testé sur la machine le 04/10/2026** |
| [39-animation-demarrage.md](39-animation-demarrage.md) | **Animation de démarrage « modded-cycles »** (demande de Maxime, logo du site) : l'OS joue déjà une animation (tâche `0x40053a6c`, 80 images de 20 ms, carreaux au hasard) pendant le chargement du projet ; écran ST7565 sur le DSPI1, double tampon colonne par colonne ; le corps de la tâche est réécrit à sa place en assembleur (690 o, aucune place libre) : les quatre carrés du logo, l'accent creusé, puis « modded-cycles » ; même durée, même fin ; prouvé en émulation avec le vrai code de l'écran, image par image ; **l'OS compte les lignes de l'écran depuis le bas** : 1ᵉʳ essai sur la machine à l'envers, corrigé ; **testé sur la machine le 05/10/2026** |
| [44-volume-pan-en-chiffres.md](44-volume-pan-en-chiffres.md) | **Volume et pan en chiffres** : LEVEL/DATA affiche le volume ou, avec FUNC, le pan sur l'écran principal ; valeurs 0–127 et −64 à 63, pas d'un cran ; masque de sprite libéré ; repris de 18nelli18, testé sur machine en amont ([PR #53](https://github.com/18nelli18/Modded-Cycles/pull/53)) |
| [45-trigless-trigs-attenues.md](45-trigless-trigs-attenues.md) | **Trigless trigs atténués** : LED de pas à 33 %, clignotement conservé par le balayage de panneau à 1 kHz ; trigs de note et lecture inchangés ; repris de 18nelli18, testé sur machine en amont ([PR #53](https://github.com/18nelli18/Modded-Cycles/pull/53)) |
| [40-navigateur-multiligne.md](40-navigateur-multiligne.md) | **Navigateur sur plusieurs lignes** : trois presets, repères du curseur, du son chargé et des dossiers ; fonction adaptée du flasher de 18nelli18 et de l’idée d’un membre de la communauté |
| [41-os-cycles-sur-samples.md](41-os-cycles-sur-samples.md) | **L'OS Cycles sur un Model:Samples, retour par USB** (Maxime) : une mise à jour USB n'est vérifiée que par l'OS qui tourne, le bootstrap démarre le conteneur écrit en `0x20000` sans contrôle (la « porte 2 » de 15 §3.4bis n'existe pas) ; l'aller passe tel quel (conteneur Samples, MAIN OS Cycles) ; le retour butait sur l'OS Cycles, qui n'accepte que la clé Cycles ; sa vérification de l'OS Cycles (`0x4005a0e4` → HMAC `0x40052750`) ne dépend du modèle que par sa constante de clé de 32 octets (`0x401296b2`, une seule référence), recalculée pour donner la clé Samples ; l'OS Samples officiel repasse alors par USB, dans le transport SysEx du Cycles ; deux choix expérimentaux dans l'onglet Samples OS ; prouvé en émulation sur les vérifications des deux OS et le chargeur du bootstrap Samples |
| [43-machine-macro.md](43-machine-macro.md) | **Machine MACRO : les 47 modèles de Braids** (demande Discord « Mutable Instruments engines », 5 votes ; « Braids d'abord », choix de Maxime) : Plaits calcule en flottant, le ColdFire n'a pas de FPU, Braids est en entiers et tourne tel quel ; une machine ajoutée (7e, 8e avec Model-TG) dont SHAPE choisit le modèle, code de Braids (MIT, Émilie Gillet) compilé sans modification ; rendu à 96 kHz, filtre demi-bande de 23 coefficients vers 48 kHz ; chaîne d'ampli de TONE ; voix muette non calculée ; charge utile tassée de 103 Ko ; identique à Braids sur ordinateur, échantillon par échantillon, en émulation ; pas de régulateur de charge ; compatible avec les moteurs du Syntakt dans les builds combinés ([51](51-macro-avec-moteurs-syntakt.md)) ; **testé sur la machine le 07/10/2026** |
| [46-ecoute-des-samples.md](46-ecoute-des-samples.md) | **Écouter les samples dans le navigateur, avec le Sampler de Model-TG** (Discord, 6 votes) : l'OS désigne le preset sous le curseur et la note suivante du pad le joue ; un fichier de sample échoue au contrôle de taille, et même désigné, l'OS efface le pointeur du son avant que `sp_lock` le lise ; tweak `sample-preview` à part, qui exige Model-TG (ses builds ne changent pas) : trois accroches en assembleur dans quatre masques 47×47 (copie du son de la piste nommée « SMP » + empreinte, chargement au premier appui en `pd_mode` 1 sans chasser un sample du projet, silence s'il ne se charge pas, copie du son écouté pour `sp_lock`) ; carte du flasher avec `requires` ; prouvé en émulation du navigateur à la vraie boucle des voix (84 vérifications, 168 avec les deux versions) ; **testé sur la machine le 07/10/2026** |
| [49-verification-mod-par-mod.md](49-verification-mod-par-mod.md) | **Vérifier le flasher mod par mod, pas combinaison par combinaison** (question de Maxime : « à chaque mod, je génère toutes les combinaisons ? ») : aucun firmware n'est stocké, mais `REF_MAINOS` listait les 10 559 combinaisons (90 % de `app.js`) et doublait à chaque carte ; remplacé par `check_overlaps.py` (sans firmware : deux mods installables ensemble n'écrivent jamais aux mêmes octets, sauf écriture identique ou mod posé par-dessus l'autre ; charges utiles enchaînées), `REF_MODS` (empreinte des écritures et de la charge utile de chaque tweak, vérifiée par la page à chaque build) et un échantillon de 464 combinaisons (seules, paires, plus grandes) ; mêmes firmwares octet pour octet, les 9 215 de la version précédente reconstruites dans la page ; `app.js` de 1,56 Mo à 203 Ko ; étape 1 d'un chemin vers des mods modulaires et des mods perso |
| [50-midi-out-thru.md](50-midi-out-thru.md) | **MIDI OUT avec THRU + bascule FUNC/appui** : variante de secours THR=BTH **testée sur machine** ; bascule cachée publiée sur le flasher test, **expérimentale, non vérifiée sur matériel** après les gels des essais précédents |
| [51-macro-avec-moteurs-syntakt.md](51-macro-avec-moteurs-syntakt.md) | **MACRO avec les moteurs du Syntakt** : versions combinées pour chaque choix des moteurs, MACRO en dernier ; Model-TG reste avant les moteurs ; charge utile compressée et décompressée au démarrage ; combinaison Model-TG + cinq moteurs testée sur un Model:Cycles, autres choix expérimentaux ([PR #70](https://github.com/18nelli18/Modded-Cycles/pull/70)) |
| [30-regulateur-charge-soutenue.md](30-regulateur-charge-soutenue.md) | **Régulateur : couper sur la charge soutenue** : relevé v8 en 6 canaux (91/71, dernière piste toujours coupée) ; le régulateur réagissait aux moments denses (5 ms) et aux blocs au-dessus de 90 % ; nouvelle règle : moyenne lente (170 ms) à 86 %, pic à 93 % (retour sous 89 %), voix du Syntakt plus comptées pour moitié ; diagnostic v9 |
| [29-voix-syntakt-en-sram.md](29-voix-syntakt-en-sram.md) | **Les états des voix du Syntakt en SRAM** : relevés v7 (une voix du Syntakt coûte autant qu'une voix d'origine ; 6 pistes ≈ 88 %, coupures de temps en temps) ; les 6 états de voix (1 800 o) passent en SRAM ; modèle : −3 points de bloc ; diagnostic v8 (pic/moyenne) |
| [28-code-syntakt-en-sram.md](28-code-syntakt-en-sram.md) | **Le code du Syntakt en SRAM** : relevés du diagnostic v6 (chaque voix du Syntakt ajoute 9 à 13 points, l'interface reste fluide) ; les 30 tables d'ondes de CHORD passent dans la charge utile, leur place en SRAM reçoit le code du Syntakt et 3 de ses tables ; régulateur à 86 % ; identique en émulation ; modèle : boucle des voix de 63,5 à 52 % avec 5 moteurs différents ; diagnostic v7 |
| [27-cinq-et-six-voix.md](27-cinq-et-six-voix.md) | **Tenir 5 et 6 voix du Syntakt** : pourquoi les notes sont coupées dès la 5ᵉ voix (régulateur à 82 % de moyenne) ; le code est devenu le premier coût (cache d'instructions de 8 Ko) ; pistes chiffrées (seuils, même moteur sur des pistes voisines, code du Syntakt en SRAM à la place des tables d'ondes de CHORD, effets) ; diagnostic v6 : coût de chaque voix sur la machine |
| [26-sram-empruntee.md](26-sram-empruntee.md) | **Voix du Syntakt moins chères** : cache de données de 8 Ko seulement ; leurs tampons de travail passent dans la zone de travail des machines d'origine en SRAM interne, leur table de sinus est lue dans celle du Cycles (identique) ; −35 à −63 % de lignes de données en SDRAM par voix, son identique en émulation |
| [16-moteur-syntakt.md](16-moteur-syntakt.md) | **Moteur audio du Syntakt** : 2e ColdFire, boucle des voix identique au Cycles, les 6 machines du Cycles dans le Syntakt, vrai SD VINTAGE émulé, **notre SD VINTAGE v2 recalé dessus** ; OS 1.42 = même section 7 que 1.41 |
| [15-demandes-reddit.md](15-demandes-reddit.md) | **Demandes de la communauté (Reddit)** : mute verrouillé et écoute d'un pas (tweaks drumkilla, livrés), OS Model:Samples / machine « samples » et machines du Syntakt (plans de recherche) |
| [21-architecture-materielle.md](21-architecture-materielle.md) | **Architecture matérielle, d'après les photos du PCB** : CPU MCF54415CMJ250, DDR2 128 Mo, flash SPI 2 Mo, eMMC 4 Go, PHY USB3300, DRV632, optocoupleurs MIDI, verrous des touches et des LED ; recoupement avec les périphériques que le firmware adresse (`tools/hw_periph_refs.py`) ; grille de debug, code « BOM » |

| [53-generateur-sequence.md](53-generateur-sequence.md) | **Générateur en gamme, SETTINGS + PAGE** : prototype Model-TG, notes/trigs sur la piste courante, bornes et densité, Undo ; 17 masques, PLAY/STOP dans le menu, velocity/decay/pan optionnels et Undo complet ; **testé sur machine par AveyCole le 10/10/2026, flasher principal 1.45** |

## Chiffres clés (OS 1.13)

| Élément | Model:Cycles | Model:Samples |
|---|---|---|
| Device id SysEx | `0x11` | `0x0F` |
| SHA-256 du `.syx` officiel | `44fe5862…9800640c` | `e11859b6…398a2ce8` |
| SHA-256 section 3 d'origine | `cc99d4f0…ee98` | `a351392c…1ab2` |
| SHA-256 section 3 patchée | `65e24b50…9555` | `321b2ea6…1a69` |
| SHA-256 du `.syx` construit | `9c631bc2…22f6` (`mc-multi-output.syx`) | `9ab32674…0169` |
| Nombre de runs de patch | 29 | 41 (diff minimal, même sémantique) |
| Blocs audio par piste (`TRACK_BASE`) | `0x80001858` | `0x80001b48` |
| Variable « base de la case courante du ring » (`SLOT_BASE`) | `0x404a05e8` | `0x404af45c` |
| Stubs (prime / token / tracks / dstoff) | `0x4019b136` / `0x4019b182` / `0x4019b1e0` / `0x4019b244` | `0x401a0144` / `0x401a0190` / `0x401a01ec` / `0x401a0250` |
| Hooks dans le pilote USB | identiques : `0x400027e8`, `0x40002a42`, `0x40002a06`, `0x400029e4` | idem |
| Conversion offset ↔ VA (section 3) | `VA = offset + 0x40000400` | idem |
| Moteur de synthèse : boucle des 6 voix / tables `update` et `render` des machines | `0x400a7d4a` / `0x40118628` et `0x40118610` | non analysé |
| Descripteurs de paramètres (entrées de `0x38` o) | `0x4010dce0` | non analysé |
| Écran 128 × 64 : tampon de dessin, envoi des blocs changés, repère des `Bitmap` | `*0x401492f0`, `0x4008e622` ; **y = 0 en bas**, x = 0 à gauche ([39 §2](39-animation-demarrage.md)) | non analysé |

Générateur de séquence (note 53) : **testé sur la machine par AveyCole le 10/10/2026**, disponible dans le flasher principal.

| Note | Résultat |
|---|---|
| [54 — Générateur étendu](54-generateur-etendu.md) | **Expérimental** : plages, modes, mutation, Euclid, son indépendant, mutes et cartouche ; preuves émulation, matériel à tester. |
| [55 — SCRAMBLE indépendant](55-scramble.md) | **Testé sur machine par AveyCole le 11/10/2026, principal** : SETTINGS + TRACK, quatre paramètres seuls, sans menu ; SCRAMBLE par pas également testé, valeurs fraîches à chaque passage ; setter natif et combinaison maximale vérifiés en émulation. |
| [56 — Génération différée](56-generation-differee.md) | **Expérimental** : staging privé, commit avant le premier trig, sous-option distincte ; correctif local des modes commun/par piste et banque de lecture prouvé en émulation, sans chaîne. |
| [57 — Séquences MIDI secondaires](57-pistes-midi-secondaires.md) | **Test expérimental avec TG** : six voies MIDI, éditeur, hooks et consommateur dédié prouvés en émulation ; installateur séparé. Banque RAM partagée entre patterns ; sauvegarde et sorties physiques à valider. |
| [58 — Second LFO](58-second-lfo.md) | **LFO 2 testé sur machine par AveyCole le 11/10/2026, flasher principal** : rendu de menu natif, phases indépendantes, mélange et publication audio prouvés ; 33 masques sans chevauchement des mods principaux. Réglages RAM seulement ; sauvegarde et coût audio matériel restent à établir. |
| [74-tempo-global-b.md](74-tempo-global-b.md) | **TEMPO global natif depuis B** : touche14 transmise, menu conservant B, garde du combo à l’accueil ; preuves natives et transfert navigateur validés, test matériel attendu. |

- [42 — Clavier d’accords diatoniques](42-clavier-accords-diatoniques.md) — upstream 1.46.
- [47 — Filtre de piste](47-filtre-piste.md) — upstream 1.46.
- [53 — MIDI THRU AveyCole](53-midi-thru-aveycole.md) — déplacement compatible du code MIDI.
- [55 — MACRO allégée et lo-fi](55-macro-allegee-et-lofi.md) — upstream 1.46.

- [59 — Commandes banque MIDI](59-commandes-banque-midi.md) — mute MIDI validé sur matériel ; candidat Genie B, undo différé et affichage TR10–TR12, sauvegarde persistante en préparation.

- [62 — Sauvegarde des LFO audio et MIDI](62-sauvegarde-lfs-ab.md) — format MBK3 par pattern ; émulation validée, matériel à tester.
- [63 — Reprise automatique MIDI et LFO](63-reprise-automatique-midi-lfo.md) — checkpoints WRK séparés du Save explicite SEQ ; candidat expérimental sur Test3.

- [64 — Enregistrement live B](64-enregistrement-live-b.md) : RECORD + PLAY, quantification native, microtiming MBK4 ; expérimental.

- [65 — Noyau performance autonome](65-noyau-performance-autonome.md) — extraction slide/Scale Lock sans sampler, bundle MIDI complet sans Model-TG ; quatre blocs réservés, boot/cache/audio, sauvegarde simulée et dix-sept builds navigateur.

## Intégration Supermodel du 13/10/2026

| Note | Résumé |
|---|---|
| [75 — ChordKeys et TG dans Supermodel](75-chord-tg-supermodel.md) | Intégration expérimentale PR87 / roterodamus, HARMONY26 isolé de LFO2, banque RAM et espace récupéré sans sauvegarde B. |


| [76-trigs-frais-et-copies-lfo.md](76-trigs-frais-et-copies-lfo.md) | **Pas frais A/B et copies LFO2 allégées** : locks/SCRAMBLE retirés à la suppression, douze CC B effacés,476 instructions/bloc en moins avec paramètres/phases identiques ; test séparé, matériel à vérifier |


- [77 — Control All Config dans le test Supermodel](77-control-all-config-supermodel.md)

- [78 — Machines facultatives avec Banque MIDI](78-machines-facultatives-banque-midi.md)

- [79 — ChordKeys indépendant](79-chordkeys-independant-prototype.md) — chargeurs autonomes, TG/machines facultatifs, un bloc cache sans TG ; neuf builds et boot/cache/audio prouvés en émulation. Test matériel attendu, main inchangé.

- [80 — Banque MIDI, supports facultatifs](80-banque-midi-support-facultatif.md) — 32 backends TG/Genie/LFO2/SCRAMBLE/Chord, noyau sans sampler, RAM seulement ; démarrage/clavier/scheduler prouvés en émulation, page de test indépendante. Test matériel attendu.

| [96 — RETROSYN](96-retrosyn.md) | Six oscillateurs retro ; TINY/WAVE conserves ; Sample Wizard facultatif ; Model-TG interdit au main. Experimental, preuves emulation et navigateur. | **RETROSYN teste sur machine par AveyCole le 16/10/2026 ; publie au principal.**

| [97 — Banque MIDI autonome actuelle](97-banque-midi-actuelle.md) | Seule ou avec RETROSYN/TINY/Wizard facultatif ; 21 builds et boots, clavier, locks/slides, Genie/Undo et scheduler en emulation. **Teste sur machine par AveyCole le 16/10/2026 ; publie au principal.** |

| [98 — Persistance MIDI actuelle](98-persistance-midi-actuelle.md) | MPI1, copies A/B par pattern, noyau autonome actuel. **Sauvegarde sur slot vide et reprise confirmees sur machine par AveyCole le 16/10/2026 ; promu au principal.** MIDI sauvegarde charge uniquement en entrant cote B, lecture arretee. |
| [99 — Beat repeat collectif](99-beat-repeat-collectif.md) | Carte autonome **testee sur la machine par AveyCole le 16/10/2026** : TRACK + RETRIG maintenus, TRIG choisit la division ; six pistes et cotes stereo Wizard, sans page ni FX master ajoutes. Preuves ColdFire ; principal 1.73 identique au candidat 2. |

| [100 — Feedback performance](100-feedback-performance.md) | Candidat experimental : popup bref des divisions beat repeat, LEDs mute B selon FUNC sans selection ; principal inchange. |

| [102 — Precision du filtre](102-precision-filtre.md) | Ladder EMAC ; **correction piste 6 confirmee sur machine par AveyCole le 16/10/2026, promue au principal 1.75.** |

| [103 — Timing Genie](103-genie-timing.md) | **Teste sur machine par AveyCole le 16/10/2026, promu au principal 1.76** : callback A/B Queue Loop/Page, frontiere MIDI partagee. |

| [104 — Capacite sans MIDI](104-capacite-sans-midi.md) | Principal 1.77 a la demande AveyCole : compression commune Wizard/moteurs, complet sans Banque MIDI avec beat repeat, environ 46 Ko de marge ; Banque MIDI experimentale, filtre en charge encore ouvert. |

| [105 — Charge filtre](105-charge-filtre.md) | Candidat : checks redondants retires, samples/etats identiques ; 22–36 % d instructions filtre en moins (candidat 2) ; test 4 confirme sur machine par AveyCole, promu 1.78 ; repeat actif -37 %, combo seul -77 % en instructions emulees. |

| [107 — Swarm LITE principal](107-swarm-lite-principal.md) | Principal 1.79 : trois oscillateurs remplacent sept a la demande AveyCole ; nette baisse de charge/clicks sur machine, son plus fin/niveau parfois reduit ; filtre/repeat/regulateur inchanges. |

| [108 — 909 modules actuels](108-909-modules-actuels.md) | Test 909 : Sample Wizard remplace Model-TG ; modules MIDI/Genie actuels et beat repeat, quatre WAV locaux. Nouvelle combinaison experimentale. Lien 909 prominent dans main. |

- [109 — Repeat MIDI et filtre Control All depuis B](109-midi-performance.md) : dernieres notes B, Off reserves, filtre audio + CC74/71 ; test experimental.

- [113 — Sauvegarde rapide stock](113-sauvegarde-rapide-stock.md) : test separe de FUNCTION+SETTINGS maintenu ; natif restaure, permanence hardware a confirmer.

- [114 — Premiere ouverture MIDI pendant lecture](114-premiere-ouverture-midi.md) : gate de contexte paresseux, test separe, diagnostics conserves.

- [115 — Phase et curseur MIDI B](115-curseur-midi-partage.md) : un curseur REC, phase initiale native, longueurs et vitesses propres ; test uniquement.

- [116 — Arpege Oct0 A/B](116-arpege-octave-zero.md) : notes tenues seules, octaves ajoutees0..3, sauvegardes et sons historiques conserves ; test uniquement.

- [117 — 909, fonctions partagees](117-909-fonctions-partagees.md) : filtre, sauvegarde et arpege/curseur MIDI main1.83 ; profil909 et WAV locaux conserves, sans diagnostic.

- [118 — Combinaisons machines](118-combinaisons-machines.md) : TINY/RETROSYN avec tous les sous-ensembles, Wizard facultatif ; combinaison signalee confirmee sur machine le 17/10/2026, catalogue verifie en emulation, aucun diagnostic principal.

- [119 — MACRO lo-fi, port test](119-macro-lofi-port.md) : correction 18nelli18 FUNC + PITCH, pas/texte/dessin amont, machines au choix ; principal1.86 sans diagnostic ; copie test conservee.
