# 99 — Beat repeat collectif sans page ni effets master

Demande d'AveyCole le 16/10/2026 : carte Cycles independante inspirée du
master beat repeat de TinyGregAudio. Precision explicite : actif uniquement
pendant TRACK + RETRIG maintenus. Adresses : VA OS 1.13.

## 1. Contrat

Maintenir TRACK + RETRIG puis un TRIG. Les pistes incluses dans Control All
Config repetent ensemble (six pistes par defaut si cette carte est absente) ;
le dernier TRIG maintenu choisit la division. Relacher un modificateur ou
tous les TRIG termine la boucle avec un fondu de 64 echantillons. Pas de
latch, page propre, popup ou FX master ajoutes. Stop et changement de projet
annulent sans reprise surprise. Les notes MIDI sortantes ne sont pas repetees.

Divisions TRIG 1–16 : 1/64, 1/48, 1/32, 1/24, 1/16, 1/12, 1/8, 1/6,
3/16, 1/4, 1/3, 3/8, 1/2, 2/3, 3/4, une mesure. Identiques a `rtg_divs` de
TinyGregAudio. Si la boucle depasse l'historique, division reduite par deux
jusqu'a tenir, comme son moteur. Ce sont des boucles audio, pas des notes
rejouees ni des modifications des patterns.

## 2. Source et integration

[FAIT] Reference locale MIT : `docs/flasher/source/sampler/model_tg.s`,
sections `rtg_audio`, `rtg_stream`, `rtg_divs`. Origine :
[TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG).
Nouvelle implementation C freestanding, avec le meme principe d'historiques
16 bits par canal, lignes de grille et fondus ; licence TinyGregAudio jointe.
Aucune recette Model-TG, machine sampler ou page master FX importee.

| Adresse | Usage |
|---|---|
| `0x4007240c` | Getter KeyEvent : intercepter les gestes avant les consommateurs |
| `0x4005982a` | Appel gain : traiter les canaux avant leur gain/mixage natif |
| `0x40000530` | Copier le module propre avant clear, puis bootstrap existant |
| `0x80001858` | Six blocs audio de 32 echantillons, stride 128 |
| `0x8000184c`, `0x40149310` | Horloge audio et tempo |
| `0x40a78628`, `0x40a78840` | Ancrage de grille au passage par le pas 1 |

Les trois detours gardent les chaines deja selectionnees. La variante JSR du
bootstrap Wizard conserve aussi son adresse de retour native ; la variante
JMP conserve sa reprise. Le petit chargeur utilise une queue libre de masque
reservee contre les cinq catalogues du principal. Le module RAM est place
apres les charges selectionnees (ou en `0x43000000` seul), sans deplacer leurs
adresses ; son image propre est ajoutee en clair apres leurs charges flash.
La limite `0x40200000` reste verifiee. Toute forme de hook inconnue est refusee.

[FAIT] GCC 15.2, `-mcpu=54418 -Os -std=gnu99 -fno-inline`, relocations ELF
`R_68K_32` explicites. Aucun scan heuristique de pointeurs. L'allocation native
retourne son pointeur dans D0 ; le prototype respecte cet ABI.

## 3. Audio et proprietes temps reel

Historique de 131 072 echantillons par canal : 1,5 Mio pour six pistes,
3 Mio avec les six cotes stereo optionnels de Wizard. Seuls les cotes actifs
sont rendus. Allocation/initialisation au premier geste UI, publication apres
clear ; aucune allocation, E/S disque, MIDI ou dessin depuis le rendu.
Le buffer est conserve jusqu'au redemarrage, pour eviter des allocations au
milieu de la performance. Les pointeurs stereo sont ceux du Wizard choisi,
sans dependance obligatoire a Wizard.

Les champs UI/audio partages sont volatils, mots 32 bits alignes. Un press
TRIG capture change son code en zero : Control All et les editeurs de pas ne
peuvent pas le reutiliser. Sa release reste capturee meme apres sortie du
combo ; un press anterieur au combo garde sa release native. Sans geste,
les echantillons restent identiques. Les retours delay/reverb ne sont pas
boucles ; les FX normaux continuent de fonctionner.

## 4. Preuves et limites

`tools/emu/test_beat_repeat.py` execute le module ColdFire compile :
deux ordres des modificateurs, 16 divisions, fallback au dernier TRIG tenu,
retour normal sur chaque release, tempos extremes, Stop/changement projet,
six amplitudes independantes, six cotes stereo, manque de memoire/IPL,
ABI gain/clavier et absence d'allocation dans le rendu.
Avec `--case`, il execute le vrai bootstrap du SYX navigateur et le
constructeur natif de cache, puis compare le module octet pour octet.
Le handler Control All reel conserve son masque pour les gestes captures.

Mesure du candidat 1 sur le corps propre a six canaux : environ 12 017 instructions par
bloc en repetition, 76 au repos apres allocation. Ce ne sont **pas** des
cycles ni un pourcentage CPU materiel. Charge, clics, grille et confort du
clavier physique restent a confirmer sur machine. L'absence de page propre
est prouvee par l'absence de tout appel dessin/menu/popup ; les reactions
des vues natives aux modificateurs restent a observer sur machine.

Page isolee : `docs/flasher-beat-repeat-test/`. Carte **experimentale**,
testable seule ou avec les machines existantes. Le principal reste inchange.
Ne pas promouvoir avant retour materiel explicite d'AveyCole.

## 5. Reproduction

Construire d'abord les cinq catalogues principaux via
`node tools/test_midi_persistence_flasher.js` puis
`node tools/test_midi_persistence_flasher.js --main`, puis :

```sh
python3 tools/gen_beat_repeat.py --catalog build/midi-persistence-main/all.json --catalog build/midi-persistence-main/alone.json --catalog build/midi-persistence-main/supports.json --catalog build/midi-persistence-main/wizard-chord.json --catalog build/midi-persistence-main/all-native.json --output build/beat-repeat-data.json --check
python3 tools/gen_beat_repeat_flasher.py --data build/beat-repeat-data.json
node tools/test_beat_repeat_flasher.js
python3 tools/emu/test_beat_repeat.py --data build/beat-repeat-data.json --case build/beat-repeat/all
python3 tools/emu/test_midi_current.py --case build/beat-repeat/all
python3 tools/check_midi_current_builds.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx --directory build/beat-repeat
```

Les images et exports locaux sont sous `firmware/` et `build/`, ignores.

## 6. Retour materiel et candidat 2 (16/10/2026)

[FAIT materiel rapporte] AveyCole confirme que le premier beat repeat
fonctionne, mais que le masque Control All Config ne choisit pas les pistes
repetees et que ses options occupent encore les touches sous TRACK + RETRIG.
Il demande que ces options disparaissent pendant le combo pour utiliser
toute la rangee de seize TRIG. Ce retour ne valide pas encore les correctifs.

[FAIT] Le premier moteur traitait toujours six pistes. Le handler `cac_keys`
lit directement le code evenement avant d'appeler le getter global : le test
precedent, qui appelait le getter avant `cac_keys`, ne reproduisait pas cet
ordre. Control All Config affiche ses choix sur les six LEDs TRIG, sans
page LCD propre.

Le candidat 2 lie `br_mask_address` au vrai octet `cac_mask` selectionne.
Un bit exclu garde le canal live ; la partie repetee suit un fondu individuel
par piste, partage avec son cote stereo. Sans Control All Config, les six
pistes restent incluses par defaut. Les vecteurs TRACK `0x40100ee8` et
`0x40100f98` passent par des wrappers : interception avant `cac_keys`, LEDs
1–16 reservees a la division tenue dans le combo, puis retour immediat aux
handlers precedents en sortie. Les transitions invalident la frame LED via
le gestionnaire racine natif, sans garder de pointeur de vue potentiellement
detruit. Aucun choix Control All n'est modifie par le geste de repeat.

[FAIT en emulation] Les 64 masques gardent exactement les echantillons live
sur les pistes exclues et repetent les autres. Le masque vaut aussi pour
les cotes stereo. Les press/release arrivent directement au wrapper TRACK,
sans passage prealable par le getter : seize divisions accessibles ; les
LEDs de configuration ne sont pas appelees pendant le combo et reviennent
au relachement. TRACK + TRIG ordinaire continue ensuite a modifier le masque.
La fixture MIDI remplace son ancien sentinel UI `1` par un objet mappe pour
permettre l'invalidation LED native. Le principal demeure inchange ; candidat
2 experimental en attente d'un nouvel essai materiel.
