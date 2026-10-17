# 113 — Restaurer la sauvegarde rapide stock

Demande AveyCole le 17/10/2026 : restaurer FUNCTION+SETTINGS maintenu vers la sauvegarde permanente, « just like stock ». Source : conversation de developpement. Test experimental separe ; principal limite a la correction filtre confirmee. Adresses : VA de l OS1.13.

## Reponse courte

[FAIT] Le getter Wizard avalait tous les evenements SETTINGS longs (flag5), meme FUNCTION. C etait une protection des accords de mods. Le candidat laisse uniquement un long FUNCTION sans accord deja utilise (mod_used=0) retourner code13 vers les memes gestionnaires stock. Pas de nouvelle routine sauvegarde, format fichier, ecriture ou attente ajoutee. Permanence apres reboot a confirmer sur appareil.

## Chemin et espace

kh_mod0x401aeae0..0x401aeb12 :50o remplaces exactement sur50. set_held0x401b24ac et mod_used+4 verifies par le generateur ; kh_eat0x401aeb62 conserve. References/credits du chemin original : TinyGregAudio, roterodamus, integration A.V. Pas de masque, payload ou etat neuf. Le nouveau corps utilise LSR pour tester bit1 FUNC et bit3 repeat via Carry, sans modifier l evenement. Corps/voisinage gardes.

Courts press/release, repeat et accords consommes conservent leurs transitions ; long SETTINGS seul reste protege. Long FUNC avec accord consomme reste avale. Les deux ordres d appui FUNC puis SETTINGS et inverse passent. Stock predicats long0x40072444 et FUNC0x40072490 executes sans modification. L ecran pattern normal reste le contexte de test ; aucun nouveau comportement de menu prive revendique.

## Preuves

Gen tools/gen_quick_save_test.py et --check ; source tools/machines/quick_save/mod.s ; constructeur tools/test_quick_save_flasher.js ; preuve tools/emu/test_quick_save.py. Vrai boot,512 combinaisons flags/etat held/used comparees au corps original : seule exception voulue long FUNC inutilise, tous autres resultats/etats identiques. Evenement intact, ABI/stack preservees. Chaine complete beat-repeat -> banque/Genie/SCRAMBLE -> Wizard verifiee avec et sans Banque MIDI. Constructeur valide aussi sans Wizard (aucun patch applique).

[FAIT en emulation] Code13 et predicats stock retablis. Ne pas confondre avec preuve d ecriture disque : la permanence du projet reste un test hardware. Diagnostic CPU/CUT et filtre conserves dans cette nouvelle page de test comme demande. Aucun diagnostic dans le principal, ni modification quick-save dans le principal.

## Publication principale (17/10/2026)

AveyCole demande explicitement la promotion du quick-save vers le principal. Seuls le corps de 50 octets et son adaptateur gardé sont promus ; aucun diagnostic ni optimisation audio de test. Le chemin de sauvegarde natif reste intact. La demande de publication ne constitue pas un nouveau relevé de persistance matérielle.

## Retour et test 2 (17/10/2026)

AveyCole signale FUNCTION allume et mute verrouille apres sortie du menu quick-save ; un tap FUNCTION ferme ce mode. [FAIT en emulation] Le handler latching-mute 0x40148744 marque tout autre accord FUNC comme utilise (0x401487ec), et le garde 0x401486fc conserve alors le verrou 0x401487ed. SETTINGS down suivi du save long laisse 0101 et le garde retourne 1 apres relachement.

Le candidat test2 termine ces deux octets uniquement lors du long FUNC+SETTINGS inutilise qui atteint deja la sauvegarde native. Aucun changement sur les autres accords ni sur le code de sauvegarde. Si aucun tweak ne possede les octets latch, aucun adaptateur ajoute. Le nouveau corps de68octets est ajoute au payload repeat apres composition ; trampoline de50octets garde sur le quick-save publie. Le test impose Control All Beat Repeat comme porteur (diagnostics retenus). Le loader et les references sont recalcules apres recompression du porteur Wizard. Une premiere allocation apres Wizard etait effacee par init du support sans Banque : rejetee avant publication. Constructeur verifie taille/references. Diagnostics conserves dans le test seulement ; principal inchange.

Preuve tools/emu/test_quick_save_latch.py :512cas gardent retour/etats SETTINGS/ABI/evenement, seule difference attendue = liberation latch lors du long FUNC non consomme. Ancien et candidat executent le vrai garde mute, ancien1 contre candidat0 apres relachement. La presentation/destruction du menu complet et les LEDs physiques restent a verifier sur appareil.
