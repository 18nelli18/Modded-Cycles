# 166 — Types et reglages FX par projet

Demande AveyCole du24/10/2026 : memoriser les types et reglages ajoutes au projet, revenir aux effets standard sur projet neuf. Tests prives116..118, shared filter, regular/adult. Main reste115/2.37. Adresses : VA de l OS1.13.

## 1. Format et espace

[FAIT] Le codec projet4005d18a produit la version6 : magicBEEFBACE, version6, nom16octets+8, UUID+24, patterns a+0x200. Le decodeur4005d3dc ignore le padding+0x1c..0x1ff. La longueur native complete reste0x210404, fenceBACEF00C a0x210400. FXP1 utilise64octets a+0x1c0, sans modifier les patterns/kits ni allonger le fichier.

FXP1 : magic4, version1octet, nombre36, deux zeros,36valeurs,16zeros, CRC32BE des60premiers octets. Validation type dans les ordres actuels, valeurs0..127, bits crusher2..16, reserved zero et CRC. Record absent/invalide => defauts compiles. Les anciens projets ne peuvent pas inventer une selection historique jamais enregistree : configurer et sauvegarder une fois.

36champs : type reverb, Chorus vitesse/profondeur, Vinyl crackle/warble/vitesse,6sends chorus,6sends Vinyl, type delay, crusher rate/bits,6sends crusher, Duck amount/release, Ring freq/depth, Phaser rate/depth/feedback, Gated time/predelay. Les parametres natifs restent aux codecs natifs.

## 2. Cycle de vie

Encode/decode detournes par trampolines rejouant leurs8octets initiaux. Seul encode reussi, en-tete complet bit16, projet connu => ecriture record. Decode reussi prepare36valeurs pour le RawProject cible ; aucun effet d un decode echoue. L entree NewProject4000f906 appelle RawProject::init40061738 puis prepare les defauts. La synchronisation UI n applique les valeurs qu au RawProject actif (singleton400cf866, getter vtable+40). Aucun UUID utilise comme evenement : Load et SaveAs le renouvellent.

Le service UI maintient les flags historiques et sauvegardes globales, mais ne les laisse plus remplacer les champs du projet. Aucun nouveau fichier annexe, allocation ni appel dans l IRQ. Owner/pending+candidate :44octets BSS4684f000. Code4684b000, fin strictement avant4684f000 ; reservation stricte avant46850000, WAVE sous4684b000 et LEGACY a46850000. Assertions trous/prologues/fins a chaque build.

## 3. Retour appareil117 et correction118

[FAIT materiel rapporte] AveyCole : charger un nouveau projet117 garde les effets du precedent. Les preuves116/117 appelaient directement fxp_sync et ont manque le chemin reel UI.

[FAIT] GCC13.1 a decompose fx_service : symbole public468036f4, corps fx_service.part.0 a46802756. fx_draw468047a2 integre la garde transport et appelle directement part.0 a468047e8.117 detournait seulement le symbole public inutilise par ce chemin.

118 detourne l entree reelle fx_draw (sync avant tout dessin, meme transport actif) et le corps part.0 (protection contre config globale). Les symboles proviennent de nm, tailles d instructions via Capstone. Trampolines : draw6octets link/pushD2, service8octets link/movem, codecs8octets lea/movem. Pas de cible dans padding.

## 4. Preuves et limites

tools/emu/test_fx_project.py : bootstrap natif puis vrai RawProject init, codecs complets, vrais SaveProject4000f762 et LoadProjectCache4006a5a0. Backend cache/disque, objet projet et delegate dessin simules. Aucun codec simule.118 appelle le vrai fx_draw a chaque chargement au lieu du helper : cette preuve echoue sur117 (record FX absent au Save) et passe sur118. Cas transport actif, nouveau projet, anciens records, CRC/version/type invalides,36champs,6pistes sends, SaveAs, export projet non actif, sauvegarde echouee, conversion partielle et nouvelle instance emulateur avec seulement le fichier sauve.

[FAIT en emulation] Le fichier natif differe seulement dans64octets padding. Les renderers machines/FX, IRQ audio, USB et recovery sont identiques a115 ; seules entrees codec/NewProject/UI et nouveau module changent.

[A FAIRE] Verification physique118 : default nouveau projet, A/B types et knobs distincts, SaveAs, reboot, six-track sends, effets non standards et sauvegarde native normale. Les preuves ne garantissent pas le stockage physique. Pas de promotion avant retour appareil.

## 5. Retour118 et correction119

[FAIT materiel rapporte] AveyCole : « still stays the same in118 ».118 ne prouvait pas le dispatch de fx_draw depuis toutes les vues : le banc l appelait directement. L explication117 ne suffit donc pas a etablir la cause physique restante.

119 ne depend plus d un dessin pour terminer la transition : fxp_decode applique immediatement au RawProject actif apres retour reussi du codec natif ; fxp_new applique les defauts avant de rendre la main a NewProject. Un Save actif capture les36champs meme si aucun dessin ne les a encore declares proprietaires. Les exports/decodes non actifs gardent leur record sans changer le son courant.

Le vrai frame commun ViewManager40076c1a entre dans fx_frame_begin. Son jsr, deja detourne vers bf_prepare par les corrections SY BITS, passe desormais par fxp_frame : sync puis bf_prepare, sans retirer LEGACY ni la correction bits. fxp_draw protege aussi tous les36champs autour de l ancien relais draw complet ; ce relais peut encore charger des fichiers globaux Chorus/Crush. Pas de popup dans les codecs ni d E/S ajoutee.

[FAIT en emulation] Le banc119 utilise le vrai getter Project400d3af6 (RawProject a self+16), teste Save avant tout dessin, verifie les champs juste au retour decode/NewProject/cacheLoad, et execute la vraie entree frame40076c1a jusqu a sa reprise40076c22 : pile, D0/D1/A0/A1, ancien service conserves. Une mutation simulee dans l ancien relais draw ne doit pas remplacer les champs du projet. L assertion Save sans dessin echoue sur118. Ces garanties ne sont pas une reproduction exacte du chemin manque sur appareil118.

[A FAIRE] Test appareil119 avant tout travail par pattern. AveyCole demande ensuite, si ce stockage fonctionne, les types et reglages FX par pattern avec application au debut du pattern effectivement lance, y compris changements queues. Aucun stockage par pattern ni automatisation des types n est ajoute dans119.

## 6.119 retire : initialisation recursive et120

[FAIT materiel rapporte] AveyCole : «119 bricked me», exception `v03m0p2430000`, volume et presque toutes les commandes vides, nom du pattern vide. Il est revenu sur118.119 retire, manifest/checklist/zip marques WITHDRAWN sans modifier les images conservees pour diagnostic. Aucune promotion publique.

[FAIT] Le getter400cf866 n est pas une simple lecture : si40fe4228 est nul, il alloue83436octets et appelle Project::Project4001134e, puis seulement publie le pointeur a400cf8d6. Un appel FX pendant ce constructeur peut reentrer le getter avant publication. Les preuves119 fournissaient toujours un singleton deja pret et masquaient ce cas.

[FAIT en emulation] reproduce_fx_startup119.py execute le vrai getter natif : fxp_sync119 construit le projet depuis une frame prematuree ; une callback pendant le constructeur provoque une deuxieme construction. Ceci reproduit un defaut concret de reentrance, pas le PC exact du crash appareil.

120 lit directement le slot volatile40fe4228 : nul => aucun acces ni construction ; non nul => getter RawProject du vtable. Aucun allocateur appele par le module. Les decodes/NewProject pendant la construction gardent leurs36valeurs en attente ; adoption seulement quand le projet est publie. Le Save pendant la construction encode le record en attente.

[FAIT en emulation] validate_fx_cold_start120.py execute le vrai getter/publish/release avec allocateur simule et corps constructeur remplace par une callback du vrai codec. Creation et restauration d un projet pendant la construction : aucune reentrance, seulement deux allocations normales83436+16, publication unique, champs FX inchanges avant publication, record en attente encode correctement puis adopte apres. Ce n est pas un boot integral de l application.

La preuve complete120 interdit tout appel du module au getter constructeur400cf866. Save/Load/cacheLoad/new/SaveAs/restart, anciens records, entree frame native et protection des anciennes preferences passent. Machine/FX DSP, IRQ audio, USB et recovery restent byte-identiques a115.120 reste experimental jusqu au retour appareil : verifier d abord nom du pattern/volume/commandes, puis sauvegarde FX. Pas de travail par pattern avant stockage projet fiable sur appareil.


## 7. Retour appareil120

AveyCole : «That worked. Let's make it save per pattern now». Autorise le travail par pattern apres confirmation de la correction120.121 est decrit dans la note167.
