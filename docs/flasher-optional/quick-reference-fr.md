# Guide des fonctions et raccourcis

Supermodel3.05 - 4 novembre2026

Principal3.05. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. Full et Lite partagent les commandes generales ; les sections machines exigent leur presence. Les extras Machine Optional sont identifies separement.

## Fonctions incluses

**Machines et son:** Six moteurs stock plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral de Glycinate, Elder, TINY, Shadow, SPEAK, RETROSYN, PUNCH et MIDI Out. Elder est inspirÃ© de Junior de Fors. PUNCH est un moteur de percussions FM de100demons (MIT).

**Performance et sÃ©quenceur:** ArpÃ¨ge, octave 0 sur notes tenues et locks dâ€™harmonie, Sequence Genie, SCRAMBLE, slides, prÃ©Ã©coute de pas, Step Recorder, mute et solo verrouillÃ©s ou quantifiÃ©s. Sidechain dÃ©clenchÃ© par les notes et listes Scramble par pattern.

**Filtres et effets:** Filtre rÃ©sonant et attaque par piste. GATED, HALL, ROOM, PS1, Ring Mod et deux Chorus ; DUCK, DUB, POTS, Ping Pong, Phaser et deux Crushers.

**Routage et travail:** MIDI Out avec neuf CC, locks et deux LFO MIDI ; bascule OUT/THRU ; USB stÃ©rÃ©o ou six pistes ; sauvegarde permanente, Mod Setup sauvegardÃ© et diagnostic DX facultatif.

**Song et navigation:** Les lignes Song combinent patterns, repetitions et mutes. Direct Pattern Jump et selection de trigs servent le jeu.

**Articulation ACID et locks:** Glide/legato ACID par piste, enveloppes A/F/AF et relance par arpege ; les locks de sample Wizard conservent le sample ; les parametres libres suivent la piste. Seuls les locks explicites priment sur CTRL-ALL, meme en boucle longue.

## Pistes, pas et performance

| Fonction | Commandes | Comportement |
|---|---|---|
| Verrou CTRL-ALL | Double tap TRACK ; TRACK ou double BACK rapide quitte | Deux taps simples en350ms verrouillent les editions CTRL-ALL. BACK simple conserve l annulation native. Selection pistes/trigs momentanee ; DATA et selecteurs FX physiques. Off au demarrage, non sauvegarde. |
| Verrou selection pattern | Double-tap PATTERN ; PATTERN ou BACK quitte | Garde le selecteur natif ouvert sans expiration. Choix repetes par les trigs. Tap simple et maintien restent natifs. Verrou non sauvegarde. |
| Track Swap | Mod Setup > Track > Swap ; lecture arretee | Choisissez From et To avec DATA, puis Swap et appuyez sur DATA. Echange sons, sequences, p-locks, volume, filtres/LFO et FX par piste du pattern courant. Sidechain et mutes Song correspondants suivent le contenu. Refaire le meme echange annule l operation ; Save Project conserve les modifications. |
| Step Recorder | Lecture arrÃªtÃ©e : REC deux fois ; PLAY avance ; STOP recule ; REC quitte | Jouez des notes pour Ã©crire les pas successifs. PLAY avance dâ€™un pas, STOP recule dâ€™un pas. Octaves : FUNC + TRACK > KBT ; +/-12 demi-tons deplace une octave. |
| Mute verrouillÃ© | TRACK + appui bref sur FUNC | Choisissez dâ€™abord Mute: LTC dans Mod Setup. FUNC quitte le mode verrouillÃ© ; Stk conserve le mode natif. |
| Solo en mute | En mode mute verrouillÃ© : FUNC + T1â€“T6 | Isole la piste. Rappuyez sur son pad, ou quittez le mode mute, pour restaurer les mutes prÃ©cÃ©dents. |
| SÃ©lection silencieuse | Choisir Pad: SIL dans Mod Setup ; T1â€“T6 | SÃ©lection sans dÃ©clenchement. TRACK + pad sÃ©lectionne et joue. Stk est le dÃ©faut. |
| PrÃ©Ã©coute de pas | Maintenir TRIG + PAGE | Ã‰coutez le pas et ses locks Ã  lâ€™arrÃªt ou en pause. |
| Slide | SETTINGS + TRIG | Active ou dÃ©sactive le glissement de paramÃ¨tres sur le pas. |
| Sequence Genie | SETTINGS + PAGE | GÃ©nÃ©rateur de la piste sÃ©lectionnÃ©e. DATA choisit ; Generate ou Queue, avec frontiÃ¨re Loop/Page. |
| SCRAMBLE | Maintenir SETTINGS + TRACK | Tire une seule fois par maintien les paramÃ¨tres cochÃ©s : Pitch, Decay, Color, Shape, Sweep, Contour. Choix dans Mod Setup > Track > SCRM. Pitch/Decay dÃ©sactivÃ©s par dÃ©faut ; Color/Shape/Sweep/Contour activÃ©s. Les pas marquÃ©s suivent la mÃªme liste, sans changer le son de base. Listes sauvegardÃ©es par pattern avec Save Project. Un appui bref sans pas tenu ouvre Mod Setup. |
| Pas SCRAMBLE / suppression | Maintenir un pas + SETTINGS + TRACK bref ; supprimer normalement | Bascule SCRAMBLE sur ce pas. Supprimer le trig retire marque et locks ; le nouveau trig repart propre. Autres pas et pistes conserves. |
| Configuration Control All | TRACK + TRIG 1â€“6 | Touches de pas1-6, pas les pads de piste. Choisissez les pistes suivant Control All ; la piste selectionnee suit toujours. |
| Beat repeat audio | Maintenir TRACK + RETRIG, puis un TRIG 1â€“16 | Le pas choisit la division des pistes incluses. RelÃ¢chez un modificateur ou le pas pour arrÃªter. |
| Verrou beat repeat | Maintenir TRACK + double RETRIG | RelÃ¢chez les deux ; maintenez un TRIG pour rÃ©pÃ©ter, relÃ¢chez-le pour arrÃªter. BACK quitte. PLAY/STOP et sauvegarde/rechargement temporaires FUNC + SETTINGS/PATTERN disponibles. |
| Filtre collectif | TRACK + MACHINES + SWEEP / CONTOUR | Coupure / rÃ©sonance des pistes incluses. Sans TRACK : piste sÃ©lectionnÃ©e. Passe-bas deux pÃ´les inspirÃ© du Polivoks. |
| Attaque synthÃ© | MACHINES + DECAY | RÃ¨gle lâ€™attaque ajoutÃ©e sur les machines compatibles. |
| ArpÃ¨ge / rÃ©glages ChordKeys | FUNC + RETRIG | Ouvre les rÃ©glages actifs. Octave 0 de lâ€™arpÃ¨ge parcourt uniquement les notes tenues. |
| Scale Lock | FUNC + PAGE > Lock / Scl / Key | Off desactive ; ORGN suit les degres ; BRDS choisit la note de gamme la plus proche (egalite vers le bas). 19 gammes par demi-tons. Sauvegarde globale a l arret. |
| Page Len / Warp | FUNC + PAGE > Page Len / Warp | Page Len :1-16 pas actifs par page. Warp ON les repartit sur la duree normale ; OFF conserve la vitesse des pas. Portee PTN ou TRK. Warp est OFF par defaut et se sauvegarde avec le pattern. |
| Type de filtre commun | Maintenir SETTINGS, puis MACHINES + tourner SWEEP | HIGH / LOW / BAND / LO/HI. Relachez pour valider. Sons neufs/effaces : LOW, coupure127, resonance0, meme si la piste est initialisee tard. Choix sauvegardes conserves au demarrage. Sample Wizard garde son filtre interne. |
| Filtre par piste | MACHINES + SWEEP / CONTOUR | Coupure / resonance de la piste selectionnee. Ajouter TRACK pour les pistes incluses dans Control All. |
| Selection de trigs | TRACK + PAGE | Active/desactive la selection. Touchez les trigs existants pour les selectionner ; ils clignotent. Relachez TRACK pour editer les pas : la selection de piste reste momentanee. Les pas vides ne sont pas crees. |
| Tous / aucun | Selection active : FUNC + PAGE | Selectionne tous les trigs accessibles ou efface la selection. PAGE change de page en la conservant. Les pas hors Page Len sont exclus. TRACK + PAGE quitte et efface la selection. |
| Direct Pattern Jump | Global > JUMP > On ; PATTERN, puis FUNC + TRIG | Avec JUMP On, saute immediatement vers le pattern choisi en conservant la position. Off suit le changement natif. Preference globale sauvegardee ; Off par defaut. |

## Mode Song

| Fonction | Commandes | Comportement |
|---|---|---|
| Ouvrir Song | SETTINGS + TRACK > Song > DATA | Song est au premier niveau, a cote de Global et Track. PLAY depuis l editeur lance la ligne selectionnee. |
| Choisir une ligne | Tourner DATA | Quatre lignes visibles. Editez a l arret, Song inactif ; double STOP annule le morceau actif avant edition. |
| Pattern / repetitions | PITCH / DECAY | Choisit A01-F16 et1-64 repetitions pour la ligne. Le morceau entier doit tenir dans64 lectures de patterns developpees. |
| Mutes de pistes | TRIG1-6 | Bascule le mute de chaque piste pour la ligne. Les mutes du morceau se combinent aux mutes existants. |
| Inserer / supprimer | PAGE / FUNC + PAGE | PAGE insere une copie apres la ligne. FUNC + PAGE la supprime ; une ligne reste toujours. |
| Fin du morceau | Appuyer sur DATA | Choisit STOP ou LOOP. FUNC + DATA fonctionne aussi. STOP arrete apres la derniere ligne ; LOOP repete l arrangement. PLAY a l arret part de la ligne selectionnee ; LOOP parcourt tout l arrangement. |
| Transport, sortie, sauvegarde | PLAY / STOP / double STOP / BACK / Save Project | PLAY a l arret demarre sur la ligne selectionnee ; STOP suspend via le transport natif ; double STOP annule Song et coupe les queues FX. BACK quitte. Save Project conserve Song et glide/legato ACID. Une longueur de chaine infinie peut retenir une ligne. |

## Effets

| Fonction | Commandes | Comportement |
|---|---|---|
| Menu reverb | Maintenir TRACK + REVERB SIZE | De haut en bas : GATED, HALL, ROOM, PS1, REVERB, CHORUS 1, CHORUS 2, RING MOD. Gauche monte, droite descend. Son inchange pendant le parcours ; relacher TRACK applique, BACK annule. |
| Menu delay | Maintenir TRACK + DELAY TIME | De haut en bas : PHASER, DUCK, DUB, POTS, PING PONG, DELAY, CRUSH 1, CRUSH 2. Depuis DELAY, gauche/haut vers Ping Pong ; droite/bas vers Crush 1 puis Crush 2. Relacher TRACK applique ; BACK annule. |
| Reverb standard | REVERB SEND / SIZE / FUNC + SIZE | Send par piste / Size, INF au maximum / Tone de -64 Ã  0 Ã  +63. |
| Reverb GATED | REVERB SEND / SIZE ; FUNC + SIZE ; SETTINGS + SIZE | Gated Send / Gate Time ; Pre-delay ; Tone. Gate Time : environ 40 msâ€“6,7 s aprÃ¨s le signal. Pre-delay : 0â€“568 ms. Essayez Gate Time 16â€“32 et Pre-delay 25â€“40 ms sur une caisse claire. |
| Reverb HALL | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | Hall Send par piste / Decay / Tone. Queue stÃ©rÃ©o large, rÃ©flexions plus longues que ROOM ; SIZE au maximum donne une longue queue amortie. |
| Ring Mod | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | Ring Send par piste / Frequency / Depth. Modulation en anneau sinusoidale metallique dans le slot reverb. RING MOD sous Chorus 1/2. Frequency et Depth partagÃ©s par les pistes du pattern ; locks via le Send natif. |
| Phaser | DELAY SEND / TIME / FUNC + TIME ; FUNC puis TRACK + TIME | Phaser Send par piste / Rate / Depth ; FUNC puis TRACK + TIME : Feedback (aussi SETTINGS + TIME). Phaser stereo deux etages dans le slot delay. PHASER au-dessus de DUCK. Tenir FUNC avant TRACK pour eviter le mute verrouille. |
| Delay DUCK | DELAY SEND / TIME / FUNC + TIME ou SETTINGS + TIME ; FUNC puis TRACK + TIME ou DELAY SEND | Delay Send natif / Time / Feedback. Tenir FUNC avant TRACK : TIME regle Amount ; DELAY SEND regle Release. Retour attenue pendant le signal puis remontee progressive ; feedback conserve. Essayer Amount 127, Release 32-64 sur notes espacees. Amount 0 : Delay standard. |
| Reverb ROOM | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | Room Send par piste / Decay / Tone. Petite ambiance stÃ©rÃ©o. ROOM au-dessus de PS1 ; relÃ¢chez TRACK pour appliquer. |
| Reverb PS1 | REVERB SEND / SIZE / FUNC + SIZE ou SETTINGS + SIZE | PS1 Send par piste / Decay / Tone. Queue stÃ©rÃ©o inspirÃ©e de PlayStation, sombre et granuleuse. |
| Chorus 1 / 2 | REVERB SEND / SIZE / FUNC + SIZE | Chorus Send par piste / Speed / Depth. Speed et Depth 0-127. Remplace la reverb du slot. |
| Delay standard | DELAY SEND / TIME / FUNC + TIME | Delay Send par piste / Time natif / Feedback natif. |
| Delay DUB | DELAY SEND / TIME / FUNC + TIME ou SETTINGS + TIME | Delay Send par piste / Time natif / Feedback. Echos stereo fortement filtres, de plus en plus etroits dans la boucle. Une source centree joue sur les deux canaux des le premier echo, meme sans feedback. |
| Delay POTS | DELAY SEND / TIME / FUNC + TIME | Echos mono de telephone de durchgemacht/model27 (MIT). Envoi natif / Time / Feedback. Delay lourd partage en MST et TRK ; Save Project conserve le choix. Un STOP conserve la queue ; double STOP la coupe. |
| Ping Pong | DELAY SEND / TIME / FUNC + TIME ou SETTINGS + TIME | Send par piste / Time / Feedback. Echos stereo alternes gauche/droite ; casque ou deux sorties. |
| Crusher Rate / Bits | CRUSH 1 ou 2 : TIME / FUNC + TIME | Rate 0-127, environ 750 Hz-48 kHz / Bits 2-16. Valeurs basses plus rugueuses. CRUSH 1 garde le direct propre ; CRUSH 2 melange direct propre/crushed. DELAY SEND affiche Crush Send ; pas d echo dans ces modes. |
| Reglages et sauvegarde FX | Sauvegarder le projet | Chaque pattern garde ses types FX, commandes ajoutÃ©es et envois supplÃ©mentaires. Sauvegardez le projet pour les retrouver au chargement. Pattern vierge : Delay/Reverb standard et commandes ajoutÃ©es par dÃ©faut. Les FX dâ€™un pattern en attente sâ€™appliquent au dÃ©but de sa lecture. Pas de destination p-lock/LFO pour les commandes ajoutÃ©es ; locks disponibles sur les envois natifs. |
| Routage FX par piste | Appui bref SETTINGS + TRACK > Global > FX > MST / TRK | MST partage les choix. TRK applique les gestes FX a la piste selectionnee ; reverbs/delays lourds natifs restent partages. Relacher TRACK valide ; BACK annule. Deux evenements encodeur par choix. Save Project conserve les choix du pattern. |
| Couper les queues FX | Appuyer deux fois sur STOP | Premier STOP : queues conservees. Double STOP : All Sound Off coupe les queues, PS1 compris. Geste stock corrige, pas nouveau raccourci. |

## Machines et commandes sonores

| Fonction | Commandes | Comportement |
|---|---|---|
| Parcours des machines | MACHINES, puis tourner DATA ; cliquer DATA pour valider en Sil | Mod Setup > Global > Mac : Sil conserve le son jusqu au clic DATA ; Stk applique chaque choix immediatement. Affichage natif conserve. MIDI Out en dernier. |
| Points de depart des machines ajoutees | Verifier la commande nommee | Les commandes numeriques comme Tone/Excite de TINY, Color/Contour de PUNCH et Wave/Warp/Noise/Motion de Elder vont de 0 au minimum a 127 au maximum ; 64 est le milieu. Les valeurs de depart ne sont pas forcement nulles. PITCH et FINE sont centres : 0 affiche signifie aucune transposition. Les selecteurs de modele SHAPE et les ratios PUNCH ont leurs propres echelles. Le minimum n est pas un reglage universel de son neutre. |
| Commandes Elder | Choisir Elder dans MACHINES | COLOR = Wave ; SHAPE = Warp ; SWEEP = Noise ; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate et Fine conservÃ©s. SynthÃ© original inspirÃ© de Junior de Fors. Valeurs de depart : Wave 0, Warp 0, Noise 0, Motion 0, Decay 50. |
| Commandes TINY | Choisir TINY dans MACHINES | COLOR : Tone ; SHAPE : Model 0â€“51 ; SWEEP : Mod ; CONTOUR : Excite. Valeurs de depart : Tone 64, Model 0, Mod 64, Excite 32, Decay 60. |
| Commandes Shadow | Choisir Shadow apres TINY dans MACHINES | COLOR : Grain ; SHAPE : Density ; SWEEP : Spread ; CONTOUR : Chaos. PUNCH : distorsion et attaque rÃ©pÃ©tÃ©e. Pitch, Fine, Decay et Gate disponibles. SynthÃ© pulsar/bruit inspirÃ© de Opal Dust de Fors. |
| Table initiale WAVE | Choisir WAVE et jouer | AV-WAVE-Morph est deja chargee : 16trames a parcourir, aucun import initial requis. COLOR choisit la position ; SHAPE ajoute le mouvement d enveloppe. Une table importee remplace la table initiale sur sa piste. |
| Dossiers WAVE | BACK dans le navigateur WAVE | BACK remonte dâ€™un dossier ; Ã  /Wavetables, il ferme le sÃ©lecteur. |
| ACID Decay et enveloppe | DECAY ; Global > ACID > A / F / AF | DECAY regle le declin du filtre. A choisit l ampli, F le filtre (defaut), AF les deux. En A/AF, Gate Off permet le declin pendant le maintien ; Gate On tient jusqu au note-off. Arpege et retrig relancent l enveloppe choisie. |
| Accent ACID | Velocite97-127 | Accent progressif du transitoire filtre et du niveau. Velocite0-96 conserve la reponse sans accent ; volume natif de velocite conserve. |
| Detune fin SY BITS | FUNC + COLOR | Pas de 0.01 demi-ton de -24.00 Ã  +24.00. COLOR change les demi-tons entiers ; FUNC + COLOR rÃ¨gle la fraction. Sauvegarde avec les sons et locks disponibles. |
| RETROSYN | MACHINES, juste avant MIDI Out | COLOR, SHAPE (six modÃ¨les), SWEEP et CONTOUR. PITCH, DECAY, Gate et Punch disponibles. |
| Commandes PUNCH | Choisir PUNCH avant MIDI Out | SHAPE choisit KIK, TOM, BNG, CNG, TAI, TIM, MAR, DJB, BLK, GNG, BUB ou ZAP. COLOR rÃ¨gle le timbre ; SWEEP choisit le ratio ; FUNC + SWEEP rÃ¨gle entre les ratios. CONTOUR et DECAY faÃ§onnent le son. Moteur de100demons, MIT. Valeurs de depart : Color 64, KIK, ratio 4:1, Contour 40, Decay 50. |
| Commandes ESTUS avancees | SETTINGS + COLOR / SHAPE / SWEEP / CONTOUR | Forme d onde / ratio FM / Drive / transitoire. Disponible en lecture. Maintenir un pas avec ce geste pour un lock avance. Certains moteurs ignorent certaines commandes. SETTINGS + MACHINES + SWEEP choisit toujours le filtre. |
| Glide ACID | Piste ACID choisie : SETTINGS + PITCH | OFF ou1-127, environ50-360ms. Les LEN chevauchees lient les notes. Defaut : environ50ms. Sauvegarde par piste avec le projet ; pas de locks de glide par pas. |
| Legato ACID | Piste ACID choisie : SETTINGS + DECAY | Gauche OFF, droite ON (defaut). ON : les notes ordinaires chevauchees ne relancent pas l enveloppe. Glide OFF change la hauteur immediatement. Legato OFF relance l enveloppe, meme avec glide actif. Arpege/retrig la relancent toujours. |

## Machine vocale SPEAK

| Fonction | Commandes | Comportement |
|---|---|---|
| Choisir SPEAK | MACHINES : apres Shadow, apres Shadow | Moteur vocal de 128 mots. Commencez vers Vol+Dist 60, Punch coupÃ©. |
| Voice / Word / Speed / Articulation | COLOR / SHAPE / SWEEP / CONTOUR | CaractÃ¨re vocal/formants / Word 0-127 / Speed (64 normal, plus bas plus lent) / Articulation. SHAPE affiche le mot et son index. Mot pris au prochain trig ; autres commandes en direct. |
| Hauteur et enveloppe | PITCH / notes ; DECAY, Fine, Punch, Gate, Attack | Hauteur indÃ©pendante de la vitesse. Commencez Ã  Decay 127 pour entendre les mots complets. Filtres et envois FX disponibles. |
| Sequences de mots et modulation | Maintenir TRIG + SHAPE, puis locks Pitch et autres commandes | Mot et autres parametres natifs acceptent p-locks et destinations LFO. COLOR/SHAPE/SWEEP/CONTOUR : MIDI CC 16/17/18/19. Espacer les mots ou augmenter Speed. |
| Exemple de phrase | Mots SHAPE et locks de notes sur des trigs successifs | HELLO 31, I 0, AM 62, A 17, ROBOT 113, I 0, LOVE 35, MUSIC 106. Lexique complet indexe a la fin du guide. |

## Commandes LFO et MACRO

| Fonction | Commandes | Comportement |
|---|---|---|
| Pages LFO audio | Appuis repetes sur LFO | Parcourt les LFO actifs. Global > LFOs choisit 1/2/3/4 (2 par defaut). LFO3/4 comme LFO2 ; reglages caches conserves. |
| Polarite et mode LFO | Menu LFO > Pol. / Mode | Bi = bipolaire ; Uni = unipolaire selon la profondeur signee. Modes FRE, TRG, HLD, ONE et HLF. Toutes les banques LFO participent a la copie, a l effacement et a Undo du son. |
| Sauvegarde LFO | Arreter ; Save Project pour les sons natifs | Save Project conserve les banques LFO ajoutees par pattern/piste, configuration LFO2 complete comprise. Donnees supplementaires a cote du projet ; les exports son/SysEx Elektron ne portent pas tous les reglages LFO ajoutes. Arreter et attendre la fin de sauvegarde avant extinction. |
| Assignation rapide LFO | Dans une page LFO : maintenir LFO et tourner un potard | Choisit sa destination ordinaire. Pour Attack/Filter/Resonance, maintenir aussi MACHINES. |
| Destinations Attack / Filter / Resonance | Dans LFO : LFO + MACHINES + DECAY / SWEEP / CONTOUR | Choisissez Attack, Filter ou Resonance avec la commande correspondante en maintenant MACHINES. |
| Accord fin MACRO | SETTINGS + PITCH | PITCH seul reste natif. FUNC + PITCH est Lo-Fi : frÃ©quence rÃ©duite Ã  gauche, bits rÃ©duits Ã  droite, centre OFF. Noms et numÃ©ros 0â€“46 des modÃ¨les visibles. |

## Sample Wizard et sauvegarde

| Fonction | Commandes | Comportement |
|---|---|---|
| PrÃ©Ã©coute sample | FUNC + MACHINES ; surligner un sample ; pad ou TRIG clavier | Ã‰coute le sample surlignÃ©. Le dÃ©filement reste silencieux. |
| Sample lock | Navigateur ouvert : surligner le sample, puis TRIG + MACHINES | Verrouille le sample choisi sur le pas de la piste Wizard. Le navigateur doit Ãªtre ouvert avec le sample surlignÃ©. |
| Modes de lecture | SETTINGS + MACHINES | One-Shot, Loop, Slice, Granular, Stretch, Pluck et Wavetable. SETTINGS + PUNCH ouvre les options du mode actif. Granular : COLOR Position, SHAPE Grain Size, SWEEP Density, CONTOUR Spray. Stretch utilise Speed au lieu de Position. |
| Affichage volume / pan | Accueil Sample Wizard : clic DATA | Alterne les barres de volume et panoramique gauche/droite. En lecture le pan suit la note et son p-lock. Affichage seulement. |
| Ã‰diteur Slice | FUNC + TRIG ; FUNC + clic DATA | FUNC avec une touche TRIG normale ou de l editeur joue les slices17-32 en mode Slice. FUNC + DATA supprime un marqueur dans l editeur. Les potards peuvent suivre les passages a zero. |
| Sauvegarde rapide permanente | Maintenir FUNC + SETTINGS | Ouvrir la sauvegarde permanente native du pattern. Raccourci stock ; distinct de la sauvegarde temporaire breve et de Save Project. |
| Copie temporaire / rappel | Bref FUNC+SETTINGS / FUNC+PATTERN | Copie temporaire native / rappel,y compris pendant le verrou retrig. |
| Reechantillonnage | Sur Sample Wizard : SETTINGS + REC | Ouvrir le menu Resample. Choisir les options d enregistrement et sauvegarder la prise depuis ce menu. |
| Priorite des p-locks | Verrouiller pitch, debut, fin ou autres commandes Wizard | La note ou boucle tenue conserve ses p-locks avant CTRL-ALL jusqu a la note suivante. CTRL-ALL modifie le son de base non verrouille. |
| Exporter une prise sauvegardee | Choisir le mode SMP ; rouvrir Elektron Transfer apres changement | Telecharger /Resampled/ en WAV 48 kHz. Stereo decodee ; gain reduit uniquement pour eviter l ecretage a l export. Sauvegarder les prises avant export. |

## Machine MIDI Out

| Fonction | Commandes | Comportement |
|---|---|---|
| Choix et rÃ©glages MIDI Out | MACHINES : MIDI Out ; FUNC + TRACK | Piste MIDI silencieuse. Track Setup : Channel, Output, KbT et Pad Note. DATA choisit ; clic avant Ã©dition ; BACK quitte. |
| Assignation CC et locks - MIDI Out seulement | SETTINGS + potard gris ; pas tenu + potard assignÃ© | Neuf potards CC. Tourner seul envoie la valeur. Chaque lock garde numÃ©ro et valeur ; enregistrement live des locks. Chance/Swing restent natifs. |
| Deux LFO MIDI | LFO : LFO 1, LFO 2, piste ; BACK quitte | DATA choisit, clic pour Ã©diter : Wav, Mul, Dst, Dep, Speed, Fade, Phase, Mode. LFO Speed rÃ¨gle le LFO ouvert ; LFO + CC choisit destination puis profondeur. |
| Notes et sauvegarde | Notes/grille habituelles ; FUNC + PAGE ; FUNC + SETTINGS | EntrÃ©e MIDI par canal de piste ou auto ; live/step record gardent notes, vÃ©locitÃ© et longueur. FUNC + PAGE : longueur. Sauvegarde projet : rÃ©glages et locks MIDI. |
| MIDI OUT + THRU | CONFIG â†’ MIDI â†’ PORTS â†’ OUT/THRU : THR ; puis FUNC + clic DATA | Bascule la sortie MIDI propre du Cycles en conservant le MIDI Thru entrant. |
| Enregistrer un clavier externe | CONFIG > MIDI : activer reception ; canal de piste ou canal auto | Channel dans Track Setup est le canal de SORTIE, pas de reception. Notes entrantes vers Output. Live : notes, velocite et duree. Step Recorder : arret, double REC, jouer puis relacher pour avancer. |
| Details enregistrement CC | SETTINGS + un des neuf potards CC ; TRIG tenu + potard assigne | OFF ou CC0-127 ; valeurs0-127. Pas vides convertis en locks seuls. Numero et valeur conserves. Chance/Swing restent natifs ; LFO Speed regle le LFO MIDI ouvert. |
| Destination du LFO MIDI | LFO > DATA pour choisir ; clic pour modifier ; BACK pour sortir | Destination OFF ou CC0-127. Edition de destination suspend la sortie de ce LFO jusqu a la sortie du champ. Autres potards CC actifs. |
| Arpege clavier | FUNC + RETRIG > Arp ; activer A. On ou maintenir RETRIG | Jouer les notes MIDI entrantes via le mode d arpege choisi. |
| Retour audio | Choisir une machine audio dans MACHINES | Notes MIDI tenues/sequencees fermees sur leur canal et port initial. Commandes de la machine audio disponibles. |

## Mod Setup

Appuyez brièvement sur SETTINGS + TRACK puis relâchez pour ouvrir Mod Setup. Maintenez la combinaison pour lancer SCRAMBLE une seule fois ; le maintien ne répète pas le tirage. Avec un TRIG tenu, un appui bref bascule sa marque Scramble. Choisissez Global, Track ou Song. DATA choisit une ligne ; clic pour modifier, tourner, puis clic pour revenir. Stk = Stock ; SIL = Silent ; LTC = Latch.

| Fonction | Commandes | Comportement |
|---|---|---|
| Global / Track / Song | DATA entre ; BACK revient | Global : Pad, Mac, USB, Num, Mute, Dly, DX, QntM, Grv, LFOs, FX, ACID si installe, JUMP. Track : SCRM, S.Chn, Human. Song ouvre la grille d arrangement. GOV choisit l ordre des coupures de voix. |
| AccÃ¨s et rÃ©glage du son | Appui bref sur SETTINGS + TRACK | Disponible depuis lâ€™Ã©cran principal ou la sÃ©lection des machines. DATA parcourt Mod Setup ; les commandes du son affichent le paramÃ¨tre deux secondes puis reviennent Ã  la mÃªme position. BACK ferme dâ€™abord la fenÃªtre puis Mod Setup ; la sÃ©lection des machines reste ouverte en dessous. |
| Mac | Sil / Stk | Parcours : Sil demande un clic DATA ; Stk applique pendant le parcours. Sauvegarde globale a l arret de la lecture/enregistrement. |
| Pad | Stk / SIL ; dÃ©faut Stk | Stk sÃ©lectionne et joue. SIL sÃ©lectionne silencieusement ; TRACK + pad sÃ©lectionne et joue. ChordKeys exige TRACK + pad pour quitter la piste. |
| USB | 2ch / 6ch ; dÃ©faut 2ch | 2ch : mix stÃ©rÃ©o avec effets. 6ch : six pistes mono avant panoramique, sans retours delay/crusher/reverb/chorus. Retour ordinateur stÃ©rÃ©o dans les deux modes. ArrÃªtez avant de changer ; le pÃ©riphÃ©rique USB se reconnecte. |
| Num | Off / On ; dÃ©faut Off | On affiche volume et panoramique en chiffres ; Off garde lâ€™affichage natif. |
| Mute | Stk / LTC ; dÃ©faut Stk | LTC : TRACK + appui FUNC verrouille ; FUNC quitte. FUNC + pad en mute verrouillÃ© : solo ; rappuyer ou quitter restaure les mutes. |
| Mute/solo quantifiÃ©s | SETTINGS + TRACK bref ; QntM | Activez ou dÃ©sactivez-le et choisissez la division temporelle sur laquelle vos mutes et solos sont quantifiÃ©s. DÃ©sactivÃ© par dÃ©faut. |
| Delay | Stk / Div ; dÃ©faut Stk | Stk : Time natif. Div : divisions musicales, pointÃ©es et triolets. Positions correspondantes corrigÃ©es au tempo ; toutes les positions ne sont pas quantifiÃ©es. UtilisÃ© en mode Delay. |
| DX | Off / On ; dÃ©faut Off | Global DX On active SETTINGS + BACK. PAGE parcourt charge CPU, coupures recentes de toutes les pistes et totaux. DATA efface ; double BACK quitte. Transport, potards et trigs restent actifs ; BACK simple conserve l annulation. DX Off interdit l acces. |
| SCRM | DATA ouvre ; tourner et appuyer ; BACK revient | Six cases par piste : Pitch, Decay, Color, Shape, Sweep, Contour. Pitch/Decay dÃ©sactivÃ©s par dÃ©faut, Color/Shape/Sweep/Contour activÃ©s. Six listes propres Ã  chaque pattern ; Save Project les conserve au chargement. Wizard autorise Pitch/Decay, commandes sample/modes exclues. |
| Routage Sidechain | Choisir la source ; SETTINGS + TRACK bref ; S.Chn > DATA | Cochez les cinq autres pistes, Rev. (retour reverb) et/ou Del. (retour delay). DATA bascule chaque cible. Dpt/Atk/Hld/Rel et Mute concernent toutes les cibles choisies. Choix sauvegardes par source et pattern avec Save Project. Plusieurs sources : attenuation la plus forte par cible. DUCK reste un type de delay distinct. |
| Dpt / Atk / Hld / Rel | Sous les cases : clic DATA, tourner, puis clic pour finir | Dpt = profondeur, Atk = attaque, Hld = maintien, Rel = relÃ¢chement. Depth : 0â€“100 %, 16 niveaux. Atk : 0â€“160 ms. Hold : 0â€“120 ms. Rel : 10 msâ€“3 s. BACK termine lâ€™Ã©dition puis revient Ã  Mod Setup. DÃ©part conseillÃ© : source sur chaque temps, Depth 60 %, Attack 0 ms, Hold 0 ms, Release 150 ms. DÃ©cocher toutes les cibles dÃ©sactive la source. |
| Mute (Sidechain) | Choisir la source ; S.Chn > Mute ; clic DATA | On : mute ou exclusion par solo bloque les trigs de sequence de la source. Les pads/TRIG joues manuellement declenchent toute l enveloppe. Off : la sequence mutee continue aussi d attenuer (defaut). Sauvegarde par source et pattern avec Save Project. |
| Sauvegarde par pattern | Save Project aprÃ¨s modification | Routage et commandes Sidechain, six listes Scramble, types et rÃ©glages FX ajoutÃ©s propres Ã  chaque pattern. Sauvegardez le projet pour les conserver au chargement. Pattern vierge : Sidechain dÃ©sactivÃ© et listes Scramble par dÃ©faut. Changement en attente appliquÃ© au dÃ©but du prochain pattern. |
| Groove | Global > Grv > On / Type | Off conserve Swing natif et memorise Type. On active Boom Bap, Disco, Reggae, Bongo, Caixixi, Highlife ou Kuduro ; Swing dose la force. Pas de Swing natif dans Type. |
| CHORD Strum | Global > Grv > Str | -80..80 ms entre voix CHORD ; le signe inverse le sens,0 joue ensemble. Independant de Groove On/Off. Quatre voix a80ms etalees sur240ms. |
| Humanize Apply / Undo | Track > Human > Trk / Tim / Vel / Apply / Undo | Reglez temps/velocite0..100 par piste ou All. A l arret, Apply modifie le pattern et Undo retablit les valeurs. Aucun aleatoire en lecture. |
| Nombre de LFO audio | Global > LFOs | 1/2/3/4 par piste audio ; 2 par defaut. Sauvegarde globale a l arret. LFO inactifs arretes, reglages conserves. |
| Mode FX | Global > FX > MST / TRK | MST utilise les choix partages ; TRK suit la piste selectionnee pour les FX legers. Reverbs/delays lourds natifs restent partages. Memes gestes TRACK + SIZE/TIME. |
| Enveloppe ACID (Full / Machine Optional) | Global > ACID > A / F / AF | Un choix global sauvegarde pour toutes les pistes ACID. A = ampli ; F = filtre (defaut) ; AF = les deux. Gate OFF laisse decroitre l ampli en A/AF ; ON maintient jusqu au note-off. Sauvegarde a l arret et au repos. Lite ne contient pas ACID. |
| JUMP | Global > JUMP > Off / On | Preference Direct Pattern Jump ; sauvegarde globale a l arret. |
| GOV | Global > GOV > Lod / Trk ; defaut Lod | Lod garde la voix admissible la plus faible. Trk coupe la piste admissible de plus petit numero quand une coupure est necessaire. Sauvegarde globale a l arret ; admissibilite, seuils et fondus conserves. |
| Track > Swap | From / To / Swap | Echange deux pistes du pattern courant a l arret. |

BACK ferme Mod Setup et sauvegarde ses préférences globales ; en lecture, cette sauvegarde attend l’arrêt. Arrêtez et attendez la fin avant extinction. Routage/réglages Sidechain, listes Scramble et types/réglages FX ajoutés propres à chaque pattern : Save Project les conserve au chargement. Fermer un sous-menu ne sauvegarde pas le projet.

## Affichage Sample Wizard

| Fonction | Commandes | Comportement |
|---|---|---|
| Forme d onde et volume | Ecran principal Sample Wizard | Nom en haut ; grande forme d onde ; piste, duree et rectangles de volume en bas. Volume de la piste, pas un vumetre audio. Navigateur, Pitch/Fine et saisie des notes gardent leurs commandes. Marqueur Start/Position si applicable. |

## Extras Machine Optional uniquement

| Fonction | Commandes | Comportement |
|---|---|---|
| Disponibilite | Full / Lite principal et Machine Optional | Full et Lite utilisent les moteurs audio indiques. Les commandes LEGACY, ChordKeys et Vinyl s appliquent si ces choix sont actifs dans Machine Optional. |
| Banques LEGACY | LEGACY : FUNC + MACHINES | DATA choisit une banque DX7 ; clic charge, BACK annule. Une banque32voix partagee par toutes les pistes Legacy. Importer via le flasheur Optional. |
| ChordKeys | CHORD : FUNC + RETRIG > Keys ON | Hors grid record, TRIG1-16 jouent les accords de la gamme. TRACK + pad change de piste. Grid : TRIG tenu + T1-T6 verrouille l harmonie ; meme pad a nouveau restaure l harmonie de base. Keys On, harmonie et reglages associes sont sauvegardes par pattern/projet ; sauvegarder avant extinction. |
| Vinyl | SIZE / FUNC + SIZE / FUNC avant TRACK + SIZE | Crackle / intensite Warble / vitesse Warble. REVERB SEND dose Vinyl. Absent du principal Full/Lite. |
| TRX-B2 / TRX-SD / TRX-CH | Choisir dans Machine Optional ; fournir votre OS Machinedrum UW1.63 | Trois moteurs : grosse caisse, caisse claire et charley ferme. Le fichier MD est requis au build. Optional conserve LEGACY, ChordKeys et Vinyl. |

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

Défauts : pads et mute stock ; USB 2ch ; Num Off ; DX Off ; mute/solo quantifiés Off. Les patterns vierges utilisent Reverb et Delay standard et les réglages ajoutés par défaut. USB six canaux sans retours stéréo des effets.
