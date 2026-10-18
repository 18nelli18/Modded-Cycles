# Vue d’ensemble des fonctions et raccourcis

A.V.’s Supermodel Edition · 17 octobre 2026

Gestes ajoutes uniquement ; transports, copies, effacements et collages calques sur le stock omis.

Installez la fonction correspondante. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. MACHINES est le bouton parfois nomme PRESET dans les instructions du sampler.

## Vue d'ensemble actuelle

Flasheur principal 1.83 · mise à jour du 17 octobre 2026. Installez les fonctions souhaitées ; le flasheur vérifie les combinaisons compatibles. [Supermodel 909 Edition](../flasher-supermodel-909/) possède sa propre sélection et sa propre version.

| Fonction | Comportement actuel |
|---|---|
| Machines ajoutées | MACRO, ACID, WAVE, TINY, RETROSYN et les moteurs dérivés du Syntakt au choix. Ces derniers nécessitent votre propre fichier OS Syntakt. |
| Swarm LITE | Remplace les sept oscillateurs par trois : fondamentale et deux dents de scie désaccordées. Charge CPU réduite, son plus fin et parfois moins fort ; des arrangements lourds peuvent encore cliquer. |
| Sample Wizard | Sampler indépendant avec sample locks, modes, découpage et rééchantillonnage. Sample Preview est testé sur machine. Model-TG est retiré du flasheur principal. |
| RETROSYN / ChordKeys | Six types d'oscillateurs rétro ; ChordKeys ajoute accords selon la gamme et voicings. Combinez librement les machines ajoutées ; seules les machines cochées apparaissent. Sample Wizard reste facultatif. |
| Filtre par piste / Synth Attack | Coupure, résonance et attaque ajoutées ; locks de filtre et Control All. Le filtre publié inclut la correction de distorsion après avoir quitté Sample Wizard. |
| Control All Config / Beat Repeat | Choix des pistes audio incluses ; répétition momentanée sur seize divisions, avec popup bref de la division. |
| Banque MIDI Out — expérimentale | Six voies MIDI parallèles : CC et locks, slides, retrigger/arpège, chance, deux LFO MIDI et sauvegarde annexe au projet. Facultative et installable sans beat repeat. Le beat repeat peut aussi être installé sans Banque MIDI. |
| Sequence Genie / SCRAMBLE | Génération ou mutation de séquences, attente d'une frontière Loop/Page, randomisation audio ou CC côté B. |
| Arpégiateur / Second LFO | Arpège des notes tenues et page de modulation supplémentaire. Oct 0 parcourt seulement les notes tenues ; 1–3 ajoutent des octaves. Confirmé sur les deux côtés. |
| Performance et édition | Mutes verrouillés, préécoute de pas, slides, noms défilants, navigateur trois lignes, volume/pan chiffrés, trigless atténués et délai de suppression des trigs. |
| Routage / tempo / démarrage | Audio USB six canaux, MIDI OUT + THRU combinés, tempo jusqu'à 546 BPM et choix d'animation de démarrage. |

**Sauvegarde :** maintenez **FUNC + SETTINGS** pour la sauvegarde permanente stock restaurée. La correction confirmée empêche aussi FUNC de rester verrouillé à la fermeture du menu. Pour les données MIDI, arrêtez la lecture avant de sauvegarder et attendez **MIDI SAVED**. Le MIDI sauvegardé charge **uniquement en entrant côté B, lecture arrêtée** ; les fichiers annexes sont hors backups SysEx Elektron.

**Diagnostics :** les affichages CPU/pic/CUT sont réservés aux builds de test et absents du principal.

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
| Lo-fi MACRO | FUNC + PITCH sur MACRO | A gauche : frequence 46K–4K ; a droite : profondeur 12B–2B ; centre OFF. Valeur affichee dans la fenetre. |

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

## Changements confirmés — publiés dans le principal 1.83

[Ouvrir le test Octave 0 + curseur MIDI B](../flasher-arp-zero-test/?v=2026-10-17-arp-zero-test-2).

| Changement | Vérification |
|---|---|
| Octave 0 sur A et B | FUNC + RETRIG → Oct. 0 parcourt uniquement les notes tenues ; 1 ajoute une octave, 2 en ajoute deux, 3 en ajoute trois. Les anciens réglages conservent leur son ; seule la numérotation affichée change. |
| Première entrée B / curseur | Ouvrir B pendant la lecture ; vérifier que le MIDI démarre sans sortir/rentrer et que REC montre un seul curseur. Chaque voie conserve sa longueur et sa vitesse. |
| Configuration du test | Garder Control All Beat Repeat sélectionné avec Banque MIDI dans ce test combiné. Cette obligation ne concerne pas le principal. Les diagnostics CPU/pic/CUT restent disponibles dans le test. |

Octave 0, le curseur B et la correction du crash ont été confirmés par AveyCole dans le test 2 et sont publiés dans le principal 1.83. Le chargement MIDI sauvegardé exige toujours la lecture arrêtée. Le beat repeat MIDI et le filtre MIDI ont été abandonnés et ne font pas partie de ce test.
