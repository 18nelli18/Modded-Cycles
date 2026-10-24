/* Contrat encodeur/audio comme le chorus ; toutes les entrees precedentes restent deleguees. */
.text
.globl cr_encoder_hook,cr_fx,cr_object
cr_encoder_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 24(%sp),-(%sp)
 jsr cr_encoder
 addq.l #4,%sp
 tst.l %d0
 beq 1f
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #1,%d0
 rts
1:movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp cr_previous_encoder
cr_fx:
 move.l %a5,-(%sp)
 move.l %a4,-(%sp)
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 jsr cr_split
 lea 20(%sp),%sp
 move.l #0xa0,%d0
 move.l %d0,%macsr
 movclr.l %acc0,%d0
 movclr.l %acc1,%d0
 movclr.l %acc2,%d0
 movclr.l %acc3,%d0
 rts
cr_object:
 move.l #cr_obj,%d0
 rts

/* Hook mixeur avant quantification sortie : rejoue les deux PEA natifs.
 * d0/d1/a0/a1 et tous les registres callee-saved conserves ; pile identique.
 * Correction apres envois Reverb : aucun anti-dry injecte dans le chorus. */
.globl cr_mix_hook
cr_mix_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 pea 0x8000b990
 jsr cr_post
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 pea 4.w
 pea 0x8000b990
 jmp 0x40056b42
