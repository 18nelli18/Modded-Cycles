# 207 — Prototype Song et articulation ACID

Demande AveyCole du 30/10/2026 : arrangement sur chaine native et articulation
ACID ; controles physiques SETTINGS + potard, uniquement sur la piste choisie.
Adresses : VA OS1.13. Generateur : `tools/gen_acid_articulation.py`.

[FAIT en emulation] Song dans Global ; DATA ligne, PITCH pattern, DECAY
repetitions, TRIG1..6 mutes, PAGE insertion, FUNC+PAGE suppression,
FUNC+DATA STOP/LOOP. La chaine native accepte64 lectures developpees.
Le raccord ISR a40055700 suit l'index deja publie ; 40055c5c ne couvre que
le chemin arrete. Le setter40055cd6 annule Song pour un choix manuel.
Les mutes Song sont ajoutes au D1 lu par40058ca6, sans ecraser le masque
utilisateur. L'arret de fin appelle le transport natif40055f14.

ACID : SETTINGS+PITCH glide OFF/50..360ms a90%, SETTINGS+DECAY legato
OFF/ON. Six reglages independants. Enveloppe F/A/AF conservee. Un chevauchement
LEN determine la liaison ; glide et retrigger d'enveloppe sont separes.
Pas de locks supplementaires ni de revendication d'emulation Devil Fish complete.

Module sparse46931000, BSS4693e000..46940000 ; chargeur chaine a celui de2.62.
Le titre experimental est2.63. Projet v6 : record SGA1 de304octets a+0x40,
CRC32, arrangement et six couples ACID. FXP1 a+0x1c0 reste intact.
Les codecs amont sont delegues ; projet absent/corrompu revient aux defauts.

Preuves : test_song_chain/playback/ui/storage et test_acid_articulation_ui/dsp.
Le test storage simule les codecs amont ; il prouve le record compile et son
isolation, pas un aller-retour complet du fichier projet sur appareil.
Les cinq editions sont construites et testees separement. Rapports et images :
`../song-test/`. Aucun resultat materiel ni mesure CPU ; pas de diagnostic CPU/CUT.

[A FAIRE sur appareil] Verifier l'affichage, pause/reprise, doubleSTOP,
changements de projet, sauvegarde native complete, son et charge polyphonique.
Les longueurs infinies suivent la politique native et peuvent retenir une ligne.
Les flasheurs publics restent2.62 ; aucune publication2.63 autorisee ici.

## Correction du dessin et de l'entree

AveyCole signale que le MenuView ne ressemble pas a sa photo et coupe le
texte. Il demande Song au premier niveau de Mod Setup. Le rendu Song devient
une grille128x64 explicite : bandeau SONG/STOP ou PLAY, quatre lignes,
numero, pattern encadre, repetitions et six cases. Police5x7 bornee ; aucun
long texte concatene. Le premier niveau contient Global, Track et Song ;
Global utilise son handler precedent et ne contient plus l'entree Song.

`render_song_grid.py` execute le vrai remplissage Bitmap40070dea dans Unicorn,
sans le stub graphique du banc de controles.657rectangles verifies dans
les limites128x64 ; PNG inspecte visuellement avec F16 et x64. Le primitive
40070efc est un contour avec interieur ; il ne convient pas aux pixels1x1.
Preuves et livraisons corrigees : `../song-grid-test/`.

## Retours appareil : menus et routage

AveyCole demande de garder le style natif au premier niveau. Celui-ci utilise
de nouveau le vrai MenuView avec Global/Track/Song ; seule la page Song a
le dessin en grille. Les retours signalent aussi des potards qui modifient
le son et FUNC+DATA sans effet. Le raccord gc_encoder seul est trop tardif
pour les potards ordinaires : l'entree Application400775f8 route maintenant
directement les evenements encodeur vers Song pendant sa page. L'entree
clavier40077720 fait de meme pour ses touches d'edition. Le transport est
prepare puis delegue une seule fois a l'application precedente.

ACID : retirer la consommation400723e0(SETTINGS), qui peut retenir sa release.
Marquer seulement wf_api[5] (mod_used), comme les FX existants. Le test exerce
wf_key appui/release et verifie set_held=0, puis un trig ordinaire.
Les tests d'edition Song passent par aa_face_encoder/aa_face_key, pas
seulement les fonctions internes. Le bandeau montre STOP/LOOP au centre et
le transport a droite. Les images avec suffixe Controls_Fix portent ces corrections.

## Global visible et DATA direct

Retour appareil : Global invisible et FUNC+DATA encore sans effet. Retirer
le dessin prealable jp_draw au premier niveau : un seul MenuView est dessine.
Conserver les callbacks d'origine gc_top_global_value/gc_top_track_value,
leur police et le libelle complet Global ; ajouter uniquement Song.
render_song_top.py execute MenuView/Bitmap/polices natifs, trois selections.
Captures Global selectionne et Song selectionne inspectees : Global complet
et lisible dans les deux etats. Un clic DATA dans Song choisit STOP/LOOP,
avec ou sans FUNC ; sa rotation reste reservee a la ligne. Verification
appui+release via Application sans double bascule. Livraisons Song_Menu_Data_Fix
sous ../song-menu-label-fix/ ; verification materielle encore attendue.

## Publication complete2.64 (30/10/2026)

AveyCole demande explicitement de publier toutes ces fonctions dans les builds,
y compris le correctif de relance arpege ACID. Le generateur combine Song,
articulation ACID et garde Wizard sur les cinq bases2.62 epinglees. Le titre
est2.64. ACID_ARP_RETRIGGER force le chemin de relance natif avant la decision
de glide/legato pour les notes du retrig natif actif. Les slides ordinaires et
les cinq couples glide/legato du banc restent valides. Les flasheurs main et
Optional servent maintenant ces images completes ; Lite conserve Song et
les fonctions partagees. Confirmation materielle encore attendue.
