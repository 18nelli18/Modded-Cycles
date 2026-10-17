# Guide des raccourcis des nouvelles fonctions

A.V.’s Supermodel Edition · 16 octobre 2026

Gestes ajoutes uniquement ; transports, copies, effacements et collages calques sur le stock omis.

Installez la fonction correspondante. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. MACHINES est le bouton parfois nomme PRESET dans les instructions du sampler.

## Performance et son

| Fonction | Geste | Resultat |
|---|---|---|
| Control All Config | TRACK + TRIG 1–6 | Inclure ou exclure les pistes de Control All. L exception native de la piste active reste applicable. Choix remis a zero a extinction. |
| Control All Beat Repeat | Tenir TRACK + RETRIG, puis un TRIG 1–16 | Repeter les pistes audio incluses. Dernier TRIG tenu prioritaire, division en popup bref. Relacher le TRIG ou un modificateur arrete. Garder les deux modificateurs tenus. |
| Mute verrouille | Tenir TRACK, taper FUNC | Garder le mode mute ouvert. Taper FUNC pour sortir. |
| Preecoute d un pas | A l arret ou en pause, tenir TRIG + PAGE | Ecouter le pas et ses locks. |
| Slides audio | SETTINGS + TRIG | Activer/desactiver le slide de parametres du pas. |
| Attack synth | MACHINES + DECAY | Regler l attaque ajoutee sur les pistes synth/drum compatibles. |
| Filtre par piste | MACHINES + SWEEP / CONTOUR | Coupure / resonance. Ajouter TRACK pour Control All des pistes audio incluses. Neutre : coupure maximale et resonance nulle. |
| Lo-fi MACRO | FUNC + PITCH sur MACRO | A gauche : frequence d echantillonnage ; a droite : profondeur en bits. |

### Divisions du beat repeat

| TRIG | Division | TRIG | Division |
|---|---|---|---|
| 1 | 1/64 | 9 | 3/16 |
| 2 | 1/48 | 10 | 1/4 |
| 3 | 1/32 | 11 | 1/3 |
| 4 | 1/24 | 12 | 3/8 |
| 5 | 1/16 | 13 | 1/2 |
| 6 | 1/12 | 14 | 2/3 |
| 7 | 1/8 | 15 | 3/4 |
| 8 | 1/6 | 16 | 1 mesure |

Les longues boucles audio sont divisees par deux aux tempos lents selon la capacite du buffer. Le repeat audio publie ne repete pas les notes MIDI ; le test ci-dessous ajoute les notes B.

## Sequence Genie, SCRAMBLE et modulation

| Fonction | Geste | Resultat |
|---|---|---|
| Sequence Genie | SETTINGS + PAGE | Generateur de la piste audio ou voie B selectionnee. DATA choisit ; clic, tourner, clic pour editer. Queue choisit les frontieres Loop/Page. |
| SCRAMBLE A | SETTINGS + TRACK | Randomiser quatre parametres de synthese. Sampler exclu. |
| SCRAMBLE de pas A | Tenir des TRIG, puis SETTINGS + TRACK | Basculer des valeurs aleatoires fraiches a chaque passage, son de base conserve. |
| SCRAMBLE B | SETTINGS + TRACK | Randomiser les valeurs CC assignees de la voie MIDI selectionnee. |
| Second LFO | Appuyer deux fois sur LFO | Ouvrir LFO 2. Dans cette page, LFO SPEED regle LFO 2. |
| Assignation rapide LFO 2 | Sur LFO 2 cote A, tenir LFO et tourner un parametre | Choisir la destination, puis regler sa profondeur signee. |
| Scale Lock | FUNC + PAGE | Acceder aux reglages ajoutes de gamme/tonalite avec le support performance installe. |
| Arpege / reglages ChordKeys | FUNC + RETRIG | Options ajoutees direction/octaves ou ChordKeys selon la fonction installee. |
| Jeu de l arpege | Tenir RETRIG avec des notes tenues | Arpeger les notes ; option A.On pour le verrouillage. |
| ChordKeys | Sur CHORD, jouer TRIG 1–16 | 1–7 : I–VII ; 8–14 : octave superieure ; 15–16 : I–II deux octaves plus haut. |

## Sample Wizard et preecoute

| Fonction | Geste | Resultat |
|---|---|---|
| Sample lock | Tenir TRIG + MACHINES | Choisir un sample lock de ce pas sur une piste Wizard. |
| Modes de lecture | SETTINGS + MACHINES | Ouvrir les modes du sampler. |
| Options du mode | SETTINGS + PUNCH | Ouvrir les options du mode sampler choisi. |
| Reechantillonnage | SETTINGS + REC | Ouvrir le resampling. |
| Sample Preview — teste sur machine | FUNC + MACHINES ; choisir un sample puis jouer pad ou TRIG clavier | Preecoute du sample dans le navigateur Wizard. Defilement seul silencieux. Compatible ChordKeys/WAVE. |
| Editeur slices : slices hautes | FUNC + TRIG 1–16 | Jouer les slices 17–32 dans l editeur. |
| Editeur slices : passage zero | FUNC + potards marqueurs 1 / 2 | Caler le marqueur correspondant au passage zero. |
| Editeur slices : retirer marqueur | FUNC + clic DATA | Retirer un marqueur. DATA seul divise ; PUNCH controle le tap slicing. |

## MIDI B et routage

| Fonction | Geste | Resultat |
|---|---|---|
| Entrer / sortir de B | FUNC + SETTINGS + TRACK | Ouvrir/fermer les six pistes MIDI paralleles. Sortie depuis l accueil B ; BACK y sort aussi. |
| Assignation CC MIDI | SETTINGS + potard gris | Assigner un CC au potard sur la voie B choisie. |
| Lock CC MIDI | Tenir TRIG + potard assigne | Ajouter un lock CC sur le pas MIDI. |
| Slides notes / CC | SETTINGS + TRIG | Activer/desactiver le slide : notes chevauchees en legato, CC glisses vers le pas marque. |
| Reglages clavier MIDI | FUNC + TRACK | Transposition clavier et Pad Note. |
| Second LFO CC MIDI | Appuyer deux fois sur LFO cote B | Ouvrir LFO CC 2. Dst : clic DATA, OFF ou CC0–127, clic DATA pour confirmer ; BACK annule. |
| MIDI OUT + THRU combines | CONFIG → MIDI → PORTS → OUT/THRU : THR, puis FUNC + clic DATA | Basculer la sortie MIDI propre du Cycles tout en gardant le Thru entrant. |

Le MIDI sauvegarde charge uniquement en entrant cote B, lecture arretee. Arreter avant Save Project et attendre MIDI SAVED. Les fichiers MIDI annexes ne sont pas inclus dans les backups SysEx Elektron.

## Test MIDI performance separe

Ces deux ajouts experimentaux sont uniquement sur la [page de test MIDI performance](../flasher-midi-performance-test/?v=2026-10-16-midi-performance-test-1), profil fixe six voix 909 et quatre WAV locaux.

| Fonction | Geste | Resultat |
|---|---|---|
| Beat repeat MIDI | Tenir TRACK + RETRIG, puis TRIG division | Repeter la derniere note sequencee des voies B incluses, canal/port actuels. Relacher arrete les notes. Pas de capture de phrase ; sortie MIDI native A hors de ce test. |
| Filtre Control All depuis B : audio + MIDI | Cote B, tenir TRACK + MACHINES et tourner SWEEP / CONTOUR | Filtres audio internes inclus et CC74 / CC71 aux instruments B configures. Voies MIDI muettes sans CC ; filtres audio toujours modifies. |
