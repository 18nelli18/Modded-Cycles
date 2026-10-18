# Supermodel 909 — fonctions et raccourcis

909.5 · 18 octobre 2026

Profil fixe909 : six voix909, Sample Wizard, ACID, filtre par piste, slides, Sequence Genie, SCRAMBLE, Second LFO, Banque MIDI avec sauvegarde, MIDI OUT + THRU, mutes verrouilles, Control All Config, Control All Beat Repeat, arpegiateurs A/B et demarrage909. Charger OS Cycles1.13 officiel et quatre WAV locaux : hats ferme/ouvert, crash et ride. Aucun sample audio heberge.

Fonctions partagees alignees sur main1.89 : correction transition filtre, sauvegarde permanente stock (tenir FUNC + SETTINGS), Oct0 A/B, premiere entree B en lecture et curseur REC unique. Longueur normale commune A/B et editable des deux cotes. Dans B, FUNC + PAGE ouvre Len : appuyez sur DATA avant de tourner, ou PAGE par16 meme hors edition. Mode par piste : longueurs MIDI independantes. LEDs selon REC natif ; ouverture B sur la page A en mode normal. Vitesses MIDI independantes. Corrections main confirmees sur machine ; integration909 verifiee en emulation. Aucun affichage diagnostic dans cette version.

Arreter avant sauvegarde MIDI et attendre MIDI SAVED. Le MIDI sauvegarde charge uniquement en entrant B, lecture arretee ; fichiers annexes hors backups SysEx Elektron.

Raccourcis ajoutes ci-dessous ; transports/copies/effacements/collages stock omis. TRIG = pas, pad = piste, DATA = LEVEL/DATA.

## Performance et son

| Fonction | Geste | Resultat |
|---|---|---|
| Control All Config | TRACK + TRIG 1–6 | Inclure ou exclure les pistes de Control All. La piste sélectionnée peut aussi être exclue. Choix remis a zero a extinction. |
| Control All Beat Repeat | Tenir TRACK + RETRIG, puis un TRIG 1–16 | Repeter les pistes audio incluses. Dernier TRIG tenu prioritaire, division en popup bref. Relacher le TRIG ou un modificateur arrete. Garder les deux modificateurs tenus. |
| Mute verrouille | Tenir TRACK, taper FUNC | Garder le mode mute ouvert. Taper FUNC pour sortir. |
| Preecoute d un pas | A l arret ou en pause, tenir TRIG + PAGE | Ecouter le pas et ses locks. |
| Slides audio | SETTINGS + TRIG | Activer/desactiver le slide de parametres du pas. |
| Attack synth | MACHINES + DECAY | Regler l attaque ajoutee sur les pistes synth/drum compatibles. |
| Filtre par piste | MACHINES + SWEEP / CONTOUR | Coupure / resonance. Ajouter TRACK pour Control All des pistes audio incluses. Neutre : coupure maximale et resonance nulle. |

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

Les longues boucles audio sont divisees par deux aux tempos lents selon la capacite du buffer. Le beat repeat agit sur l’audio interne et ne répète pas les notes MIDI sortantes.

## Sequence Genie, SCRAMBLE et modulation

| Fonction | Geste | Resultat |
|---|---|---|
| Sequence Genie | SETTINGS + PAGE | Generateur de la piste audio ou voie B selectionnee. DATA choisit ; clic, tourner, clic pour editer. Generate est premier, Queue second. Loop attend la prochaine boucle de piste ; Page, la prochaine page de 16 pas. |
| SCRAMBLE A | SETTINGS + TRACK | Randomiser quatre parametres de synthese. Sampler exclu. |
| SCRAMBLE de pas A | Tenir des TRIG, puis SETTINGS + TRACK | Basculer des valeurs aleatoires fraiches a chaque passage, son de base conserve. |
| SCRAMBLE B | SETTINGS + TRACK | Randomiser les valeurs CC assignees de la voie MIDI selectionnee. |
| Second LFO | Appuyer deux fois sur LFO | Ouvrir LFO 2. Dans cette page, LFO SPEED regle LFO 2. |
| Assignation rapide LFO 2 | Sur LFO 2 cote A, tenir LFO et tourner un parametre | Choisir la destination, puis regler sa profondeur signee. |
| Scale Lock | FUNC + PAGE | Acceder aux reglages ajoutes de gamme/tonalite avec le support performance installe. |
| Reglages arpege A/B | FUNC + RETRIG | Cotes A et B : direction et Oct0–3 ; Oct0 joue seulement les notes tenues. |
| Jeu de l arpege A/B | Tenir RETRIG avec des notes tenues | Arpeger les notes ; option A.On pour le verrouillage. |

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

