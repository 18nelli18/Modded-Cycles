/* SPDX-License-Identifier: MIT
 * Seul l'appel 0x400107a4 atteint ce crochet. 0x400106de ne crée pas de
 * cadre : A6 reste celui de 0x400107d8. A6+4 = 0x4001c1a2 identifie le
 * raccourci FUNC + RELOAD PTN ; les rechargements du menu restent d'origine.
 * Six mots 8.8 du kit RAM (+16) sont copiés vers le tampon sérialisé v4
 * (+20) avant le décodeur et les notifications. Aucun fichier n'est écrit.
 * D0/A0/A1 sont volatils ; pile, arguments, A6 et registres préservés par
 * l'ABI restent intacts. Pas d'état, d'accroche audio ou de recopie au boot.
 */
.section .cave,"ax"
.globl reload_keep_levels
reload_keep_levels:
 move.l 4(%a6),%d0
 cmp.l #0x4001c1a2,%d0
 bne.s .Lstock
 move.l 4(%sp),%a0
 move.l 8(%sp),%a1
 tst.l %a0
 beq.s .Lstock
 tst.l %a1
 beq.s .Lstock
 move.l (%a1),%d0
 cmp.l #4,%d0
 bne.s .Lstock
 move.w 16(%a0),20(%a1)
 move.w 18(%a0),22(%a1)
 move.w 20(%a0),24(%a1)
 move.w 22(%a0),26(%a1)
 move.w 24(%a0),28(%a1)
 move.w 26(%a0),30(%a1)
.Lstock:
 jmp 0x4005d080
