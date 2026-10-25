# 169 — Sidechain et listes Scramble par pattern

Demande AveyCole du24/10/2026 : sidechain par declenchement, cinq cases cibles par source, Depth/Attack/Hold/Release ; listes Scramble propres au pattern. Nom UI Sidechain, distinct du delay DUCK, titre Side / Chain. Recette `gen_governor_recovery_test.py --sidechain`, sources originales `tools/machines/sidechain`, preuves `test_sidechain122.py`, `test_sidechain_ui122.py`. Adresses : VA OS1.13.

## 1. Hooks et audio

[FAIT] Filtre arp a40058e28 : notification des notes arrivees a echeance, apres suppression arp et avant masque mute natif. Le constructeur SCRAMBLE40054c0e est volontairement inchange : il precede la file temporelle et ne doit pas produire de pulse anticipe. Notes off, SRC=-1 et locks trigless ignores. Wrapper400a7d4a recoit aussi les masques de declenchement reels, preserve registres et SR avant trampoline. Br_gain_hook appelle du_audio, qui conserve br_audio puis applique le gain avant gain/pan/envois natifs.

Six enveloppes Q16 par source, 1500blocs/s. Depth16niveaux, Attack8presets0..160ms, Hold4presets0..120ms, Release16presets10..3000ms. Chaque cible prend le minimum des gains sources ; pas de multiplication cumulative. Rampe32echantillons identique mid/side ; source non ciblee par elle-meme. Aucun float, EMAC, allocation, fichier ou attente dans ce chemin.

## 2. RAM et stockage

[FAIT] Code Sidechain46833000..46835000, BSS46835000..46836000. Etat pattern46836000..46840000, apres code chaud FX46832f78 et avant Fundamentals46840000. Le ring GATED occupe468c0000..46900000 : une premiere reservation468d0000 a ete rejetee avant livraison, deplacement et assertions interdisent tout recouvrement. WAVE commence46900000. Boot et clear natifs verifies.

F2 : tailles natives inchangees.48octets finaux a0x39d0 plus6octets libres d en-tete0x3990+[29,30,31,36,37,39]. Identite2octets, CRC24sur49octets,387bits utiles. FX36champs243bits, Scramble6x6bits, Sidechain6x18bits. Masque5cibles sans soi5bits, profondeur4, attack3,hold2,release4. Les autres octets natifs et ChordKeys32..35/40..63 restent exacts. Aucune donnee dans les trous de locks qui se remplissent avec un pattern dense.

Etat actif72octets : FX36, Scramble6, routage/reglages30. Publication reelle40055c5c, SaveProject et codecs natifs. Ancien record FXS1 du121 accepte ; nouveaux F2 ne sont pas compris par121. Compatibilite de lecture vers l avant uniquement, guide indique conserver une copie avant downgrade. CRC invalide : defauts du seul pattern concerne. Listes globales /Scramble.cfg ignorees dans122 uniquement. Defauts60 pour six listes, routes0, depth60%,attack0,hold0,release150ms.

## 3. Preuves et retour appareil

[FAIT en emulation] Boot,72valeurs A/B/95, nouveaux patterns, activation queuee, metadata/ChordKeys gardes, codecs projet/pattern, copy/clear, CRC isole, SaveProject/CacheLoad et nouveau processus pour restauration. Ancien121 accepte. Startup sans getter constructeur. ABI voix/SR preservee, pas de pulse au constructeur, note-off/trigless exclus. Mid/side identiques, cibles seulement, rampe et retour unite. Bypass du_process9instructions ; cas six sources/six pistes stereo7021instructions emulees, pas un pourcentage CPU materiel. Menus natifs et largeurs de police verifies, DATA/BACK/limites et cinq cibles pour les six sources. Lecture disque/cache simulee dans les preuves, pas de revendication de test physique par l agent.

[FAIT rapporte par AveyCole] «122 worked, push that to main.» Autorise promotion2.39 du fichier regulier exact. Lexique adulte prive. Blurb fourni byte-identique. Le test utilisateur ne signifie pas mesure exhaustive du CPU ni validation physique de toute combinaison de routage.

SHA256 SysEx `7d2d564cc1cf34c585ec2bad3134531197d97d2136ef57cab73ca53d31172db0` ; MAIN `196f12214a3d382cfc037e5d933e17c4ffdb74171b177cf18453445a1e889a07`.

Controles generaux : check_overlaps passe. gen_flasher_tweaks --check et registry --check signalent des sorties deja obsoletes ; leurs generateurs, donnees JSON et sorties restent inchanges dans cette promotion. Test Chromium : vraie validation image et reconstruction fixe exactes, importeurs, lexique public, guide EN/FR/mobile et blurb preserve, aucun MIDI physique envoye. Guide PDF9pages rendu et inspecte.
