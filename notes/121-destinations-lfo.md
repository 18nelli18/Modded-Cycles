# 121 — Destinations LFO et retour des gestes MACHINES

Demande AveyCole, conversation du 18/10/2026 : attaque, coupure et resonance dans les deux LFO audio ; assignation rapide ; retour a la piste apres une action MACHINES. Adresses : VA de OS1.13.

## Reponse courte

Deux pages de test seulement : `flasher-lfo-destinations-test` (principal1.89) et `flasher-supermodel-909-lfo-test` (909.5). Versions publiees conservees, diagnostics en test. Statut experimental, validation physique a faire.

## 1. Observations

[FAIT] Les destinations23/24/25 existent deja dans les moteurs. Le proprietaire ne voit pas ATK dans les deux menus avec Synth Attack installe. [HYP] Le chemin de presentation des noms masque cette entree ; la disparition exacte sur appareil n'est pas reproduite dans le catalogue complet emule. Le test force les libelles ATK/FLT/RES pour ces numeros et conserve les autres noms natifs, ainsi que les routines audio existantes.

Le descripteur d'un potard et la destination ne sont pas le meme indice. La table se deplace selon les moteurs installes : employer le mapper natif, jamais une copie de sa table. Les limites de descripteurs restent celles du build.

## 2. Adaptations UI

- Appel de nom LFO1 a0x4002650e ; deux appels du menu/scan LFO2 detournes.
- Appels de mapping quick assign LFO1 a0x4001e190 et0x4001eb52, et appel LFO2 : LFO+MACHINES et DECAY/SWEEP/CONTOUR donnent23/24/25. Le deuxieme geste conserve l'ajustement de profondeur natif.
- Slot potard ParameterPageView0x401005a8 : resultats et quatre arguments preserves ; gestes attaque et filtre ferment le selecteur sous-jacent.
- Presentation0x4007700e : prologue8octets rejoue, puis code natif a0x40077016. Une nouvelle vue autre que le selecteur MACHINES, avec MACHINES tenu, ferme le selecteur sous-jacent.
- Fermeture differee native0x40076126, uniquement pour le vptr stock0x40117920. Aucune destruction dans le dispatch ; les vues privees B/LFO2 restent ouvertes. Liste bornee a32vues. MACHINES seul conserve son comportement.

## 3. Placement et assemblage

`tools/gen_lfo_destinations_test.py` compile le C/assembleur ColdFire (-mcpu=54418, GCC Debian/Ubuntu), relocalise son helper a la fin du dernier payload et regenere les deux pages avec `--check`. Le chargeur de copie est agrandi si necessaire ; sans payload existant, le petit chargeur Beat Repeat et son masque redirige chargent uniquement ce helper a0x43000000. Avec Wizard en place, la limite reserved_end de zero BSS est avancee et alignee16octets afin de ne pas effacer le helper au boot. Toutes les modifications ont des gardes d'octets/hachages.

Aucune nouvelle ecriture dans les routines de synthese ou LFO audio. Donnees firmware, WAV et fixtures signes restent ignores dans build/.

## 4. Preuves

[FAIT en emulation] `tools/test_lfo_destinations_flasher.js` : cinq selections avant/apres signees (ensemble complet avec et sans MIDI, Wizard avec et sans LFO2, Arp seul sans autre payload). `tools/test_909_current.js` avec LFO_DEST_909_TEST=1 : quatre vrais uploads WAV, signature, remplacement et invalidation ; aucun transfert automatique.

`tools/emu/test_lfo_destinations.py` execute le bootstrap reel, noms sur six pistes, scan reel LFO2 dans les deux sens, quick assign reel LFO2 puis profondeur, fermeture differee native, conservation des autres vues et de la presentation, gardes de touches et IRQ.

`tools/emu/test_lfo_destinations_audio.py` compare les deux vrais moteurs LFO et leur melange : destinations identiques/distinctes23..25, sorties/etats de phase bornes et strictement identiques avant/apres, meme nombre d'instructions executees. Cette mesure ne remplace pas les delais physiques de la machine.

## 5. Verification demandee sur appareil

ATK/FLT/RES dans LFO1 et2 ; assignation puis profondeur avec LFO+MACHINES ; attaque/filtre avec ou sans TRACK ; retour piste apres popup/action, ouverture MACHINES seule normale. Les diagnostics test sont disponibles avec Beat Repeat et compteurs SY dans le principal, actives automatiquement pour909. Aucun diagnostic ajoute aux versions principales.

## 6. Libelles RETROSYN (test2, 18/10/2026)

AveyCole demande des noms correspondant au DSP de cette machine. COLOR devient Timbre/TIMB (rapport pulse, table, cadence bruit, boucle selon oscillateur), SHAPE Oscillator/OSC (six types), SWEEP Pitch Sweep/PSWP, CONTOUR Chord Arp/ARP. Les noms longs (+44) et courts (+52) des quatre descripteurs propres a RETROSYN changent ; bornes, valeurs, identifiants de destinations, sauvegarde et DSP restent identiques. Les autres machines et le profil909 conservent leurs noms. Le pointeur de table actif et le nombre de descripteurs donnent la derniere machine ajoutee, avec garde groupe6 et cles11..14. Si le bundle MIDI est recompresse, la source du chargeur Beat Repeat est recalculee. La preuve execute le vrai lookup de noms sur les six pistes et les builds couvrent aussi RETROSYN sans Wizard ni MIDI.

## 7. Quick assign : garder LFO visible (test3, 18/10/2026)

AveyCole confirme libelles RETROSYN et quick assign sur appareil ; le selecteur MACHINES masque encore le LFO. [FAIT] Son ouverture passe par0x40077da8, distinct de la presentation0x4007700e interceptee en test1/2. Au debut de la branche MACHINES de ParameterPage0x4001c252, le test3 consomme le geste si LFO(code8) est tenu, avant allocation et presentation. Sans LFO, le trampoline rejoue exactement movel d3,-(sp) et lea0x400724a0,a3 puis reprend0x4001c25a. Sous LFO, reprise de la branche consommee0x4001c2a8 ; D0/D1/A0/A1 et pile preserves. Les gestes quick assign, leurs destinations/profondeurs et les noms test2 sont conserves. La preuve execute cette branche depuis le vrai site avec appui/relachement/appui long et verifie aucune allocation. Verification physique du menu encore requise.
