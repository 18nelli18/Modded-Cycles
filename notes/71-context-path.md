# Diagnostic Test3 : contexte toujours absent

Le retry n'a pas résolu le rapport matériel. B-side redevient accessible après un délai mais Save Project affiche encore MIDI: CONTEXT.

Le message de contexte distingue désormais : CTX: NO LOAD (aucune notification de chargement), CTX: NO UI (service UI jamais entré), CTX: UI IPL (service refusé sous masque IRQ), CTX: BUSY (I/O occupée), CTX: RAM (allocation refusée), CTX: STATE (autre état). Compteurs UI dédiés, aucune désactivation de la protection entre projets. Ce build est diagnostique et ne confirme pas la persistance.

Quick assign LFO2 en développement séparé : preuve isolée douze potards × six pistes réussie ; placement combiné non publié. Le générateur historique refuse aussi le conflit déjà existant lfo-plus/LFO2 au hook 0x401016e4. Aucun nouveau LFO2 dans ce build.
