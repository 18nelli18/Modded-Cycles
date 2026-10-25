# Guide des fonctions et raccourcis

Supermodel2.40 - 24 octobre2026

Principal2.40. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. Toutes les fonctions ci-dessous sont incluses.

## Fonctions incluses

**Machines et son:** Six moteurs stock plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral de Glycinate, Elder, TINY, Shadow, SPEAK, LEGACY, RETROSYN et MIDI Out. Elder est inspiré de Junior de Fors. La selection conserve les valeurs synth ; quatre commandes Wizard separees tant que MACHINES reste ouvert.

**Performance et séquenceur:** Arpège, octave 0 sur notes tenues, ChordKeys et locks d’harmonie, Sequence Genie, SCRAMBLE, slides, préécoute de pas, Step Recorder, mute verrouillé et solo. Sidechain déclenché par les notes et listes Scramble par pattern.

**Filtres et effets:** Filtres pistes/Wizard inspires Polivoks, second LFO, MACRO Fine/Lo-Fi ; GATED, HALL, Ring Mod, ROOM, PS1, Vinyl, Reverb et Chorus 1/2 ; Phaser, DUCK, DUB, Ping Pong, Delay et Crush 1/2. Menus opaques appliques au relachement TRACK. Optimisations PS1/filtre cumulees. Les deux Shimmer et tous les modes combines sont retires.

**Routage et travail:** MIDI Out avec neuf CC, locks et deux LFO MIDI ; bascule OUT/THRU ; USB stéréo ou six pistes ; sauvegarde permanente, Mod Setup sauvegardé et diagnostic DX facultatif.

## Nouveautés 2.40 - raccourcis, labels Sidechain et niveaux

| Fonction | Commandes | Comportement |
|---|---|---|
| Mod Setup / Scramble | SETTINGS + TRACK bref / maintien | Appuyez brièvement sur SETTINGS + TRACK puis relâchez pour ouvrir Mod Setup. Maintenez la combinaison pour lancer SCRAMBLE une seule fois ; le maintien ne répète pas le tirage. Avec un TRIG tenu, un appui bref bascule sa marque Scramble. DATA choisit une ligne ; clic pour modifier, tourner, puis clic pour revenir. Stk = Stock ; SIL = Silent ; LTC = Latch. |
| S.Chn > | DATA ouvre le sous-menu Sidechain | Trk. N = piste cible ; Dpt = profondeur, Atk = attaque, Hld = maintien, Rel = relâchement. Routage et commandes toujours sauvegardés par pattern avec Save Project. |
| Niveaux Elder / Shadow | VOL + DIST | Elder retrouve son niveau original. Shadow gagne 12 dB par rapport à son niveau original. |

## Nouveautés 2.39 - Sidechain et Scramble par pattern

| Fonction | Commandes | Comportement |
|---|---|---|
| Routage Sidechain | Choisir la source ; SETTINGS + TRACK bref ; S.Chn > DATA | Cochez avec DATA les pistes à atténuer lors des notes de la source, parmi les cinq autres. Pas de cible vers soi-même. DATA parcourt et coche. Plusieurs sources : atténuation la plus profonde par cible. DUCK reste un type de delay séparé. Trk. 1–6 désignent les cibles ; la source est omise. |
| Dpt / Atk / Hld / Rel | Sous les cases : clic DATA, tourner, puis clic pour finir | Dpt = profondeur, Atk = attaque, Hld = maintien, Rel = relâchement. Depth : 0–100 %, 16 niveaux. Atk : 0–160 ms. Hold : 0–120 ms. Rel : 10 ms–3 s. BACK termine l’édition puis revient à Mod Setup. Départ conseillé : source sur chaque temps, Depth 60 %, Attack 0 ms, Hold 0 ms, Release 150 ms. Décocher toutes les cibles désactive la source. |
| Sauvegarde par pattern | Save Project après modification | Routage et commandes Sidechain, six listes Scramble, types et réglages FX ajoutés propres à chaque pattern. Sauvegardez le projet pour les conserver au chargement. Pattern vierge : Sidechain désactivé et listes Scramble par défaut. Changement en attente appliqué au début du prochain pattern. |
| Compatibilité projet | Garder une copie avant retour à un ancien firmware | Ce build charge les FX par pattern du v121. Les anciens firmwares ne restaurent pas les FX personnalisés des nouveaux records v122. Gardez une copie antérieure du projet pour un éventuel retour. |

## Nouveautés 2.38 - FX par pattern et WAVE plus fort

| Fonction | Commandes | Comportement |
|---|---|---|
| FX par pattern | TRACK + REVERB SIZE / DELAY TIME | Chaque pattern garde ses types FX et tous les réglages ajoutés, dont les envois supplémentaires. Sauvegardez le projet pour les retrouver au chargement. Les paramètres natifs gardent leur comportement habituel par pattern. |
| Patterns vierges et en attente | Choisir ou mettre un pattern en attente | Un pattern vierge commence avec Delay et Reverb standard et les réglages ajoutés par défaut. Les modifications restent avec ce pattern. Les FX changent au début réel du pattern en attente. |
| WAVE plus fort | Choisir WAVE et jouer | Sortie augmentée de 6 dB pour la table initiale et les tables importées. LEVEL/DIST règle toujours le niveau de la piste. |

## Nouveautes2.37 - WAVE pret a jouer

| Fonction | Commandes | Comportement |
|---|---|---|
| Table initiale WAVE | Choisir WAVE et jouer | AV-WAVE-Morph est deja chargee : 16trames a parcourir, aucun import initial requis. COLOR choisit la position ; SHAPE ajoute le mouvement d enveloppe. Une table importee remplace la table initiale sur sa piste. |
| Dossiers WAVE | BACK dans le navigateur WAVE | Remonte un dossier. A /Wavetables, BACK ferme la selection. Maintien et relachement apres une remontee laissent la vue ouverte. Chargement des tables avec YES/pad comme auparavant. |

## Nouveautes2.36 - Acid,SY BITS et Elder

| Fonction | Commandes | Comportement |
|---|---|---|
| DECAY du filtre ACID | DECAY | Decroissance du filtre uniquement. Volume tenu jusqu a note-off puis relachement court fixe ; Gate ne transforme plus Decay en enveloppe de volume. Slides et commandes existantes conserves. |
| Accent ACID | Velocite97-127 | Accent progressif du transitoire filtre et du niveau. Velocite0-96 conserve la reponse sans accent ; volume natif de velocite conserve. |
| Detune fin SY BITS | FUNC + COLOR | Pas de0.01demi-ton entre -24.00 et +24.00. Petit popup decimal signe actualise en direct. COLOR ordinaire change les demi-tons entiers sans perdre la fraction. Valeurs conservees avec les sons et disponibles aux locks. |
| Niveau Elder | VOL + DIST | Elder retrouve son niveau original. Le précédent gain de 6 dB est retiré ; commandes de synthèse inchangées. |

## Nouveautes 2.35 - banques et RETROSYN

| Fonction | Commandes | Comportement |
|---|---|---|
| Importer une banque DX7 | Flasheur > Importateurs WAV / DX7 | Arretez la lecture. Choisissez une banque Yamaha .syx de 32 voix, connectez le MIDI USB Model:Cycles, choisissez 1-16 et envoyez. Attendez LEGACY BANK SAVED. Le meme emplacement est remplace. Le son actif ne change pas. |
| Charger une banque | LEGACY : FUNC + MACHINES ; DATA ; BACK | Maintenez FUNC et appuyez MACHINES. Tournez DATA pour choisir, appuyez DATA pour charger ; BACK annule. Factory restaure les voix incluses. Une banque active de 32 voix est partagee par toutes les pistes LEGACY. Banques conservees apres redemarrage, hors sauvegarde de projet Elektron. |
| Voix LEGACY faibles | Automatique, fixe par note | Compensation limitee du gain de sortie des carriers faibles. Velocite et enveloppes conservees ; un operateur silencieux ou desactive ne devient pas audible. Charge CPU reduite conservee. |
| RETROSYN | MACHINES, juste avant MIDI Out | Color, Shape (six modeles), Sweep et Contour. Pitch, Decay, Gate et Punch disponibles. IDs existants conserves ; Elder reste dans la liste. MIDI Out reste dernier. |
| Mises a jour HALL et SPEAK | HALL : SIZE ; SPEAK : SHAPE | Retour HALL releve d environ 6 dB ; SIZE maximal donne une queue amortie plus longue. SPEAK un peu plus clair, CAREFUL (123) puis CREATURE (124). Vocabulaire regulier uniquement. |
| Menu FX superpose | Maintenir TRACK + tourner REVERB SIZE / DELAY TIME | Menu opaque complet au-dessus de Machines et des autres fenetres. Tournez pour parcourir sans changer le son ; relachez TRACK pour appliquer. Fenetre precedente conservee derriere. Selection Control All liberee au relachement TRACK. |

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
| SCRAMBLE | Maintenir SETTINGS + TRACK | Au maintien, tirez les parametres coches de cette piste : Pitch,Decay,Color,Shape,Sweep,Contour. Choix dans Mod Setup > SCRM. Decay fonctionne ; Punch reste inchange. Quatre commandes originales actives par defaut. Pas marques : meme liste,son de base intact. La liste est propre à cette piste dans le pattern courant ; sauvegardez le projet pour la conserver. Une seule fois par maintien ; le relâchement n’ouvre pas le menu. Un appui bref sans pas tenu ouvre Mod Setup. |
| Pas SCRAMBLE / suppression | Maintenir un pas + SETTINGS + TRACK bref ; supprimer normalement | Bascule SCRAMBLE sur ce pas. Supprimer le trig retire marque et locks ; le nouveau trig repart propre. Autres pas et pistes conserves. |
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
| Menu reverb | Maintenir TRACK + REVERB SIZE | De haut en bas : GATED, HALL, ROOM, PS1, REVERB, VINYL, CHORUS 1, CHORUS 2, RING MOD. Gauche monte, droite descend. Son inchange pendant le parcours ; relacher TRACK applique, BACK annule. |
| Menu delay | Maintenir TRACK + DELAY TIME | De haut en bas : PHASER, DUCK, DUB, PING PONG, DELAY, CRUSH 1, CRUSH 2. Depuis DELAY, gauche/haut vers Ping Pong ; droite/bas vers Crush 1 puis Crush 2. Relacher TRACK applique ; BACK annule. |
| Reverb standard | REVERB SEND / SIZE / FUNC + SIZE | Send par piste / Size natif, INF au maximum / Tone -64 a 0 a +63. Format natif restaure immediatement apres Chorus, meme en lecture. |
| Reverb GATED | REVERB SEND / SIZE ; FUNC + SIZE ; SETTINGS + SIZE | Gated Send / Gate Time ; Pre-delay ; Tone. Gate Time 0-127 : environ 40 ms-6,7 s apres le signal. Pre-delay 0-568 ms : pas de 1 ms jusqu a 64 puis 8 ms. Sans echos ajoutes ; dry immediat, gate apres le signal retarde. Essayer Gate Time 16-32 et Pre-delay 25-40 ms sur caisse claire. Gate Time et Pre-delay sont propres à chaque pattern ; sauvegardez le projet pour les conserver. |
| Reverb HALL | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | Hall Send par piste / Decay / Tone. Queue stereo large, reflexions plus longues que ROOM. Quatre voies amorties et deux diffuseurs par canal a 12 kHz, memoire reverb reutilisee. |
| Ring Mod | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | Ring Send par piste / Frequency / Depth. Modulation en anneau sinusoidale metallique dans le slot reverb. RING MOD sous Chorus 1/2. Frequency et Depth partagés par les pistes du pattern ; locks via le Send natif. |
| Phaser | DELAY SEND / TIME / FUNC + TIME ; FUNC puis TRACK + TIME | Phaser Send par piste / Rate / Depth ; FUNC puis TRACK + TIME : Feedback (aussi SETTINGS + TIME). Phaser stereo deux etages dans le slot delay. PHASER au-dessus de DUCK. Tenir FUNC avant TRACK pour eviter le mute verrouille. |
| Delay DUCK | DELAY SEND / TIME / FUNC + TIME ou SETTINGS + TIME ; FUNC puis TRACK + TIME ou DELAY SEND | Delay Send natif / Time / Feedback. Tenir FUNC avant TRACK : TIME regle Amount ; DELAY SEND regle Release. Retour attenue pendant le signal puis remontee progressive ; feedback conserve. Essayer Amount 127, Release 32-64 sur notes espacees. Amount 0 : Delay standard. |
| Reverb ROOM | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | Room Send par piste / Decay / Tone. Petite ambiance stereo a 12 kHz. ROOM au-dessus de PS1 ; relacher TRACK pour appliquer. Retour wet releve de 6 dB aux niveaux usuels, avec compression douce des cretes ; dry inchange. |
| Reverb PS1 | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | PS1 Send par piste / Decay / Tone. Queue stereo inspiree PlayStation, sombre et granuleuse ; optimisations de traitement conservees. Retour wet releve de 6 dB aux niveaux usuels, avec compression douce des cretes ; dry inchange. |
| Chorus 1 / 2 | REVERB SEND / SIZE / FUNC + SIZE | Chorus Send par piste / Speed / Depth. Speed et Depth 0-127. Remplace la reverb du slot. |
| Vinyl | REVERB SEND ; SIZE / FUNC + SIZE / FUNC puis TRACK + SIZE | Vinyl Send ; Crackle / Warble Amount / Warble Speed. Tenir FUNC puis TRACK pour Speed. Send 0 sec ; Crackle 0 coupe la poussiere. Pops/clics independants dans les pauses. Volume, pan et mute respectes. |
| Delay standard | DELAY SEND / TIME / FUNC + TIME | Delay Send par piste / Time natif / Feedback natif. |
| Delay DUB | DELAY SEND / TIME / FUNC + TIME ou SETTINGS + TIME | Delay Send par piste / Time natif / Feedback. Echos fortement filtres alternant gauche/droite, de plus en plus etroits dans la boucle. Reutilise le delay natif et le rebond stereo. Casque ou deux sorties pour le mouvement. |
| Ping Pong | DELAY SEND / TIME / FUNC + TIME ou SETTINGS + TIME | Send par piste / Time / Feedback. Echos stereo alternes gauche/droite ; casque ou deux sorties. |
| Crusher Rate / Bits | CRUSH 1 ou 2 : TIME / FUNC + TIME | Rate 0-127, environ 750 Hz-48 kHz / Bits 2-16. Valeurs basses plus rugueuses. CRUSH 1 garde le direct propre ; CRUSH 2 melange direct propre/crushed. DELAY SEND affiche Crush Send ; pas d echo dans ces modes. |
| Reglages et sauvegarde FX | Sauvegarder le projet | Types FX et réglages ajoutés propres à chaque pattern ; sauvegardez le projet pour les retrouver au chargement. Les patterns vierges utilisent Delay/Reverb standard et les réglages ajoutés par défaut. Pas de destination p-lock/LFO pour les réglages ajoutés ; les envois natifs gardent leurs verrous. Shimmers et modes combinés retirés. |

## Machines et commandes sonores

| Fonction | Commandes | Comportement |
|---|---|---|
| Defilement machines | MACHINES + tourner DATA | Tours rapides bornes a une machine par evenement accepte,espaces de40ms,pour ne pas sauter Wizard. IDs et ordre TINY/Shadow/SPEAK/MIDI conserves. |
| Commandes Elder | Choisir Elder dans MACHINES | COLOR = Wave ; SHAPE = Warp ; SWEEP = Noise ; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate et Fine conservés. Synthé original inspiré de Junior de Fors. |
| Anciens sons Retrosyn | Elder remplace ChpHzrd / Retrosyn | Le même emplacement joue Elder : le timbre des anciens sons Retrosyn change. Autres moteurs et correctifs CPU conservés. Feral est de Glycinate. |
| Commandes TINY | Choisir TINY dans MACHINES | COLOR : Tone ; SHAPE : Model0–51 ; SWEEP : Mod ; CONTOUR : Excite. Les52modeles originaux ; Feral et tous les autres moteurs conserves. |
| Commandes Shadow | Choisir Shadow apres TINY dans MACHINES | COLOR : Grain ; SHAPE : Density ; SWEEP : Spread ; CONTOUR : Chaos. PUNCH : attaque repetee. Pitch,Fine,Decay et Gate conserves. Synthese pulsar/bruit originale inspiree de Opal Dust de Fors. Sortie à +12 dB du niveau original ; VOL + DIST règle le niveau d’écoute. |

## Machine LEGACY

| Fonction | Commandes | Comportement |
|---|---|---|
| LEGACY / selection | MACHINES : avant RETROSYN et MIDI Out | FM six operateurs Dexed MSFA, 32 algorithmes ; une voix par piste. MIDI Out toujours dernier. COLOR = Velocity, SHAPE = Voice, SWEEP = Brightness, CONTOUR = EG Time. Locks/CC/LFO natifs ; Voice et Velocity sont pris au prochain trigger. |
| Banque de voix | SHAPE : slots 0-31 | Commence par Tooropulse, Delicho et EinstofPia. Huit slots plus faibles remplacent leurs voix par PIANO 1, E.PIANO 1, BASS 1, BRASS 1, STRINGS 1, CLAV 1, E.ORGAN 1 et MARIMBA de la cartouche ROM1A fournie. |
| Velocity / brillance | COLOR / SWEEP | Velocity 0-127 agit sur les operateurs a chaque trigger ; defaut 100. Brightness 64 conserve la voix. Plus bas adoucit la modulation ; plus haut ajoute du mordant. |
| Duree des enveloppes | CONTOUR / DECAY | EG Time 64 conserve les durees de la voix ; plus bas accelere, plus haut ralentit. DECAY et gate conservent l enveloppe d amplitude native. PITCH/FINETUNE transposent ; operateurs a frequence fixe selon la cartouche. |
| Importer une banque DX7 | Flasheur > Importateurs WAV / DX7 | Arretez la lecture. Choisissez une banque Yamaha .syx de 32 voix, connectez le MIDI USB Model:Cycles, choisissez 1-16 et envoyez. Attendez LEGACY BANK SAVED. Le meme emplacement est remplace. Le son actif ne change pas. |
| Credits et charge | Dexed / Google MSFA | Composant MSFA Apache de Dexed par Google, Pascal Gauthier et contributeurs ; integration Cycles originale. Voix de cartouches fournies par l utilisateur. Certaines voix six operateurs demandent plus de calcul. |

## Banque de voix LEGACY

| Fonction | Commandes | Comportement |
|---|---|---|
| 0 | Tooropulse | Cartouche Legowelt Magic |
| 1 | Delicho | Cartouche Legowelt Magic |
| 2 | EinstofPia | Cartouche Legowelt Magic |
| 3 | Overcast P | Cartouche Legowelt Magic |
| 4 | STRINGS 1 | ROM1A |
| 5 | PWMfuzzy | Cartouche Legowelt Magic |
| 6 | Sharpieblo | Cartouche Legowelt Magic |
| 7 | RoboticSeq | Cartouche Legowelt Magic |
| 8 | SplitStran | Cartouche Legowelt Magic |
| 9 | PIANO   1 | ROM1A |
| 10 | Heimwave | Cartouche Legowelt Magic |
| 11 | CLAV    1 | ROM1A |
| 12 | Synthotape | Cartouche Legowelt Magic |
| 13 | Wavesply | Cartouche Legowelt Magic |
| 14 | Poldermood | Cartouche Legowelt Magic |
| 15 | FelineSaw | Cartouche Legowelt Magic |
| 16 | Aguirio | Cartouche Legowelt Magic |
| 17 | E.PIANO 1 | ROM1A |
| 18 | E.ORGAN 1 | ROM1A |
| 19 | Pinkcookie | Cartouche Legowelt Magic |
| 20 | ObieSplash | Cartouche Legowelt Magic |
| 21 | MARIMBA | ROM1A |
| 22 | Garudaydre | Cartouche Legowelt Magic |
| 23 | VillageOrg | Cartouche Legowelt Magic |
| 24 | BASS    1 | ROM1A |
| 25 | Litehouze | Cartouche Legowelt Magic |
| 26 | NostroSpli | Cartouche Legowelt Magic |
| 27 | Velobleepb | Cartouche Legowelt Magic |
| 28 | DimPacific | Cartouche Legowelt Magic |
| 29 | SequenceMe | Cartouche Legowelt Magic |
| 30 | BRASS   1 | ROM1A |
| 31 | Swissynth | Cartouche Legowelt Magic |

## Machine vocale SPEAK

| Fonction | Commandes | Comportement |
|---|---|---|
| Choisir SPEAK | MACHINES : apres Shadow, avant LEGACY | Moteur vocal original a formants, 128 mots anglais. Microphone ; CLASS VOICE / STYLE TALK / STR 1, DEX 5, MAG 5. v90 equilibre les phonemes, adoucit les transitions et eclaircit les harmoniques vocales sans renforcer le souffle. Commencer vers Vol+Dist 60, Punch coupe. |
| Voice / Word / Speed / Articulation | COLOR / SHAPE / SWEEP / CONTOUR | Caractere vocal/formants / Word 0-127 / Speed (64 normal, plus bas plus lent) / Articulation. SHAPE affiche mot et index. Mot pris au prochain trig ; autres commandes en direct. Les mots lents continuent dans les silences phonemiques ; le detecteur idle ne suspend plus une parole inachevee. |
| Hauteur et enveloppe | PITCH / notes ; DECAY, Fine, Punch, Gate, Attack | Hauteur independante de la vitesse. Commencer a Decay 127 pour les mots complets. Filtres et sends existants disponibles. Etat vocal distinct par piste. |
| Sequences de mots et modulation | Maintenir TRIG + SHAPE, puis locks Pitch et autres commandes | Mot et autres parametres natifs acceptent p-locks et destinations LFO. COLOR/SHAPE/SWEEP/CONTOUR : MIDI CC 16/17/18/19. Espacer les mots ou augmenter Speed. |
| Exemple de phrase | Mots SHAPE et locks de notes sur des trigs successifs | HELLO 31, I 0, AM 62, A 17, ROBOT 113, I 0, LOVE 35, MUSIC 106. Lexique complet indexe a la fin du guide. |
| Accord SPEAK | PITCH / FINETUNE | Reference corrigee d environ 1,17 demi-ton vers le bas. Registre vocal, formants et durees des mots conserves. |

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

Appuyez brièvement sur SETTINGS + TRACK puis relâchez pour ouvrir Mod Setup. Maintenez la combinaison pour lancer SCRAMBLE une seule fois ; le maintien ne répète pas le tirage. Avec un TRIG tenu, un appui bref bascule sa marque Scramble. DATA choisit une ligne ; clic pour modifier, tourner, puis clic pour revenir. Stk = Stock ; SIL = Silent ; LTC = Latch.

| Fonction | Commandes | Comportement |
|---|---|---|
| Pad | Stk / SIL ; défaut Stk | Stk sélectionne et joue. SIL sélectionne silencieusement ; TRACK + pad sélectionne et joue. ChordKeys exige TRACK + pad pour quitter la piste. |
| USB | 2ch / 6ch ; défaut 2ch | 2ch : mix stéréo avec effets. 6ch : six pistes mono avant panoramique, sans retours delay/crusher/reverb/chorus. Retour ordinateur stéréo dans les deux modes. Arrêtez avant de changer ; le périphérique USB se reconnecte. |
| Num | Off / On ; défaut Off | On affiche volume et panoramique en chiffres ; Off garde l’affichage natif. |
| Mute | Stk / LTC ; défaut Stk | LTC : TRACK + appui FUNC verrouille ; FUNC quitte. FUNC + pad en mute verrouillé : solo ; rappuyer ou quitter restaure les mutes. |
| Delay | Stk / Div ; défaut Stk | Stk : Time natif. Div : divisions musicales, pointées et triolets. Positions correspondantes corrigées au tempo ; toutes les positions ne sont pas quantifiées. Utilisé en mode Delay. |
| DX | Off / On ; défaut Off | DX On : appui bref FUNC, second appui sous 350 ms, maintien au moins 0,5 seconde puis relacher. Toute autre commande annule. Affiche/remet a zero A/P/O/N : charge moyenne/pic, overruns, voix coupees par le gouverneur. Remplace ancien raccourci ; verrou retrig sans diagnostic. Off par defaut. |
| SCRM | DATA ouvre ; tourner et appuyer ; BACK revient | Six cases par piste : Pitch, Decay, Color, Shape, Sweep, Contour. Pitch/Decay désactivés par défaut, quatre autres activés. Six listes propres à chaque pattern ; Save Project les conserve au chargement. Wizard autorise Pitch/Decay, commandes sample/modes exclues. |
| Routage Sidechain | Choisir la source ; SETTINGS + TRACK bref ; S.Chn > DATA | Cochez avec DATA les pistes à atténuer lors des notes de la source, parmi les cinq autres. Pas de cible vers soi-même. DATA parcourt et coche. Plusieurs sources : atténuation la plus profonde par cible. DUCK reste un type de delay séparé. Trk. 1–6 désignent les cibles ; la source est omise. |

BACK ferme Mod Setup et sauvegarde ses préférences globales ; en lecture, cette sauvegarde attend l’arrêt. Arrêtez et attendez la fin avant extinction. Routage/réglages Sidechain, listes Scramble et types/réglages FX ajoutés propres à chaque pattern : Save Project les conserve au chargement. Fermer un sous-menu ne sauvegarde pas le projet.

## Lexique SPEAK

| Index | Word | Index | Word | Index | Word | Index | Word |
|---:|---|---:|---|---:|---|---:|---|
| 0 | I | 32 | GOODBYE | 64 | IS | 96 | ONE |
| 1 | YOU | 33 | GOOD | 65 | WAS | 97 | TWO |
| 2 | WE | 34 | BAD | 66 | WERE | 98 | THREE |
| 3 | THEY | 35 | LOVE | 67 | WILL | 99 | FOUR |
| 4 | HE | 36 | LIKE | 68 | CAN | 100 | FIVE |
| 5 | SHE | 37 | WANT | 69 | COULD | 101 | SIX |
| 6 | IT | 38 | NEED | 70 | HAVE | 102 | SEVEN |
| 7 | ME | 39 | KNOW | 71 | HAS | 103 | EIGHT |
| 8 | US | 40 | THINK | 72 | HAD | 104 | NINE |
| 9 | THEM | 41 | FEEL | 73 | BEEN | 105 | ZERO |
| 10 | MY | 42 | SEE | 74 | IN | 106 | MUSIC |
| 11 | YOUR | 43 | HEAR | 75 | ON | 107 | SOUND |
| 12 | OUR | 44 | SAY | 76 | AT | 108 | BEAT |
| 13 | THIS | 45 | SPEAK | 77 | TO | 109 | RHYTHM |
| 14 | THAT | 46 | TELL | 78 | FOR | 110 | BASS |
| 15 | THESE | 47 | ASK | 79 | FROM | 111 | DRUM |
| 16 | THOSE | 48 | DO | 80 | WITH | 112 | MACHINE |
| 17 | A | 49 | MAKE | 81 | WITHOUT | 113 | ROBOT |
| 18 | AN | 50 | PLAY | 82 | OF | 114 | HUMAN |
| 19 | THE | 51 | STOP | 83 | UP | 115 | TIME |
| 20 | AND | 52 | START | 84 | DOWN | 116 | NIGHT |
| 21 | OR | 53 | GO | 85 | HERE | 117 | DAY |
| 22 | BUT | 54 | COME | 86 | THERE | 118 | WORLD |
| 23 | IF | 55 | STAY | 87 | NOW | 119 | FRIEND |
| 24 | SO | 56 | MOVE | 88 | THEN | 120 | HAPPY |
| 25 | BECAUSE | 57 | TURN | 89 | AGAIN | 121 | SAD |
| 26 | YES | 58 | TAKE | 90 | ALWAYS | 122 | NEW |
| 27 | NO | 59 | GIVE | 91 | NEVER | 123 | CAREFUL |
| 28 | NOT | 60 | GET | 92 | ALL | 124 | CREATURE |
| 29 | PLEASE | 61 | BE | 93 | SOME | 125 | LOUD |
| 30 | THANK | 62 | AM | 94 | MORE | 126 | DREAM |
| 31 | HELLO | 63 | ARE | 95 | LESS | 127 | FUTURE |

Défauts : pads et mute stock ; USB 2ch ; Num Off ; DX Off. Les patterns vierges utilisent Reverb et Delay standard et les réglages ajoutés par défaut. USB six canaux sans retours stéréo des effets.
