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


## Candidat prive v13 : Swing physique, note-off auto et raccord CHORD (21/10/2026)

[FAIT, demande utilisateur] Le v9 filtre reste publie en main 2.11. Apres la
publication, Swing MIDI Out ne bouge plus au potard ; notes parfois tenues ;
Attack CHORD clique a chaque nouvelle note, meme en augmentant sa valeur.
La nouvelle enquete sur la distorsion USB est exclue de ce tour a sa demande.
L'interaction plus large arp Tone/MIDI Out est aussi laissee de cote apres son
message « arp thing is probably fine too ». Aucun changement USB dans v13.

[FAIT en emulation] Le potard Swing entre dans le vrai TrackAccessor 400fd204.
Son setter 40016378 change le timing, puis le pont ajoute au v6 relit le mot6
DU SON (encore zero) et annule le mouvement. Le pont doit donc seulement agir
sur SoundAccessor 400fd134. Preuve `test_midi_swing_encoder_release.py` : vrai
ParameterPageView, evenement physique12, delta accelere calibre Q8 (accelerateur
instrumente, pas son setter). Tone4 donne Swing4 ; MIDI17 donne Swing8 et le
garde. Le constructeur d'evenement natif 400548ce rend ensuite les delais
[0, 864000, 0, 864000] sur quatre pas alternes. Les deux variantes passent.

[FAIT en emulation] Avec une note arp Tone tenue sur le canal auto, selectionner
MIDI Out avant son relachement faisait perdre la fin de note dans v9. Capturer
piste/note traduite/canal a l'attaque conserve le destinataire de son note-off.
`test_midi_input_owner_release.py` reproduit v9, puis passe 24 changements par
variante v13 (Tone0/3, MIDI1/2/4/5, notes36/60/84), sans double relachement.
Cela ne prouve pas la disparition de toutes les causes de notes tenues.

[FAIT en emulation] La rampe Attack partagee repart brutalement a zero au
retrig : la queue CHORD precedente est coupee. Avec le vrai renderer et Attack32,
le raccord mesure passait de 8158579 a 0 sur un echantillon. Le wrapper
`chord_attack.c` reprend la vraie sortie du bloc precedent et compense le
premier echantillon apres Attack/filtre par une queue lineaire de 64 echantillons
(1,33ms). La difference et la somme sont saturees ; etat propre a chaque piste,
aucune allocation, aucune sortie MIDI. La duree et la rampe natives restent
identiques ; Attack=0 et les autres machines deleguent sans modifier l'audio.
Le hook est le JSR 4014b0aa de ava_post, vers avfc_run pour filtre et ava_run
sans filtre. La cible de delegation est capturee apres verification des octets.

`test_chord_attack_release.py` : six pistes, continuite exacte au redemarrage,
fin du raccord apres64samples, rampe native reprise exactement, Attack=0 et
Tone/Wizard/MIDI exacts echantillon par echantillon. La fixture rejoue la copie
native des wavetables CHORD via chord_boot_fixture ; sans ce boot2 les tables
etaient nulles et le faux silence n'etait pas une preuve audio.
Preuve audio locale `prove_chord_retrig_v13.py` : renderer natif, Attack32,
retrig bloc100 ; premiere sortie du retrig=derniere sortie precedente, deux
variantes. La preuve ne remplace pas une ecoute physique des notes isolees.

Autres regressions passees sur les deux .syx finaux : 128 hauteurs entrantes x
six pistes, live/step rec et save/load natifs, note-offs apres changement de
machine/canal/port, reset et STOP live, sequence file audio -> worker -> USB/DIN,
LFO1/2 et CC locks, transitions vers17machines audio, Slice preview/grille/rec,
TRACK+FUNC, neuf CC assignables, menus/valeurs stock, Dest silencieux, Sample sur
Wizard et sprite droit, beat repeat sans diagnostic. Sources locales des
preuves et builder sous output/firmware ; preuves principales sous tools/emu.

Les deux candidats sont experimentaux, sans diagnostics, non promus :
- Filtre : `all-features-midi-playability-no-diagnostic-v13.syx`, SHA-256
  `4e9d7ad55faf68e15f1df0c681ad6bc17fa650eda318b51ae4dfc9273d3b17e1`.
- Sans filtre : `no-filter-midi-playability-no-diagnostic-v13.syx`, SHA-256
  `c5009039f084b48cbcb9bf29421abb9110390f2a3c67b95fc2466b31d4a822b2`.

[À FAIRE sur machine] Ecoute CHORD Attack (minimum, lent, isole et retrig), Swing
MIDI Out au potard et sequences, relachements pendant les changements de piste.
La page privee locale v13 sert exactement le candidat filtre epingle par SHA,
et propose les deux fichiers. Le MAIN public reste le v9 approuve.

[FAIT en emulation] Cout CHORD, filtre ouvert : +46instructions par piste au
regime etabli ; +738 pendant le premier bloc du raccord (par rapport au
delegate natif). Comptage d'instructions, pas mesure des cycles ni du temps IRQ
sur appareil. HTTP local : les deux fichiers servis sont identiques aux
candidats, tous checksums SysEx valides ; page epinglee SHA verifie, Connect
active seulement apres validation, aucune connexion ni installation lancee.


## Retour materiel v13, CHORD et Swing (21/10/2026)

[FAIT sur machine, AveyCole] « chord fix worked » ; le potard Swing bougeait,
mais les notes MIDI semblaient encore droites, y compris avec de nouveaux pas.
Pendant l'enquete, avant toute modification du firmware, il confirme ensuite :
« idk what changed but its working now ». Le v13 reste donc intact. Aucun v14
compile ni servi, aucune promotion main demandee par ce retour.

[FAIT en emulation] L'enquete supplementaire execute les wrappers reels du
builder, puis l'ordonnanceur complet 400550e0..4005542e et la queue audio native.
Swing0 : messages MIDI aux temps 5500000,10900000,16300000,21700000.
Swing30 : 5500000,14140000,16300000,24940000. Les deux contretemps sont retardes
de3240000 ; le message MIDI conserve sa date exacte. Conversion native du
pattern 4005b642 puis4005b4ec conserve aussi Swing8 et les flags alternes.
Cela complete le test precedent du seul offset du builder ; la cause du
comportement transitoire sur appareil n'est pas etablie. Ne pas la presenter
comme corrigee par un nouveau changement. Pas de capture MIDI ni flash lance.


## Publication 2.12 : DX optionnel, LTC et SIL (21/10/2026)

[FAIT, demande utilisateur] AveyCole demande explicitement de promouvoir le
candidat filtre avec DX, Off par defaut, puis de raccourcir les valeurs du menu
Latch en LTC et Silent en SIL. Cette demande remplace la politique historique
qui reservait tout diagnostic aux tests. Aucun resultat materiel supplementaire
n'est deduit du mot « perfect » ni de l'autorisation de publication.

[FAIT en emulation] Depuis le candidat v14 epingle, seuls neuf octets des deux
chaines changent ; tailles, pointeurs, code et etats sont identiques. Le
conteneur est reconstruit depuis l'officiel, autres sections identiques. Le
MenuView natif rend LTC et SIL sans chevauchement. DX Off/On, defilement,
64 combinaisons sauvegardees, attente d'arret pour les E/S et popup P/O/N
verifies. Le regulateur audio conserve exactement son etat avec DX Off/On.

Source : `all-features-dx-ltc-main-212.syx`, SHA-256 `5111c5401520856496c9626598b6a10c4929e123052d512cc5384621b8ca73ab`.
MAIN SHA-256 `0df3485544eba89e0e934d979f28acf512548aee074c87669114e0ffe2b1c14c`.
Generateur : `tools/build_dx_main_release.py`. Filtre conserve ; USB2ch par
defaut ; DX Off par defaut et sauvegarde avec les autres preferences.

[FAIT en verification de livraison] Chromium charge les deux OS officiels requis,
produit les octets exacts 2.12, telecharge le meme fichier et rejette une image
corrompue sans fallback. PDF trois pages rendu et inspecte. Chevauchements :
171 tweaks, aucun conflit nouveau. Les controles generiques tweaks.js/REGISTRY
signalent des sorties deja desynchronisees ; aucun tweak ni allocation de ces
catalogues n'est modifie par cette publication d'image fixe.


## Identites MACHINES privees v15 (21/10/2026)

[DEMANDE AveyCole] Avant le retrait des pages de test, donner aux machines
ajoutees des profils STR/DEX/MAG differents et des initiales anguleuses propres.
Sample Wizard conserve explicitement son chapeau natif. Servir uniquement via
le flasheur prive habituel ; aucun changement du principal 2.12.

[FAIT en emulation] Les statistiques stock sont des images 48x33, pas des
parametres sonores. Douze triplets uniques dans machine_identity/profiles.json ;
onze icones 34x34 dessinees depuis les grilles originales du generateur. Les
valeurs sont des profils visuels, sans action sur le DSP. Wizard affiche ses
trois stats sous son titre deux lignes ; les pixels de sa moitie droite et son
pointeur chapeau sont exactement ceux de 2.12. Les six cartes stock conservent
leurs pixels exacts. Les 18 cartes passent le rendu natif avec pile et registres
preserves. DX Off/On et le vrai popup P/O/N restent verifies.

Trois detours UI seulement : chargement sprite gauche 46788124, droite4678813e,
entree titre Wizard467b668c. Donnees et helpers dans 467c2000..467c47f0 ;
les instructions audio sont identiques et les autres sections restent celles
du conteneur officiel. Generation : tools/build_machine_identity_test.py ;
preuve : tools/emu/test_machine_identity.py. Test materiel encore necessaire.

Candidat prive : all-features-machine-identity-test-v15.syx, SHA-256
`2b8da1cd8be34cadd6f6db83900473c1580c1085b112a480041b259c9386d99b`.
SHA-256 du main2.12 toujours
`5111c5401520856496c9626598b6a10c4929e123052d512cc5384621b8ca73ab`.
La suppression des anciennes pages reste dans une branche locale separee,
non publiee, conformement a la demande de priorite.


## Promotion 2.13 et variante sans filtre (21/10/2026)

[FAIT, demande utilisateur] « perfect, push that to main and give me the no
filter version ». Le main2.13 sert exactement le candidat v15 approuve, SHA256
`2b8da1cd8be34cadd6f6db83900473c1580c1085b112a480041b259c9386d99b`, sans recompilation ni modification.
Les profils restent purement graphiques ; aucun nouveau resultat audio ou
materiel n'est revendique. La suppression des anciennes pages reste en attente.

La variante privee sans filtre reprend le v14 sans filtre epingle, puis les
abreviations LTC/SIL et les memes profils/icones v15. Chapeau Wizard identique.
SHA256 `41559fab2ce3784ab262cb35173be6f5e8bd932aa379181b8728f50147450a08`.
Les18cartes, le bootstrap natif et le popup DX passent en emulation.
