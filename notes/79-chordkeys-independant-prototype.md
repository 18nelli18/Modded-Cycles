# 79 — ChordKeys indépendant : prototype de chargement

Demande d’aveycole du 13/10/2026 : rendre ChordKeys, Model-TG et Banque MIDI
sélectionnables indépendamment, puis résoudre leurs exclusions réelles.
Adresses : VA de l’OS 1.13. Aucun changement publié dans les flashers.

## En bref

[FAIT] Le placement ChordKeys actuel inclut 17 réserves, soit 5 016 octets
de code/données propres, dans le RAW Banque MIDI. La dépendance du catalogue
vient de cette installation au boot ; retirer seulement `requires` casserait
les cibles des hooks. Les autres fragments Chord restent dans leurs sprites.

`gen_chord_independent_payload.py` isole ces fragments dans une charge creuse
de 9 388 octets, compressée à 4 025 octets. Les espaces entre fragments sont
initialisés à zéro. Tous les symboles propres doivent être fournis soit par
ces réserves, soit par les écritures Chord ; aucun helper Banque n’est ajouté.
Les hooks natifs Chord et le slot HARMONY26 restent identiques.

[FAIT en émulation] `test_chord_independent_payload.py` installe exclusivement
ces fragments et les écritures Chord sur l’OS officiel : six pistes × seize
touches, notes on/off et configurations utilisent les vraies fonctions.
Ni Banque, ni Model-TG, ni moteurs supplémentaires ne sont installés.
La relecture du flux compressé restitue exactement le RAW propre.

## Prototype de bootstrap

`gen_chord_independent_boot.py` produit uniquement un candidat local marqué
`flashable:false`, absent du catalogue. Il réutilise deux masques libres sans
Banque : loader `0x401907a4` et décompresseur propre `0x40167c50`. Les sprites
sont redirigés vers leurs copies. Le décompresseur est celui de notre source
MIT `midi_lanes/lfo_cc_depack.s`, sans ses fonctions musicales.

Le flux commence à la fin du MAIN officiel ; le loader le décompresse avant
le clear BSS. Le clear préserve seulement la plage Chord alignée et son propre
helper, puis rejoint `0x4000053a`. La preuve ciblée
`test_chord_independent_boot.py` vérifie le chargement, le clear hors réserve,
la pile et la reprise. Les registres cache MOVEC ne sont pas simulés.

## Ce qui reste à faire

- Intégrer un bootstrap commun avec TG, Banque et tous les moteurs : les deux
  masques du prototype sont déjà utilisés lorsque Banque est installée.
- Prouver la réserve mémoire sur le démarrage complet et le cycle de vie OS,
  au-delà du contrat ciblé décompression/clear.
- Vérifier les chemins audio, MIDI, sauvegarde Chord, gammes TG et les images
  complètes navigateur/Python de chaque combinaison avant un test matériel.
- Découpler les supports de Banque qui appellent encore TG/LFO/Genie.
- Résoudre les autres exclusions de mémoire/hooks ; ne pas les effacer du
  catalogue sans remplacement vérifié.

Les sauvegardes MIDI restent désactivées. Ce prototype ne change pas les
mesures CPU et ne réintroduit pas la copie LFO optimisée rejetée sur matériel.

## 13/10 — Candidat indépendant et réserve cache native

[FAIT] Les réserves originales occupaient le septième bloc cache natif :
elles doivent être retirées du LRU disque, pas seulement protégées du clear.
`gen_chord_low_cache.py` reloge ces fragments dans le premier bloc sans TG.
Le runtime propre commence à `0x401aba60` et, avec clear et adaptateur pads,
occupe 9 600 octets. Un bloc de16 KiB retiré, quinze blocs disque conservés.
Avec TG, son emplacement `0x401c383c` retire sept blocs au total (six TG et
un Chord), laissant neuf blocs disque. Avec Banque, la réserve existante
de neuf blocs et son runtime compatible sont conservés.

Le loader en masque lit le flux à `0x401f8f76`, après tous les flux moteurs.
Une réserve flash explicite bornée depuis `0x401aa140` maintient cette source
fixe. Le builder ne l’accepte que pour ChordKeys et cette adresse ; la limite
globale `0x40200000` reste obligatoire. Le tampon disque nul TG est intact.

[FAIT en émulation] Startup TG, MACRO, ACID, Syntakt et ensemble complet,
avec/sans TG, sans Banque : décompression et clear réels. Le constructeur
cache natif `0x4007929c` ne relie que les blocs restants ; runtime conservé.
Le clavier autonome passe six pistes × seize touches. Le vrai getter de
configuration et le DSP passent patterns0/1/95, ABI, SHAPE/COLOR, données
invalides, PCM stock avec Keys OFF et activation au bloc suivant. Cela ne
mesure pas le CPU matériel.

`gen_chord_independent_flasher.py` vérifie les reprises propres de254 recettes
moteurs et leurs hashes. Le candidat navigateur passe neuf sélections :
Chord seul, TG, MACRO, ACID, Syntakt, Banque sans moteurs, Banque complète,
ensemble TG sans Banque, ensemble sans TG/Banque. Conteneurs et hashes mods
vérifiés ; images intégrales identiques en Python et navigateur. Les neuf
chaînes boot restituent leurs RAW exacts. Clear et cache natifs sont exécutés
pour les sept variantes autonomes. Banque garde sa chaîne éprouvée, vérifiée
jusqu’au flush de son loader. MOVEC/cache matériel non simulé.

Sans Banque, un pad sélectionne sa piste s’il n’y a aucun TRIG physique tenu.
Tenir un TRIG conserve les modificateurs HARMONY et leurs releases, même après
relâchement du TRIG. Les deux interfaces PadsView sont vérifiées. Le nouveau
geste de pads et le masquage des LEDs grille dans le runtime Banque restent
un changement distinct à terminer ; ne pas les attribuer à ce candidat.

Page prévue : `flasher-chord-independent-test`, build
`2026-10-13-chord-independent-startup`. Expérimental, main inchangé, sauvegarde
MIDI désactivée. Control All Config est marqué testé après confirmation
matérielle d’aveycole. Les autres exclusions non liées aux moteurs et les
dépendances de Banque restent à résoudre sans retirer leurs gardes à l’aveugle.
