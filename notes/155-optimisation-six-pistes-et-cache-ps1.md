# 155 — Optimisations six pistes et conflits de cache PS1

Demandes AveyCole du23/10/2026 dans cette conversation : continuer l optimisation avec P120 sur v73 (Shimmer, Kick/Snare/Metal/Perc/Swarm, piste6 muette), usage principalement USB2ch, puis clics PS1 et Vinyl avec six pistes sur v74. Priorite explicite : sauver PS1 et viser un cout inferieur a la reverb native. Generateur `tools/gen_governor_recovery_test.py`, sources `fx_menu/`, `delay_crush_send/`, `syntakt_cpu/`; preuves `tools/emu/test_ps1_cache.py`, `test_fx_idle.py`, `test_active_fx.py`, `test_fx_combo_cpu.py`. Adresses : VA de l OS1.13.

## Reponse courte

[FAIT rapporte sur appareil] v73/v74 ne suffisent pas : surcharge/clics avec PS1, Vinyl, Shimmer et six pistes. Aucun gain temporel materiel nouveau revendique. Principal2.29/v70 conserve, shared-filter seulement, CLOUD absent.

[FAIT en emulation] v76 conserve exactement les PCM et etats logiques PS1 de v75 sur8192blocs. Il espace de16octets les huit buffers comb, sans changer leur longueur2048 ni les indices/coefficients. Plus128octets BSS, dans les bornes existantes. Meme nombre d instructions executees. [HYP] Gain temporel reel par reduction des conflits de cache ; a mesurer en comparant le meme pattern et les compteurs A/P/O/N, notamment face a la reverb native.

## 1. v73/v74 : travail conserve

Shimmer1 : produits fractionnaires EMAC mathematiquement exacts ; wrapper sauvegarde les48bits ACC0, ACCext01 et MACSR, restauration verifiee dans64contextes. Recherche d alignement reutilise32echantillons references. Apres258blocs d entree quantifiee nulle, historique FIR/ring entierement vide : chemin leger qui avance phase/index, sans couper la diffusion de Shimmer2. Preuve1500blocs par mode +512continus, silence/reveil/reset et PCM/etats exacts.

Face a v72, Shimmer1 actif environ36% d instructions en moins, silence etabli92.6%; Shimmer2 silence64.3% en moins, actif continu surcout0.26% et phase calme avant vidage3.2%. Ce sont des instructions, pas des cycles.

Le resonateur Syntakt natif62octets en SRAM est reecrit sur place sans changer la recurrence, la saturation ni les registres rendus. Preuve288cas, puis192blocs avec les cinq moteurs et une composition Kick/Snare/Metal/Perc/Swarm/Tone. Gain noyau15%, gain voix complet modeste0.4..0.8%.

PS1 partage seulement le filtre d entree si les32paires sont identiques en16bits et leurs quatre etats egaux. Combs/reflexions/allpass stereo restent independants. `no-unswitch-loops` evite une duplication du noyau. Gain instructions mono6.69%, surcout stereo0.324% face a v73.

Aux Vinyl/Chorus et Both Crush/Delay : pas de copie mid/side quand toutes les sources sont mono ; bus stereo original conserve sinon. Somme L/R unique seulement quand pointeurs/gains presents/cibles sont identiques sur les6pistes. Copie exacte des gains de sortie. Sends/rampes/tails et quantification inchanges.

## 2. v75 : Vinyl actif et comparaisons figees

`--all-fx-opt --stage` : compile `dsp.c` O3 sans deroulage, autres politiques conservees. Vinyl actif512blocs exacts et -22.72% instructions noyau. Essai O3 crusher rejete (+2% instructions) ; le crusher final garde O2,640blocs et memes instructions que v73. Mixeur12cas x24blocs : sends90/127, pan64/21, source mono/stereo, extinction des sends a16blocs. PCM, gains et etats semantiques exacts face a v73. Les echantillons du test ne remplacent pas le pattern utilisateur.

v73 SHA256 `27d28414c9ace0e04cc3daae933d6b18e0b30db186fec0d730a29402759cf62a`.
v74 SHA256 `b683edcb39f91cf73fe3bc87cddeb9cfc7515d99e832df5aee5219bbd228312a`.
v75 staging SHA256 `bc725e60a5d9456df40ede24b8120b12e1ba483f5293d800ace9330f60025a83`.

Les numeros deja essayes ne sont plus remplaces. `--stage` prepare les nouveaux octets hors validation ; livraison par copie exacte apres preuves. Les images precedentes et le principal restent fixes.

## 3. v76 : conflit des huit combs PS1

[FAIT documentation] MCF5441x : caches I/D8Ko, quatre voies, lignes16octets et128sets. Source primaire : [NXP MCF54418RM, chapitre6](https://www.nxp.com/docs/en/reference-manual/MCF54418RM.pdf). Le cache DDR couvre `0x40000000..0x47ffffff` (notes17/23/26), donc aussi code et BSS des effets.

Ancienne declaration `s16 ps_comb[2][4][2048]` : pas4096octets entre lignes de delay, qui donne le meme index cache modulo2048 pour les huit positions d ecriture courantes. Huit tags se disputent quatre voies, meme avant les voix et l interface. Ce probleme ne se voit pas dans un simple comptage d instructions.

Sous `FX_PS1_CACHE_OPT`, pas2056echantillons =4112octets. Les huit positions courantes utilisent huit sets successifs. La longueur acoustique et le masque restent2048/2047 ; les16octets ajoutes par ligne sont inutilises, verifies par canaries. Nouveau `--ps1-cache-opt` implique v75, cree v76 et enregistre `ps1_comb_stride=2056`. Le fallback compile exactement les anciennes compositions.

[FAIT modele] Trace d acces PS1 apres160blocs,16blocs observes, cache LRU idealise8Ko/4voies/16o, donnees PS1 seulement : memes7024acces,2453->637misses,1975->178evictions sales. LRU est un modele de comparaison, pas le remplacement materiel exact ni une estimation de cycles. Le vrai mixeur six pistes (`test_ps1_cache_native.py`) donne80blocs PCM exacts, sources mono et mid/side :6159->1628misses et5221->749evictions sales dans la trace DDR par cas40blocs. Pas de simulation des caches/timers materiels.

Plusieurs transformations C (prefiltrage separe, traitement par comb/bloc, options GCC), et un filtre FIR combine ont ete sondes dans le laboratoire local `ps1-cpu-lab`. Rejetes : plus chers ou PCM differents. Aucun de ces filtres, code flottant ni preset du depot ipatix n est copie dans le firmware. [Reference utilisateur](https://github.com/ipatix/lv2-psx-reverb) etudiee : structure PSX et licence permissive, implementation flottante pour hote LV2.

Le premier comparatif instructions du noyau etablit environ8205 pour Reverb native, jusqu a9214 pour PS1 v75 selon etat et signal. La disposition v76 ne change pas ce compte ; le but inferieur au stock sur appareil n est donc pas declare atteint.

## 4. Enregistrement utilisateur et etat de validation

WAV fourni : `TRACK06_ST_01 (2).wav`, stereo float32/48kHz,41.0467s, peak0.75809, aucun sample au plein niveau. Analyse numerique : discontinuites de0.72..0.94 apres31.385s ; compatible avec les overruns rapportes, sans prouver la causalite ni pretendre a une ecoute. Rapport local `output/firmware/recording-ps1-clicks-analysis.json`. Fichier utilisateur traite comme donnees uniquement.

v76 SHA256 `0615c8d4814a2e69f72dd830269ba6c8bae10770d6c80b352a8ac6dd2b6bfd26`.
Preuves :8192blocs PS1 PCM/etats exacts,320PS1 changeants face a v70,600blocs par Shimmer et320retours natifs par type ; Vinyl512/crusher640 ; DX vrai scan, menus/modificateurs, bootstrap exact et source compressee non ecrasee, gouverneur/seuils/compteurs inchanges. Les autres objets DSP/voix/UI sont identiques a v75.

[A FAIRE appareil] Checklist `output/firmware/validation/v76-test-checklist.md` : six pistes2ch, comparaison Reverb/PS1 sur durees egales, meme pattern que le WAV, P/O/N, transitions et tails, puis Vinyl et FX combines. Ne pas publier sans acceptation du retour appareil.

## 5. v77 : filtre partage apres retour v76

[FAIT appareil rapporte] AveyCole : v76 est mieux, mais clics persistants avec reverb + filtre sur six pistes ; confirmation explicite : O augmente encore. v76 fige a son SHA ci-dessus, aussi copie sans changement dans validation. Le gain cache ne suffit donc pas sur ce pattern.

`--filter-pair-opt` implique v76 et produit v77. Seul le noyau du filtre partage change : deux samples par iteration, roles des registres x1/x2 et y1/y2 alternes, puis roles d origine retrouves apres la paire. Cela supprime trois copies d historique par sample et une partie du controle de boucle. Les trois operations EMAC par sample, leur ordre, le clip134213632, les coefficients, cutoff/resonance, bypass, silence, quatre historiques et contrat MACSR/ACC1..3 sont conserves. Aucun changement au filtre interne du Wizard.

[FAIT en emulation] `test_filter_pair.py` :4288blocs exacts sur six lanes, controle changeant/extremes/saturation, zeros/reveil/historiques, contexte EMAC48 et ABI ;154800->130224instructions sur192blocs actifs chauds, soit15.876% du filtre seul. Gain callback global non assimile a ce pourcentage. `test_filter_ps1_mix.py` couvre la composition utilisateur Kick/Snare/Metal/Perc/Swarm/Tone, six filtres avant sends et PS1/mixeur natif ; rendu sans sequenceur/interface/USB/temps reels.

v77 SHA256 `601130a00db22443274116cf1550212d419606f2ee24c44a20985c74fe1eb546`. [A FAIRE appareil] Meme pattern2ch, tous six actifs, PS1+filtres et lecture P/O/N sur duree egale face a v76 ; verifier aussi caractere du filtre, resonance, sweep/LFO/p-lock et tails. Aucun resultat d absence de clic revendique.

## 6. v78 : noyau PS1 chaud et retour appareil

[FAIT appareil rapporte] v77 : « maybe a little bit better ... still clicking ... filter is closed most of the way on everything ». Cutoff/resonance tenus fixes, sans modulation. Le recalcul des coefficients n explique donc pas ces pointes. Comparaison v77 voix+six filtres+PS1 :4035372->3986988instructions sur64blocs, soit1.20% seulement du rendu couvert, coherent avec le petit gain rapporte.

`--ps1-fast-opt` implique v77 et produit v78. Nouveau `ps1_fast.c` + `ps1_hot.S` : le noyau chaud traite les16samples24k par buffers, entree quatre etages exactement arrondis vers zero ; lecture des deux canaux comb partagee, produits Q15 EMAC exacts ; allpass stereo avec memes seuils/saturations et interpolation. Longueurs/coefficients/send/tone/decay/sample-rate inchanges. Le noyau C initial reste pour les128premiers blocs apres reset ; surcout mesure14instructions par appel froid. Le wrapper chaud garde MACSR, ACC0 physique48bits et ACCext01 ; ACC1..3 intacts.

[FAIT invariants] ps_filled2048 et ps_w multiple16 ouvrent le chemin chaud. Tous les comb taps1187..2040 et allpass277..444 sont alors initialises ; les16positions consecutives du bloc n incluent aucun tap lu dans ce bloc. Pas de changement de comportement a la transition, au wrap ou apres reset. Emulation8192blocs avec input random/silence/fullscale, mono/stereo, in-place, controles min/max/negatifs et resets : PCM et tous etats logiques exacts face a v77.64contextes MACSR/F/I/SU/OMC/R + valeurs physiques48bits et registres ABI verifient le wrapper.

La banque code principale etait presque pleine (32732o pour32768disponibles). Le nouveau code est place en `.ps1hot` a `0x46830000..0x468308b3`,2228octets, apres le BSS PS1 finissant `0x468280f4`, dans l arena privee deja bornee a `0x46840000`. Ancien C compile separement avec `fx_ps1=fx_ps1_cold`; objcopy ne change que la liaison des onze symboles PS1 BSS pour les rendre accessibles au nouvel objet. Aucune copie de code Sony/native ou du plugin ipatix. Le generateur verifie tous les intervalles, assemble les deux sections sans chevauchement et le vrai bootstrap recharge les octets exacts sans ecraser la source compressee. Les bancs EMAC installent explicitement la deuxieme plage.

[FAIT mesures emulees] `test_ps1_fast.py` :14.23% d instructions chaudes en moins ; profil stereo etabli9117->7897,217->113lignes de code executees de16o. Ce sont des instructions et une empreinte executee, pas des cycles ou misses materiels. La valeur7897 est sous8205 du premier profil natif Reverb (§3), sans revendiquer un cout CPU materiel inferieur au stock. Demarrage +14instructions seulement. Les tentatives precedentes assemblees avec diffusion C non-inline etaient plus lentes et sont rejetees.

[FAIT appareil rapporte] Pendant les preuves finales, AveyCole : « noticeably way less clicky now in78 with6tracks, the filter and ps1 reverb ». Ce retour valide une amelioration percue de la surcharge sur son pattern, pas une absence de clics ou un O nul. Lecture A/P/O/N sur huit mesures demandee ; pas encore recue au moment de la note.

v78 SHA256 `5e0da3858f8d2d00711f0f0b53f7c3df5650442f8183e0e1e5f1d124d094db4b`. v78 fige, principal v70 conserve. Preuves bootstrap natif2623158octets, gouverneur/diagnostics et UI/DX inchanges ; `test_filter_ps1_mix.py ... v78 ... v77 --closed` couvre six voix et six filtres fixes64/res4096, PS1 et mixeur, sans temps materiel. Checklist `output/firmware/validation/v78-test-checklist.md`.


## 7. v79/v80 : retirer Shimmer et tous les modes combines

[FAIT appareil rapporte] Apres v78 l utilisateur ne se rappelle plus A/P/O/N, mais signale encore beaucoup de N. Il demande d enlever Shimmer2 et tous les Both, puis aussi Shimmer1. N reste le compteur de decisions de vol du gouverneur ; ce n est pas le compteur O des overruns.

`--lean-fx` produit l intermediaire v79 (Shimmer1 seul). `--no-shimmer` implique les optimisations v78 et lean-fx, produit v80. Ce dernier expose Reverb/Chorus1/2/Vinyl/PS1 et Delay/Crush1/2/PingPong uniquement. Ordre demande : PingPong au-dessus de Delay, puis Crush1 et Crush2 en-dessous (`[5,0,1,2]`). Reverb garde `[7,3,0,1,2]`. IDs stables, pas de renumerotation des sons/projets. La selection differee et le popup opaque sont conserves.

Migrations FX01 : anciens Vinyl+REV4 vers Vinyl3 ; CHOR+REV5/6 vers Chorus1/2 ; CRU+DEL3/4 et Shimmer6/7 vers Delay0. CLOUD8 absent, replie vers0. Format de60octets et complements identiques ; aucun parametre de pattern reecrit. cr_service charge la preference historique avant FxMix, pour eviter un ecrasement au premier dessin. Reecriture uniquement UI arretee, jamais depuis audio/lecture.

Les branches de DSP combinees, bus/gains crusher auxiliaires et diffuseur Shimmer2 sont exclus en v79. v80 compile `ping.c` a la place du moteur pitch entier ; ring8192, FIR, alignement, tables et wrapper EMAC Shimmer absents. Uniquement le retour stereo natif est permute pour PingPong, avec memes fondus. Code FX32728->24564o ; crusher8680->5836o, soit11008o de code retires. BSS FX131316->56432o, soit74884o de moins. L etat inutilise retire ne consommait pas de calcul continu : aucun gain CPU proportionnel a cette taille n est revendique.

[FAIT en emulation] 72migrations de preferences ; menus18positions, application a release/BACK, ordre des modificateurs, save/reload, retrig/DX et overlays opaques verifies. PS1 :8192blocs exacts,64contextes EMAC physiques ; bootstrap2623158octets exact sans ecrasement source. Gouverneur/seuils/diagnostics inchanges. Six vraies voix, six filtres fixes64/res4096 et PS1 :3906926->3900846instructions face a v78 sur64blocs (0,156%, pas cycles materiels), PCM/historiques exacts. Le banc fixe maintenant les coefficients apres `e.block`, avant les six appels filtres, et verifie explicitement cutoff64 ; les anciennes mesures initialisees avant le rendu voix ne prouvaient pas a elles seules la valeur finale du cutoff.

v80 SHA256 `fac5ae3d1f6a30512223049798307ac85a86533bd147e29d40e107d9d2c0affe`. v78 et principal v70 se reconstruisent exactement, v79 est conserve a part. [A FAIRE appareil] Checklist v80, memes huit mesures2ch/six pistes, PS1/filtres fixes et comparaison O/N. Ne pas declarer l absence de clics sans retour appareil.

[FAIT en emulation] Les13cas de mixeur conserves,32blocs chacun, mono/mid-side/pans, sends actifs puis0, restent PCM exacts face a v78. Quatre retours PingPong natifs alternent et sont exacts, plus420blocs de transitions Delay/Ping/Crush. [FAIT appareil rapporte] AveyCole : « v80 seems chill ». Image figee, sans promotion du principal.
