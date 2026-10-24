| PS124k, entree filtre4etages, quatre combs stereo, deux allpass par canal.
| Voie chaude seulement : filled2048 et w multiple16 ; aucun tap ne recoupe
| les16ecritures du bloc. Chaque helper garde d2-d7/a2-a6 par ABI.
| ps_hot garde MACSR et les48bits physiques ACC0/ACCext01 ; autres ACC intacts.
| Contrats jobs : ps_job44o (voir ps1_fast.c), ap_job32o. Coefficients Q15
| mis a l echelle<<16 avant MAC fractionnaire, meme floor que le C.
.text
.globl ps_comb_kernel,ps_hot
ps_comb_kernel:
 lea -52(%sp),%sp
 movem.l %d2-%d7/%a2-%a6,(%sp)
 move.l 56(%sp),%a5
 move.l %a5,44(%sp)
 move.l (%a5),%a2
 move.l 4(%a5),%a3
 move.l 8(%a5),%a4
 move.l 28(%a5),%a0
 move.l (%a0),%d2
 move.l 32(%a5),%a0
 move.l (%a0),%d3
 move.l 36(%a5),%a6
 move.l 40(%a5),%a5
 move.l 44(%sp),%a0
 move.l 16(%a0),%d0
 move.l %d0,%d1
 sub.l 20(%a0),%d0
 and.l #2047,%d0
 add.l %d0,%d0
 sub.l 24(%a0),%d1
 and.l #2047,%d1
 add.l %d1,%d1
 move.l 16(%a0),%d4
 add.l %d4,%d4
 lea (%a2,%d4.l),%a0
 lea (%a3,%d4.l),%a1
 lea 32(%a0),%a6
 move.l %a6,48(%sp)
 move.l 44(%sp),%a6
 move.l 36(%a6),%a6
1:
 mvs.w (%a2,%d0.l),%d4
 mvs.w (%a3,%d1.l),%d5
 add.l %d4,128(%a4)
 add.l %d5,132(%a4)
 move.l %d4,%d6
 lsl.l #3,%d6
 sub.l %d4,%d6
 add.l %d5,%d6
 bpl 2f
 addq.l #7,%d6
2:
 asr.l #3,%d6
 sub.l %d2,%d6
 mac.l %d6,%a6,%acc0
 movclr.l %acc0,%d6
 add.l %d6,%d2
 move.l %d5,%d6
 lsl.l #3,%d6
 sub.l %d5,%d6
 add.l %d4,%d6
 bpl 2f
 addq.l #7,%d6
2:
 asr.l #3,%d6
 sub.l %d3,%d6
 mac.l %d6,%a6,%acc0
 movclr.l %acc0,%d6
 add.l %d6,%d3
 move.l 0(%a4),%d6
 bne 3f
 move.l %d2,%d7
 addq.l #1,%d7
 cmp.l #3,%d7
 bcc 3f
 moveq #0,%d2
3:
 asr.l #2,%d6
 mac.l %d2,%a5,%acc0
 movclr.l %acc0,%d7
 add.l %d6,%d7
 cmp.l #32767,%d7
 ble 4f
 move.l #32767,%d7
4:
 cmp.l #-32768,%d7
 bge 5f
 move.l #-32768,%d7
5:
 move.w %d7,(%a0)+
 move.l 4(%a4),%d6
 bne 3f
 move.l %d3,%d7
 addq.l #1,%d7
 cmp.l #3,%d7
 bcc 3f
 moveq #0,%d3
3:
 asr.l #2,%d6
 mac.l %d3,%a5,%acc0
 movclr.l %acc0,%d7
 add.l %d6,%d7
 cmp.l #32767,%d7
 ble 4f
 move.l #32767,%d7
4:
 cmp.l #-32768,%d7
 bge 5f
 move.l #-32768,%d7
5:
 move.w %d7,(%a1)+
 addq.l #2,%d0
 and.l #4094,%d0
 addq.l #2,%d1
 and.l #4094,%d1
 lea 8(%a4),%a4
 cmp.l 48(%sp),%a0
 bne 1b
 move.l 44(%sp),%a5
 move.l 28(%a5),%a0
 move.l %d2,(%a0)
 move.l 32(%a5),%a0
 move.l %d3,(%a0)
 movem.l (%sp),%d2-%d7/%a2-%a6
 lea 52(%sp),%sp
 rts
| Conserver le contexte physique MAC comme le contrat PS1 C existant.
ps_hot:
 lea -12(%sp),%sp
 move.l %macsr,%d0
 move.l %d0,(%sp)
 moveq #0,%d0
 move.l %d0,%macsr
 move.l %acc0,%d0
 move.l %d0,4(%sp)
 move.l %accext01,%d0
 move.l %d0,8(%sp)
 moveq #32,%d0
 move.l %d0,%macsr
 moveq #0,%d0
 move.l %d0,%acc0
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 jsr ps_hot_core
 lea 12(%sp),%sp
 moveq #0,%d0
 move.l %d0,%macsr
 move.l 4(%sp),%d0
 move.l %d0,%acc0
 move.l 8(%sp),%d0
 move.l %d0,%accext01
 move.l (%sp),%d0
 move.l %d0,%macsr
 lea 12(%sp),%sp
 rts

.globl ps_input_kernel
ps_input_kernel:
 lea -32(%sp),%sp
 movem.l %d2-%d7/%a2-%a3,(%sp)
 move.l 36(%sp),%a0
 move.l 40(%sp),%a1
 move.l 44(%sp),%a2
 lea 128(%a0),%a3
 move.l (%a2),%d2
 move.l 4(%a2),%d3
 move.l 8(%a2),%d4
 move.l 12(%a2),%d5
1:
 mvs.w 0(%a1),%d0
 move.l %d0,%d1
 add.l %d2,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d2
 asr.l #1,%d0
 move.l %d0,%d1
 add.l %d3,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d3
 asr.l #1,%d0
 move.l %d0,%d1
 add.l %d4,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d4
 asr.l #1,%d0
 move.l %d0,%d1
 add.l %d5,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d5
 asr.l #1,%d0
 move.l %d0,%d6
 mvs.w 8(%a1),%d0
 move.l %d0,%d1
 add.l %d2,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d2
 asr.l #1,%d0
 move.l %d0,%d1
 add.l %d3,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d3
 asr.l #1,%d0
 move.l %d0,%d1
 add.l %d4,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d4
 asr.l #1,%d0
 move.l %d0,%d1
 add.l %d5,%d0
 bpl 2f
 addq.l #1,%d0
2:
 move.l %d1,%d5
 asr.l #1,%d0
 add.l %d0,%d6
 move.l %d6,(%a0)
 lea 8(%a0),%a0
 lea 16(%a1),%a1
 cmp.l %a3,%a0
 bne 1b
 move.l %d2,(%a2)
 move.l %d3,4(%a2)
 move.l %d4,8(%a2)
 move.l %d5,12(%a2)
 movem.l (%sp),%d2-%d7/%a2-%a3
 lea 32(%sp),%sp
 rts

.globl ps_ap_kernel
ps_ap_kernel:
 lea -40(%sp),%sp
 movem.l %d2-%d7/%a2-%a5,(%sp)
 move.l 44(%sp),%a5
 move.l (%a5),%a0
 move.l 4(%a5),%a1
 move.l 8(%a5),%a2
 lea 1024(%a2),%a3
 lea 256(%a0),%a4
 move.l 12(%a5),%d4
 move.l 16(%a5),%d5
 move.l 20(%a5),%d6
 move.l 24(%a5),%d7
 move.l 28(%a5),%d3
1:
 move.l (%a1),%d0
 bpl 2f
 addq.l #3,%d0
2:
 asr.l #2,%d0
 mvs.w (%a2,%d4.l:2),%d1
 move.l %d0,%d2
 addq.l #1,%d2
 cmp.l #3,%d2
 bcc 3f
 move.l %d1,%d2
 addq.l #1,%d2
 cmp.l #3,%d2
 bcc 3f
 moveq #0,%d0
 moveq #0,%d1
3:
 move.l %d0,%d2
 asr.l #1,%d2
 sub.l %d2,%d1
 cmp.l #32767,%d1
 ble 4f
 move.l #32767,%d1
4:
 cmp.l #-32768,%d1
 bge 5f
 move.l #-32768,%d1
5:
 move.l %d1,%d2
 asr.l #1,%d2
 add.l %d0,%d2
 cmp.l #32767,%d2
 ble 6f
 move.l #32767,%d2
6:
 cmp.l #-32768,%d2
 bge 7f
 move.l #-32768,%d2
7:
 move.w %d2,(%a2,%d4.l:2)
 move.l %d1,%d0
 addq.l #1,%d4
 cmp.l %d6,%d4
 bne 8f
 moveq #0,%d4
8:
 mvs.w (%a3,%d5.l:2),%d1
 move.l %d0,%d2
 addq.l #1,%d2
 cmp.l #3,%d2
 bcc 3f
 move.l %d1,%d2
 addq.l #1,%d2
 cmp.l #3,%d2
 bcc 3f
 moveq #0,%d0
 moveq #0,%d1
3:
 move.l %d0,%d2
 asr.l #1,%d2
 sub.l %d2,%d1
 cmp.l #32767,%d1
 ble 4f
 move.l #32767,%d1
4:
 cmp.l #-32768,%d1
 bge 5f
 move.l #-32768,%d1
5:
 move.l %d1,%d2
 asr.l #1,%d2
 add.l %d0,%d2
 cmp.l #32767,%d2
 ble 6f
 move.l #32767,%d2
6:
 cmp.l #-32768,%d2
 bge 7f
 move.l #-32768,%d2
7:
 move.w %d2,(%a3,%d5.l:2)
 move.l %d1,%d0
 addq.l #1,%d5
 cmp.l %d7,%d5
 bne 8f
 moveq #0,%d5
8:
 move.l %d3,%d2
 add.l %d0,%d2
 bpl 2f
 addq.l #1,%d2
2:
 asr.l #1,%d2
 swap %d2
 clr.w %d2
 move.l %d2,(%a0)
 move.l %d0,%d2
 swap %d2
 clr.w %d2
 move.l %d2,8(%a0)
 move.l %d0,%d3
 lea 16(%a0),%a0
 lea 8(%a1),%a1
 cmp.l %a4,%a0
 bne 1b
 move.l %d4,12(%a5)
 move.l %d5,16(%a5)
 move.l %d3,28(%a5)
 movem.l (%sp),%d2-%d7/%a2-%a5
 lea 40(%sp),%sp
 rts
