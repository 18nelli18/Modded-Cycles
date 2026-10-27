# Performance Mode / Mode Performance - source preview

**EN:** Experimental standalone source contribution. This feature is not registered in the web flasher and is not a selectable combination of existing mods. Build only from your own official Model:Cycles OS 1.13 file. Maintainer hardware validation and combination testing remain pending.

**FR :** Contribution source autonome experimentale. Cette fonction n'est pas inscrite dans le flasheur web et ne constitue pas une combinaison selectionnable avec les autres mods. Partez uniquement de votre propre OS Model:Cycles 1.13 officiel. La validation materielle du mainteneur et les essais de combinaisons restent a faire.

## Controls / Commandes

| Action | English | Francais |
| --- | --- | --- |
| FUNC + GATE | Open PERF. | Ouvrir PERF. |
| LEVEL/DATA turn / rotation | Select M1-M15; it does not adjust the amount. | Selectionner M1-M15, sans modifier le montant. |
| LEVEL/DATA click / clic | Open the selected macro's SET screen. | Ouvrir SET pour la macro selectionnee. |
| BACK | SET to PERF, then exit; amounts remain active. | De SET a PERF, puis sortie ; les montants restent actifs. |
| MAIN VOLUME short press / appui bref | Reset the selected macro amount to zero. | Remettre uniquement le montant selectionne a zero. |
| FUNC + RECORD | Copy the whole selected macro. | Copier toute la macro selectionnee. |
| FUNC + PLAY | Clear the whole selected macro. | Effacer toute la macro selectionnee. |
| FUNC + STOP | Paste into the selected macro. | Coller dans la macro selectionnee. |
| FUNC + SETTINGS | Native TEMP SAVE, including macro definitions and amounts. | Sauvegarde TEMP native, definitions et montants compris. |
| FUNC + PATTERN | Native TEMP RELOAD, including macro definitions and amounts. | Rechargement TEMP natif, definitions et montants compris. |
| FUNC + PUNCH | Native Quantize menu. | Menu Quantize natif. |
| SETTINGS > CONFIG > CLICK | Native Click menu. | Menu Click natif. |

**EN:** Holding MAIN VOLUME retains native power behavior. Plain RECORD/PLAY/STOP retain transport control. Hidden native menus and dialogs keep their own input handling. Guarded recording/UI states do not allow macro clipboard edits.

**FR :** Le maintien de MAIN VOLUME conserve sa fonction d'alimentation native. RECORD/PLAY/STOP seuls conservent le transport. Les menus et boites de dialogue natifs gardent leurs commandes. Les etats d'enregistrement/interface proteges interdisent les modifications du presse-papiers des macros.

## Fifteen controls / Quinze commandes

| Row / Rangee | 1 | 2 | 3 | 4 | 5 |
| --- | --- | --- | --- | --- | --- |
| 1 | M1 PITCH | M2 DECAY | M3 COLOR | M4 SHAPE | M5 MAIN VOLUME |
| 2 | M6 SWEEP | M7 CONTOUR | M8 DELAY SEND | M9 REVERB SEND | M10 REVERB SIZE |
| 3 | M11 LFO SPEED | M12 VOL + DIST | M13 SWING | M14 CHANCE | M15 DELAY TIME |

**EN:** In PERF these knobs change amounts from 0 to 127. They are controllers, not fixed macro destinations. The original knob functions return after leaving PERF, while the macro offsets remain active.

**FR :** Dans PERF, ces potentiometres reglent les montants de 0 a 127. Ce sont des commandes, pas des destinations imposees. Leurs fonctions natives reviennent a la sortie de PERF ; les offsets des macros restent actifs.

## Four destinations / Quatre destinations

| SET control / Commande SET | English | Francais |
| --- | --- | --- |
| PITCH | Select row 1-4. | Selectionner la ligne 1-4. |
| DECAY | Choose T1-T6 or FX. | Choisir T1-T6 ou FX. |
| COLOR | Choose the destination parameter. | Choisir le parametre destination. |
| SHAPE | Set signed depth, -127 to +127; zero disables the row. | Regler la profondeur de -127 a +127 ; zero desactive la ligne. |
| MAIN VOLUME turn / rotation | Adjust the selected macro amount; top-right slider. | Regler le montant de la macro selectionnee ; curseur en haut a droite. |

**EN:** Track destinations are Pitch, Decay, Color, Shape, Sweep, Contour, Delay Send, Reverb Send, Volume + Distortion, Pan, LFO Speed, LFO Depth, LFO Multiplier and Track Level. FX offers Reverb Size, Reverb Tone, Delay Time and Delay Feedback. Only stock-machine bindings and one LFO are implemented. Amount 0 adds no offset; amount 127 applies full configured depth. Native parameter limits and stepped destinations still apply. A new macro starts at amount 0 with four T1 Pitch rows at depth 0.

**FR :** Les destinations de piste sont Pitch, Decay, Color, Shape, Sweep, Contour, Delay Send, Reverb Send, Volume + Distortion, Pan, LFO Speed, LFO Depth, LFO Multiplier et Track Level. FX propose Reverb Size, Reverb Tone, Delay Time et Delay Feedback. Seuls les branchements des machines d'origine et un LFO sont implementes. Le montant 0 n'ajoute aucun offset ; 127 applique la profondeur configuree complete. Les bornes natives et les parametres par paliers restent respectes. Une nouvelle macro part au montant 0 avec quatre lignes T1 Pitch de profondeur 0.

## Copy, clear and paste / Copier, effacer et coller

**EN:** Select M1, FUNC + RECORD, select M2, FUNC + STOP: all four destination rows, their signed depths and the current amount replace M2. SET's highlighted row does not restrict the scope: operations always affect the whole macro. Pasting a nonzero amount can change the sound immediately. Clear resets amount and all four rows but keeps the clipboard. Copy is a snapshot; changing the source later does not alter it. Copy/paste works across PERF and SET and across patterns within one project. Explicit track targets stay explicit: T3 remains T3. Changing project or restarting empties this dedicated clipboard. Empty paste leaves the destination unchanged. The footer shows COPIED, CLEARED, PASTED or EMPTY briefly. The native pattern/sound clipboard is separate.

**FR :** Selectionnez M1, FUNC + RECORD, selectionnez M2, FUNC + STOP : les quatre destinations, leurs profondeurs signees et le montant courant remplacent M2. La ligne surlignee dans SET ne limite pas l'action : toute la macro est concernee. Coller un montant non nul peut changer le son immediatement. Effacer remet le montant et les quatre lignes a zero mais garde le presse-papiers. La copie est un instantane ; modifier ensuite la source ne le change pas. On peut copier/coller entre PERF et SET et entre les motifs d'un meme projet. Les pistes restent explicites : T3 reste T3. Un changement de projet ou un redemarrage vide ce presse-papiers dedie. Un collage vide laisse la destination intacte. Le pied d'ecran affiche brievement COPIED, CLEARED, PASTED ou EMPTY. Le presse-papiers natif des motifs/sons est distinct.

## Pattern and project recall / Rappel des motifs et projets

**EN:** A1 M1 = 127 and A2 M1 = 32 remain independent. Returning to A1 restores 127 and its assignments/depths. While playing, recall happens when the next pattern actually starts. TEMP SAVE at amount 50, edit to 0, TEMP RELOAD restores 50 together with the native pattern parameters. Save the project normally for work across restart. Older definition-only records load with neutral amounts; set and save those amounts again. Firmware predating amount-saving cannot read the newer macro records.

**FR :** A1 M1 = 127 et A2 M1 = 32 restent independants. Le retour a A1 restaure 127 et ses destinations/profondeurs. En lecture, le rappel a lieu au demarrage effectif du motif suivant. TEMP SAVE au montant 50, modification a 0, puis TEMP RELOAD restaure 50 avec les parametres natifs du motif. Sauvegardez normalement le projet pour le retrouver apres redemarrage. Les anciens enregistrements sans montant sont charges avec des montants neutres ; reglez-les et sauvegardez-les de nouveau. Les firmwares anterieurs a la sauvegarde des montants ne lisent pas les nouveaux enregistrements de macros.

## Selective TEMP reload / Rappel TEMP selectif

**EN:** In Config, open **MACROS** and click LEVEL/DATA on **RLD: OFF / RLD: ON** to toggle. Choose the value, then use **Save Project**. Each project recalls its own saved choice on load or restart; new and older projects without this setting default OFF. OFF restores all fifteen saved macro amounts with FUNC + PATTERN. ON keeps the current M5, M10 and M15 amounts while restoring the other twelve amounts and all saved destinations/depths. The saved TEMP snapshot is unchanged, so switching OFF and reloading again restores all original saved amounts. Pattern switching leaves RLD unchanged; loading another project recalls its saved choice.

**FR :** Dans Config, ouvrez **MACROS** puis cliquez LEVEL/DATA sur **RLD: OFF / RLD: ON** pour basculer. Choisissez la valeur puis utilisez **Save Project**. Chaque projet rappelle son propre choix sauvegarde au chargement ou apres redemarrage ; les projets nouveaux ou anciens sans ce reglage commencent OFF. OFF rappelle les quinze montants sauvegardes avec FUNC + PATTERN. ON conserve les montants actuels de M5, M10 et M15 tout en restaurant les douze autres montants et toutes les destinations/profondeurs sauvegardees. Le contenu TEMP reste intact : revenir sur OFF puis recharger restaure tous les montants d'origine. Le changement de motif laisse RLD inchange ; charger un autre projet rappelle son choix sauvegarde.

**EN:** During playback, changing amounts or destinations, resetting MAIN, clearing and pasting macros now update the saved macro data without restarting the audio kit state. Native save mirrors stay synchronized. BACK from MACROS returns to Config.

**FR :** En lecture, les modifications de montants/destinations, la remise a zero MAIN et l'effacement/collage mettent maintenant les donnees de macros a jour sans reinitialiser l'etat du kit audio. Les miroirs natifs de sauvegarde restent synchronises. BACK depuis MACROS revient a Config.

## Preview release notes / Notes de cette preversion

**EN - 2026-10-28:** Reduced active-macro audio processing overhead. Controls, destination values and saves stay the same. This standalone preview adds Performance Mode to the six stock machines, their stock LFO and global FX; it does not add other machines or LFOs. Maintainer testing of this stock-only build remains pending.

**FR - 28/10/2026 :** Reduction du travail audio des macros actives. Les commandes, valeurs des destinations et sauvegardes restent identiques. Cette preversion autonome ajoute le mode Performance aux six machines d'origine, a leur LFO d'origine et aux FX globaux ; elle n'ajoute ni machine ni LFO. Les essais du mainteneur de cette compilation autonome restent a faire.

**EN - 2026-10-22:** RLD is now saved separately in each project. Set the toggle and Save Project to retain it through loading and restart. Existing macro records and native project fields are unchanged; older/new projects default OFF.

**FR - 22/10/2026 :** RLD est maintenant sauvegarde separement dans chaque projet. Reglez le choix puis Save Project pour le conserver au chargement et apres redemarrage. Les records de macros et champs natifs du projet restent inchanges ; projets anciens/nouveaux par defaut OFF.

**EN - 2026-10-21:** Added the Config selective-reload toggle with compact labels and a fix for kit-state resets when editing macros during playback. Updated source, native proofs and build reference. This remains a standalone experimental source preview, pending maintainer hardware and combination checks.

**FR - 21/10/2026 :** Ajout du rappel TEMP selectif dans Config avec libelles compacts et correction de la reinitialisation du kit lors de l'edition de macros en lecture. Sources, preuves natives et reference de compilation mises a jour. Cette preversion source reste autonome et experimentale ; essais materiels du mainteneur et combinaisons a verifier.

**EN - 2026-10-18:** Source preview of fifteen per-pattern performance macros, four track/FX destinations each, persistent amounts and whole-macro copy/clear/paste. Standalone source build only, MIT. No web-flasher card, firmware image, screenshot or extracted OS section is included. See [technical note 58](../../notes/58-mode-performance.md) for validation and integration limits.

**FR - 18/10/2026 :** Preversion source de quinze macros de performance par motif, quatre destinations piste/FX chacune, montants sauvegardes et copier/effacer/coller de macros entieres. Compilation source autonome uniquement, MIT. Ni carte dans le flasheur web, ni image firmware, ni capture d'ecran, ni section extraite de l'OS n'est fournie. Voir la [note technique 58](../../notes/58-mode-performance.md) pour la validation et les limites d'integration.
