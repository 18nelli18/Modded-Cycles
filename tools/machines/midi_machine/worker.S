/* D0 est le message retire de la mailbox native. Rejouer les8octets ecrases
 * pour tout autre message ; leurs flags de CMP restent ceux du branchement.
 */
 .text
 .globl mm_worker_hook
mm_worker_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l %d0,-(%sp)
 jsr mm_cc_worker
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp 0x4008a0e2
1: movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #1,%d1
 move.l %d0,%a3
 mvs.b (%a3),%d0
 cmp.l %d0,%d1
 jmp 0x4008a0f8
 .globl mm_sequence_hook
mm_sequence_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 pea 1
 move.l 4(%a3),-(%sp)
 move.l %a2,-(%sp)
 move.l %d2,-(%sp)
 jsr mm_sequence
 lea 16(%sp),%sp
 tst.l %d0
 bne 1f
 tst.l mm_sequence_api
 beq 1f
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 move.l mm_sequence_api,-(%sp)
 rts
1:
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 clr.l 0x40a78e18
 jmp 0x400591a4
 .data
 .globl mm_sequence_api
mm_sequence_api:
 .long 0,0
 .text
 .globl mm_lock_only_hook
mm_lock_only_hook:
 lea 12(%sp),%sp
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 clr.l -(%sp)
 move.l 4(%a3),-(%sp)
 move.l %a2,-(%sp)
 move.l %d2,-(%sp)
 jsr mm_sequence
 lea 16(%sp),%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp 0x400591a4
