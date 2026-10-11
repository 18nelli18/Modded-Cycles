# 56 — Génération au prochain cycle

Demande d’AveyCole, conversation des 10–11/10/2026 : préparer pendant la lecture
puis appliquer au prochain tour, option séparée sous Sequence Generator.
Adresses : VA de l’OS 1.13. Générateur `tools/gen_seq_gen.py --queued`,
preuve `tools/emu/test_seq_gen_queue.py`. Flasher de test 2 seulement.

## 1. Comportement et limites

Generate pendant la lecture travaille dans une copie privée ; Queued indique
la préparation et Cancel queue l’annule. Avant la première lecture des trigs
suivants, les données terminées remplacent celles de la piste. Arrêter pour
Undo. Fermeture, arrêt, changement de pattern, édition concurrente ou changement
de longueur/vitesse annulent la préparation. Une préparation à la fois.
Préparer un nouveau résultat remplace l’ancien point Undo.

Première version : longueur et vitesse communes (mode 0), longueur 1–64,
une seule entrée dans la liste de patterns et celle-ci doit être le pattern
actif. Les modes par piste et les chaînes sont refusés sans écriture.
Cette limitation est présentée dans la sous-option du flasher.

## 2. Données et frontière

`[FAIT]` Le getter piste éditable utilise +16 (UI), +32 (audio), +44 (pool),
+56 (index). La conversion native `0x4005b642` transforme les 722 octets UI
vers les 722 octets du lecteur. Pool étendu : 4 385 octets par piste,
64 × 34 mots puis 33 indicateurs ; le lecteur `0x4005487c` utilise exactement
ce format, à pattern audio +4 332 +index×4 385.

Page augmentée à 0x3000 octets : snapshot Undo inchangé, objets privés,
722 octets de travail, pool privé, conversion audio et ancienne conversion.
Les setters OS et la conversion travaillent sur ces copies, notifications
muettes. Aucun setter, ordonnanceur, allocation ou notification UI dans l’ISR.
Publication atomique seulement après la préparation complète.

Hook `0x400550da` : rejouer `movea.l 0x40a7887c,a2`, garder tous registres et SR.
Au tick séquenceur, prochain pas piste 0 = 0 et phase piste 0 = 0 : avant le
parcours `0x4005510e`, avant `0x400548ce` et la construction des événements.
Valider identités, snapshots UI/audio et pool ; copier les quatre blocs sous
IPL7. Hook Stop `0x40055f14` : annuler une préparation même si Play suit avant
le prochain tick. Les notifications natives et le dessin sont différés à l’UI.
Les accès non alignés des pools sont autorisés par MCF54418RM §20.4.8.

## 3. Preuves et ce qu’elles ne prouvent pas

`[FAIT en émulation]` Six pistes, longueurs 1/16/64, staging sans écriture
ni notification, frontière avant lecture, copie exacte et Undo. Cas stale :
notes, pools UI/audio, pointeurs, longueur, vitesse, pattern, chaîne, arrêt,
fermeture et annulation. Registres, pile et SR conservés.
Le vrai parcours horloge → lecteur → événement OS et copie des locks est
exécuté aux sept vitesses et microtimings -23/0/+23. Note et locks neufs
sont dans le premier événement, avant sa mise en file. Allocateurs, décision
de condition, file temporelle et notifications externes simulés.

8 378 octets dans 61 masques redirigés et vérifiés. Les deux variantes
Model-TG et la combinaison maximale (SCRAMBLE, tous moteurs, arp, USB6,
MIDI, affichage) passent les mêmes preuves. Le hook complet utilise au plus
23 213 instructions dans les cas couverts. Les 861 combinaisons de référence
et les 153 tweaks du catalogue sont vérifiés ; le navigateur construit la
sélection maximale avec les empreintes Python.

Le nombre d’instructions est borné et mesuré par la preuve ; il ne constitue
pas une mesure du temps DDR/cache sur la machine. Le coût sous IPL7, la charge
audio maximale, le boot complet et les conditions/retrigs/slide particuliers
restent à tester sur le matériel. Statut expérimental ; aucun résultat
matériel revendiqué pour la nouvelle variante.

## 4. Sélection et indépendance

Case Queued generation sous Sequence Generator, décochée initialement.
Décochée : exactement les octets du générateur déjà testé. SCRAMBLE est une
carte indépendante avec variantes de chaîne adéquates. Select all coche aussi
la sous-option et conserve Model-TG et Live MIDI OUT + THRU en priorité.
Les deux flashers existants et leurs catalogues restent inchangés.

## 5. Refus en lecture malgré mode commun (11/10/2026)

AveyCole signale « Check range/stop », option différée cochée, longueur/vitesse
communes et sans chaîne. `[FAIT en émulation]` Cas reproduit : longueur brute
de piste +713 = 64 et longueur effective du parent = 16. Le contrôle initial
comparait la longueur brute à celle du pattern et refusait ce cas valide.
Le getter natif `0x40016402` consulte le parent +60 : `0x4000c964` lit le mode
et `0x4000c994` retourne la longueur commune. Le clone garde ce parent ;
le générateur et le writer vérifient donc déjà la vraie longueur effective.
Suppression de la comparaison brute ; conservation de toutes les validations
d’identité, de snapshots et de frontière. Régression avec vrais getters natifs,
longueur effective 16 et longueur masquée 64 : l’ancien build refuse, le
correctif doit préparer, appliquer seize pas et garder la longueur masquée.
Cette cause reproduite peut expliquer le rapport ; confirmation matérielle
du correctif encore attendue.
