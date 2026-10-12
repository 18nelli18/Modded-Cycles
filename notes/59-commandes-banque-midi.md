# 59 — Commandes de la banque MIDI, candidat du 12/10/2026

Demandes AveyCole : clavier hors REC selon gamme, LED pads, slides legato,
PAGE borné par longueur et réglages déplacés dans FUNC + PAGE. Adresses :
VA de l'OS 1.13. Ce candidat est expérimental, non testé sur matériel.

## 1. Interface et clavier

FUNC + SETTINGS + TRACK ouvre/ferme la banque. REC actif garde la grille ;
REC inactif joue le clavier MIDI privé. Le getter REC natif 0x4006b978 est
exécuté. La formule d'octave reprend celle du clavier stock. Le wrapper
mlp_scale_note appelle directement snap_note Model-TG : aucune seconde table
musicale. La preuve du bundle exécute cinq gammes × douze tonalités × 128
notes. Les résultats hors MIDI 0..127 sont refusés avant publication.

La file clavier privée (320 octets) est consommée par la tâche MIDI IPL0,
séparément des notes du séquenceur. Release après changement de voie/REC,
ancienne touche après nouvelle, tap avant consommation, fermeture et entrée
TEMPO/LFO/REC sont couverts sans note-on retardé. Les handlers globaux sont
transmis ; leur comportement complet dans la pile UI réelle reste à tester.

## 2. Affichage, longueur et slides

Le rendu stock reste TR7..TR12 avec badge B. FUNC + PAGE ouvre Scale Setup
natif avec onze réglages privés, quatre lignes défilantes. DATA hors menu
sélectionne le pas ; il n'ouvre plus les réglages. PAGE ne visite que les
pages couvertes par la longueur, et la réduction de longueur borne la
sélection sans effacer les pas masqués.

SETTINGS + TRIG bascule flags bit 1 et conserve bit 0 note actif. Note On
suivant précède Note Off précédent sur un slide de hauteur différente ;
même hauteur = retrigger. Stop et réserve note-off restent prouvés.

## 3. LED pads sans données audio

Mapping natif 0x400060bc / vecteur 0x404a8ba0 : six pads. Writer first-wins
0x40005f86 et pulse 0x4008e8c4, exclusivement dans le callback UI LED.
Le pad sélectionné reçoit couleur 3, les autres couleur 1, comme la vue
stock étudiée. Un compteur de note acceptée par voie réveille le poll UI
borné à six compteurs, puis pulse une seule fois le pad correspondant.
L'interruption ne dessine rien, n'alloue rien et n'appelle aucun writer.
Les seize trigs gardent leur mapping et leur curseur indépendant.

[FAIT en émulation] Six voies × quatre pages, claims big-endian, mapping et
writer natifs, dispatcher RTTI réel, priorité B-side et restauration de la
vue audio après retrait. Pulses indépendants et cent polls sans changement
ne redessinent pas. Le test runtime mesure au plus 200 instructions pour
ml_pattern_tick ; ce n'est pas une mesure du temps matériel.

## 4. Validation et publication séparée

Bundle complet TG/ST : boot, décompression/copie/cache, scheduler natif,
worker dédié, DIN/USB OUT et THRU, banques par pattern et raccourci TRACK.
Tests clavier, runtime, LED et rendu natif ; navigateur EN/FR et contrôles
Select All/OS Cycles + Syntakt. Envois simulés complets de 672 blocs avec
banque et 667 sans banque ; firmware sans banque identique à main.

Page candidate : docs/flasher-midi-controls-test/. Elle utilise les mêmes
builder.js, tweaks.js, flasher.js, app.js et style.css que main, leurs hashes
Git étant vérifiés égaux aux fichiers distants avant publication. La page
et son bundle sont séparés de flasher-midi-test, chargé par main. Aucune
image OS n'est distribuée, aucun statut matériel n'est ajouté.

## 5. Sauvegarde en chantier

[FAIT en émulation] audit_midi_storage_write.py exécute le wrapper natif
0x4007bb0a : ordre lock/write/unlock, arguments, incrément d'offset seulement
pour un résultat positif, écritures partielles, zéro/erreur et refus système
absent/handle fermé/non inscriptible. Backend et sémaphore simulés : aucun
disque écrit, aucune preuve de fermeture durable ou de création du chemin.

[À FAIRE] Save/Save As/load, clé projet stable et isolation, tâche stockage,
création/fermeture durable et reprise après interruption. La banque reste
RAM seulement : un projet par session, redémarrer avant de changer de projet.
LFO vers CC cutoff et intégration Sequence Genie B-side restent à faire.
AveyCole demande explicitement Sequence Genie après ce prochain test.

Suite locale après publication du candidat : le test exécute aussi close
0x4007bc1c et son helper natif 0x4007ed7c. Ils annulent le drapeau du handle
et son bit dans 0x40fe8e10, sans flush explicite. Un résultat close=0 ne
suffit donc pas à conclure à la durabilité : la prochaine preuve doit suivre
le writer sous-jacent jusqu'au stockage, avant raccordement Save/Save As.

## 6. Testé sur la machine (12/10/2026)

AveyCole demande : « Publish current midi test build as hardware tested. »
Cette validation porte sur le candidat publié d6afc841, MAIN OS SHA-256
2c7c7f74fa45cb38719cc60bfa65f70f725ace756ec8003c0e724e2167c7f9c0.
Promotion du statut de ce candidat uniquement, sans changement de code
firmware. Sauvegarde persistante et Sequence Genie B-side ne sont ni inclus
ni validés par ce résultat. La page principale garde son bundle existant.

## 7. Adaptateur Genie B en préparation, non publié

`genie.s` / `test_midi_lane_genie.py` : conversion d'un tableau de notes
Genie vers une voie candidate privée de 264 octets. Longueur 1..64 égale à
celle de la voie ; 254 conserve, 255 repose, nouvelles notes 36..96. Note
active conserve slide mais force bit note ; vélocité invalide devient 100,
gate invalide devient 1. Source et pas hors longueur restent intacts.
Validation complète avant écriture ; buffers superposés et IPL>0 refusés.
Preuve ColdFire sur longueurs 1/16/17/32/48/64 et erreurs au dernier pas.
Aucune entrée audio, p-lock natif ou file MIDI n'est touchée. Non raccordé au
menu/bundle ; publication, undo, queue et options avancées restent à faire.

## 8. Régression FUNC + pad signalée après validation

AveyCole rapporte que FUNC + pad côté B coupe les pistes audio A au lieu
MIDI OUT B. La promotion de main demandée juste avant ce signalement reste
en attente de correction : aucune nouvelle sélection firmware dans main.

[HYP confirmée par contrat de callback] FUNC retournait 0, laissant ouvrir
QuickMuteMenu audio au-dessus de la banque. Le candidat consomme maintenant
appui/release FUNC B ; seul le release initial d'un FUNC tenu en A lors de
l'entrée est transmis une fois. Désactivation MIDI OUT libère la file de
séquence ET celle du clavier et réveille le worker. La preuve focalisée
exécute les callbacks sur les six voies : répétition idempotente, notes-off
et données audio intactes. Le dispatch supérieur réel et le résultat
matériel restent à vérifier, donc le candidat corrigé est expérimental.


## 9. Genie côté B et affichage, candidat du 12/10/2026

AveyCole confirme la correction mute sur matériel, mais signale la perte
de sortie FUNC + SETTINGS + TRACK. Le getter de banque accepte désormais
son état FUNC privé, sans dépendre du bit natif consommé par le correctif.
TR10–TR12 utilisent la police stock compacte au même centre : le grand
texte dépassait la zone droite. Le rendu bitmap natif est vérifié.

[FAIT en émulation] `genie_router.s` redirige uniquement les deux appels
Generate/Undo du menu et son callback pad. Les actions natives audio et
l'appel interne de génération audio différée restent inchangés. En B,
les algorithmes natifs de gamme/notes, mutation, cible rythme/notes et
Euclide lisent une façade privée, puis `genie.s` crée une voie candidate.
La vélocité aléatoire suit les bornes ; aucun p-lock audio n'est écrit.
Decay/pan ne sont pas représentés dans les voies MIDI et restent audio.

À l'arrêt, copie atomique de 264 octets. En lecture, un seul candidat
attend le pas zéro de sa voie/pattern. Avant copie, comparaison complète
avec le snapshot : toute différence annule le candidat. Undo annule une
demande en attente ou prépare la restauration au prochain tour. Stop
applique la demande via service UI ; changement de pattern l'annule.
L'IRQ ne génère aucune note aléatoire et n'appelle ni OS ni MIDI physique.
Sauvegarde persistante toujours non raccordée ; les données restent RAM.

`test_midi_lane_genie_router.py` exécute les vrais algorithmes et le menu
avec getter événement synthétique : six voies isolées, Generate/Undo
arrêtés/différés, erreurs concurrentes, Euclide 4/16, vélocités 80..110,
SR conservé, aucune donnée audio modifiée. Les nouveaux raccordements
restent expérimentaux, à tester sur la machine.


## 10. Raccourci SETTINGS + PAGE côté B (12/10/2026)

AveyCole confirme SETTINGS + PAGE, sans FUNC, et signale que Genie ne
s'ouvre pas en B. Le getter B suit désormais SETTINGS localement et
ouvre le menu directement avec PAGE, sans les gardes de vue audio/TG du
getter historique. A conserve sa chaîne existante. FUNC + PAGE conserve
Scale Setup, PATTERN seul ne déclenche rien. Événements répétés et release
PAGE consommés de façon idempotente. La preuve exécute le getter B avec
TG_set_held=0, puis le vrai constructeur/menu Genie et les actions MIDI.
Raccourci et ouverture B restent à vérifier sur matériel.
