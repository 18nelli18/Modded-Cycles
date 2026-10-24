# 164 — ACID, detune SY BITS et niveau Elder, principal2.36

AveyCole demande les fondamentaux ACID et SY BITS puis un niveau Elder plus fort. Apres essais107/108/110 et correction du popup decimal : « 111 worked, push that to main ». Adresses : VA de l OS1.13.

## Image approuvee

Principal2.36 : octets exacts du111 regulier partage, SHA256 `fa66d0aa955ed68461ae5be5fbbd87c4a89fd3a53ff2cd693ccf48bd2589951a`. RETROSYN22 avant MIDI Out17,23machines156descripteurs, fonctions105 conservees. Vocabulaire adulte prive uniquement. Blurb fourni par l utilisateur identique au principal2.35.

## ACID

Le wrapper historique appliquait DECAY a la fois au MEG du filtre et a l ampli natif. Le nouveau wrapper tient le gate de volume jusqu au note-off et choisit une release courte fixe (table native4), independante de DECAY. Le filtre garde sa table de200ms..2s et les slides existants. Velocites97..127 donnent un accent progressif : jusque0,75octave d ouverture transitoire du filtre et environ3dB de gain avant saturation du modele. La velocite native de volume reste active ; ce n est pas une simulation exacte des circuits d accent historiques.

Sources ACID d origine MIT de Kevin-Shallvari/Modded-Cycles, commit5b6108ee57cdee4767f91bfb894ccefaadf4210d, modele Open303 par Robin Schmidt et filtre mystran/kunn credites dans les sources. Adaptations sous `tools/machines/fundamentals/`, licences conservees. Les autres moteurs ne sont pas remplaces.

## SY BITS

Le DSP accepte deja la fraction8.8 de COLOR ; l edition UI est corrigee sans nouveau format de son. COLOR ordinaire avance par demi-tons et conserve la fraction. FUNC + COLOR avance par centiemes, arrondis a la precision native1/256demi-ton (erreur maximale environ0,2cent). Bornes -24.00..+24.00. Les callbacks du record51 partage sont delegues aux autres machines.

Le popup stock conservait un grand entier et une legende decimale en cache. La correction111 ajoute une couche finale a la chaine de popup, lit la valeur de chaque frame et dessine le nombre signe a deux decimales dans la petite police native. La vtable du controle reste intacte. Les premieres tentatives de callback de widget ne touchaient pas le bon dessinateur. Le retour appareil111 confirme le resultat demande.

## Elder

Sortie du rendu Elder multipliee par2 (+6,0206dB), saturation signee avant repliement entier. Rendu/etat/onde/enveloppe du moteur Junior original inspires de Fors conserves. Le gain precede le gain commun natif de piste ; celui-ci peut donner1LSB d ecart d arrondi par rapport au double de la sortie finale ancienne.

## Integration et preuves

Code46840000..46848000, BSS46848000..46850000, cave inutilisee de la composition105. Delegation de l edition native MACRO preservee ; preparation UI avant draw existant ; remplacement des deux pointeurs ACID13 et du rendu Elder16 seulement. Popup final chaine au popup LEGACY ; bootloader/updater preserves par le generateur officiel et ses gardes d octets.

`tools/emu/test_fundamentals111.py` : vrai setter FUNC,100valeurs distinctes par demi-ton, bornes, labels signes, sauvegarde/rechargement son natif ; autres machines deleguees. Boucle audio native : sustain de volume identique DECAY0/127, MEG different, release courte independante de DECAY et Gate ; seuils d accent96/97/127 ; six voix Elder a2x, tolerance1LSB du gain commun, cretes bornees.

Popup natif rendu sur six valeurs successives, dont +1.68,-1.68,+24.00,-24.00 : nouvelle couche appelee a chaque frame, images distinctes et pile valide. Chromium reel : flasheur avec fichiers OS utilisateur, SHA exact111, importateurs WAV/DX7, guide EN/FR, mobile sans debordement, MIDI simule. PDF8pages rendu et controle. Aucun nouveau resultat de charge CPU appareil revendique. Le principal sert l image testee, sans recompilation de promotion.
