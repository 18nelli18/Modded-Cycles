# 201 — Editions Full et Lite

AveyCole demande le27/10/2026 un choix Lite et la mise à jour Full vers v204 vérifié, puis les defaults de filtre et une réparation de latence DATA. Adresses : VA de l’OS1.13.

## Réponse courte

[FAIT] Principal2.56 livre Full208 et Lite211, explicitement approuvés. Full208 reprend204 avec LOW/ouvert127/résonance0 pour les sons neufs/effacés. Lite211 garde les six moteurs d’origine, toutes les fonctions communes et diffère les écritures de préférences pendant un geste. Les titres affichent2.56 ; protocole natif inchangé.

## Contrats natifs

`stock206_assets.py` détache les callbacks WAVE dont le code a été retiré, restaure les reprises stock et utilise le sous-objet natif connect à+20. La preuve via le vrai `0x400ddf60` reproduit le mauvais callback206 et compare207+ à Full204 sur les76descripteurs stock.

Les sons neufs utilisent le chemin `0x400141da`, les lecteurs de fichiers gardent leurs appels génériques. Clear publie cutoff/résonance sur la piste visée ; clear des sons du pattern applique les six. Le dernier mot libre du SoundCopy160 garde le type pour copie/Undo ; aucune taille d’allocation supplémentaire. Sequence-only et chargement disque ne remettent rien à zéro.

[FAIT en émulation] Les écritures Filter/LfoPol pouvaient synchroniser juste après DATA. `ui_idle210_assets.py` horodate l’entrée globale avant les menus ; les écritures Filter, polarité, nombre LFO, banques3/4 et Groove attendent une seconde sans entrée. Les réglages restent actifs et dirty en RAM puis sont sauvegardés. Aucun changement DSP prévu. La preuve reproduit les écritures209 pendant DATA et leur report211, avec sauvegarde après20détentes et repos.

## Vérification et livraison

[FAIT rapporté] AveyCole : « filter clears worked », puis sur Lite211 « Seems much more responsive now. and dx works. » Il autorise Full208/Lite211. Cela ne prouve pas toutes les fonctions sur matériel. Le rapport de pistes muettes provenait du filtre ; le rapport de clics a été retiré.

Pour chaque édition : SHA SysEx/MAIN, paquets, capacité flash, layout de décompression et bootstrap Samples natif exacts. Les deux transports Samples gardent les sections protégées et les32octets de clé ; conversions Python/JavaScript identiques. Les caches et fallbacks sont séparés par édition, fichiers immuables et commit épinglé. Le navigateur vérifie Lite sans Syntakt, bons downloads, course de chargement, blocage pendant envoi et français. Le texte fourni de la présentation Full reste byte-identique.

## Suite

[À FAIRE] Flasheur Machine Optional séparé. Ne pas confondre validation des524288sélections avec une preuve de démarrage matériel de chaque combinaison.
