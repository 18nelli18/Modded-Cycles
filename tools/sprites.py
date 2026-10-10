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

Même principe pour onze sprites 47x47 (constructeurs 0x400ac784..0x400b0580) : leurs masques
de 376 o sont identiques (un carré opaque de 47 colonnes, octets ff ff ff ff ff fe 00 00 par
ligne). On garde celui de 0x40172220 ; les autres peuvent pointer dessus (notes/32 §11).
Chacun n'est désigné que par la constante du constructeur. Ces masques ne sont pas à 0xFF :
le contrôle des caves de build.py ne les voit pas, les octets « old » des écritures si.
"""
BASE = 0x40000400
SHARED_MASK = 0x40154ae4        # masque du sprite 32x260 (1040 o), gardé intact
SHARED_47 = 0x40172220          # masque d'un sprite 47x47 (376 o), gardé intact
SHARED_34 = 0x4016bfc8          # masque d'un sprite 34x34 (272 o), gardé intact (15 copies identiques, notes/53)

# va du masque : (taille, va de la constante 32 bits qui le désigne, description[, masque partagé])
MASKS = {
    0x4015c044: (720, 0x400b6434, "sprite 64x90 (cadre), constructeur 0x400b6432"),
    0x4016cae8: (1024, 0x400b1106, "sprite 64x128 (damier de test), constructeur 0x400b1104"),
    0x4018a788: (1024, 0x400ad1aa, "sprite 64x128 (damier inverse), constructeur 0x400ad1a8"),
    0x40189930: (376, 0x400ad328, "sprite 47x47, constructeur 0x400ad326", SHARED_47),
    0x4018a220: (376, 0x400ad202, "sprite 47x47, constructeur 0x400ad200", SHARED_47),
    0x401904b4: (376, 0x400ac784, "sprite 47x47, constructeur 0x400ac782", SHARED_47),
    0x40183118: (376, 0x400adf9e, "sprite 47x47, constructeur 0x400adf9c", SHARED_47),
    0x40185018: (376, 0x400adba8, "sprite 47x47, constructeur 0x400adba6", SHARED_47),
    0x40185968: (376, 0x400ada00, "sprite 47x47, constructeur 0x400ad9fe", SHARED_47),
    0x40185c58: (376, 0x400ad9e0, "sprite 47x47, constructeur 0x400ad9de", SHARED_47),
    0x40192ba4: (272, 0x400ac276, "sprite 34x34, constructeur 0x400ac274", SHARED_34),
}


def redirect_write(mask_va):
    """Écriture JSON qui fait pointer le sprite de mask_va sur le masque partagé."""
    ptr, shared = MASKS[mask_va][1], (MASKS[mask_va][3:] or (SHARED_MASK,))[0]
    return {"off": ptr - BASE, "old": mask_va.to_bytes(4, "big").hex(),
            "new": shared.to_bytes(4, "big").hex()}


def zone(mask_va):
    """(va, taille) de la zone libérée."""
    return mask_va, MASKS[mask_va][0]
