| Régulateur de charge (notes/36) : les 6 tableaux de gains des pistes que le mix de l'OS met à jour à chaque bloc
| (principal G/D et envois ; ceux que lit voice_quiet de Model-TG), un mot long par piste ; puis 0.
        .text
        .globl  gov_gains
gov_gains:
        .long   0x40a78c08, 0x40a78be8, 0x40a78bd0, 0x40a78bb8, 0x40a78b9c, 0x40a78b80, 0
