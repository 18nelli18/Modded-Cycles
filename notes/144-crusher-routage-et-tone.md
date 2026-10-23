# 144 — Crusher cinq routes et nom Tone intact

Demande AveyCole, chat du22/10/2026 : Crush1 parallele, Crush2 direct entierement wet selon Send, Both1 direct propre/echos ecrases, Both2 direct et echos ecrases ; davantage de course entre modes. Signalement : bits4 et moins muets, Tone devenu « epth ». Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] v41/v41nf prives servis ; principal2.17 reste le v40 exact approuve. Aucun test materiel v41 revendique.

## 1. Causes

[FAIT] v40 tronquait vers zero en pleine echelle Q31. Une sinusoide de pic180000000 donne zero aux bits2,3,4 et trois niveaux au bit5 : rapport utilisateur reproduit exactement.

[FAIT] Tone partage le suffixe de la chaine « Reverb Tone », adresse0x40129960. Ecrire « Ch II Depth » a0x40129959 changeait aussi la carte Tone. En v41, les chaines natives restent immuables ; les popups se dessinent deja avec leurs propres labels Speed/Depth. Les libelles natifs des autres menus restent Reverb Size/Tone.

## 2. Conception privee

Sources `tools/machines/delay_crush_wet/` distinctes du v40. `--crusher-wet` reconstruit depuis le conteneur officiel et les recettes v17 epinglees. Quantification symetrique au plus proche, echelle stereo commune suivant le pic, decroissance1/64 par bloc ; zero reste zero. Les queues faibles peuvent etre plus granuleuses. Rate/Bits globaux lisses ; deux etats independants direct/echo.

Positions : Delay, Crush1, Crush2, Both1, Both2. Deux evenements encodeur signes par changement, chorus compris ; magnitude acceleree ignoree pour le choix du mode. CR02 sauvegarde les cinqpositions ; ancien CR01 Both migre vers Both1. E/S toujours hors audio et transport arrete.

[FAIT en emulation] Send maximal vaut (127/128)^2 du direct. Le retour FX natif applique le meme gain. Le nouveau hook0x40056b38 corrige le mix APRES les envois reverb et AVANT la conversion de sortie, puis rejoue les deux PEA natifs et reprend a0x40056b42. En Crush2/Both2 : ajouter Q(Send)-Send/Smax ; pas d'anti-dry injecte dans reverb. Correction Q20, produits32 seulement, saturation finale. Le Send0 reste propre ;127 retire le direct propre apres rampe. Le chemin USB6 pistes reste natif.

## 3. Preuves

- DSP :224blocs aleatoires PCM/etat exacts par variante, ABI/extremes/lissage ; Delay natif PCM/SRAM exact, feedback Both natif exact, silence et dixtransitions.
- UI : cinqmodes, bornes/configs invalides/migration/retry, delegation ;24vrais popups par variante, constructeurs/presentation/destruction ; chaines Tone natives intactes dans tous les modes chorus. Capture graphique inspectee.
- Mixeur natif :45cas par variante (cinqmodes, troisSend, troispans), retrait dry aSend127 et postmix des routes classiques exact ; erreur maximale3863 Q31 (arrondis Q20).
- Chorus :192blocs exacts/variante, reverb natif exact, correctif sifflement conserve.
- Integration : bootstrap natif et sections horsMAIN exacts ;24blocs sixvoix avec Wizard stereo et ChordKeys identiques au v40.
- HTTP/flasher : SHA/product17/checksums, EN/FR,390px, connexion disponible sans MIDI automatique, corruption refusee. Main et fichiers v40 conserves.
- Reproductibilite : v40partage exact8e11e8be…41e7cb ; v41/v41nf --check exacts.

Les couts emules ne sont pas des pourcentages CPU materiels ; Both2 ajoute un traitement du direct et coute davantage. AveyCole doit comparer A/P/O/N et casque/ligne.

## 4. Livraison

Partage :13fe5372d3f8c63bc97bd95f57259a8c64f6a6c3f9392d9c3f2c3939ab9af5f9.
Sanspartage :df9dea1391e93ab362bc13a0c86bcaf2865ea1a27b74d710e010570b02449d50.
Pages `crush-routing-filter.html?v=41` et `crush-routing.html?v=41` ; SysEx `crush-filter-v41.syx` et `crush-no-filter-v41.syx`.
