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
