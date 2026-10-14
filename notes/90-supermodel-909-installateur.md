# 90 — Supermodel 909 : quatre WAV locaux et installateur dédié

Édition séparée demandée par A.V. le 14 octobre 2026. La page principale reste inchangée.
Adresses : VA de l’OS 1.13.

## Réponse courte

La page `flasher-supermodel-909` construit localement depuis l’OS officiel Cycles 1.13 et quatre WAV :
hi-hat fermé, ouvert, crash, ride. Aucun firmware ou audio utilisateur n’est publié. Interface fixe crème/gris/orange,
sans sélection de mods. Transport classique et rapide repris du flasher fonctionnel.

## Profil fixe

Six emplacements stock remplacés par Model909 (DMDaudio, MIT), plus ACID, SCRAMBLE, banque MIDI parallèle,
MIDI Out/Thru, Sequence Genie, mute verrouillé, deuxième LFO, Control All Config avec piste active et démarrage
SUPERMODEL/by A.V./909 EDITION. Support Model-TG conservé ; aucun moteur Syntakt/MACRO ni ChordKeys.
La banque reste en RAM : aucune sauvegarde expérimentale ajoutée.

## Samples et espace réservé

`gen_model909_sample_template.py` compile un modèle sans audio. Les quatre descripteurs sont volatils afin
que le compilateur lise les tailles et pointeurs modifiés au build. Table `0x46703c4c`, pool `0x46740000`,
180000 octets réservés. Pool avant les chaînes et ACID ; charge rangée 207612 octets avant la banque MIDI.
Le navigateur convertit PCM/float WAV en mono 32 kHz par sinc fenêtré, normalise, coupe les silences,
applique un fondu final de 10 ms, puis encode IMA ADPCM (nibble bas d’abord, prédiction/index initiaux zéro).
Les quatre fichiers sont requis ; dépassement refusé sans troncature. Remplacer ou retirer un fichier invalide
la construction en cache. L’OS doit être celui reconnu par son SHA-256 officiel.

## Démarrage

`gen_boot_supermodel_909.py` ajoute la troisième ligne avec fonte originale. Variante 890 octets dans
le corps natif ; 80 images, 90 attentes, durée stock 1,8 s. Anciennes animations incompatibles.
Le comportement du générateur SUPERMODEL sans option demeure inchangé.

## Preuves

[FAIT en émulation] 11 variantes des six slots × 24 blocs : PCM natif identique au C hôte avec les
mêmes données WAV injectées ; étage TG une seule fois. Construction navigateur/Python identique,
image 2091499 octets. Test DOM : quatre uploads, OS officiel, firmware signé, aucun transfert automatique,
cache invalidé par fichier manquant/invalide. Démarrage : 80 images pixel exact, contrat minuterie/sémaphore
stock et écritures bornées. Copie/clear complet de la nouvelle charge vérifiés séparément.

[MATÉRIEL] A.V. a validé les voix de la construction privée précédente. La nouvelle combinaison
avec upload navigateur, Control All Config, affichage des LEDs et animation 909 reste expérimentale.

## Sources

Model909 : `DMDaudio/model909`, commit `12e359160132fe7df4560ee3e53bd50ab9eebd2b`, MIT,
licence servie avec la page. Les échantillons d’A.V. restent uniquement dans les sorties privées ignorées.
