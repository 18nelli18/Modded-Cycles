/*
 * MODAL : les tailles que le C (modal_dsp.h) et l'assembleur (modal_asm.S) doivent partager. Seulement des #define :
 * ce fichier est lu par le preprocesseur de l'assembleur.
 *
 * Le coeur calcule Rings a 24 kHz (notes/81) : un bloc du Cycles (32 trames a 48 kHz) est un bloc de 16 trames du
 * coeur, remonte a 48 kHz par la passerelle (modal.c). Les lignes des cordes gardent la meme note la plus grave en
 * hertz que Rings a 48 kHz avec 2 048 mots : 1 024 mots a 24 kHz.
 */
#ifndef MODAL_CFG_H
#define MODAL_CFG_H

#define MB          16                               /* trames par bloc du coeur (24 kHz) */
#define MB_SHIFT    4                                /* log2(MB) */
#define DLINE       1024                             /* kDelayLineSize (Rings : 2 048 a 48 kHz) */
#define SLINE       512                              /* la ligne de l'etirement (kDelayLineSize / 2) */
#define HBN         7                                /* paires du filtre demi-bande de la passerelle (27 coefficients) */

#endif
