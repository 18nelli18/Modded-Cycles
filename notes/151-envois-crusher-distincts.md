# 151 - Envois delay et crusher distincts

Demande AveyCole du22/10/2026 dans Codex : FUNC+DelaySend doit doser le
crusher independamment du delay en Both1/Both2. V51 possede deja les six
icones restantes. Sources `tools/machines/delay_crush_send/`, option privee
`tools/gen_governor_recovery_test.py --split-sends`, preuves
`test_crush_send_control.py`, `test_crush_send_popup.py`,
`test_delay_crush_sends.py`. Adresses : VA de l'OS1.13.

## Reponse courte

V53 retient les cinq routes et les reglages Rate/Bits precedents. En Both1/2,
DelaySend reste l'envoi delay natif ; FUNC+DelaySend (encodeur8) dose un nouvel
envoi crusher0..127 par piste. Both1 garde le direct propre. Both2 transforme
le direct aussi, meme si le delay est coupe. Crusher0 donne un delay propre.

Le crusher agit sur la portion envoyee AVANT le delay natif ; il ne s'agit
plus de quantifier tout son retour melange. Cela permet aux pistes propres et
crushees d'alimenter le meme delay sans propager le dosage d'une piste aux autres.
Les repetitions et leur feedback conservent le processeur delay natif.

## 1. Routage et stockage

Deux bus stereo par sixpistes : direct et intersection delay/crusher. Les
coefficients dry et send viennent du mixeur stock ; sommes via son EMAC
0x40056716, rampes32samples, pas de modification du pattern. La branche
Both2 reprend le mid/side Wizard avant sa conversion native tardive.
La correction direct a0x40056b38 reste Q20 avec saturation ; meme crusher0,
la conversion Q31/Q20 peut arrondir les11bits bas du direct (moins de2048Q31).
Delay/Crush1/Crush2 deleguent leurs routes precedentes.

`/CrushSend.cfg` :18octets CS01, sixvaleurs, sixcomplements,A5/5A.
Zero par defaut, sauvegarde UI uniquement, transport arrete ; preferences
GLOBALes par piste, pas des reglages de son/pattern. Pas de destination LFO
ni p-lock pour ce nouveau send ; le send delay natif garde ses locks.
`/Crush.cfg` et `/Chorus.cfg` conservent leurs formats precedents.
Code crusher0x467fb000, BSS0x467fe000, bornes verifiees sous0x46800000.
Aucun E/S ni allocation dans le bloc audio. Les snapshots des tests servent
uniquement a reutiliser des fixtures natives, aucun DSP n'est simule.

## 2. Exception v52 et correction v53 (22/10/2026)

[FAIT, retour utilisateur] Sur all-features v52, FUNC+DelaySend provoque
« exception v04m0p400fbd68 ». Cette adresse appartient a des tables RTTI,
pas a une fonction. Le raccourci et le rendu appelaient0x40012412 sans objet.
Cette fonction appelle virtuellement le getter de son argument : une valeur
sur la pile devenait un pointeur d'objet puis une adresse de code invalide.
Le nouveau `cr_selected` obtient0x400cf866(), passe root+48 a0x40012412 et
refuse une piste hors0..5. Le popup utilise le graphique delay natif, avec
sa propre valeur et le label Crush Send. Les deux chemins passent par le
meme getter corrige. Le test de controles v52 echoue avec le vrai getter ;
les stubs historiques de getter selection ne pouvaient pas exposer ce contrat.

[FAIT en emulation] V53 : vraie entree encodeur FUNC+DelaySend -> getter
natif -> construction/presentation/dessin/destruction du vrai popup, sur
sixpistes, deux variantes.18popups par composition, ABI/pile verifies.
Bornes0/127, pistes independantes, delegation des autres raccourcis,
sauvegarde/reload et fichiers invalides passent sur chaque composition.
Le chargeur natif produit exactement2423813/2425552octets sans ecraser
la source compressee ; marges849359/847738octets.

## 3. Teste sur la machine (22/10/2026)

AveyCole : « that worked, push all features 53 to main ». Cela approuve
l'image partagee v53 et son comportement rapporte, sans pretendre a une
mesure CPU complete ni a un test materiel de la variante sans filtre partage.
V52 n'est pas promu. V51 et les autres comparaisons privees sont conserves.

## 4. Publication2.23

Fichier exact approuve : all-features-polivoks-cpu-trim-test-v53.syx.
SHA256 : `9a3384e76134f0ed7e9fbcc700220641a9d3ee46f855ef0ae0987a8117a17d77`.
MAIN : `4f595a0fb72ee18e1d030373c317e8736068a74989e15c8d237965172399341f`.
Seule image de livraison deja suivie remplacee ; aucun autre dump ajoute.
Notes et guides EN/FR,PDF4pages mis a jour. Le navigateur telecharge les memes
octets apres verification des fichiers officiels, refuse une image corrompue,
conserve credits et historique ;49lignes de controle sans debordement a390px.
