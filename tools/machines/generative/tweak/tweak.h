/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Commun à tweak.c (le générateur dans l'OS : Random, Undo, écriture des pistes) et page.c (la page GEN). */
#ifndef TWEAK_H
#define TWEAK_H

#include "../core/gen.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t s32;
typedef int16_t s16;
typedef int8_t s8;

#define FN(a, ret, ...) ((ret (*)(__VA_ARGS__))(a))
/* L'OS rend les pointeurs dans d0, mais m68k-linux-gnu-gcc lit un pointeur rendu dans a0 : les fonctions de l'OS
 * qui rendent un pointeur sont donc déclarées rendre un u32, converti ensuite. */
#define FNP(a, ...) (void *)FN(a, u32, __VA_ARGS__)
#define NEW(n)      FNP(0x400802e0, u32)(n)                       /* operator new ; 0 en cas d'échec */
#define DTIM0       (*(volatile u32 *)0xfc07000c)                 /* compteur libre à 135,168 MHz */

/* État de Model-TG (TG 70b39dd, octets vérifiés par tools/gen_generative.py) */
#define TG_SET_HELD (*(volatile u32 *)0x401b235c)                 /* SETTINGS enfoncé */
#define TG_MOD_USED (*(volatile u32 *)0x401b2360)                 /* au relâchement de SETTINGS : pas de Config Menu */
#define TG_RTG_ON   (*(volatile u32 *)0x401b6d8c)                 /* page retrig de TG ouverte */
#define TG_SLE_ON   (*(volatile u32 *)0x401bcaec)                 /* éditeur de tranches de TG ouvert */

#define EV_CODE(e)  (*(u32 *)((u8 *)(e) + 12))
#define EV_FLAGS(e) (*(volatile u32 *)((u8 *)(e) + 16))

extern u16 ours_controls[GEN_CONTROLS];
extern u32 ours_seed;
extern u32 pg_lock;                 /* verrous, bit t : Random laisse les pistes verrouillées */
extern u32 pg_owned;                /* bit t : la piste t a été générée (Random ou un réglage), Style peut donc la réécrire */
extern u16 pg_rhythm[GEN_TRACKS];   /* les 16 premiers pas de chaque piste tels que le pattern les tient, bit s = pas s */

/* Tout ceci tourne dans la tâche d'interface. */
void tw_random(void);               /* tire les pistes non verrouillées (après une copie, pour Undo) */
void tw_undo(void);                 /* retour à l'état d'avant le dernier Random */
int tw_edit(int t);                 /* régénère et écrit la piste t d'après ours_controls */
void tw_read_rhythms(void);         /* relit pg_rhythm dans le pattern */
int tw_ready(void);                 /* tables construites et réglages initialisés ; 0 si la mémoire manque */
u16 tw_even_count(int n, int k);    /* plage de régularité pour le style de densité en cours */

/* Accroche de l'accesseur de touche, devant celle de Model-TG : le code à rendre, ou TW_PASS pour laisser Model-TG. */
#define TW_PASS 0xffffffffu
u32 tw_chord(void *ev);             /* accords SETTINGS+PATTERN / SETTINGS+TEMPO */
void page_changed(void);            /* redessine la page et ses voyants, si elle est ouverte */

#endif
