# Guide des fonctions et raccourcis

Supermodel2.27 - 23 octobre2026

Principal2.27. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. Toutes les fonctions ci-dessous sont incluses.

## Fonctions incluses

**Machines et son:** Six moteurs stock plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral de Glycinate, Elder, TINY, Shadow et MIDI Out. Elder est inspiré de Junior de Fors. La selection conserve les valeurs synth ; quatre commandes Wizard separees tant que MACHINES reste ouvert.

**Performance et séquenceur:** Arpège, octave 0 sur notes tenues, ChordKeys et locks d’harmonie, Sequence Genie, SCRAMBLE, slides, préécoute de pas, Step Recorder, mute verrouillé et solo.

**Filtres et effets:** Filtres pistes/Wizard inspires Polivoks,second LFO,MACRO Fine/Lo-Fi ; combinaisons Delay/Crush,Chorus1/2+Reverb et Vinyl+Reverb. Menus appliques au relachement TRACK. Fenetres FX opaques ; SETTINGS+Size/Time regle Tone/Feedback en modes combines. Poussiere Vinyl continue dans les pauses. Ajoute Ping Pong stereo,Shimmer 1 entierement transpose et Shimmer 2 mixte/diffuse precedent.

**Routage et travail:** MIDI Out avec neuf CC, locks et deux LFO MIDI ; bascule OUT/THRU ; USB stéréo ou six pistes ; sauvegarde permanente, Mod Setup sauvegardé et diagnostic DX facultatif.

## Pistes, pas et performance

| Fonction | Commandes | Comportement |
|---|---|---|
| Step Recorder | Lecture arrêtée : REC deux fois ; PLAY avance ; STOP recule ; REC quitte | Jouez des notes pour écrire les pas successifs. PLAY avance d’un pas, STOP recule d’un pas. |
| Mute verrouillé | TRACK + appui bref sur FUNC | Choisissez d’abord Mute: LTC dans Mod Setup. FUNC quitte le mode verrouillé ; Stk conserve le mode natif. |
| Solo en mute | En mode mute verrouillé : FUNC + T1–T6 | Isole la piste. Rappuyez sur son pad, ou quittez le mode mute, pour restaurer les mutes précédents. |
| Sélection silencieuse | Choisir Pad: SIL dans Mod Setup ; T1–T6 | Sélection sans déclenchement. TRACK + pad sélectionne et joue. Stk est le défaut. |
| Préécoute de pas | Maintenir TRIG + PAGE | Écoutez le pas et ses locks à l’arrêt ou en pause. |
| Slide | SETTINGS + TRIG | Active ou désactive le glissement de paramètres sur le pas. |
| Sequence Genie | SETTINGS + PAGE | Générateur de la piste sélectionnée. DATA choisit ; Generate ou Queue, avec frontière Loop/Page. |
| SCRAMBLE | Appui bref SETTINGS + TRACK | Au relachement, tirez les parametres coches de la piste. Choix dans Mod Setup > Scramble : Pitch,Decay,Color,Shape,Sweep,Contour. Quatre commandes originales actives par defaut. Les pas marques suivent la meme liste, son de base intact. |
| Configuration Control All | TRACK + TRIG 1–6 | Inclut ou exclut les pistes audio des changements collectifs. |
| Beat repeat audio | Maintenir TRACK + RETRIG, puis un TRIG 1–16 | Le pas choisit la division des pistes incluses. Relâchez un modificateur ou le pas pour arrêter. |
| Verrou beat repeat | Maintenir TRACK + double RETRIG | Relachez les deux ; maintenir un TRIG repete, relacher arrete. BACK quitte. Copier/coller/effacer bloques ; PLAY/STOP simples disponibles. Non sauvegarde. FUNC+SETTINGS/PATTERN temporaires disponibles ; aucun diagnostic depuis le verrou. |
| Filtre collectif | TRACK + MACHINES + SWEEP / CONTOUR | Coupure / résonance des pistes incluses. Sans TRACK : piste sélectionnée. Passe-bas deux pôles inspiré du Polivoks. |
| Attaque synthé | MACHINES + DECAY | Règle l’attaque ajoutée sur les machines compatibles. |
| Arpège / réglages ChordKeys | FUNC + RETRIG | Ouvre les réglages actifs. Octave 0 de l’arpège parcourt uniquement les notes tenues. |
| ChordKeys | Sur Chord : jouer TRIG 1–16 | Voicings en gamme. TRACK + pad de piste est nécessaire pour quitter une piste ChordKeys. |
| Locks d’harmonie ChordKeys | Grille : maintenir TRIG et appuyer T1–T6 ; live : accord puis pad d’harmonie | Le même pad sur un pas tenu restaure son harmonie de base. Sauvegardé avec le pattern, indépendamment du LFO 2. |

## Effets

| Fonction | Commandes | Comportement |
|---|---|---|
| Menu slot reverb | Maintenir TRACK + REVERB SIZE | Fenetre opaque par-dessus l’ecran normal ; trois choix defilants. Gauche/haut : VINYL,puis VINYL+REV. Centre : REVERB. Droite/bas : CHORUS1,CHORUS2,CHOR1+REV,CHOR2+REV. Parcourir ne change pas le son ; relacher TRACK applique,BACK annule. |
| Menu slot delay | Maintenir TRACK + DELAY TIME | Gauche/haut depuis DELAY : CRUSH1,CRUSH2,PING PONG,SHIMMER 1,SHIMMER 2. Droite/bas : CRU1+DEL,CRU2+DEL. Fenetre opaque ; son inchange avant relachement TRACK. BACK annule. |
| Reverb Tone | REVERB : FUNC+SIZE ; combine : SETTINGS+SIZE | En CHOR1+REV,CHOR2+REV et VINYL+REV, maintenez SETTINGS et tournez REVERB SIZE pour le Tone natif sans quitter le mode. Relacher SETTINGS revient a Reverb Size. Le mode REVERB standard garde FUNC+SIZE. |
| Chorus seul | SIZE = Speed ; FUNC + SIZE = Depth | Chorus I/II : Speed et Depth0-127. REVERB SEND devient Chorus Send par piste. |
| Commandes chorus + reverb | SIZE / FUNC+SIZE / FUNC puis TRACK+SIZE | Reverb Size / Chorus Speed / Chorus Depth. Maintenir FUNC puis TRACK n’ouvre pas Track Setup. |
| Envois chorus + reverb | REVERB SEND / FUNC+REVERB SEND | Reverb Send natif / Chorus Send distinct0-127 par piste. Chaque effet reste independant. |
| Vinyl seul | SIZE / FUNC+SIZE / FUNC puis TRACK+SIZE | Crackle / Warble Amount / Warble Speed. Vinyl Send0 : sec. Pops/clics brillants independants, presents dans les pauses ; Crackle0 coupe la poussiere. Volume,pan et mute de piste respectes. |
| Commandes Vinyl + reverb | SIZE / FUNC+SIZE / FUNC puis TRACK+SIZE | Reverb Size / Crackle / Warble Amount. FUNC puis TRACK+REVERB SEND regle Warble Speed. |
| Envois Vinyl + reverb | REVERB SEND / FUNC+REVERB SEND | Reverb Send natif / Vinyl Send distinct par piste. Vinyl Send0 garde la reverb normale. |
| Time / Feedback delay | DELAY : TIME / FUNC+TIME ; combine : SETTINGS+TIME | TIME simple garde Time natif en CRU1+DEL/CRU2+DEL. Maintenez SETTINGS et tournez DELAY TIME pour le Feedback natif ; relacher SETTINGS revient a Time. FUNC puis TRACK+DELAY SEND regle aussi Feedback. |
| Ping Pong | TIME / FUNC+TIME ou SETTINGS+TIME / DELAY SEND | Temps / Feedback / envoi par piste. Echos alternes gauche/droite ; casque ou deux sorties. Remplace le delay standard,sans variante combinee. |
| Shimmer 1 / Shimmer 2 | TIME / FUNC+TIME ou SETTINGS+TIME / DELAY SEND | Temps / Feedback / envoi par piste. Shimmer 1 : chaque echo monte d une octave,filtre pour lisser les repetitions. Shimmer 2 : ancien melange echo propre/octave diffusee. Sans variantes combinees. |
| Rate crusher | CRUSH : TIME ; CRU+DEL : FUNC+TIME | Rate0-127,environ750Hz-48kHz. Plus bas : degrade ; plus haut : propre. |
| Bits crusher | CRUSH : FUNC+TIME ; CRU+DEL : FUNC puis TRACK+TIME | Bits2-16. Les valeurs basses affectent aussi les signaux faibles. Silence conserve. |
| Envois crusher / delay | Combine : DELAY SEND / FUNC+DELAY SEND | Delay Send / Crush Send distinct0-127 par piste. CRU1+DEL garde le direct propre ; CRU2+DEL melange le direct meme delay0. Crusher0 donne des echos propres. Seul : Crush Send. |
| Reglages FX et sauvegarde | Relacher TRACK ; arreter la lecture | Modes et controles globaux,puis six envois par effet,sauvegardes apres arret. Nouveaux controles/envois sans p-lock/LFO. Parametres delay/reverb natifs conserves. |

## Machines et commandes sonores

| Fonction | Commandes | Comportement |
|---|---|---|
| Defilement machines | MACHINES + tourner DATA | Tours rapides bornes a une machine par evenement accepte,espaces de40ms,pour ne pas sauter Wizard. IDs et ordre TINY/Shadow/MIDI conserves. |
| Commandes Elder | Choisir Elder dans MACHINES | COLOR = Wave ; SHAPE = Warp ; SWEEP = Noise ; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate et Fine conservés. Synthé original inspiré de Junior de Fors. |
| Anciens sons Retrosyn | Elder remplace ChpHzrd / Retrosyn | Le même emplacement joue Elder : le timbre des anciens sons Retrosyn change. Autres moteurs et correctifs CPU conservés. Feral est de Glycinate. |
| Commandes TINY | Choisir TINY dans MACHINES | COLOR : Tone ; SHAPE : Model0–51 ; SWEEP : Mod ; CONTOUR : Excite. Les52modeles originaux ; Feral et tous les autres moteurs conserves. |
| Commandes Shadow | Choisir Shadow apres TINY dans MACHINES | COLOR : Grain ; SHAPE : Density ; SWEEP : Spread ; CONTOUR : Chaos. PUNCH : attaque repetee. Pitch,Fine,Decay et Gate conserves. Synthese pulsar/bruit originale inspiree de Opal Dust de Fors. |

## Commandes LFO et MACRO

| Fonction | Commandes | Comportement |
|---|---|---|
| Second LFO audio | Appuyer deux fois sur LFO | Ouvre LFO 2 et ses réglages de vitesse, forme, destination et profondeur. |
| Assignation rapide LFO | Dans une page LFO : maintenir LFO et tourner un potard | Choisit sa destination ordinaire. Pour Attack/Filter/Resonance, maintenir aussi MACHINES. |
| Destinations Attack / Filter / Resonance | Dans LFO : LFO + MACHINES + DECAY / SWEEP / CONTOUR | Choisit attaque / coupure / résonance selon la machine. Relâchez MACHINES pour les destinations ordinaires. |
| Accord fin MACRO | SETTINGS + PITCH | PITCH seul reste natif. FUNC + PITCH est Lo-Fi : fréquence réduite à gauche, bits réduits à droite, centre OFF. Noms et numéros 0–46 des modèles visibles. |

## Sample Wizard et sauvegarde

| Fonction | Commandes | Comportement |
|---|---|---|
| Préécoute sample | FUNC + MACHINES ; surligner un sample ; pad ou TRIG clavier | Écoute le sample surligné. Le défilement reste silencieux. |
| Sample lock | Navigateur ouvert : surligner le sample, puis TRIG + MACHINES | Verrouille le sample choisi sur le pas de la piste Wizard. Le navigateur doit être ouvert avec le sample surligné. |
| Modes de lecture | SETTINGS + MACHINES | One-Shot, Loop, Slice, Granular, Stretch, Pluck et Wavetable conservés. SETTINGS + PUNCH : options du mode. Commandes Wizard separees des synths pendant la session MACHINES ; valeurs restaurees au retour. |
| Éditeur Slice | FUNC + TRIG ; FUNC + clic DATA | FUNC joue les slices 17–32 ; FUNC + clic DATA efface un marqueur. FUNC + potards 1/2 cale les marqueurs au passage zéro. |
| Sauvegarde rapide permanente | Maintenir FUNC + SETTINGS | Sauvegarde permanente du projet par l’action native. |
| Copie temporaire / rappel | Bref FUNC+SETTINGS / FUNC+PATTERN | Copie temporaire native / rappel,y compris pendant le verrou retrig. |

## Machine MIDI Out

| Fonction | Commandes | Comportement |
|---|---|---|
| Choix et réglages MIDI Out | MACHINES : MIDI Out ; FUNC + TRACK | Piste MIDI silencieuse. Track Setup : Channel, Output, KbT et Pad Note. DATA choisit ; clic avant édition ; BACK quitte. |
| Assignation CC et locks - MIDI Out seulement | SETTINGS + potard gris ; pas tenu + potard assigné | Neuf potards CC. Tourner seul envoie la valeur. Chaque lock garde numéro et valeur ; enregistrement live des locks. Chance/Swing restent natifs. |
| Deux LFO MIDI | LFO : LFO 1, LFO 2, piste ; BACK quitte | DATA choisit, clic pour éditer : Wav, Mul, Dst, Dep, Speed, Fade, Phase, Mode. LFO Speed règle le LFO ouvert ; LFO + CC choisit destination puis profondeur. |
| Notes et sauvegarde | Notes/grille habituelles ; FUNC + PAGE ; FUNC + SETTINGS | Entrée MIDI par canal de piste ou auto ; live/step record gardent notes, vélocité et longueur. FUNC + PAGE : longueur. Sauvegarde projet : réglages et locks MIDI. |
| MIDI OUT + THRU | CONFIG → MIDI → PORTS → OUT/THRU : THR ; puis FUNC + clic DATA | Bascule la sortie MIDI propre du Cycles en conservant le MIDI Thru entrant. |

## Mod Setup

Maintenez SETTINGS + TRACK pour ouvrir Mod Setup puis relâchez. Un appui bref lance SCRAMBLE au relâchement. DATA choisit une ligne ; clic pour éditer, tourner, puis clic pour revenir. Stk = Stock ; SIL = Silent ; LTC = Latch.

| Fonction | Commandes | Comportement |
|---|---|---|
| Pad | Stk / SIL ; défaut Stk | Stk sélectionne et joue. SIL sélectionne silencieusement ; TRACK + pad sélectionne et joue. ChordKeys exige TRACK + pad pour quitter la piste. |
| USB | 2ch / 6ch ; défaut 2ch | 2ch : mix stéréo avec effets. 6ch : six pistes mono avant panoramique, sans retours delay/crusher/reverb/chorus. Retour ordinateur stéréo dans les deux modes. Arrêtez avant de changer ; le périphérique USB se reconnecte. |
| Num | Off / On ; défaut Off | On affiche volume et panoramique en chiffres ; Off garde l’affichage natif. |
| Mute | Stk / LTC ; défaut Stk | LTC : TRACK + appui FUNC verrouille ; FUNC quitte. FUNC + pad en mute verrouillé : solo ; rappuyer ou quitter restaure les mutes. |
| Delay | Stk / Div ; défaut Stk | Stk : Time natif. Div : divisions musicales, pointées et triolets. Positions correspondantes corrigées au tempo ; toutes les positions ne sont pas quantifiées. Utilisé en mode Delay. |
| DX | Off / On ; défaut Off | Diagnostic CPU optionnel. Maintenez physiquement TRACK+RETRIG au moins350ms puis relachez. Le verrou retrig ne declenche jamais le popup. Off par defaut. |
| SCRM | DATA ouvre ; tourner et appuyer ; BACK revient | Six cases par piste : Pitch,Decay,Color,Shape,Sweep,Contour. Pitch/Decay desactives par defaut, quatre autres actives. Choix conserves entre projets et apres extinction ; sauvegarde a l’arret. Wizard autorise Pitch/Decay, commandes sample/modes exclues. |

Préférences globales. BACK ferme Mod Setup et sauvegarde ses preferences globales ; la liste Scramble de chaque piste se sauvegarde au retour du sous-menu. Si la lecture tourne, la sauvegarde attend son arrêt. Arrêtez et attendez la fin de sauvegarde avant extinction. Choix restaurés au redémarrage. Modes d’effets et réglages crusher sauvegardés également après arrêt.

Défauts : pads et mute stock ; USB 2ch ; Num Off ; DX Off. Reverb et Delay par défaut sans préférences d’effets sauvegardées. USB six canaux sans retours stéréo des effets.
