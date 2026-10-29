# 202 — Delay POTS de model27

Demande AveyCole, conversation Codex du 29/10/2026 : ajouter le delay POTS de
durchgemacht aux choix de delay, dans toutes les editions. Adresses : VA OS1.13.

## Reponse courte

[FAIT] Le DSP MIT de model27 est repris sans modification, revision
`5badf6ad27d956e86d32ff331c480a84ef74db92`. Credit durchgemacht and Claude.
Source et licence : `tools/machines/pots/`. Integration dans
`tools/machines/track_fx/build_firmware.py` et `pots-slot.c`.
POTS ajoute un delay mono telephone, renvoye sur les deux canaux stereo.
Son moteur interne tourne a12kHz, comme la revision amont epinglee.

## 1. Interface et sauvegarde

[FAIT] Huit choix : Phaser, Duck, Dub, POTS, Ping Pong, Delay, Crush1, Crush2.
TRACK + TIME ouvre le choix ; relacher TRACK applique ; BACK annule.
TIME et FUNC + TIME restent les commandes natives Time/Feedback. Les gestes
d'envoi et les locks existants passent par le handler historique.
Le wrapper lui presente temporairement ID0 au lieu du nouvel ID12.
Les deux chemins de dessin du menu sont detournes. Optional conserve Vinyl,
Legacy et ChordKeys ; le principal conserve le retrait de Vinyl.

[FAIT] POTS est un effet lourd partage, y compris en mode FX TRK. Le format
MFT1 accepte ID12 aux octets37/39. Le premier choix POTS en MST initialise la
banque avant capture : le sidecar peut donc restaurer ce choix apres le codec
historique, qui ne connait pas ID12. Pas de modification des exports natifs.

## 2. DSP, memoire et transitions

[FAIT] Code/constantes dans46900000..46910000, etat dans46910000..46920000.
La ligne POTS est reservee a46980000..469c0000, apres GATED et avant WAVE.
Les assertions du composeur refusent leur chevauchement. Le DSP compte les
frames ecrites depuis reset : une ligne non initialisee n'est jamais lue.
Un reset logique constant suffit ; aucun effacement de262144octets dans l'IRQ.

[FAIT] Fondu de32blocs a la sortie et32blocs a l'entree. A l'entree POTS,
un bloc natif silencieux avec feedback nul prepare les buffers DMA du Delay.
Le DSP amont est ensuite appele directement. Le tempo nul est garde dans
l'adaptateur. Les sept anciens modes restent delegues au processeur existant.

[FAIT] All Sound Off appelle aussi pots_reset. Le premier STOP ne reset pas
la ligne ; le second la rend immediatement inaccessible au bloc suivant.

## 3. Preuves et limites

`tools/emu/test_pots_delay.py --build <dossier> --output <preuve.json>
--objdump <m68k-elf-objdump.exe>` charge l'image par son bootstrap natif.
Le test exerce le vrai code ColdFire : huit positions, release/BACK,
deux chemins de dessin, delegation Time/Feedback, sauvegarde MFT1 et reload
froid, choix TRK, DSP EMAC, ligne empoisonnee et canaris, reset double STOP,
et1050blocs de transitions avec le vrai Delay natif et ses buffers DMA.
Les E/S fichiers, objets de projet et peripheriques sont simules.
Le test historique PS1 reste applicable a ces images.

[A FAIRE] Confirmer sur appareil le timbre, la charge CPU sous polyphonie,
les transitions et la sauvegarde apres extinction. Une preuve d'instructions
emulees ne fournit pas un pourcentage CPU materiel. Ne pas reprendre les
resultats appareil de model27 comme preuve de cette integration Supermodel.
Publication experimentale2.61 autorisee par AveyCole : Full, Lite et Machine Optional.
Startup et les deux flasheurs affichent2.61. Preuves :
`docs/flasher/release261-validation.json`. Les65masques du selecteur Optional
exerces en natif donnent5265choix et1625dispatches ; huit variantes signees
sont generees, chacune dans deux transports Samples. Le navigateur reel
verifie les choix All/None/Legacy et le verrou pendant envoi.
