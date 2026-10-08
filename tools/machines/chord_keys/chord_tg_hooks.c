/* Coexistence avec le Scale Lock Model-TG (notes/40).
 * Les notes CHORD Keys sont déjà des hauteurs chromatiques : ne pas les
 * interpréter une seconde fois comme des indices de degré. Les autres pistes
 * et Keys OFF conservent le détour Model-TG installé dans le firmware.
 */
#include "chord_ui.h"

extern const unsigned char ck_tg_key_release_return[];

unsigned ck_tg_scale_bypass(unsigned track, unsigned note, const unsigned *frame)
{
    if (track >= 6)
        return 0;
    /* Le helper stock 0x40019c84 conserve 16 o de registres et pousse 16 o
     * (racine, vélocité, note, piste). note_off ajoute son retour et l'ancien
     * fp : fp+4 désigne 0x40019cba, fp+40 le retour du helper vers notre relais.
     * Ne lire ce second retour qu'après avoir reconnu le premier. L'identité
     * de la pile distingue notre touche d'un note-off API ou clavier stock de
     * même hauteur ; aucun état global, même avec des appels imbriqués.
     */
    if (frame && note < 128 && frame[1] == 0x40019cbau &&
            frame[10] == (unsigned)ck_tg_key_release_return)
        return 1;
    if (!(ck_ui_config_get(track) & 0x80000000u))
        return 0;
    return ((int (*)(void *, unsigned))0x4001e318)(0, track) == 5;
}
