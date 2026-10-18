# 127 - Preecoute Sample Wizard dans909

Demande AveyCole18/10/2026 : servir d'abord le prototype machine MIDI, puis ajouter Sample Preview a l'edition909. Le prototype a ete servi et verifie HTTP200 avant ce port.

## Reponse courte

[FAIT en emulation] Activer le module Wizard Sample Preview existant dans le profil fixe909. Aucun changement des six voix909, des quatre WAV locaux ou du flasheur principal. Les octets du module sont identiques a ceux du principal ; verification materielle de cette combinaison encore attendue.

## 1. Composition

tools/web/model909/sample-preview.js ajoute sample-preview au profil, attend Current/Crossover/LFO, coche la carte si necessaire et ajoute le nom au recapitulatif. Le composeur Wizard existant ajoute wizard-sample-preview ; aucun nouveau detour assemble. Le module ajoute est marque experimental dans ce port, sans changer le statut des autres modules. tools/gen_909_sample_preview.py conserve la version909 existante a partir du commit f7298611cea3f48db0d6a02bf047412022fb96e2 et produit uniquement script, cache/version909.7, metadonnees et guides bilingues. Aucun diagnostic dans la release909.

## 2. Geste

FUNC + MACHINES : navigateur Sample Wizard. Choisir un sample, puis jouer le pad ou clavier pour l'ecouter avant chargement. Les quatre WAV du kit909 restent fournis localement par l'utilisateur ; aucun son ni firmware heberge.

## 3. Validation

- gen_909_sample_preview.py --check : generation reproductible.
- test_909_current.js sur docs/flasher-supermodel-909 : vrais fichiers WAV, signature du firmware, presence du module et octets identiques au catalogue preview du principal, invalidation/remplacement/retrait des WAV et refus OS non officiel. Les autres modules restent presents et les diagnostics absents.
- emu/test_909_sample_preview.py : vrai bootstrap909 sur le fichier signe, toutes les ecritures preview conservees apres initialisation, identiques au catalogue Wizard ; aucun Model-TG ni diagnostic.
- emu/test_909_crossover.py : filtre, suppression du second passage, quick save et wrapper hors BSS conserves apres boot.

[A FAIRE] Audition du navigateur et chargement depuis le stockage physique a confirmer sur appareil. Les pilotes physiques, fichiers et audio reel ne sont pas prouves par le seul bootstrap.
