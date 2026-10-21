# 85 — Fondu ACID de Kevin sur Supermodel

Demande d’AveyCole du 14/10/2026 : remplacer ACID par le correctif de Kevin,
puis intégrer WAVE séparément. Source MIT : Kevin-Shallvari/Modded-Cycles,
wave-acid-preview, commit 5b6108ee57cdee4767f91bfb894ccefaadf4210d.
Adresses : VA de l’OS 1.13.

## Réponse courte

[FAIT] Nouveau trig : rampe sur 32 échantillons (~0,67 ms). Aucun fondu
supplémentaire sur un slide. Quatre corps liés, partagés par 128 recettes,
augmentent de 72 octets ; aucun moteur stock remplacé.

Le flasher de test reprend le main TG, les recettes RAM de Banque et ChordKeys.
Le moteur complet comprimé avec profondeur 512 augmente de 20 octets.
La source flash Banque/ChordKeys et son unique immédiat dans le crochet
0x401907a4 passent de 0x401f8f76 à 0x401f8f8a. Les destinations RAM,
réservations cache et routines Banque ne changent pas. Pas de sauvegarde MIDI.
Références des écritures et charges utiles recalculées pour chaque recette.

## Preuves

Navigateur : ACID seule, TG, MACRO, MACRO+TG, Select All et Banque sans ChordKeys.
Chaque image est construite depuis l’OS officiel ; références strictes, conteneur
et signature vérifiés. ACID reste expérimental : pas de test matériel d’AveyCole.

Émulation : tools/emu/test_kevin_acid_fade.py utilise la boucle audio native et
compare au DSP C de référence. tools/emu/test_kevin_acid_browser_boot.py compare
l’image Python/navigateur et contrôle démarrage/cache de la Banque.
MOVEC observé : la cohérence physique du cache n’est pas simulée.

## Reproduction

Le générateur tools/gen_kevin_acid_test.py prend le catalogue main exporté,
le dossier main et tools/machines/acid/kevin-fade-map.json comme --upstream.
Le map conserve les quatre anciens/nouveaux corps compilés de Kevin et les
courtes modifications PACK ; aucun firmware Syntakt extrait n’y est stocké.
Le code source du DSP et la licence de Kevin accompagnent le test.

WAVE et Model909 sont des intégrations distinctes encore en investigation.

## Vérification matérielle (14/10/2026)

AveyCole : « Push acid fix to main as hardware tested ». Correctif promu sur
le flasher principal ; test séparé conservé. Aucun ajout WAVE ou Model909 au main.

## Gain de sortie ACID (21/10/2026)

AveyCole signale un niveau ACID trop faible. Copie privée : gain fixe de
2 (+6,02 dB) après le rendu ACID natif, avant le filtre de piste. Source :
`tools/machines/acid/output_gain.S`. Le dispatch render ACID à `0x467890c4`
pointe vers `0x467b4100`, qui appelle le rendu original `0x46776404`, puis
double ses 32 échantillons avec saturation signée (`addl`, `satsl`). DRIVE,
état du DSP, enveloppes et fondu de retrig restent ceux du rendu original.
Le masque partagé `0x40154ae4` reste entièrement libre.

Reproduction privée : `output/firmware/build_acid_gain_v1.py`, variantes
`all-features-acid-gain-test-v1.syx` et
`no-filter-pon-acid-gain-test-v1.syx`, depuis les recettes USB return v1.
Les deux conservent les correctifs précédents et le diagnostic P/O/N.
Seule la section 3 du conteneur officiel est reconstruite et resignée.

[FAIT en émulation] `tools/emu/test_acid_output_gain.py` charge le bootstrap
natif des deux images. Saturation aux limites int32, canaris autour du buffer,
retour D0 et registres D2/A2 préservés ; six voix ACID simultanées, changement
de note et retrig : échantillons exactement égaux à la référence doublée et
saturée, états des voix et du DSP identiques. Les six machines stock restent
identiques. Coût ajouté mesuré : 205 instructions par voix et bloc de 32
échantillons, hors rendu original ; ce nombre ne mesure pas les cycles matériels.
La preuve USB return passe aussi : 36 scénarios 2ch/6ch sans trame corrompue.

Retour matériel d'AveyCole : « everything seems golden i went ahead and found
the.syx and tested it, sounds great ». Le message confirme le résultat sonore
du gain ; la variante exacte n'est pas précisée. Le main servi reste 2.09,
inchangé en attendant une demande de promotion.

## Exception pendant beat repeat, variante filtre (21/10/2026)

AveyCole demande ensuite une promotion avec filtre, puis l'annule avant toute
publication. Il rapporte `V04 M5 P400CF866`, pendant beat repeat. La confirmation
sonore precedente ne vaut donc pas validation de stabilite de la variante v1.

[FAIT] Le lien prive v12 assigne `mi_beat_popup=br_popup_out` (`0x467abee8`),
au lieu de `br_popup` (`0x467abe3c`). Le premier est uniquement l'epilogue
`movem / unlk / rts` du popup. Au premier relachement TRACK+RETRIG, le diagnostic
P/O/N l'appelle sans son prologue et depile le cadre appelant. La preuve
precedente `prove_filter_pon_midi_v12_usb_return.py` simulait directement
`0x467abee8` : elle masquait precisement ce defaut. L'adresse `0x400cf866`
est le getter projet natif, pas une adresse du gain ACID. Le PC materiel exact
n'est pas reproduit ; la corruption de pile du chemin signale l'est.

Correction privee v2 : appel `0x467b1b08` redirige vers l'entree complete
`0x467abe3c`. Un seul octet MAIN decompresse change par rapport au v1 filtre ;
gain ACID, filtre, repeat audio, USB et tous les autres correctifs identiques.
Le lien dans le constructeur v12 est corrige aussi ; contrat explicite dans
`filter_diagnostic.c`. Aucun firmware historique n'est remplace.

[FAIT en emulation] `tools/emu/test_filter_repeat_diagnostic.py` reproduit
le depilage du mauvais cadre avec l'ancien firmware, puis execute le vrai
corps popup corrige (allocations/presentation UI simulees) : deux ordres de
relachement, quatre repetitions chacun, formatage natif P108 O41 N39,
compteurs remis a zero, pile et registres non volatils preserves. Regression
ACID six voix/note/retrig/saturation et six machines stock conservee.
Le v2 reste a tester sur appareil. Principal public 2.09 inchange ; la copie
locale non publiee `all-features-acid-gain-main-210.syx`, creee avant annulation,
n'est pas servie.

Demande suivante d'AveyCole : meme version filtre, sans diagnostic. Copie
`all-features-acid-gain-filter-no-diagnostic-v2.syx`, SHA256
`5bb7426da624ee453aa4875f5d06448ff2aa7f8d4a54373e61d77b9c80a3ffd9`.
Constructeur prive `build_acid_no_diagnostic_v2.py` : retire les sections P/O/N,
restaure l'entree du regulateur et l'appel br_key original, efface le helper
diagnostique. Aucun changement du filtre ni du gain. Le resultat est identique
octet pour octet a la copie 210 non publiee (le helper corrige est entierement
efface dans les deux cas). La preuve beat repeat couvre aussi cette variante :
deux ordres de relachement x4, aucun popup diagnostic, pile et registres
preserves ; ACID six voix/machines stock et USB 36 scenarios passent.
Fichier livre pour essai, sans publication ni resultat hardware revendique.


## Promotion confirmee sans diagnostic (21/10/2026)

AveyCole rapporte « no crash, make that the version served by main please ».
Principal 2.10 : copie exacte du fichier filtre sans diagnostic v2, SHA256
`5bb7426da624ee453aa4875f5d06448ff2aa7f8d4a54373e61d77b9c80a3ffd9`. Gain ACID +6,02 dB, filtre et correctifs precedents
conserves. Aucun rebuild du candidat teste ; aucun diagnostic ajoute.
Le retour confirme son essai beat repeat sans crash, sans mesure de stabilite
longue duree revendiquee.
