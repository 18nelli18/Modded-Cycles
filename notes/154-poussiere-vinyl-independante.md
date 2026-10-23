# 154 - Poussiere Vinyl independante

Demande AveyCole du23/10/2026 dans Codex : pops/clics de disque plus brillants, poussiere presente dans les pauses, puis publication. Adresses : VA OS1.13. Publication principale2.26, source privee v58 avec filtre partage.

## Reponse courte

[FAIT] L'ancien crackle etait multiplie par le niveau instantane du son. Le nouveau generateur est independant de ce signal, avec deux graines stereo, petits clics et pops amortis. Bande plus audible et gain corrige apres un preview trop faible (-80dBFS RMS). Le nouveau preview natif est environ30dB plus fort, sans normalisation de fichier. Warble et routage natif conserves.

## Conception et preuves

Sources locales : `tools/machines/fx_menu/dsp.c`, macro `FX_DUST` ; generation depuis OS officiel avec `--vinyl-dust`. Code module `0x46800000`, etat `0x46808000`; fin v58 `0x4680ca64`. Gain poussiere par cote = maximum des sends de pistes admissibles, pondere par volume et pan ; mute exclu. Pas six couches additionnees. Send0 et Crackle0 ne laissent pas de bruit. Fondu32trames exact, y compris niveaux1..31 vers0. Aucun E/S/allocation dans audio.

[FAIT en emulation] `test_vinyl_dust.py` :1024blocs PCM exacts contre reference, silence avec sends actifs, preview8s avec chaque quart de seconde actif, rampes send nul, spectre et bornes. Les bins au-dessus de4kHz portent66,6% de l'energie. `test_new_delays.py` du v60 verifie aussi les cibles Vinyl/Vinyl+Rev sur source muette, volume0 et mute. Les tests legacyDelay/Crush sont PCM exacts face au v57. `--fx-overlay --check` reproduit le v57 approuve exact ; `--vinyl-dust --check` reproduit le v58 ci-dessous. Les objets chorus/crusher/moteurs restent identiques.

## Retour utilisateur et publication

[FAIT, retour utilisateur] AveyCole : "Crackle sounds better" sur le test cumulatif v59. Ce retour concerne le grain ; ne pas inventer un test materiel exhaustif du fichier v58. La demande initiale autorise la publication du changement Vinyl. Les delays Ping Pong/Shimmer du test v59 sont signales sans effet clair et avec reprise visuelle Crush ; correction privee v60, hors principal2.26.

SysEx v58 : `c155ee9df5d4b8450f2faa876ccaa51ea5addc15b60e2fce415b92d0844a6752`.
MAIN : `1b3244ff6f4555a28f579d26ba91383e8980c87cd6a4ee918c64c030807c181d`.

Le fichier servi reste uniquement `docs/flasher/all-features-usb-2ch-default.syx`. Guides EN/FR et PDF mis a jour. Aucun autre dump ni conteneur ajoute. La publication est preparee depuis `edb2334` pour conserver la promotion2.25 effectuee par Claude.
