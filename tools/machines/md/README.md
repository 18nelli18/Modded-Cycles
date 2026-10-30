# Machines Machinedrum pour Machine Optional

Source : [Talachan12/Elektron-Model-Machinedrum](https://github.com/Talachan12/Elektron-Model-Machinedrum),
revision `70e1483535c5a6919ff170ce3b79ba4a10c066ac`.
Les sources du noyau et leurs commentaires sont conserves tels quels.
Credit : Talachan12 pour le port TRX-B2, TRX-SD et TRX-CH, construit sur
Modded-Cycles de18nelli18. Les algorithmes reproduisent les moteurs Machinedrum.

Le29/10/2026, AveyCole confirme dans la conversation Codex :
« Great news: I got permission! » apres la question explicite sur la reutilisation
et redistribution du code dans le flasheur Optional. Cette confirmation est la
base d'autorisation de cette integration ; elle n'est pas presentee comme une
licence MIT generale de l'amont.

`base-map.json` epingle les adresses et gardes du socle Optional2.61.
`tools/gen_optional_machinedrum.py` compile le noyau et les metadonnees28machines.
Les tables et echantillons sont extraits du fichier1.63 de l'utilisateur au build.
La recette navigateur publique contient des zones nulles pour ces donnees.
Le sinus est recalcule avec l'algorithme amont, puis stocke en deltas16bits et
reconstruit exactement au boot. Aucun interpréteur DSP n'est embarque.

Le code/constantes MD occupe469c0000..469f8000 ; le BSS commence469f8000 et
se termine avant46a00000. POTS, GATED et WAVE conservent leurs zones.
Trois IDs stables :25=TRX-B2,26=TRX-SD,27=TRX-CH. IDs0..24 conserves.
Le selecteur utilise22bits et garde MIDI Out en derniere position.

Voir note203 pour les preuves et limites. Statut experimental ; aucune
confirmation de cette integration sur appareil n'est encore revendiquee.
