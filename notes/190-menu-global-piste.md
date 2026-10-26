# 190 — Entree Mod Setup Global et Track

Demande AveyCole25/10/2026 : ouvrir Mod Setup sur deux sous-menus Global et Track. Generateur --mod-hierarchy, candidat157, base156. Adresses : VA OS1.13.

## Reponse courte

[FAIT en emulation] Racine Global/Track, DATA entre, BACK revient d un niveau ; BACK sort d abord de l edition. Reouverture a la racine. Pas de modification des valeurs ou des setters historiques.

## 1. Contenu et contrats

Global : Pad, USB, Num, Mute, Dly, DX, QntM, Grv. Grv : choix Groove et Strum global. Track : SCRM, S.Chn, Human. Human : Trk, Tim, Vel ; entree choisit la piste native courante, All reste disponible. Global garde les indices0,1,2,3,4,5,8,9 des handlers existants ; Track garde6,7,8. Le Humanize occupe son propre sous-menu et ne delegue jamais son DATA a QntM. Etat d arborescence uniquement UI dans la reservation156. Source control157.c distincte de156, meme fichier de preferences.

## 2. Preuves et limites

test_mod_hierarchy157.py : tous huititems globaux, sixsetters historiques, QntM/Groove et leurs BACK ; troisitems Track, Scramble/Sidechain/Humanize, amount piste courante, edit/BACK, fermeture/reouverture. test_groove_menu_pixels156.py157 : vrai MenuView natif, police, pile et pixels ; root Global/Track dessine par callbacks de police petite pour conserver les mots complets, noms Groove raccourcis pour eviter collision. Popup parametre et BACK ancien137 verifies. Le test FX synthetique forcait field6 Crackle avec mode0 Reverb : corrige en mode3 Vinyl, aucune modification firmware necessaire ; image VINYL-crackle-corrected.png. Tous objets/bins audio156/155 exacts, bank151 intact et sections horsMAIN exactes. --check standard/adulte exacts. Verification appareil attendue ; principal inchange.
