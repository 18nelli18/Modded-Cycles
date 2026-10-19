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
