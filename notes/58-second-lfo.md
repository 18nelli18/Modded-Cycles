# 58 — Second LFO indépendant

Demande d'AveyCole, conversation du 11/10/2026 : clone du premier LFO,
accessible au deuxième appui sur sa page. Adresses : VA de l'OS 1.13.

## 1. Réponse courte

[FAIT en émulation] La routine native peut faire évoluer deux banques de
six états indépendantes avec des paramètres distincts. Mélange, page et
initialisation sont prouvés, y compris aux adresses de placement firmware.
La sauvegarde et le coût audio combiné restent à établir ; aucun nouveau
flasher livré.

## 2. État natif et preuve

[FAIT] `0x40091ab2` reçoit les paramètres des six pistes, le tempo et le masque
de retrigger. Deux références initiales chargent la banque `0x40fde838`
et les indicateurs à banque +28. Chaque état occupe 32 octets ; six états
occupent 192 octets. Les paramètres de piste occupent 66 octets.

[FAIT en émulation] `tools/emu/test_lfo_secondary_state.py` exécute la vraie
routine avec EMAC exacte, 128 doubles mises à jour à 120 BPM. Deux banques
et deux tableaux de paramètres sont utilisés alternativement. Chaque phase
est comparée à son modèle indépendant ; la banque non sélectionnée doit
rester entièrement identique. Les douze phases passent.

Cette preuve reloge les deux références uniquement dans l'émulateur ; elle
ne propose pas de modifier le code à chaque appel sur la machine. Les
adresses RAM choisies appartiennent à la fixture, pas à une réservation
validée sur le matériel. Destinations désactivées dans cette première preuve.

## 3. Prochaines validations

[À FAIRE] Wrapper réentrant avec banque propre sans modifier les instructions
pendant la lecture ; destinations différentes et identiques, modulation
additive sans accumulation ni écrasement de la première ; formes, modes,
fondu et retrigger indépendants ; budget audio maximal avec les moteurs.

[À FAIRE] Deuxième page LFO, état sélectionné, stockage persistant démontré
libre, copie/changement/sauvegarde du pattern. Ne pas prendre le raccourci
réservé à la seconde banque MIDI ou aux autres mods.

## 4. Entrée indépendante et mélange exécutés (11/10/2026)

[FAIT en émulation] `tools/machines/lfo_secondary/update.s` reproduit le
prologue de `0x40091ab2`, reçoit la banque en quatrième argument, puis rejoint
le corps natif à `0x40091aca`. L'épilogue natif restaure les registres et la
pile ; aucune instruction native n'est réécrite entre les appels. Les douze
phases restent indépendantes sur 128 doubles mises à jour.

[FAIT en émulation] `mix.s` reçoit sortie, base non modulée, taille en mots,
et les deux banques. Il rassemble au plus douze destinations, additionne
leurs deltas signés, puis sature une seule fois à 0..32 512. Aucun allocateur,
140 octets de pile. Le test assemble et exécute ce code ColdFire avec les
sorties natives, destinations machine identiques/distinctes (11/14), six
pistes, bases 0/16 384/32 512, 48 mises à jour. Il vérifie le bloc entier et
répète le mélange avec la même base pour exclure une accumulation.

[À FAIRE] Mesure des instructions/temps et intégration au caller
`0x4005979e` : celui-ci obtient le bloc via `0x40058474`, le prépare via
`0x40056e24`, puis appelle le LFO à `0x400597c6`. Le mélange doit conserver la
base avant cette modulation. Les destinations LFO elles-mêmes, toutes les
formes/modes, l'étendue exacte du bloc et les retriggers restent à couvrir.
Les buffers de preuve sont simulés ; aucun LFO 2 installé dans le flasher.

Dans les cas couverts, maximum observé : 930 instructions pour l'entrée LFO,
1 807 pour le mélange. Ce comptage n'est ni une mesure DDR/cache, ni une
validation de la marge audio. Le test couvre un cas où saturer après chaque
LFO donne un résultat différent de la saturation unique retenue.

## 5. Dispatcher et édition des réglages (11/10/2026)

[FAIT] Le caller natif `0x400597c6` reçoit un bloc de 238 mots (476 octets),
produit à `0x8000100c` par `0x40058474`. Le dispatcher conserve ce bloc avant
le LFO primaire, applique le deuxième LFO à une copie portant ses 8 réglages
par piste, puis somme les deux deltas depuis la même base. Contexte nul :
appel natif identique. Contexte de fixture 1240 octets, aucune allocation audio.

[FAIT en émulation] 64 doubles mises à jour dans le dispatcher, tout le bloc
comparé ; aucune accumulation. `lf2_edit` valide huit réglages sur six pistes,
enums en octet haut et destination OFF 127, sans modifier phases/buffers.
Le multiplicateur natif accepte 0..23 (synchrone et libre), pas seulement 0..11.
Les limites wave 0..6 et mode 0..4 sont celles du chemin natif.

[À FAIRE] Allocation/pointeur matériel, deuxième appui LFO et vrais callbacks
d'édition, persistance, formes/retriggers complets, budget audio et générateur.
Aucun firmware LFO 2 publié.

## 6. Initialisation et navigation native (11/10/2026)

[FAIT en émulation] `init.s` prépare 1240 octets avant publication du pointeur
audio : phases/buffers vides, huit réglages clonés depuis chaque LFO natif,
destination OFF 127 et profondeur neutre 16 384. La source et les sentinelles
restent intactes. Avec ce contexte initialisé, huit blocs de modulation
primaire active restent identiques au natif, états primaires compris.
Ne jamais réinitialiser ce contexte lorsqu'il est déjà publié pendant la
lecture ; la gestion du changement de pattern reste à écrire.

[FAIT] Le handler LFO `0x40024e0c` reconnaît le code 8. Au relâchement sans
FUNC, il ferme la page via vtable +124, sauf garde +604 (LFO tenu pendant un
geste potard). Le vtable principal contient ce handler à `0x401016c8` ; le
sous-objet +56 passe par `0x40024e86` (pointeur à `0x401016e4`).

[FAIT en émulation] `key.s` propose deux entrées correspondantes. Un callback
UI prêt peut ouvrir la deuxième page sur ce relâchement ; callback absent,
refusé, contexte interruption ou autre événement : handler natif. Les
accessors d'événements ne sont pas doublés (lecture directe des mêmes champs
+12/+16). 33 792 combinaisons code/flags/garde, vtable principal et sous-objet,
callback absent/refusé/accepté et IPL vérifient ce contrat. Le garde natif
continue à empêcher un changement de page après LFO+potard.

[À FAIRE] Dessin/édition de la vraie page et callback d'ouverture, allocation,
remplacement des pointeurs vtable et callsite audio, persistance, marge audio
sur matériel. Le callback de preuve est simulé ; cette navigation n'est pas
installée dans un flasher.

## 7. Page d'édition native expérimentale (11/10/2026)

[FAIT en émulation] `page.s` construit une page avec le constructeur OS
MACHINES `0x400a22b0`, comme le générateur (adaptation Model-TG, MIT).
Vtables privés principal, encodeur +4 et pads +16. Le callback d'ouverture
s'intègre à `key.s` ; les trois premières gardes refusent contexte absent,
IPL non nul et gestionnaire non initialisé. Une deuxième ouverture simultanée
est refusée. Les deux allocations directes page/détenteur ont un nettoyage
sur refus ; les allocations internes du constructeur restent celles de l'OS.

L'ouverture lit la piste sélectionnée par la chaîne native `0x400cf866` →
`0x4000eb90` → `0x40012412`. Le sélecteur Track et les six pads permettent
d'éditer les autres LFO secondaires, sans changer la sélection native ni
jouer de note. DATA parcourt neuf lignes (Track + huit paramètres) ; clic
DATA entre/sort de l'édition. Les mots continus avancent de 256, les enums
de 1. Les limites sont celles du setter, avec OFF après destination 32.

Le rendu affiche LFO 2 à y=49, puis trois lignes à y=35/21/7. Sept noms de
formes et cinq noms de modes viennent des tables natives `0x40108f24` et
`0x40108f40`, vérifiées dans les formateurs OS `0x400458dc/0x40045950`.
Le prochain relâchement LFO ferme la page ; RETURN/SETTINGS la ferment
également. Play/Stop simples passent à la gestion native. Le contexte audio
reste alloué après fermeture : les phases et réglages ne sont pas libérés.

`test_lfo_secondary_page.py` exécute ouverture via second appui, getters de
sélection, constructeur et destructeur OS réels. Présentation, allocations,
pixels, delta encodeur et fermeture par gestionnaire sont simulés. Vérifie
108 positions de rendu, 48 champs dans les deux sens jusqu'aux bornes,
non-modification des autres champs/phases/buffers, deux entrées encodeur,
pad invalide, transport, fermeture/réouverture et refus d'allocation.

[À FAIRE] Libellés musicaux des multiplicateurs et destinations, réservation
du code, allocation/initialisation du contexte dans la tâche UI, installation
des hooks, sauvegarde et budget audio. Pas de LFO 2 flashable à ce stade.

## 8. Préparation avant publication audio (11/10/2026)

[FAIT en émulation] `prepare.s`, entrée `lf2_prepare(frame)`, alloue 1240
octets via l'allocateur OS dans le contexte UI (IPL nul). `lf2_context`
reste nul pendant toute l'initialisation ; publication par un seul long
aligné après `lf2_init`. Un garde refuse les rappels réentrants. Un échec
d'allocation laisse le pointeur nul et permet une nouvelle tentative.
Un contexte déjà publié est conservé sans nouvelle allocation ni reset des
réglages/phases. Le chemin audio ne fait toujours aucune allocation.

La preuve de page vérifie cette publication, les données neutres exactes,
la conservation d'une modification, les gardes IPL/frame nul/réentrance et
l'échec de l'allocateur simulé. Les vrais hooks UI/audio ne sont pas encore
installés ; il reste à raccorder cette préparation à l'ouverture, réserver
le code, sauvegarder les réglages et vérifier le budget audio combiné.

## 9. Placement et raccordement expérimental (11/10/2026)

[FAIT en émulation] `launch.s` raccorde le deuxième appui à `lf2_prepare`
puis à la page. Le frame natif à `0x8000100c` reste intact. Un échec
d'allocation revient au handler natif, qui ferme sa page normalement ; une
nouvelle tentative fonctionne. Entrées principale et sous-objet +56 prouvées.

[FAIT] `gen_lfo_secondary.py` produit `experimental/lfo-secondary/52-lfo-secondary.json`.
Les grosses routines de page sont réparties entre sections, avec des sauts
absolus entre masques ; les branches internes restent courtes. Chaque masque
est vérifié identique à son exemplaire conservé, avec une seule référence
alignée redirigée. Le placement exclut les écritures de tous les tweaks
principaux, y compris Model-TG. 27 masques, 57 écritures dont les trois
hooks : pointeurs `0x401016c8/0x401016e4`, appel audio `0x400597c6`.
Le générateur contrôle aussi l'absence de chevauchement pour ces hooks.

[FAIT en émulation] Les preuves de page et d'états acceptent `--tweak` pour
exécuter les octets placés réellement dans l'image, sans relink à une adresse
de fixture. Page entière, allocation/publication, navigation, deux banques
de phases, mélange, 64 blocs de dispatcher et 33 792 événements passent.
`--check` reproduit le JSON. Cela prouve le code placé et les callbacks,
pas encore le budget audio physique ni la persistance des réglages.
La preuve exécute aussi le vrai appel patché `0x400597c6` avec ses trois
arguments et vérifie le retour `0x400597cc`/la pile ; contexte nul, frame et
états identiques au LFO natif. Les entrées UI sont lues depuis les deux vrais
pointeurs vtable patchés, avec callback `lf2_launch` présent dans l'image.

[À FAIRE] Libellés musicaux, sauvegarde/copie/changement de pattern, marge
audio avec les moteurs et intégration du catalogue de test avant publication.
Le prototype conserve les réglages seulement en RAM. Aucun statut matériel
ni carte de flasher ajoutés par ce générateur.

## 10. Toutes les formes et modes dans le dispatcher (11/10/2026)

[FAIT en émulation] La preuve d'états exécute 1120 blocs supplémentaires
avec sept formes et cinq modes dans chaque banque, les 33 destinations,
réglages distincts entre pistes/banques et un retrigger toutes les huit
itérations. Après chaque bloc, le frame entier doit correspondre à la base
plus les contributions signées des deux banques, avec une seule saturation.
Les 96 octets de réglages secondaires restent identiques. Les cas RND sont
inclus. Ce test valide la composition des sorties natives, pas une mesure
de marge audio physique. Le compteur affiche séparément le maximum du
dispatcher complet (deux banques et mélange), en instructions.

## 11. Premier flasher matériel, réglages RAM (11/10/2026)

[FAIT en émulation] `gen_lfo_test_flasher.py` prépare un catalogue autonome
`docs/flasher-lfo-test/` à partir du catalogue principal, sans retirer aucun
mod testé. LFO 2 est une sélection indépendante expérimentale, compatible
avec Model-TG. Les 1007 combinaisons de référence passent la construction
Python ; `test_lfo_flasher.js` vérifie les 125 sélections contenant LFO 2
dans le vrai builder navigateur, chacune avec empreinte Python identique.
EN/FR, guide local, sélection indépendante et priorités Select all vérifiés.

Ce premier essai sert à vérifier contrôles et audio sur matériel avant la
persistance. Les réglages LFO 2 sont communs à la session, gardés en RAM
entre ouvertures ; ils ne sont pas sauvés avec les patterns/projets et
disparaissent au redémarrage. Cette limite figure sur la page, la carte et
le guide. La sauvegarde reste du travail en cours, pas une fonctionnalité
revendiquée. Le flasher principal reste inchangé. Maximum observé du
dispatcher complet : 5153 instructions, pas une mesure matérielle de durée.

[À FAIRE] Publication Pages/retour matériel, puis poursuite de la sauvegarde
et de la banque MIDI indépendante ; aucun statut « testé sur machine » ajouté.
