# 206 — Song sur chaine native et articulation ACID

Demande AveyCole du 30/10/2026 : mode Song inspire de la photo fournie,
avec la chaine existante, et portamento/legato proches du TB-303 ou Devil Fish.
Adresses : VA de l'OS 1.13. Ceci est une investigation et une proposition,
pas une fonctionnalite presente dans les candidats 2.62.

## Reponse courte

[FAIT] La chaine native accepte 64 entrees. ACID possede deja un glissement
sur notes chevauchees. [A FAIRE] Ajouter un editeur d'arrangement, sa sauvegarde
et des controles explicites d'articulation ; valider leurs hooks natifs avant
de produire un firmware.

## 1. Song

[FAIT] `0x40055cd6` copie au plus 64 couples pointeur pattern/pointeur kit
dans `0x40a7863c`. Position : `0x40a78634`, nombre : `0x40a78638`.
Le test Direct Jump utilise deja cette voie native.

[PROPOSITION] Quatre lignes visibles : numero, pattern, repetitions, six
cases de pistes. DATA choisit/modifie le champ. Conserver le sequenceur natif
pour le tempo, les locks et les transitions. L'arrangement fournit les entrees
et applique les mutes a la frontiere de ligne.

Compter les transitions de chaine, pas seulement les changements de pointeur
pattern : deux repetitions du meme pattern doivent avancer correctement.
Ne pas developper une liste au-dela des 64 entrees natives ; une fenetre de
lecture ou un controleur de lignes est necessaire pour les arrangements longs.
Definir explicitement la duree avec CH.LEN INF et les longueurs par piste.

[PROPOSITION] STOP suspend, double STOP revient au debut et conserve le panic
FX existant ; fin STOP ou LOOP. Un saut manuel interrompt le pilotage Song.
Les mutes Song restent distincts des mutes manuels et sont retires a la sortie.
Sauvegarde par projet dans un fichier associe a son identite, hors interruption
audio et hors lecture ; aucun octet de pattern declare libre sans preuve.

[A FAIRE] Prouver les frontieres de cycle, les repetitions du meme pattern,
les changements de kit, les longueurs inegales, pause/reprise, boucle, saut,
chargement de projet et la coexistence avec Direct Jump. UI et stockage doivent
etre disponibles dans Full, Lite et Optional.

## 2. ACID

[FAIT] `fundamentals/acid.c` derive le slide de held/idle/LEN_LEFT et de la
machine precedente. Il supprime le nouveau trigger natif sur chevauchement ;
`acid_dsp.h` garde l'enveloppe et lisse la hauteur avec `ACID_SLIDE_A`.
La constante actuelle donne environ 90 % de convergence en 50 ms. Ce n'est
pas une preuve d'equivalence avec le temps audible d'un circuit analogique.
Le selecteur global F/A/AF et son fichier AcidEnv.cfg existent deja.

[PROPOSITION] Distinguer trois decisions : gate lie, retrigger d'enveloppe,
glissement de hauteur. Un slide de pas doit lier la note vers la suivante ;
un vrai repos doit couper cette liaison. Conserver le reglage F/A/AF et verifier
la priorite des notes MIDI, les note-off anciens et les changements de machine.
Ne pas confondre PUNCH (forme saw/square dans ACID) et accent.

Le manuel primaire Devil Fish decrit un slide RC et des commandes distinctes
de gate, decay normal/accent, attaque et overdrive. L'explication du circuit
303 decrit aussi l'interaction accent/resonance et l'accumulation entre accents.
L'accent actuel est un boost simple ; une meilleure fidelite demande un modele
dynamique, pas seulement une hausse du gain.

Sources :
- https://www.firstpr.com.au/rwi/dfish/Devil-Fish-Manual.pdf
- https://www.firstpr.com.au/rwi/dfish/303-unique.html

[A FAIRE] Premier prototype : articulation explicite, regression des notes
detachees et mesures de glide. Ensuite profil Devil Fish avec plage de slide
et enveloppes adaptees, comparaison audio et charge CPU mesuree. Aucun nouveau
hook, espace RAM ou resultat materiel revendique dans cette note.
