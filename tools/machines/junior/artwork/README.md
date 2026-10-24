# Elder — icone originale 34 x 34

Vieil homme chauve a lunettes et barbe, tenant une console portable avec
ecran, croix directionnelle et boutons. Dessin original dans `../elder_icon.py`.

- `elder-gameboy_34x34.png` : PNG1bit, blanc = pixel actif, noir = fond.
  Ouvrir ce fichier dans <https://durchgemacht.github.io/1-Bit-Editor/>.
- `elder-gameboy_34x34.bin` :272octets, colonnes natives, Y inverse,
  deux mots32bits par colonne, format du meme editeur.
- `elder-gameboy.json` : grille source du dessin (pas un document de l’editeur).

L’export binaire est compare aux fonctions toBin/fromBin de l’editeur
de durchgemacht/DavidCaruso ; aller-retour34x34 exact. Le rendu de carte est
execute par le renderer natif du firmware Elder35 avec ce seul bitmap injecte
en memoire ; le cote gauche (nom/classe/stats) reste exact. Le PNG de menu
est dans `output/elder-icon/elder-menu-preview.png`.

Aucun firmware ni flasheur n’est modifie par cette etape de dessin.

Integration approuvee dans les deux firmwares prives v36 : meme dessin et
rendu natif exact. Seul le bitmap change par rapport a v35 ; audio exact en
emulation, principal inchange. Voir notes/140-junior-prive.md, section7.
