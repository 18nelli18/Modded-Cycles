# 120 — Pages MIDI : LEDs natives et longueur commune

Demande AveyCole, 17/10/2026 : cote B, la page selectionnee doit etre fixe et la page jouee clignotante, comme stock. Il precise ensuite que la longueur doit suivre A sauf en mode de longueur par piste ; confirmation explicite « Yes—follow A-side unless per-track length mode is enabled ». Test seulement avant validation materielle. Adresses : VA OS1.13.

## Reponse courte

Le callback prive B ecrivait les LEDs des16pas et6pads mais pas les4LEDs PAGE. Les vues A sous-jacentes dessinaient donc leurs pages. Le nouveau callback garde le rendu B existant, revendique ces4LEDs et utilise les fonctions natives : mapping0x400060ac, writer boolean0x40005fe6. La boucle native0x400222f2..0x40022346 fournit la reference : page jouee prioritaire, allumee si (dernierPas &3)>1 ; sinon page editee fixe, autres eteintes. Quand editee et jouee coincident, cette page clignote.

## 1. Horloge et rafraichissement

Le dernier pas B vient du compteur next-step de la voie selectionnee, avec retour a longueur-1 lorsque next=0. Transport arrete/pause, horloge invalide ou pattern edite distinct du pattern joue : seule la page editee reste fixe. Le poll prive est etendu par une cle page-editee/page-jouee/phase ; une lecture hors page affichee continue donc d'actualiser le clignotement meme si le curseur16pas rend -1. Identique cle = aucun redraw supplementaire. Aucun pulse A ni selection audio modifie.

[FAIT] Les fonctions natives du firmware rendent leurs pointeurs dans D0 ; le cast C doit les declarer comme u32, pas comme retour pointeur A0 de l'ABI GCC m68k. Le premier test du writer a identifie ce contrat avant publication.

## 2. Longueur

Pattern audio actif0x40a7887c : mode a +30667, longueur commune BE16 a +30662. Mode0 et longueur1..64 : les six headers longueur B sont aligns sur A avant l'horloge et dans le poll UI. Les configurations longueur B sont bornees a cette longueur commune, sans ecriture dans A. Mode1 : aucune substitution ; editions de longueurs MIDI independantes. Les vitesses et notes ne changent pas. Banque MIDI vide partagee exclue des ecritures. Les pas au-dela de la longueur restent stockes.

Le wrapper de ml_clock est court, sans heap/I/O/port physique. Il appelle le vrai ordonnanceur prive une fois apres synchronisation. Le wrapper de ml_config conserve les autres champs. Le mode commun utilise A comme source ; les longueurs B sont editables independamment en mode par piste.

## 3. Composition

`tools/gen_midi_page_leds_test.py --check` compile le helper relogeable puis copie le principal1.86 dans `docs/flasher-midi-page-leds-test`, avec diagnostics facultatifs. Le JS remplace seulement le pointeur du callback B, son appel de poll et les appels prives clock/config. Taille du chargeur brut et adresse physique sont recalculees apres recompression du MIDI ; sinon une modification du pointeur changerait sa taille aplib et casserait la chaine du repeat. References builder regenees ; principal et909 inchanges.

## 4. Preuves

Trois profils signes avant/apres : MIDI seul ; banque complete Wizard/MACRO/ChordKeys avec repeat et diagnostic ; banque complete sans Wizard ni repeat. Vrais bootstraps executes. Chaque profil compare924 etats joues au vrai fragment stock : six voies, longueurs5/16/17/31/32/48/64, pages disponibles, positions et phases de blink. Arret/pause, revendications big-endian, sortie B, polling hors page, absence d'allocation verifies.

Longueurs normales1/5/16/17/31/32/48/64 : vrai clockwrap B sur deux tours et edit/config. Mode par piste :6longueurs5/7/12/16/31/64 sur80ticks, intactes ; banque vide immuable et pattern A octet-identique. Le helper et son pointeur vtable survivent au constructeur cache disque. Validation materielle utilisateur attendue.
