# 133 — MIDI Out et charge Chord

Demande Austin/AveyCole, 19/10/2026 : canal MIDI modifie par LFO2, destination ERR,
notes live bloquees et clicks Chord/ChordKeys. Test .syx confirme « way better »
puis promotion explicitement demandee. Principal 2.00 ; edition909 conservee.
Adresses : VA OS1.13.

## Resultat

[FAIT] Le bridge audio lf2n_write ecrit k28..32, alors que la machine MIDI range
son LFO2 dans k23..30 et canal/port/marqueur dans k31..32. Le detour secondaire
redirige uniquement les pistes MIDI vers leur banque propre.48editions natives
sur six pistes preservent le routage. Les vues MIDI consomment LFO et ferment
une ancienne vue audio secondaire avant leur setup. Le rendu primaire affiche
OFF pour une destination indisponible ; le scan des choix garde sa validation.

[FAIT] Le producteur live natif peut mettre ses propres messages dans la mailbox
avant le relais direct du MIDI Out. Les detours400817aa/40081552 suppriment
cette duplication pour MIDI17 seulement. Enregistrement audio natif conserve ;
notes sequencees, CC locks et note-offs sur canal/port captures verifies.

[FAIT] L'update Chord inactif ne copie plus33mots. Le crochet des rapports lit
le quatrieme argument natif,44(sp), au lieu de depasser les parametres natifs.
Le cache harmonique est prive par piste et utilise seulement dans l'IRQ audio.
Ses cles couvrent configuration, note bornee, COLOR, SHAPE et geste harmonique.
Les33parametres frais et le DSP natif restent appliques a chaque update.
720updates : etat DSP complet et nom d'accord identiques au code precedent.
Instructions : OFF -16,15%; hit -29,55%; miss +4,24%. Pas une mesure de cycles.

[FAIT] Le raccourci MIDI inactif et le fondu Q16 terminant a zero sont ceux du
test confirme. Le filtre/sampler resident est identique au test6. Aucun filtre
12dB experimental ni autre candidat audio rejete n'est ajoute.

## Recettes et publication

Sources MIDI : tools/machines/midi_machine ; cache : machines/midi_safety.
Sources fondu/raccourci : machines/cut_endpoint et machines/midi_idle.
Compiler gen_midi_safety.py, gen_midi_idle.py, gen_cut_endpoint.py ; puis
executer gen_midi_safety_release.py. --check de ce dernier valide les recettes.
Le composeur tools/web/midi-safety-release.js ajoute uniquement du code propre,
recette Syntakt extraite des fichiers de l'utilisateur et pointeurs controles.
Le catalogue conserve18machines, startup Supermodel, sans banque B ; seul USB6
reste selectable. Les hashes de chaque mod et la signature .syx sont verifies.

Le principal attend MCMidiSafetyReady. Aucun br_observe_before/br_load_address
ni module audio-load-diagnostic n'est accepte. Le diagnostic reste dans les tests.
Les generateurs release specifique et principal passent --check ; les deux builds
reels USB oui/non constituent la validation du flasheur.

## Verification

- tools/test_midi_machine_main.js : vrai preset et upload OS/Syntakt, signature,
  deux USB, startup,18machines, absence diagnostic et banque B.
- tools/emu/test_midi_safety.py : collision native avant/apres, producteurs live,
  LFO1/2, notes et ancien routage ; MIDI_SAFETY_CASE choisit le main.
- test_midi_machine_all.py : sequence->worker, CC, locks, deux LFO, save/load33mots,
  transitions vers les17machines audio ; MIDI_MACHINE_CASE choisit le main.
- test_midi_safety_chord.py : DSP/cache ; test_cut_endpoint.py :640blocs extremes
  par profil et vrai voice_after ; absence du detour diagnostic dans audio_end.

[FAIT] Retour materiel : nette amelioration, promotion autorisee. Aucun engagement
zero click sous toute charge : le processeur peut encore depasser son budget.


## Publication 2.11 : commandes MIDI et titre Sample Wizard (21/10/2026)

[FAIT] AveyCole autorise la promotion du candidat filtre v9, sans diagnostic.
Fichier source : `all-features-midi-playability-no-diagnostic-v9.syx`, SHA-256
`b6a49bffb29b7846a5fc2068a9448851e9f1e589bdc2c085e093141138c3e2a2`.
MAIN OS : `bdb5ee72f18cfdef18a1a9bb5c6741fc6bd88a27b90ba7c5a71a9ad4342812aa`.
La copie canonique du flasheur est identique octet par octet ; aucune recompilation
lors de la promotion. Filtre inclus, USB stereo par defaut, aucun diagnostic.

[FAIT sur machine] v6 : Chance, valeurs LFO, arp et Speed fonctionnent ; le titre
restait incomplet et parcourir Dest envoyait des CC au synth externe. v9 corrige
ces deux points. Le signalement de notes tenues apres Stop disparait apres
redemarrage du synth ; AveyCole confirme ensuite sequence et relachements live
normaux sur v9. Etat de sustain externe probable, CC exact non capture.

Commandes : neuf CC assignables ; Speed, Swing et Chance reserves. Le setter
Swing natif du son ne publiait pas le Swing du pattern MIDI : `mx_parameter`
appelle aussi le setter de piste 40016378, respectant Swing All, hors IRQ et hors
geste Nudge de pas tenu. Arp clavier : RETRIG tenu OU A. On natif, ownership
note-off et reset conserves. TRACK tenu + FUNC arme le latch sans seuil temporel.
Speed publie un mot atomique pour le LFO actif ; la phase continue pendant une
note tenue et le prochain trig reprend les locks du son.

[FAIT] Le titre du catalogue pointait sur le buffer mutable du nom de sample
401b11a8 ; verifier ce seul pointeur ne prouvait pas le vrai ecran MACHINES.
`wizard_title.S` intercepte 400a2612 pour la machine6 seulement : deux appels au
vrai drawText, police native de la vue, Sample au-dessus de Wizard. Le masque
opaque de l'icone gauche aurait efface le texte : seul le sprite droit est
appele. Pile et chemin des 17 autres machines conserves. Titre catalogue
immuable distinct du buffer des noms de samples.

Edition Destination : le producteur CC et les deux chemins de vidage worker
ignorent uniquement le LFO dont Dest est en edition. Les anciens paquets deja
en attente sont jetes ; les CC manuels, l'autre LFO et les autres pistes restent
actifs. Sortir du champ reprend la modulation. Aucun getter UI dans l'IRQ.

Preuves : `test_sample_wizard_selection_release.py` execute le chemin MACHINES
et les primitives/polices natives ; comparaison des 17 autres machines au v6,
nom mutable modifie trois fois, pile equilibree et rendu PNG inspecte.
`test_midi_lfo_destination_release.py` reproduit le defaut v6 et verifie les
128 numeros sur les deux LFO, le vrai encodeur DATA, les queues et la reprise.
Ces preuves utilisent les candidats et leurs metadonnees locaux sous
output/firmware, apres bootstrap natif. Autres preuves locales : LFO Speed
sur phase native, arp entrant jusque dans la queue audio native, valeurs
Chance/Swing stock, Slice enregistrement/grille, repeat sans diagnostic et
retour USB. Le worker natif emet les note-offs sur expiration et Stop dans v6
et v9. `test_fixed_main_delivery.js` exige le SHA approuve, le telechargement
exact dans Chromium et le refus d'une image corrompue. Generateur principal
verifie par --check. Autres sections du conteneur officiel conservees.
