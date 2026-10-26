# 180 — Diagnostic des banques DX7 du navigateur

Demande AveyCole25/10/2026 : import depuis le lien du flasher, «bank sent» sans confirmation sur le Cycles ; une reussite apres passageCYC/SMP, non reproductible. Sources bank.c/library.c, ancien legacy-bank-ui.js ; preuve test_dx7_repeated148.py. Adresses : VA OS1.13.

## Reponse courte

[FAIT] Le navigateur n'ouvre aucune entree MIDI et ne recoit aucun accuse de sauvegarde. out.send ne prouve que la remise au pilote. [FAIT en emulation]32sauvegardes consecutives sur16emplacements reussissent avec fragmentation1/3/64/128/256/512/4096/4121octets, ancien protocole4121octets et fichiers modelises. Aucun echec materiel reproduit ici.

## 1. Conditions et limites

Le service differe toute validation/ecriture pendant lecture ; un message complet occupe la seule boite RX de son port jusqu'au prochain service UI. Les messages suivants sont alors ignores. La confirmation firmware dure2s alors que le navigateur verrouille Send pendant2,5s apres out.send. Cela peut cacher la confirmation, sans expliquer a lui seul les fichiers absents. N0x400d0a10 initialise/retourne le gestionnaire de projet ; ce n'est pas une simple sonde booleenne disque.

## 2. Suite

[HYP] Perte d'un gros message dans le transport, cadence UI ou confirmation trop breve. Le changementCYC/SMP n'est pas etabli comme cause ni correctif. Test150 separe : petits messages checksummes, cadence75ms, erreurs visibles et confirmation5s. Le principal conserve son importateur jusqu'au retour appareil. Aucun resultat d'emulation ne prouve le chemin USB/disque physique.
