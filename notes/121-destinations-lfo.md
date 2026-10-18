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

## 8. Fermer LFO apres toute assignation rapide (test4, 18/10/2026)

Demande AveyCole : tous les quick assigns doivent quitter le menu au relachement LFO. Le garde primaire +604 conservait le menu ; le drapeau secondaire lf2p_assigned faisait aussi consommer ce relachement sans fermer. Le test4 intercepte la methode native0x40024e0c : evenement LFO(code8), bit appui absent, +604 actif => effacement du garde et appel de la fermeture virtuelle native +124. Sinon, prologue natif rejoue et comportement historique. Les deux routes this/sous-objet restent valides. Avec LFO2, le callback de touche installe dans la vtable privee est redirige vers un wrapper equivalent, utilisant lf2p_assigned et la fermeture +40. Le callback original reste le repli, donc navigation normale et entree LFO2 sans assignation conservees. FUNC n'empeche pas la fermeture d'une assignation terminee. Aucun changement du choix de cible, de la profondeur, du son ou des donnees sauvegardees. Preuve native : appui/maintien/autre touche ne ferment pas ; relachement avec/sans FUNC ferme les deux pages ; entree LFO2 sans assignation preservee. Test uniquement, diagnostics conserves.

## 9. LFO1, marqueur persistant (test5, 18/10/2026)

AveyCole signale que le relachement ne ferme pas LFO1 en test4 ; LFO2 n'est pas signale defaillant. [FAIT] La routine encodeur native0x40024db6 ecrit +604 selon l'etat physique LFO a chaque evenement2..13. Un evenement traite apres relachement physique peut donc remettre le garde a0 avant traitement de la touche. Test5 : au site0x40024df8, conserver un garde deja arme si D0=0 ; ne l'armer que si LFO est tenu. Le handler de touche le consomme et le remet a0 comme en test4. Pas de changement supplementaire LFO2. La preuve rejoue cet ordre avec la vraie routine encodeur, les vrais vtables LFO1 et la fermeture de sa vue embarquee +56 : test4 perd le marqueur, test5 le conserve et ferme sur relachement. Sans geste, un encodeur seul ne l'arme pas. [HYP] Cet ordre explique le comportement observe sur l'appareil ; verification physique test5 requise.

## 10. Retour au menu persistant et capture de cible (test6, 18/10/2026)

AveyCole annule release-to-exit et demande le meme maintien du menu pour LFO2 que LFO1. Les hooks de relachement/sticky test4/5 sont retires ; les comportements de touches natifs sont restores. L'ouverture MACHINES reste inhibee pendant LFO tenu. Le proprietaire decrit aussi l'alternance rapide Sweep/Filter et Contour/Resonance, y compris sans MACHINES. Le test6 supprime la substitution de destination dans les lectures UI ordinaires. Une enveloppe autour des deux vrais quick assigns capture index physique et MACHINES une seule fois par evenement ; DECAY(index1), SWEEP(4), CONTOUR(5) ciblent18/13/14 sans MACHINES,23/24/25 avec le module concerne. Toutes les conversions internes au meme geste utilisent cette cible, puis le contexte precedent est restaure. Les autres potards conservent la conversion native. Le trampoline primaire rejoue lea-60(sp), moveq11,d0 ; celui de LFO2 rejoue lea-12(sp), movem d2-d4 avant le corps original. Aucun hook audio. Preuves : menus persistants, lectures hors geste sans alias, stress des deux cibles pendant changement descripteur/modificateur et reglages LF2 reels. Verification physique encore requise.

## 11. Eligibilite ATK et filtre propre a Wizard (test7, 18/10/2026)

AveyCole precise : Attack existe comme controle machine mais manque aux destinations LFO sur toutes les machines, en test6. [FAIT] Le descripteur13 (groupe7, cle23) porte un masque nul a+36 ; le constructeur de liste natif0x4000bffc exige0x600 pour le LFO. Les noms forces des tests precedents ne corrigeaient pas cette exclusion. Test7 ajoute ce masque au descripteur source, avant sa copie dans la table active au demarrage. La preuve execute la vraie liste native : ATK absent avec masque0, present avec0x600, sur six machines stock et Wizard. Aucun changement de valeur, plage, moteur ou format sauvegarde.

[FAIT] Wizard (machine6) utilise les cles13/14 pour son filtre/resonance, et les lookups24/25 renvoient le descripteur Error. Apres sa vraie recherche de potards0x4004df5c(7), les noms13/14 deviennent Filter/Res. Les assignations du test6 vers24/25 etaient donc incorrectes pour cette machine. Test7 capture aussi le contexte de piste : les deux pages assignent13/14 sur Wizard, avec ou sans MACHINES ; ailleurs le schema test6 reste identique. Les affichages nomment ces cibles FLT/RES independamment des rafraichissements des noms partages. LFO2 ignore les destinations24/25 inexistantes sur Wizard au lieu de leur fabriquer un nom valide. Le pointeur de piste LFO2 est distinct du selecteur A, pour respecter sa piste courante. Boucles et lectures bornees, aucun hook DSP.

[FAIT en emulation] Le test execute le vrai lookup Wizard et80 assignations LFO2 pendant alternance MACHINES, plus la capture primaire avec descripteurs contradictoires ; cibles13/14 stables, aucune fuite d'override. Les menus restent ouverts apres quick assign, suppression du selecteur MACHINES et libelles Retrosyn conserves. Deux copies test seulement, diagnostics conserves. Validation physique test7 a faire.

## 12. Libelles pendant le mouvement (test8, 18/10/2026)

AveyCole confirme Attack correctement ajoute sur appareil ; Wizard affiche encore Sweep/Contour pendant la rotation puis Filter/Resonance a la fin. [FAIT en emulation] Apres la vraie recherche Wizard0x4004df5c(7), une recherche KICK0x4004df5c(1), utilisee par les quick mappers, restaure les noms partages SWEP/CONT des descripteurs73/74. Le remplacement du seul rendu de destination ne protege pas les autres rendus pendant l'encodeur.

Test8 detourne les getters natifs de noms courts0x4000b208 et longs0x4000b22a. Pour le contexte exact SoundParameterOwner0x400fd134, getter brut valide et machine6, les cles13/14 donnent FLT/Filter et RES/Resonance. Tous les autres appels reproduisent exactement le lookup natif du champ+52/+44 dans la table active, borne par le nombre de descripteurs du build. Aucun nom partage n'est reecrit par le helper : le nom est choisi selon le son reel, sans dependance au dernier lookup d'une autre machine. La garde de classe evite de traiter les contextes de trig/pattern/settings comme des sons. Aucun hook audio ni changement d'assignation ou de valeur.

La preuve reproduit le nom partage errone pendant40 alternances de touche et execute les vrais getters accroches : noms Wizard stables courts/longs, tandis que le meme descripteur utilise par CHORD conserve ses noms natifs (SWEP/CONT en principal ; BITS/---- en909). Eligibilite Attack, les deux LFO, catalogues minimaux/complets et909 restent couverts. Test uniquement, validation physique requise.
