# 183 — File de reception des banques DX7

Retour AveyCole25/10/2026 sur150 : «incomplete bank, bank rx error». Generateur prive --bank-queue, bank.c/bank_chunks150.c/dx7_assets.py ; preuves test_bank_queue151.py et test_bank_chunks151.py. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] Ancien150 perd les messagesSML2 recus entre deux passages UI : une seule boite rx.ready, les autres octets sont ignores. Un burst34messages reproduit zero sauvegarde puis INCOMPLETE BANK.151 conserve ces34messages jusqu'au service UI et sauvegarde une seule fois. Le protocoleSML2 et l'importateur75ms sont conserves ; la file supprime cette dependance a un passage UI entre chaque message. [A FAIRE appareil] Confirmer la disparition des erreurs ; aucune affirmation que tout probleme USB physique est resolu.

## 1. Correction importante de182

L'allocation150 a0x46880000 n'etait PAS libre : wave_starter_assets.py charge les donnees factoryWAVE dans0x46860000..0x46881800. La garde locale DX7 code/art ignorait cette seconde occupation.150 pouvait donc ecrire dans les samples en RAM. Erreur de placement de l'agent,150 retire du test actif. Aucune ecriture de la ROM ni modification du bootloader ; les donnees factory sont rechargees au demarrage. Ne pas affirmer que150 respecte WAVE. L'archive garde ce resultat historique avec avertissement.

## 2. Disposition151 et file

Assembler la banque et conserver les messages dans la meme section NOLOAD dediee0x468a8000..0x468acd74 (19828octets), apres HALL0x468a6b2a, avant artPUNCH0x468ae000. Hors factoryWAVE, codeDX7 et BSS/overlay ; flags147/149 interdits dans ce test. La garde finale du generateur verifie cette fenetre ET tous ses octets initiaux zero apres composition des autres modules. Le payload existant initialise les octets au boot natif.

Deuxfiles DIN/USB independantes,40slots de139octetsmax,39utilisables, suffisants pour34messages d'une banque complete. Producteur IRQ : copie bornee, longueur puis publication d'indice avec barriere memoire. Consommateur UI : validation/reconstruction existante, libere chaque slot seulement apres lecture ; borne a l'indice d'ecriture observe a l'entree. Aucun fichier dans l'IRQ. Compteurs de pertes distincts producteur/consommateur ; overflow = abandon de la file et de la transaction, BANK RX FULL, puis nouveau BEGIN possible. Pas d'ecrasement silencieux. AncienSML1 garde son chemin et Yamaha conserve ses formats. MIDI/realtime inchanges.

## 3. Preuves livrees

Test natif150/151 avec memes34messages sans service intermediaire : echec150, succes151.151 :32banques sur16slots, fragments1/3/64/128/512/4486, wrapdesindices, reception pendant lecture sans acces fichier jusqu'au STOP, overflow de deuxbanques puis reprise, deuxports simultanes. FactoryWAVE137216octets strictement identiques apres tous ces transferts. Regressions de150 :32transferts,32voixvalidees, pas de fichier avant COMMIT, erreurs checksum/manque/ordre/transaction, duplicata/retry, erreur disque, anciensSML1 et MIDIordinaires/realtime, confirmation5s/compteurwrap. Popup/QntM/retentionMIDI24machines/sixpistes passes. Navigateur Edge file:// verifie avec MIDI simule uniquement. Standard/adulte reproductibles --check. Seuls objets bank.c et library.c changent ; FX et Fundamentals ne changent que les adresses des relaisDX7. Sections protegees horsMAIN exactes. Aucun nouveau gain CPU annonce, principal2.47 inchange.

## 4. Essai appareil

Flasher151, ouvrir importer/index.html fourni dans Chrome/Edge, arreter lecture et envoyer la meme banque vers deuxslots puis repeter. Attendre LEGACY BANK SAVED ; noter toute erreur BANK RX FULL, BANK RX ERROR, INCOMPLETE BANK ou BANK SAVE ERROR. Le navigateur ne confirme pas la sauvegarde appareil.151 n'inclut pas149.146 reste disponible.

## 5. Retour CPU appareil25/10/2026

AveyCole rapporte «151 is getting113p», confirme «Repeatedly during playback». [FAIT appareil rapporte] P113 repete, pas seulement premier releve. Ne pas traiter comme optimisation validee ni ignorer ce retour. Derniere base avec meme pattern/reglages encore demandee ; succes de banque pas confirme par ce retour.

[FAIT en emulation] Comparaison151/148 : PCM et comptes instructions strictement identiques dans deux bancs12blocs Speech/troisPUNCH/KICK/ACID ouMACRO24, HALL/PingPong/Sidechain. SansMACRO493852instructions total, pire61310 ; avecMACRO24616665total, pire61281, identiques avant/apres. dx7_service retourne pendant lecture en9instructions dans les deuxbuilds. Modules PUNCH/Speech/Sidechain/HALL/filtreMACRO/gouverneur exacts146/148/151. Cela ne prouve PAS une egalite de cycles physiques : emulation sans caches/bus/interruptions USB reels. Cause du P113 encore inconnue ; aucun nouveaubuild ou changement du calculP pour masquer le resultat. Principal inchange.

## 6. Correction de comparaison appareil25/10/2026

AveyCole precise que147 etait sensiblement plus bas, mais qu'il avait remplace MACRO par LEGACY : le113 ne constitue donc PAS une regression comparee a pattern identique. Nouvel essai151 : «speak macro punch punch kick acid getting101p», soit SPEAK/MACRO/deuxPUNCH/KICK/ACID. Conserver ce101 separe des charges LEGACY. Demande suivante explicite : optimiser LEGACY autant que possible ; conserver les samples et les controles, preuve avant livraison. Le diagnostic precedent ne prouve ni innocuite physique generale ni regression113 de151.

## 7. Transfert confirme appareil25/10/2026

AveyCole : «the bank send worked with the importer on151 too. bank recieving then legacy bank saved». [FAIT appareil rapporte] Reception puis sauvegarde banque confirmee avec le couple151/importateur. Ne pas remplacer ce resultat par une simple emulation. Aucun retour ne demande encore la promotion de151 au principal. Optimisation LEGACY demandee ensuite.
