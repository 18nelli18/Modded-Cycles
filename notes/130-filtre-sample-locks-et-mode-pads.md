# 130 — Filtre Control All des sample locks et mode des pads

Demande AveyCole,18/10/2026 : Control All filtre aussi les pas sample-lockes de Sample Wizard ; ajouter un choix Silent/Stock dans un menu. Adresses : VA OS1.13.

## En bref

Test separe base sur principal1.96, sans modifier le principal ni909. Diagnostics CPU/CUT conserves. Deux variantes USB signees. Reglages live, non sauvegardes dans ce prototype : redemarrage revient a Silent et efface les overrides.

## Filtre

[FAIT] Le sample lock joue un son du pool, avec ses mots de filtre. Le test observe la vraie delegation encodeur400775f8, avant/apres TRACK(2)+MACHINES(5)+SWEEP/CONTOUR(6/7). Il capture uniquement les pistes Wizard dont le mot natif13/14 a change : les exclusions Control All ne sont pas contournees. Les autres champs, tokens, slots et slices ne sont jamais ecrits.

Deux lectures seulement, `sp_flt_go` et `sp_flt_fok`, sont remplacees par des getters bornes. Un override actif fournit la valeur capturee au ladder Wizard existant. Aucune passe audio supplementaire. L'autre parametre reste celui du sample lock tant que son propre override n'est pas actif. Les getter UI restent hors IRQ ; le callback audio ne lit que le cache et les mots du son de base deja references. Une modification du mot hors delegation UI invalide l'override. Ce test ne promet pas la persistance projet ni la combinaison des overrides avec les locks/LFO sur les memes cibles.

[FAIT] Le preset sans banque B compacte le sampler dans le payload du catalogue. Le composeur modifie la copie en SDRAM destinee au sampler, recalcule la taille compressee, replace la source du dernier payload et met a jour `br_boot_source`. VA des fonctions et references de charge utile preservees. Gardes d'octets exactes avant chaque remplacement.

## Pad Setup

SETTINGS+TRACK ouvre un modele prive d'une ligne dessine par `MenuView` natif400423e4. DATA selectionne l'edition, puis la rotation choisit Silent/Stock. BACK ferme. Le choix est global en RAM, Silent au demarrage.

Le branchement de PadsView4001d372 est remplace par un helper lisant le choix global. Il reprend les branches stock/inversees selon D7 et rejoue le test D3. Aucun octet executable n'est reecrit a chaud. Navigateur, selection et note-off memorise restent natifs. La release SETTINGS est deleguee a la chaine, avec `mod_used`, pour ne laisser ni CONFIG ni le fine tune MACRO bloques.

Le callback valeur du menu prend cinq arguments natifs ; les appels terminaux sont desactives lors de la compilation afin de ne pas reutiliser une pile de callback comme celle d'une primitive graphique a six arguments.

## Preuves et limites

`test_wizard_control.js` : preset complet, deux USB, demande Syntakt et upload natif, build signe et references. `test_wizard_control.py` : delegation encodeur, exclusions, cutoff/res independants, vrai bloc coefficients Wizard sur deux frames representant des sample locks, pile/registres preserves, menu et PadsView six pistes en Silent/Stock avec navigateur et release.

`render_wizard_pad_menu.py` : vrais MenuView, polices et Bitmap, images navigation/edition. `test_wizard_pad_modifiers.py` : vraie chaine de touches avec fine tune MACRO. Verification manuelle des samples, du son et des gestes physiques encore requise ; aucune validation materielle revendiquee.
