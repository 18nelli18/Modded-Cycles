# 136 — Step Recorder et solo du mute verrouillé

Cette intégration ajoute au firmware principal fixe l'enregistrement pas à pas confirmé par AveyCole et le solo dans le mode mute verrouillé. Le filtre par piste, les moteurs, MIDI Out et le menu USB 2/6 canaux restent dans le build. Source : conception Step Recorder documentée dans la branche 18nelli18/Modded-Cycles (note 73 et PR #101) ; solo écrit ici. Générateur des données navigateur : `tools/gen_step_rec_main_data.py` ; générateur Step Recorder : `tools/gen_step_rec.py` ; preuve : `tools/emu/test_step_rec.py` et test du build principal `tools/test_midi_machine_main.js`. Adresses : VA de l'OS 1.13.

## 1. Fonctionnement

### 1.1 Step Recorder

Séquenceur arrêté, un double appui sur REC ouvre l'enregistrement pas à pas. Les notes jouées sur les touches TRIG en mode chromatique, les pads T1-T6 ou un clavier MIDI sont écrites au pas courant. Le pas avance au relâchement de la dernière note. PLAY avance, STOP recule, REC quitte. Le pas et sa page clignotent rapidement ; la fonction s'arrête aussi en fin de piste.

### 1.2 Solo dans le mute verrouillé

En mode mute verrouillé seulement, maintenir FUNC et presser T1-T6 met cette piste en solo. Presser à nouveau la piste solo ou quitter le mode mute restaure l'état mute antérieur, y compris les pistes déjà mutées. Hors du mode mute verrouillé, FUNC + pad conserve le comportement normal de sélection/lecture.

## 2. Intégration

Le Step Recorder réutilise ses accroches OS et ses variables SRAM validées dans la preuve précédente. Le profil principal avec filtre occupe l'ancien emplacement de test à `0x4671f490`; le composer place donc les deux blocs dans la fin libre du payload beat repeat, à partir de `0x467ada5e`, après les correctifs MIDI. Le Step Recorder occupe 2 396 octets ; le solo de 426 octets suit, jusqu'à `0x467ae564`, sous la limite vérifiée `0x467b0000`. Le compositeur vérifie que le début correspond exactement à la fin du payload assemblé, étend la taille chargée au démarrage et met à jour son empreinte. Le gestionnaire de solo intercepte le pad à `0x40023550` et vérifie d'abord l'indicateur du mode mute verrouillé à `0x401487ed`. Son masque temporaire est à `0x401487c0..0x401487c7`. À la sortie du mode mute, il restaure les mutes capturés.

La composition navigateur injecte les deux blocs dans cette zone, puis recalcule les empreintes du moteur et des accroches avant que le flasheur vérifie le firmware. Les deux choix USB produisent le même code de jeu ; seul le tweak USB 6 canaux change. Le filtre par piste reste dans la composition principale. Aucun diagnostic audio n'est ajouté.

## 3. Validation

- `[FAIT]` L'image officielle Model:Cycles OS 1.13 est vérifiée par son SHA-256 avant la construction.
- `[FAIT]` Le Step Recorder et le solo ont été testés dans l'émulateur sur le code OS et le chargement du payload.
- `[FAIT rapporté par AveyCole]` Le Step Recorder a fonctionné sur sa machine ; le solo limité au mode mute verrouillé a aussi été confirmé.
- `[FAIT]` Le build principal est construit avec USB 6 canaux et USB standard ; le filtre reste présent, les empreintes et le conteneur SysEx sont vérifiés.

Le firmware principal reste un preset complet ; le seul choix du flasheur est USB 2/6 canaux. Le diagnostic de charge reste absent du firmware principal.
