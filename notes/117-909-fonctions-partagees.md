# 117 — Fonctions partagees actuelles dans Supermodel909

Demande AveyCole du17/10/2026 : « UPDATE 909 EDITION WITH FEATURE CROSSOVERS ». Reprendre les fonctions deja presentes et ameliorees dans main1.83, sans ajouter ses autres banques de machines. Adresses : VA OS1.13.

## En bref

909.3 reprend le filtre rapide confirme et la suppression du second passage apres Wizard ; sauvegarde rapide stock et sortie mute ; Oct0 de l'arpege MIDI ; premiere entree B pendant lecture et curseur REC unique. Le profil conserve six voix909, ACID, Sample Wizard, quatre WAV locaux et ses fonctions existantes. La preecoute Sample Preview est marquee testee comme au principal. Aucun diagnostic embarque.

Les reparations ont ete confirmees dans le principal. La nouvelle integration909 est verifiee en emulation, sans inventer de nouveau resultat materiel909. Le statut historique de son kit reste celui de la version909.2.

## Composition et gardes

`gen_909_crossover.py` conserve l'index909 de41fa13db et ajoute les adaptateurs apres le compositeur du profil fixe. Le compositeur909 valide toujours les sources ACID/Wizard, puis remplace ces recettes par les sources909. Appliquer les modifications avant cette substitution les perdrait ; modifier le resolver avant ses gardes rendrait les empreintes initiales fausses.

L'adaptateur situe donc les fonctions Wizard dans le payload fusionne avec la table `midi_current_copies` du stage de boot. Chaque entree donne source,destination,compte de mots ; le patch est applique a la source correspondante. Le code save50octets et l'ancien corps filtre678octets sont verifies avant remplacement. Le vieux BSR filtre est aussi garde byte-a-byte avant ses deuxNOP. References et source du loader repeat recalculees apres compression.

L'adaptateur du principal est ensuite repris a l'identique : garde curseur/phase612octets, affichage Oct20octets et wrapper save92octets dans le payload reserve. Aucun ChordKeys, SY, MACRO, TINY ou RETROSYN ajoute au profil909. Dans909.3, A-side arp absent du profil : seul l'arp MIDI deja installe recoit Oct0. Les machines et donnees echantillons909 ne sont pas regenerees.

## Documentation et validation

Guide, references EN/FR et version909.3 propres au profil fixe. Anciens encarts rouges du haut retires ; instructions MIDI arretes conservees. `gen_909_release.py` appelle le nouveau generateur pour eviter une regression au vieux snapshot.

`test_909_current.js` : vrais uploads de quatre WAV synthetiques, signature, remplacement qui change le firmware, retrait qui l'invalide, refus d'une image non officielle, profil sans Model-TG ni diagnostic. Le harness rejoue aussi le marqueur inline de publication que son chargeur de scripts externes ignorait auparavant.

`test_909_combos.py` : getters apres vrai boot/cache ; Genie, SCRAMBLE, B-side, slides et mute verrouille. `test_midi_cursor.py` : sept vitesses de chaque cote, fractions, longueurs5/7/12/16/31/64 et un curseur. `test_arp_zero.py` : menu B0..3 et notes sans transposition a0. `test_quick_save_exit.py` :512cas clavier. `test_909_crossover.py` : code filtre/save exact apres bootstrap, wrapper charge hors BSS. `test_909_current.py` : les six callbacks909 compares au C hote, passage Wizard unique et zones protegees intactes.

[A FAIRE sur appareil] Verifier le profil909 mis a jour dans les gestes ordinaires, entree B/REC et filtre. Les mesures de temps CPU et les I/O physiques ne sont pas deduites de l'emulateur.


## 909.4 : arpegiateur sur les deux cotes (17/10/2026)

AveyCole precise : « Oh, it needs arp on both sides I think », puis « fix that and then update again ». Ajout explicite de la carte arp au profil avant sa selection par le timer909 ; pas de modification de909-data.js ni des voix/samples. L adaptateur main1.83 applique alors aussi son changement de numerotation au menu A. FUNC+RETRIG propose Oct0..3 des deux cotes,0 ne transpose pas. Les labels et guides sont corriges pour indiquer A/B. Tests navigateur imposent presence de la recette arp. Menus/repetitions A et B executes dans le vrai firmware909, puis regressions voix, combos et cursor. Aucun diagnostic.


## 909.5 : rattrapage des pages et longueurs MIDI main1.89 (18/10/2026)

AveyCole demande « push crossover updates to 909 edition ». Les anciens correctifs filtre/save/curseur/Oct0 portent deja les memes donnees que main1.89. Les changements partages manquants sont ceux des pages MIDI et de la longueur commune. MACRO et les combinaisons de banques de machines ne concernent pas le profil fixe909 et ne sont pas ajoutes.

Le generateur copie les donnees et l adaptateur MIDI-pages approuves du principal, avec une seule adaptation : sa promesse attend `MC909CrossoverReady`, pour agir apres la fusion909/Wizard et les corrections precedentes. Les quatre LEDs PAGE suivent les modes REC natifs ; l entree B reprend la page A en mode normal ; la longueur commune est editable depuis B par FUNC+PAGE, clic DATA puis rotation, ou PAGE par16 meme hors edition. Mode par piste : longueurs MIDI independantes. Diagnostics absents ; code des six voix909 et chargement des quatre WAV inchanges.

[FAIT en emulation] Vrai build signe issu de quatre uploads WAV synthetiques, remplacement puis suppression WAV, refus d image modifiee. Bootstrap/cache, gardes filtre/save, gestes Genie/SCRAMBLE/B/slides/mute verifies. Preuve MIDI-pages sur la vraie composition909 :1848 etats LED, longueurs normales, six longueurs par piste, selection DATA, cycles PAGE, notifications natives, notes preservees et reprise de page. Les six callbacks audio restent exactement egaux au C hote sur trois variantes,24blocs chacune, avec un seul passage Wizard et regions protegees intactes. Le principal1.89 reste octet-identique. Les fixes source sont confirmes sur le principal ; aucune nouvelle validation materielle909 inventee.
