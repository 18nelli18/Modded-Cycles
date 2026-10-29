# Module FX par piste et corrections audio — 2.57

Sources propres du module integre aux livraisons 2.57. `light-routing.c` produit
le fichier de compilation `routing.c`. Le bypass nul conserve le clear de sortie
et retourne lorsque `lt_active == 0`. Le masque d'historique reste `now & 31`.
Les noyaux de chorus, modulation et crusher sont extraits des sources publiques
sous `CREATURE_ROOT/tools/machines` au moment de la compilation.

Les bases originales sont les compositions epinglees v215 (Full, SHA
`c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6`) et v216
(Lite, SHA `0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e`).
Elles doivent etre disponibles avec leurs metadonnees dans
`CREATURE_ROOT/output/firmware/staging/`; l'OS officiel utilisateur est dans
`CREATURE_ROOT/firmware/model-cycles_OS1.13.syx`. Le socle de developpement
comprend aussi les fichiers de compilation et recettes references par le script.
`M68K_CROSS` et `MACRO_VENDOR` permettent de choisir la chaine ColdFire et
les sources Braids. Aucune image originale, dependance tierce ou binaire objet
n'est incluse dans ce dossier.

Pour les bases Machine Optional, compiler chaque edition avec :

```
python tools/machines/track_fx/build_firmware.py --edition full --runtime-headroom --unique-punch --macro-eco-only --destination <sortie>
```

Remplacer `full` par `lite` pour l'autre edition. Legacy, ChordKeys et Vinyl
restent disponibles. `--macro-eco-only` conserve le traitement Legacy original
et applique uniquement le comportement ECO selectif de MACRO utilise par Full.
L'integration native conserve les effets lourds reverb/delay partages et ajoute
les controles Global FX MST/TRK, la persistance par pattern et le stockage projet.

Pour Full principal, les options historiques sont `--remove-chordkeys --eco24
--runtime-headroom --remove-legacy --unique-punch --no-vinyl` ; les deux entrees
de dessin `fx_overlay` et `fx_overlay.part.0` sont remplacees avec leurs ABI
respectives. Les anciennes donnees Vinyl deviennent Reverb.

Apres composition, `tools/retitle_fixed_firmware.py` applique le numero de
release a l'ecran de demarrage, avec garde SHA du titre precedent et preuve
que seuls les octets du titre ont change. Ensuite `tools/gen_optional_selection.py`
ajoute le selecteur stable aux bases Optional, avec SHA Full/Lite explicites.
Avant publication, executer `tools/check_release_versions.py --base origin/main`
ainsi que les tests de livraison, de transport et d'emulation pertinents.

Les validations restent experimentales et ne constituent pas une mesure CPU,
une preuve de timing DDR/cache ou un test physique de toutes les combinaisons.

La version2.58 ajoute filter-startup.c : attente de six buffers de sons neufs, resolution par getter/frame UI, annulation au reemploi par initialiseur natif. Les filtres sauvegardes ne sont pas remis a zero au boot. fx-panic.c reporte All Sound Off au bloc audio suivant, avec invalidation logique des historiques ; le premier STOP conserve les queues. ACID conserve son Punch natif sans transitoire ajoute. Preuves : tools/emu/test_filter_startup.py et test_track_fx_panic.py.

Prototype prive2.59 : Track > ACID ajoute A/F/AF (A : ampli seul, F : filtre seul historique par defaut, AF : les deux). DATA active l edition puis parcourt A/F/AF ; BACK termine l edition. Gate reste natif en A/AF : OFF laisse DECAY attenuer la note, ON soutient jusqu au note-off. Preference globale par piste dans /AcidEnv.cfg (18octets valides/complements), ecriture UI au repos et apres delai d inactivite ; non embarquee dans les sons/projets/SysEx. Sans effet sur les pistes utilisant une autre machine. Le nouveau noyau compile depuis fundamentals/acid.c avec ACID_ENV_SELECT ; F est prouve sample-identique a2.58. UI, tables natives contigues, sauvegarde/rechargement et six couples mode/Gate verifies par test_acid_envelope_ui.py et test_acid_envelope_dsp.py. Aucun test materiel annonce.

Prototype2.60 : le selecteur ACID est deplace dans Global, apres FX. Une seule valeur ae_mode32bits pilote les six voix. /AcidEnv.cfg v2 contient8octets (AE,version2,compte1,mode,complement,A5,5A) ; les preferences v1 uniformes migrent vers cette valeur, les anciennes valeurs mixtes reviennent a F. Sauvegarde globale au repos ; Track garde SCRM/S.Chn/Human. Tests UI couvrent les11 lignes Global, les3 lignes Track, edition FX conservee et migration. Le test DSP verifie qu une seule ecriture commute les six pistes.
