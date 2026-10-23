# Guide des fonctions et raccourcis

Supermodel2.18 - 22 octobre2026

Principal2.18. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. Toutes les fonctions ci-dessous sont incluses.

## Fonctions incluses

**Machines et son:** Six moteurs stock plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral de Glycinate, Elder et MIDI Out. Elder est inspiré de Junior de Fors.

**Performance et séquenceur:** Arpège, octave 0 sur notes tenues, ChordKeys et locks d’harmonie, Sequence Genie, SCRAMBLE, slides, préécoute de pas, Step Recorder, mute verrouillé et solo.

**Filtres et effets:** Attaque par piste et passe-bas résonant deux pôles inspiré du Polivoks ; passe-bas interne Wizard ; second LFO ; MACRO Fine/Lo-Fi ; Reverb/Chorus I/II et Delay/Crush1/Crush2/Both1/Both2.

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
| SCRAMBLE | Appui bref SETTINGS + TRACK | Randomise Color, Shape, Sweep et Contour au relâchement. Compatible avec les p-locks. |
| Configuration Control All | TRACK + TRIG 1–6 | Inclut ou exclut les pistes audio des changements collectifs. |
| Beat repeat audio | Maintenir TRACK + RETRIG, puis un TRIG 1–16 | Le pas choisit la division des pistes incluses. Relâchez un modificateur ou le pas pour arrêter. |
| Verrou beat repeat | Maintenir TRACK + double RETRIG | Relachez les deux ; maintenir un TRIG repete, relacher arrete. BACK quitte. Copier/coller/effacer bloques ; PLAY/STOP simples disponibles. Non sauvegarde. |
| Filtre collectif | TRACK + MACHINES + SWEEP / CONTOUR | Coupure / résonance des pistes incluses. Sans TRACK : piste sélectionnée. Passe-bas deux pôles inspiré du Polivoks. |
| Attaque synthé | MACHINES + DECAY | Règle l’attaque ajoutée sur les machines compatibles. |
| Arpège / réglages ChordKeys | FUNC + RETRIG | Ouvre les réglages actifs. Octave 0 de l’arpège parcourt uniquement les notes tenues. |
| ChordKeys | Sur Chord : jouer TRIG 1–16 | Voicings en gamme. TRACK + pad de piste est nécessaire pour quitter une piste ChordKeys. |
| Locks d’harmonie ChordKeys | Grille : maintenir TRIG et appuyer T1–T6 ; live : accord puis pad d’harmonie | Le même pad sur un pas tenu restaure son harmonie de base. Sauvegardé avec le pattern, indépendamment du LFO 2. |

## Effets et Elder

| Fonction | Commandes | Comportement |
|---|---|---|
| Mode Chorus / Reverb | TRACK + REVERB SIZE | À droite : Reverb → Chorus I → Chorus II ; à gauche pour revenir. I est lent/doux ; II plus rapide/profond. Reverb restaure Size/Tone. Deux evenements encodeur par changement. |
| Speed / Depth chorus | REVERB SIZE / FUNC + REVERB SIZE | Vitesse / profondeur 0–127. REVERB SEND dose par piste. Départ conseillé : Speed 42, Depth 64, envoi modéré. |
| Mode Delay / Crush / Both | TRACK + DELAY TIME | Delay → Crush1 → Crush2 → Both1 → Both2 ; a gauche pour revenir. Deux evenements encodeur par changement. |
| Time / Feedback delay | Mode Delay : TIME / FUNC + TIME | Time / Feedback natifs. En Both, revenez à Delay pour régler puis à Both. Les réglages delay et crusher restent distincts. |
| Rate crusher | En Crush/Both : DELAY TIME | Rate 0–127, environ 750 Hz–48 kHz. Plus bas : plus dégradé ; plus haut : plus propre. DELAY SEND dose par piste. |
| Bits crusher | En Crush/Both : FUNC + DELAY TIME | Bits2–16. Plus bas = plus de grain, y compris sur les signaux faibles a2–4bits. Silence conserve. |
| Routage crusher | DELAY SEND par piste | Crush1 : direct propre + envoi ecrase. Crush2 : direct propre/ecrase. Both1 : direct propre + echos ecrases. Both2 : direct et echos ecrases. Send127 retire le direct propre des modes2. |
| Réglages d’effets et sauvegarde | Relâcher TRACK ; arrêter la lecture | Modes et Rate/Bits globaux sauvegardes apres arret. Rate/Bits sans p-locks ; envois avec locks. Speed/Depth reutilisent Size/Tone du pattern. Both2 coute plus de calcul. |
| Commandes Elder | Choisir Elder dans MACHINES | COLOR = Wave ; SHAPE = Warp ; SWEEP = Noise ; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate et Fine conservés. Synthé original inspiré de Junior de Fors. |
| Anciens sons Retrosyn | Elder remplace ChpHzrd / Retrosyn | Le même emplacement joue Elder : le timbre des anciens sons Retrosyn change. Autres moteurs et correctifs CPU conservés. Feral est de Glycinate. |

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
| Modes de lecture | SETTINGS + MACHINES | One-Shot, Loop, Slice, Granular, Stretch, Pluck et Wavetable conservés. SETTINGS + PUNCH : options du mode. |
| Éditeur Slice | FUNC + TRIG ; FUNC + clic DATA | FUNC joue les slices 17–32 ; FUNC + clic DATA efface un marqueur. FUNC + potards 1/2 cale les marqueurs au passage zéro. |
| Sauvegarde rapide permanente | Maintenir FUNC + SETTINGS | Sauvegarde permanente du projet par l’action native. |

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
| DX | Off / On ; défaut Off | On : diagnostic A/P/O/N après relâchement de TRACK + RETRIG : moyenne, pic, blocs surchargés, nouvelles voix coupées. Compteurs remis à zéro après affichage. Préférence sauvegardée. |

Préférences globales. BACK ferme Mod Setup et sauvegarde les six choix ensemble. Si la lecture tourne, la sauvegarde attend son arrêt. Arrêtez et attendez la fin de sauvegarde avant extinction. Choix restaurés au redémarrage. Modes d’effets et réglages crusher sauvegardés également après arrêt.

Défauts : pads et mute stock ; USB 2ch ; Num Off ; DX Off. Reverb et Delay par défaut sans préférences d’effets sauvegardées. USB six canaux sans retours stéréo des effets.
