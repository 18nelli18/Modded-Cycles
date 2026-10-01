# 31 · Model-TG : intégration

Travail du 01/10/2026, à la demande de l'utilisateur : « Voici un autre projet que j'aimerais que tu intègres à notre projet : https://github.com/TinyGregAudio/Model-TG. Gère bien tout ce qui concerne la performance, l'optimisation, etc., pour l'intégrer au précédent ajout sans tout détruire. »

Décisions de l'utilisateur, après l'analyse du §3 :
- **Model-TG seul d'abord** dans le flasher, puis la version combinée avec les moteurs du Syntakt ;
- dans la version combinée, **le Sampler en 7ᵉ machine**, les moteurs du Syntakt ensuite (8ᵉ à 12ᵉ).

## 0. En bref

| | État |
|---|---|
| Model-TG seul dans le flasher web | `[FAIT]` tel que son propre build l'exporte, même empreinte (§2) |
| Model-TG avec l'audio USB 6 canaux | `[FAIT]` aucune écriture commune ; pas encore testé sur la machine (§2) |
| Conflits avec les moteurs du Syntakt | `[FAIT]` analysés (§3) |
| Version combinée Model-TG + moteurs du Syntakt | `[À FAIRE]` plan au §4 |

## 1. Ce qu'est Model-TG

Source : dépôt [TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG), commit `454963b` (01/10/2026), `README.md`, `docs/INTERNALS.md`, `docs/PAYLOAD.md` et `build.py`.

- **Ce qu'il ajoute** :
  - une machine **Sampler** (index 6, la 7ᵉ) à sept modes de lecture ;
  - le rééchantillonnage, une page de retrig avec 12 effets master ;
  - Attack, Filtre et Résonance sur les machines d'origine ;
  - Scale Lock, l'envoi d'échantillons par Elektron Transfer, une page System (charge processeur) ;
  - une charge processeur plus basse.
- **Licence MIT**. Aucun octet Elektron dans le dépôt : l'image se construit depuis l'OS de l'utilisateur, comme ici.
- **Comment il se pose dans l'OS** (`build.py`, `docs/INTERNALS.md`) :
  - un seul bloc de code de **80 592 o** en `0x401ab750`, exécuté **en place** ;
  - ce bloc occupe 5 des 16 blocs de 16 Ko du **cache du système de fichiers** (`0x401ab750..0x401eb750`), retirés au cache en réécrivant son initialisation (`0x400792f2`, `0x400792bc`) ;
  - **131 écritures** sur l'OS, toutes vérifiées sur les octets d'origine ;
  - son crochet de démarrage remplace l'appel de la remise à zéro du BSS (`jsr 0x400004b2` en `0x40000530`). Il règle aussi `ACR1` (cache en écriture immédiate pour `0x4C000000..0x4FFFFFFF`) et remet le BSS à zéro, sauf son bloc ;
  - il garde une **zone d'échantillons de 64 Mo** en `0x4a800000..0x4e800000` (la réserve du Model:Samples).
- **Ses optimisations** (`docs/INTERNALS.md`) :
  - pistes muettes non calculées ;
  - effets d'envoi sautés quand tout est silencieux (étage de sortie au repos : environ 24 → 13 %) ;
  - KICK et CHORD plus rapides, à l'identique ;
  - temps de chaque piste mesuré par un minuteur (`0xfc07800c`).
- **Prévu pour ce flasher** : `build.py --modded-cycles` exporte Model-TG au format de nos tweaks (`docs/PAYLOAD.md`). Le texte demande :
  - un ajout après l'OS sans fichier Syntakt ;
  - de le garder exclusif ;
  - d'afficher la provenance et la licence MIT.

## 2. Phase 1 : Model-TG seul dans le flasher `[FAIT]`

**Génération** : `tools/gen_model_tg.py`, depuis un clone du dépôt au commit épinglé.
- Il lance le `build.py` de Model-TG, relu au préalable : il n'appelle que l'assembleur, l'éditeur de liens, git et l'outil de dépaquetage, et n'écrit que dans son dossier `build/`.
  - On lui donne la section 3 dépaquetée par nos outils, et un outil de dépaquetage qui ne fait rien.
  - Ses écritures et son ajout sont repris tels quels. Seuls l'identifiant, le nom, la description et la liste des incompatibilités sont les nôtres.
- Résultat : `tweaks/model-cycles_OS1.13/30-model-tg.json` (131 écritures, 86 240 o ajoutés après l'OS), et sa licence `LICENSE-Model-TG`.
- **Notre constructeur redonne l'empreinte annoncée par son build** : MAIN OS `fb985a16…`. Le générateur le vérifie à chaque fois.

**Flasher web** :
- Une carte « Model-TG », par TinyGregAudio, avec un lien vers sa licence (servie à côté de la page) et ses crédits.
  - Rappel quand elle est cochée : n'installer un OS qu'avec l'identité CYC (Device Config > Transfer) ; les projets avec le Sampler ne jouent pas sur un autre firmware.
- **Exclusive** :
  - avec les trois tweaks de drumkilla, que Model-TG contient déjà (son mute verrouillé est modifié) ;
  - avec les moteurs du Syntakt : 12 écritures communes, §3.
  - Cocher l'une décoche l'autre.
- Un tweak « append » sans morceau du Syntakt ne demande plus le fichier Syntakt (`builder.js`, `build.py`).
- **Avec l'audio USB 6 canaux** : aucune écriture commune, donc la combinaison est proposée (MAIN OS `1511f84c…`).
  - Pas encore testée sur la machine.
  - En particulier, le rééchantillonnage de l'audio USB de l'ordinateur (mode A+M de Model-TG) n'a pas été essayé avec le mod 6 canaux.
- 513 combinaisons, `webflash_smoke.sh` ALL OK (621 vérifications, dont l'exclusivité et les deux combinaisons Model-TG). Build `2026-10-01-12`, version 1.5.

**Pas d'émulation de Model-TG pour l'instant** :
- Notre banc ne rejoue que la boucle des voix. Les voix de Model-TG y sortent presque muettes, parce que son code attend un état mis en place au démarrage et par l'interface.
- Son build est testé sur la machine par son auteur. Pour la phase 2, il faudra un banc qui reproduit cet état.

## 3. Conflits avec les moteurs du Syntakt

Source : comparaison des écritures (`30-model-tg.json` et nos tweaks `24-syntakt-*`), et lecture de `src/model_tg.s`, `src/phase1.s` et `build.py`.

**Écritures communes** : 12 endroits.

| Endroit | Model-TG | Nous |
|---|---|---|
| Bornes du nombre de machines (`0x400147a5`, `0x400148ab`, `0x400148b3`, `0x400a25e1`, `0x400a26e9`, `0x400a7df5`) | 5 → 6 | 5 → 5 + n |
| Recherche de descripteur (`0x4004df5c`, `0x4004df76`) | ses détours (Sampler) | nos détours (machines ajoutées) |
| LFO et Amp Decay par machine (`0x4005a6a6`, `0x4005a6b6`) | `sampler_lfo_gate`, `sampler_amp_gate` | nos bornes |
| Noms des machines (`0x400a2615`) | sa table de noms | notre table |
| Appel update/render de chaque piste (`0x400a7e02`) | `sampler_dispatch` | notre détour en `0x400a7dfe` |

**Autres conflits, sans octet commun** :
- **Démarrage** : son crochet remplace l'**appel** de `0x400004b2` ; le nôtre est **dans** `0x400004b2`, qui ne serait plus appelée. Notre charge utile ne serait jamais recopiée.
- **Tables update/render** : nous les déplaçons pour y ajouter nos machines ; son dispatch lit la table de render d'origine (`0x40118610`, 6 entrées) en dur.
- **Mémoire** :
  - les adresses `0x48000000..` sont une seconde vue, sans cache, des mêmes 128 Mo que `0x40000000..` (la sortie audio en `0x4a3ed080` correspond à `0x423ed080`) ;
  - sa zone d'échantillons correspond donc à `0x42800000..0x46800000`, **où se trouve notre charge utile** (`0x43000000..0x43042000`) : charger des échantillons l'écraserait.
- **Place sous la zone de travail du bootstrap** : après son bloc (`0x401bf220`), il reste **265 696 o** jusqu'à `0x40200000`. Notre charge utile à 5 moteurs fait **269 056 o**.
- **Pistes muettes** : son dispatch a sa propre logique (`voice_quiet`, `sil_note`). Elle juge une voix d'après l'état de voix du Cycles, que nos moteurs du Syntakt ne mettent pas à jour. Et notre régulateur ne verrait pas le Sampler.

**Ce qui est compatible** :
- Son CHORD optimisé (`chord_osc`) reçoit ses tables d'ondes par les pointeurs que nous redirigeons (`0x40118590`, [28](28-code-syntakt-en-sram.md)) : il suivra.
- Son Sampler calcule dans son propre tampon (`sampler_buf`), pas dans la zone de travail en SRAM que nous empruntons ([26](26-sram-empruntee.md)). Il ne touche pas aux zones de SRAM reprises aux tables de CHORD.
- Sa sonde de charge (vecteur de l'interruption audio, `0x4005966a`) et ses crochets de l'étage de sortie (`0x40059872`, `0x4005981e`) ne recouvrent pas les nôtres (`0x40059382`).
- Ses optimisations (effets au repos, KICK, CHORD) s'ajoutent aux nôtres.

## 4. Plan de la phase 2 : Model-TG + moteurs du Syntakt `[À FAIRE]`

1. **Banc d'émulation de Model-TG** : rejouer sa boucle des voix avec l'état qu'il attend, pour avoir une référence (machines d'origine, Sampler) avant de toucher à quoi que ce soit.
2. **Mémoire** : poser notre charge utile au-dessus de sa zone d'échantillons, vers `0x46800000` (sous la pile, en `0x48000000`).
3. **Taille** :
   - ne plus stocker les zones à zéro de notre charge utile : morceaux séparés au lieu d'un seul bloc ;
   - gain de quelques dizaines de Ko, pour tenir dans les 265 696 o disponibles.
4. **Démarrage** : un seul crochet, qui recopie notre charge utile (posée après son bloc) puis passe la main à son `boot_extra_hook`. Il sera vérifié en émulation comme aujourd'hui, car un OS qui ne démarre plus ne se rattrape pas sans interface MIDI.
5. **Machines** :
   - Sampler en index 6, moteurs du Syntakt à partir de 7 ;
   - nos détours (noms, descripteurs, enregistrements, potards) laissent la machine 6 aux siens ;
   - bornes à 6 + n.
6. **Boucle des voix** : un seul dispatch.
   - Le Sampler et les machines d'origine passent par le sien.
   - Nos moteurs (index ≥ 7) passent par notre passerelle, avec la table de render agrandie.
   - Notre régulateur encadre toutes les voix, Sampler compris.
   - Sa mesure par piste (page System) est gardée.
7. **Preuve en émulation**, puis firmware de diagnostic et essai sur la machine.

Il faudra adapter quelques endroits du code source de Model-TG (licence MIT). Les modifications seront appliquées au build et listées, pour pouvoir suivre ses nouvelles versions.
