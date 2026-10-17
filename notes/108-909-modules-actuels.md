# 108 — Supermodel 909 avec les modules actuels du principal

Demande AveyCole, 16/10/2026 : actualiser seulement les mods communs a 909 et main, ajouter Control All Beat Repeat et remplacer Model-TG par Sample Wizard comme dans main. Ajouter aussi un lien 909 bien visible au flasheur principal. Nouvelle combinaison en test separe ; edition 909 publiee conservee jusqu au retour machine.

## Profil

Six slots 909 (BD, SD, hats CH/OH, rim/clap, trois toms, cymbales crash/ride), Sample Wizard, ACID actuel, SCRAMBLE, Sequence Genie, Second LFO, mute verrouille, MIDI Out/Thru, Control All Config, Banque MIDI actuelle et beat repeat actuel avec popup. Animation 909 conservee. Aucun moteur Syntakt/MACRO/TINY/RETROSYN ajoute. Aucun fichier Syntakt necessaire. Les quatre WAV locaux restent requis ; aucun audio ni firmware distribue.

Le profil appelle les composeurs main actuels : sauvegarde MIDI MPI1, chargement en entrant B lecture arretee, LEDs FUNC B sans surlignage, Genie Queue Loop/Page sur A/B, repeat TRACK + RETRIG avec masque Control All et seize divisions. Leur nouvelle combinaison reste experimentale ; le retour hardware de main ne valide pas ce nouveau layout.

## Assemblage et place

`export_909_current_scaffold.js` choisit les supports main exacts et exporte les references, ainsi que Wizard seul. Le catalogue partiel ACID/Wizard mettait les hooks du moteur dans les writes de Wizard et laissait le moteur sans writes. `gen_909_current.py` separe les deltas a partir de Wizard seul pour fournir au composeur MIDI son vrai detour moteur. Meme contexte principal, pas de recette Model-TG. Les SHA des deux recettes originales sont controles avant transformation navigateur.

Compilation des voix depuis `tools/machines/model909_full/` (DMDaudio/model909 MIT, source deja presente et creditee), meme algorithme et commandes, GCC ColdFire 15.2. Code 909 en `0x46709000`, etats de six voix en `0x46743000` (hors tables CHORD/Wizard), pool ADPCM `0x46748000`, capacite 180000 octets, noms en `0x46774000`. ACID principal en `0x46776000` conserve. Descripteurs extraits de l OS utilisateur au build ; seules leurs valeurs/chaines sont relogees. Les tables natives et relogees update/render des six slots pointent vers 909. Les slots 6 Wizard et 7 ACID restent inchanges.

Les parties propres ajoutees sont controlees contre les parties existantes ; la plage de tables Wizard/CHORD `0x46737000..0x46742000` est surveillee pendant les tests DSP pour prouver qu elle n est pas modifiee par les voix 909. Le composeur principal compresse et prepare le bootstrap/cache. Aucun nouveau format audio 909, aucune modification du bootloader ou de l updater.

## Page et preuves

`gen_909_current_page.py` copie main vers `flasher-supermodel-909-current-test`, impose le profil fixe, ajoute les quatre uploads et des informations EN/FR. Le code et les references main sont embarques ; seuls les samples de l utilisateur remplissent le pool dans son navigateur. Retrait/fichier invalide invalide le firmware ; remplacement valide doit changer son hash. Aucun transfert MIDI automatique. Le lien prominent du principal pointe vers l edition 909 publiee.

`test_909_current.js` : vrais FileReader/WAV, construction sans Syntakt, signature, refs, presence Wizard et absence Model-TG, persistance, nouveau statut experimental, changement de WAV, limite du pool et invalidation. Build Python/navigateur compare sur le catalogue prepare.

`test_909_current.py` : vrai boot/cache navigateur, ensuite callbacks notes/render 909 charges, six slots simultanes, trois jeux de types, 24 blocs chacun avec retriggers. Comparaison sample exacte au C hote ; capture avant ah_noenv et un seul passage par l etage Wizard ; signal audible apres cet etage et tables Wizard preservees. Les notes sont fournies explicitement aux callbacks. Le banc reduit de boucle sequenceur ne transmettait pas les trigs aux voix sous ce profil ; il n est PAS utilise comme preuve sonore ni preuve de sequenceur complet. Les instructions EMAC du nouveau corps sont explicitement emulees, hors des plages historiques Syntakt du banc.

Regressions sur le vrai firmware construit : `test_midi_current.py --scheduler`, LEDs 64 masques x six selections, `test_genie_timing_current.py`, `test_midi_persistence.py` (slots vides/existants, redemarrage simule, lecture/IPL sans E/S) et `test_beat_repeat.py --case ...` (boot/cache, divisions/masques/fondus/ABI). Peripheriques, filesystem et cache physique simules : aucun resultat hardware invente.

## A verifier sur machine

Partir d un projet de test neuf lors du changement de sampler. Six machines et tous les types, quatre WAV, ACID, Wizard et ses modes de lecture ; Sequence Genie A/B Loop/Page, sauvegarde MIDI puis B lecture arretee, LEDs FUNC, Control All Config, beat repeat et release, Second LFO, SCRAMBLE, mute verrouille, Out/Thru, animation. Ne pas promouvoir la combinaison avant retour AveyCole. Le main recoit uniquement le lien visuel et l hebergement du dossier test.

Le meme banc de boucle reduite a ete compare a l edition 909 publiee, avec les memes samples synthetiques : ancienne et nouvelle images recoivent toutes deux six trigs nuls et rendent zero dans cette fixture. Cette limite est donc aussi presente pour le firmware ancien confirme sur machine. La preuve sonore retenue reste celle des callbacks notes explicites, et non la boucle reduite.
