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

`[FAIT]` Le getter piste éditable utilise +16 (UI), +32 (stockage A), +44 (pool),
+56 (index). Le lecteur actif utilise le format B, comme l’UI. La conversion
`0x4005b642` transforme B vers le stockage A, pas vers le lecteur. Pool étendu : 4 385 octets par piste,
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

## 6. Refus persistant et diagnostic ciblé (11/10/2026)

AveyCole confirme que le correctif précédent refuse encore Generate en lecture,
« Check range/stop », sans produire de séquence. Option différée cochée,
longueur/vitesse communes, sans chaîne ; 16 pas, d’abord piste 6, puis
confirmation que toutes les pistes sont concernées. Generate fonctionne arrêté.
La régression longueur masquée est réelle, mais n’explique donc pas à elle seule
le comportement matériel signalé. Cause restante non établie.

Test 2 : chaque groupe de validations UI garde un motif précis, affiché sur
la ligne Generate en cas de refus : transport, mode, chain, track, audio, data,
locks, build ou Queue pending. Aucun journal ni notification ajouté à l’ISR.
Les refus mode/chain/audio/data/locks sont provoqués en émulation sur piste 6,
et leur texte et absence d’écriture audio sont contrôlés. Les validations
restent actives. Ce build sert à identifier la cause matérielle, pas à annoncer
un correctif confirmé. Taille différée : 8 632 octets, 61 masques.

## 7. Diagnostic des valeurs de mode (11/10/2026)

AveyCole obtient « Queue: mode ». Ce motif englobait encore quatre contrôles :
mode brut +30667, longueur commune +30662, vitesse +30668 et état de lecture
piste 0 à `0x40a78848`. Le rapport ne permet pas de choisir lequel échoue.
Test 2 affiche désormais le contrôle et sa valeur exacte sur cinq chiffres :
`Q mod 00001`, `Q len 00000`, `Q spd 00007`, `Q run 00000`, par exemple.
Formatter UI borné à cinq divisions, aucune API OS et aucun changement ISR.
Les quatre refus sont provoqués séparément dans la preuve et leur texte exact
est vérifié ; les validations restent inchangées. Cause matérielle à déterminer
avec la valeur remontée, aucun correctif de lecture revendiqué.

Build valeurs : 8 762 octets dans 62 masques ; interface principale inchangée.

## 8. Banque de lecture et frontières propres aux pistes (11/10/2026)

AveyCole rapporte ensuite `Q mod 00001`, puis `Queue: audio`.
[FAIT] La valeur 1 est un mode natif valide, avec longueur/vitesse par piste.
Le helper accepte maintenant les modes 0/1/2 : commun, par piste, longueur
par piste avec vitesse commune. La frontière utilise les compteurs de la
piste ciblée, pas ceux de la piste 1.

[FAIT] Correction de l'interprétation initiale du pointeur piste +32 :
`0x400156d0` et `0x4000c570` le lient au stockage du pattern. Il ne doit pas
être égal à la banque de lecture active. Celle-ci est lue via `0x40a7887c` ;
son identité est vérifiée avec la banque native `0x406fa040 + index × 30710`.
Le pointeur +32 est conservé pour détecter un changement de contexte, sans
imposer l'ancienne égalité erronée. Cette recherche concluait à tort que `0x4005b642` était nécessaire pour le
lecteur ; correction ci-dessous (§11).

[FAIT en émulation] Vraie liaison +32, préparation puis commit ; modes par
piste sur six pistes et sept vitesses, longueur piste 16 différente de la
longueur commune 64 ; vrai ordonnanceur, lecteur et constructeur d'événement
sur les modes 0/1/2, sept vitesses et microtimings -23/0/+23. Les nouvelles
notes et locks sont présents dès le premier trig. Même preuve avec la
combinaison maximale, SCRAMBLE compris. Test : `tools/emu/test_seq_gen_queue.py`.

Build local : 8 924 octets, 63 masques. Pas encore publié ni confirmé sur
matériel. Les chaînes restent exclues ; ces preuves ne mesurent pas le temps
réel d'exécution de l'interruption sur l'appareil.

## 9. Retour matériel du test combiné (11/10/2026)

AveyCole confirme le SCRAMBLE par pas et l'intro SEQUENCE GENIE dans le test
`2026-10-11-test-2-genie-scramble-queue`. La préparation différée est acceptée,
mais au changement de mesure aucune séquence n'est appliquée ; le texte
revient à `Queue: build`. Ce résultat ne valide pas la génération différée.
Le motif build est posé avant la préparation ; les annulations du hook ne
l'actualisent pas. Il peut donc être un motif périmé, et ne permet pas encore
d'attribuer le refus à la construction. Les gardes de frontière et les
snapshots doivent être diagnostiqués séparément.

Diagnostic de frontière préparé localement : chaque groupe conserve son motif
propre, dont `Q: UI data`, `Q: UI locks`, `Q: play data`, `Q: play locks`
pour les quatre comparaisons complètes. Le service UI affiche ce motif après
annulation ; aucune API UI ajoutée au hook. Génération locale : 9 105 octets,
63 masques. Ce diagnostic n'est pas inclus dans la promotion principale du
SCRAMBLE par pas ; validation de la preuve et publication test distinctes.

[FAIT en émulation] Les quatre mutations raw/pool/audio/audio-pool provoquent
les quatre motifs attendus après service UI. Même contrôle sur la combinaison
maximale ; registres/SR, absence d'écriture tardive, modes 0/1/2 et lecteur
natif conservés. Catalogue test : 861 références, 153 tweaks, audit des caves
et équivalence navigateur/Python réussis. Build de diagnostic destiné au
matériel, pas un correctif confirmé de la cause de l'annulation.

## 10. Snapshot du lecteur réel (11/10/2026)

Retour matériel : `q: play data`. Le refus correspond à la comparaison des
722 octets audio, avant toute écriture. [FAIT] Le code reconstruisait ce
snapshot à partir des données UI avec `0x4005b642`, au lieu de copier le
lecteur actif. Une différence préexistante entre les deux représentations
annulait donc la demande même sans édition concurrente.

Le staging copie maintenant les 722 octets réellement lus à la demande,
avant la construction privée. Le résultat audio part de cette copie, puis
subit la conversion native de la nouvelle séquence. Les quatre gardes de
comparaison restent actives : une modification postérieure annule toujours
la demande. Aucun travail supplémentaire dans l'interruption ; la copie
supplémentaire se fait dans le service UI.

La preuve ajoute six cas dont la vélocité du lecteur diffère déjà de celle
de l'UI : le snapshot doit être identique au lecteur et le commit doit
réussir. Ce correctif vise le refus observé ; validation matérielle requise.

## 11. Corruption du format après commit différé (11/10/2026)

Retour matériel après `queue-playback-snapshot` : trigs inaudibles, vélocité
`--`, octave zéro, mauvais locks et éditions ultérieures altérées. Le snapshot
réel a levé le refus, exposant une erreur distincte dans le résultat.

[FAIT] `0x400548ce` reçoit directement la banque active et lit la note à
+580, la vélocité à +128, la condition à +516 : format B de l'UI.
`0x4005b642` est B→A pour +32 (stockage), pas pour ce lecteur. Le staging
copiait donc A dans une banque B. Le résultat est désormais une copie B→B.

La preuve précédente recréait également la banque active en A et contrôlait
le mot événement +22 comme une note. C'est la vélocité (8.8) ; la note est
un long à +28. La fixture initialise désormais B et contrôle séparément
les deux champs. Les vraies routines de probabilité/condition ne sont plus
remplacées. Les conclusions antérieures sur la note jouée étaient erronées ;
la preuve corrigée remplace ces résultats.

À la demande d'AveyCole : plage générable 36..96 ; chaque note effectivement
modifiée reçoit des flags note 0x201, une vélocité explicite 1..127 (défaut
de piste valide, sinon 100), une condition sans suppression (100) et aucun
preset-lock hérité. Locks decay/pan séparés ; Undo conserve l'original. Ces
garde-fous ne réparent pas automatiquement un pattern déjà corrompu ni un
son muet/mute de piste. Correctif non confirmé sur matériel.

## 12. Validation matérielle et passage au principal (11/10/2026)

[FAIT] AveyCole confirme que le flasher `2026-10-11-test-2-queue-format-velocity` fonctionne sur son Model:Cycles : plus de trigs corrompus. Il demande explicitement de marquer la génération différée comme testée et de la publier au principal. Le catalogue principal conserve une sous-option séparée, les plages et Euclid ainsi que le cartouche SEQUENCE GENIE. Le format B reste B ; les nouvelles notes ont une vélocité explicite non nulle. Les caves occupées par chord-keys/track-filter peuvent être partagées puisque ces deux mods excluent les deux bases Model-TG requises. Les modulations LFO2 et pistes MIDI supplémentaires restent en développement.

## Génération différée incluse — 12/10/2026

À la demande d'AveyCole, Sequence Generator sélectionne automatiquement
la variante queued déjà testée, avec ou sans moteurs Syntakt. La sous-case
est supprimée ; SCRAMBLE choisit toujours la variante compatible queued
quand le générateur est présent. Aucun octet firmware modifié.
La sélection ne dépend plus de l'ancien état queued éventuellement faux.
`test_sequence_queue_included.js` couvre activation/réactivation, EN/FR,
SCRAMBLE et Select All/ST ; `test_midi_flasher.js` couvre les builds et les
transferts simulés intégraux. Les références existantes des variantes queued
restent utilisées. La sauvegarde MIDI n'est pas incluse dans ce changement.
