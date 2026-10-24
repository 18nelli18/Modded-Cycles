# 167 — FX par pattern et niveau WAVE

Demande AveyCole du24/10/2026 : garder types FX et reglages ajoutes par pattern, defauts sur pattern vierge, augmenter WAVE. Adresses : VA OS1.13. Recette `tools/gen_governor_recovery_test.py --fx-pattern`, module `tools/fx_project_assets.py`, preuves `tools/emu/test_fx_pattern121.py` et `test_fx_startup_guard.py`.

## 1. Stockage et activation

[FAIT] Le codec natif pattern v4 ecrit14848octets. Les48derniers, offset0x39d0, ne sont pas lus/ecrits par les copies natives. Record FXS1 : magic4,version1,count36,reserve2,36valeurs,CRC32sur44octets. Taille native de projet et codecs natifs conserves. Aucun fichier annexe. Header FXP1 au padding0x1c0 passe en version2 avec marque PAT1 ; anciens projets v1 acceptes, anciens fichiers sans record donnent les defauts.

36champs : types reverb/delay, Chorus speed/depth, Vinyl crackle/warble/speed, sends6pistes Chorus/Vinyl/Crush, rate/bits, Duck amount/release, Ring freq/depth, Phaser rate/depth/feedback, Gated time/predelay. Les parametres natifs restent dans les codecs natifs.

[FAIT] Detour a40055c5c sur la publication reelle du pattern actif40a7887c : sauvegarde36valeurs precedentes et restauration ou defauts du nouveau pattern. Requetes queues40055cd6 ne changent pas les FX avant publication. IRQ : copies RAM bornees seulement, aucun CRC, fichier, allocateur ou popup. Registres et SR preserves. Copies30710octets RawPattern transportent le record via banque et8clips temporaires. Initialisation d un pattern efface son record.

Code4684b000, fin avant4684f000. BSS121468bd000..468c0000, apres RETROSYN468bc168 et avant anneau Gated468c0000. Assertions tailles a chaque construction. Lecture volatile du singleton40fe4228, jamais getter constructeur400cf866 : correction120 conservee.

Longueur native d initialisation40195ad8 etendue de0x110e08 a0x114810 pour inclure la nouvelle BSS jusqu a468bfb70 ; le bootstrap natif efface bien cette zone. L audit byte a byte autorise uniquement cette longueur et les detours decrits ; les renderers machines/FX, IRQ audio, USB et recovery sont preserves.

## 2. WAVE

Seul rendu WAVE467796fc est enveloppe : doublement saturant des32echantillons, avant filtre de piste. +6,0206dB. Oscillateur/table, import et table initiale inchanges. Pas de traitement flottant ni nouveau tampon audio. Crediter le moteur WAVE/convertisseur existant de Kevin-Shallvari/Modded-Cycles, MIT, comme note165.

## 3. Validation et publication

[FAIT en emulation] Vrai bootstrap, vraie publication native A/B/slot95,36champs et sends independants, defauts vierges, requete queue, codecs projet complets, CRC invalide isole, copie clipboard, initialisation, codecs pattern seul, vrais SaveProject4000f762 et CacheLoad4006a5a0. Backend disque/cache simule ; pas de stockage physique simule comme resultat appareil. Getter startup teste sans reentrance.

[FAIT materiel rapporte] AveyCole : «121 worked push to main». Publication2.38 autorisee pour les octets reguliers121 exacts. Ceci rapporte son essai, pas un test physique exhaustif realise par l agent. Version adulte privee. Aucune modification de laboratoire posterieure au121 approuve.

SHA256 SysEx `8c2ed40ff1687dfa9ecaace5234b902133db1df45bb266d94f0ecfa0b5d4c834`, MAIN `cb9b7745abb1b349ed42ea0183a1c1713927d7ff9ab858e6850df7726ba3f296`.
