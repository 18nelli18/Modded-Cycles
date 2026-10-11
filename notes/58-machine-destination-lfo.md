# 58 — Machine comme destination du LFO

Demande de djd_oz, contribution du 12/10/2026 : proposer la sélection de machine comme destination du LFO,
avec le libellé court **MCHN**, et conserver la plage des firmwares avec machines ajoutées. L'auteur demande
l'intégration à Modded Cycles sous MIT. Tweak `61-mchn-lfo.json`, générateur `tools/gen_mchn_lfo.py`,
source `tools/machines/mchn_lfo/mchn_lfo.S`, preuve `tools/emu/test_mchn_lfo.py`.
Adresses : VA de l'OS 1.13.

## Réponse courte

[FAIT en émulation] L'OS possède déjà le paramètre Algorithm et son chemin de modulation. Il suffit de le rendre
éligible et de donner son libellé court au sélecteur. Les accesseurs partagés permettent de suivre les tables
reconstruites par les mods de machines, sans coder leur nombre. Le tweak vise l'OS officiel 1.13 et les combinaisons
construites par ce dépôt : il ne prétend pas reconnaître tous les firmwares modifiés de provenance extérieure.

## 1. Paramètre et accesseurs

| Adresse | Rôle [FAIT] |
|---|---|
| `0x4010dce0` | Descripteurs, pas de 56 o ; Algorithm : identifiant 41, groupe 7, case 9 |
| descripteur +12 | Maximum de machine, modifié par les générateurs de machines ajoutées |
| `0x4005a85e` | Accesseur d'éligibilité ; borne dans `d1`, argument à `4(sp)` |
| `0x4000b208` | Accesseur de libellé court ; borne dans `d1`, argument à `8(sp)` |
| `0x40129965` | Chaîne longue Algorithm, partagée par les copies des descripteurs |
| `0x4000c140` | Sélecteur de destination LFO, testé pour chaque machine installée |
| `0x4005aa54` | Numérotation des destinations enregistrées, inchangée |

Les générateurs Model-TG/Syntakt reconstruisent leurs tables depuis l'OS original. Une simple écriture dans le
descripteur original ne suffit donc pas pour toutes les combinaisons. Les bornes de leurs accesseurs restent intactes.

## 2. Écritures et espace libre

[FAIT] Cinq écritures :

- Redirection du masque 48×22 `0x40152d38` vers sa copie identique `0x4014b364`, référence à `0x400b9726`.
- 56 o de code original dans le masque libéré, sans variable ni état RAM.
- Saut absolu à `0x4005a860`, six octets : pour l'identifiant 41, renvoie `0x600` (LFO et vélocité).
  Pour les autres, rejoue le chargement et la comparaison, puis reprend à `0x4005a866`.
- Saut absolu à `0x4000b20a`, six octets : pour 41, renvoie l'adresse du libellé MCHN.
  Pour les autres, rejoue le chargement et la comparaison, puis reprend à `0x4000b210`.
- Remplacement des dix octets `Algorithm\0` par `MCHN\0` suivi de cinq zéros.

Les copies des tables gardent le pointeur de chaîne longue ; aucun pointeur de table, maximum, moteur audio,
format sauvegardé, bootloader ou updater n'est changé. [FAIT] L'éligibilité partagée ajoute aussi la destination
MCHN au sélecteur de vélocité. `tools/check_overlaps.py` et `tools/registry.py --check` contrôlent les conflits
et la libération du masque. Les hooks sont distincts de ceux des autres tweaks proposés.

## 3. Preuve sur le code de l'OS

La preuve applique les mêmes autres tweaks et charges utiles des deux côtés, puis ajoute seulement MCHN à droite.
Elle appelle les vraies fonctions de l'OS avec Unicorn, vérifie registres/pile et les accès mémoire.

| Contrôle | Sans MCHN | Avec MCHN [FAIT en émulation] |
|---|---|---|
| Éligibilité, identifiants 0–139 | Originale | Seul 41 devient `0x600` |
| Libellés courts | Originaux | Seul 41 devient MCHN |
| Sélecteur LFO pour chaque machine | Liste originale | Ajout unique de la case `0x900`, ordre des autres conservé |
| Maximum de machine | Table de la combinaison | Identique |
| Numérotation des destinations | Originale | Identique |
| Calcul LFO réel, six pistes, 100 blocs | Calcul original | Même sortie et état LFO ; case machine modulée |

Vérifié seul (six machines), avec Model-TG (sept), les cinq moteurs Syntakt (onze), Model-TG/Syntakt/MACRO/LFO 2–4 (treize), et avec `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,
level-pan-values,trigless-dim,lfo-plus` (douze machines). Le test accepte `--with` et `--syntakt` pour reproduire
les autres combinaisons. Le générateur vérifie le hash de l'OS officiel, les octets remplacés, l'unique référence
au masque et sa copie identique ; `--check` compare le JSON produit au fichier enregistré.

## 4. À vérifier sur le matériel

[À FAIRE] Test de cette intégration par Maxime : six machines, puis Model-TG et moteurs Syntakt, avec et sans
LFO 2/3/4. Choisir MCHN avec DEP à zéro, monter progressivement DEP, tester plusieurs formes/vitesses et les
machines aux deux extrémités. Vérifier les changements de son, la sauvegarde/recharge de destination, l'affichage,
la vélocité et la mise à jour USB. Aucun résultat matériel du mainteneur n'est encore revendiqué : expérimental.

L'auteur a confirmé sur son appareil une version antérieure à écritures de données, avec six et onze machines ;
ce résultat ne remplace pas le test des nouveaux accesseurs de cette PR.
