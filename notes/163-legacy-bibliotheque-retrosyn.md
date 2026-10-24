# 163 — Bibliotheque LEGACY et RETROSYN, principal2.35

Demande AveyCole du24 octobre2026 : « 105 worked », puis publication du105retro avec importateurs WAV et DX7 cote a cote. Le blurb ecrit par l utilisateur reste identique, SHA256 du bloc HTML `970eb2992fd46f428b4281e96bd28cca1b0acd12c9b926b1f95986171390ea05`.

## Image approuvee

Le flasheur sert les octets exacts du candidat partage regulier105retro, SHA256 `ef01ba93a63f7dda8d161d6aa7f19a60114f7b190e3d6687a5b15df42f149bc8`. Aucune modification audio a la promotion, aucun vocabulaire adulte, aucun changement ACID/SY BITS106. RETROSYN ajoute l ID22 avant MIDI Out17 ;23machines,156descripteurs. Elder et les autres IDs restent stables. Section3 uniquement ; chargeur et updater conserves par le generateur.

## Bibliotheque et gel d import

[FAIT]16emplacements `/Legacy01.cfg`..`Legacy16.cfg` avec noms `.nam`, sauvegarde5000octets verifiee, banque active conservee jusqu au chargement DATA. Factory restaure la banque compilee. FUNC + MACHINES utilise la vraie touche5 et un getter machine8bits, sans supposer les bits hauts nuls. Banque globale aux pistes LEGACY, hors sauvegardes projet Elektron.

[FAIT] Message proprietaire4121octets `F0 7D 53 4D 4C 01 slot nom16 payload4096 checksum F7`. La signature complete reserve le message au module ; le parseur Elektron ne le recoit plus. Les autres SysEx et MIDI sont retransmis. Etats distincts USB/DIN, prefixe differe de6octets maximum, realtime immediate. Tampon USB borne, publication et disque uniquement a l arret.

[FAIT] Les popups natifs de notification ont ete retires du chemin banque. Le message est dessine dans la couche finale sans allocation/presentation de fenetre ; garde anti-reentree du service. La preparation precede le draw natif et ne rappelle plus ce service depuis une vue verrouillee.

## Autres changements cumulatifs

Optimisations LEGACY conservees : caches frequence/commandes, chemins neutres, multiplication Q16 equivalente. Compensation de carriers faibles choisie au trig, fixe pendant la note, maximum64x ; ni AGC ni changement des octets du patch. Les32voix incluses gardent le gain initial ; les banques utilisateur faibles peuvent etre relevees. Les voix volontairement silencieuses ne sont pas inventees.

HALL : retour wet releve et feedback maximal allonge ; retenue du reste fractionnaire du filtre pour reduire les biais. SPEAK regulier : harmonies voix legerement plus claires, consonnes et accord conserves ; CAREFUL123, CREATURE124 adjacents. Menu FX opaque dessine en fin de pile du ViewManager, conserve la vue derriere. Relachement physique TRACK ferme la selection Control All concerne seulement sa vue native.

## Validation

Emulation native105retro : USB fragmente1/5/6/64/4096octets et message complet4121, sauvegarde sans popup natif ; DIN proprietaire non retransmis ; Yamaha, notes et realtime conserves. Vraie touche MACHINES ouvre la bibliotheque avec bits hauts du getter sales.32voix LEGACY comparees104/105 : PCM identique avec leur gain nul, gain fixe borne et saturation explicite.

`tools/test_v105_delivery.js` : Chromium reel, MIDI simule, fichier firmware valide puis vrai chemin flasheur avec OS proprietaire fourni localement, SHA exact, conservation du blurb, paquet DX7/checksum, rejet invalide, exclusion transferts concurrents, colonnes egales avec separateur, mobile sans debordement, guide EN/FR. Aucune emission MIDI reelle par ce test. PDF8pages rendu pour controle visuel. Retour hardware utilisateur positif pour105, pas une revendication de mesure CPU ou de test exhaustif de chaque banque.

La page `docs/flasher/convert.html` conserve le convertisseur WAV et ajoute a droite l importateur. Les deux transferts partagent un verrou cote page ; la confirmation de sauvegarde est lue sur l appareil. Un envoi ne pretend pas etre un accuse de reception.

Verification des recouvrements :171tweaks,17603ecritures,139ensembles valides. Syntaxe Python et guide canonique verifies. Le check du catalogue historique `gen_flasher_tweaks.py --check` signale un catalogue/licence deja desynchronise : generateur, fichiers tweak, licences et `tweaks.js` restent identiques au HEAD initial625dac2. Cette promotion utilise le chemin image fixe verifie, pas une regeneration de ce catalogue.
