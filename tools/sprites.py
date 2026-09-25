"""Masques de sprites du MAIN OS 1.13 du Model:Cycles : de la place libérable (notes/14 §5).

Les grands blocs 0xFF de l'image ne sont pas des caves libres : ce sont les MASQUES de
sprites (classe Bitmap, constructeur 0x40070172). Chaque sprite a deux plans de même
taille : l'image (champ +0x10) et le masque (champ +0x14). Quatre masques sont
entièrement à 0xFF (opaques), donc identiques octet pour octet.

On garde intact le plus grand (celui du sprite 32x260, 1040 o) et on fait pointer les
autres dessus, en réécrivant la constante 32 bits passée au constructeur. Le rendu est
identique (mêmes octets lus) et le plan d'origine du masque devient réellement libre.
Le destructeur ne libère pas ces plans (sprite statique, drapeau +0x18 = 0).

Un tweak qui veut une de ces zones inclut redirect_write(zone) : build.py voit alors que
la seule référence vers la zone est réécrite et accepte d'y écrire.
"""
BASE = 0x40000400
SHARED_MASK = 0x40154ae4        # masque du sprite 32x260 (1040 o), gardé intact

# va du masque : (taille, va de la constante 32 bits qui le désigne, description)
MASKS = {
    0x4015c044: (720, 0x400b6434, "sprite 64x90 (cadre), constructeur 0x400b6432"),
    0x4016cae8: (1024, 0x400b1106, "sprite 64x128 (damier de test), constructeur 0x400b1104"),
    0x4018a788: (1024, 0x400ad1aa, "sprite 64x128 (damier inverse), constructeur 0x400ad1a8"),
}


def redirect_write(mask_va):
    """Écriture JSON qui fait pointer le sprite de mask_va sur le masque partagé."""
    size, ptr, _ = MASKS[mask_va]
    return {"off": ptr - BASE, "old": mask_va.to_bytes(4, "big").hex(),
            "new": SHARED_MASK.to_bytes(4, "big").hex()}


def zone(mask_va):
    """(va, taille) de la zone libérée."""
    return mask_va, MASKS[mask_va][0]
