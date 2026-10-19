/* Relais live apres le traitement natif audio/enregistrement. Les autres
 * machines reprennent exactement le chemin stock. Tous les volatils sont
 * sauvegardes ; l'ABI C preserve d2-d7/a2-a6. Aucun contexte global de pile.
 */
 .text
 .macro save
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 .endm
 .macro restore
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 .endm
 .macro on
 move.l %d4,-(%sp)
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr mm_live_on
 lea 12(%sp),%sp
 tst.l %d0
 .endm
 .macro off
 move.l %d3,-(%sp)
 move.l %d2,-(%sp)
 jsr mm_live_off
 addq.l #8,%sp
 tst.l %d0
 .endm
 .globl mm_key_on_hook
mm_key_on_hook:
 jsr (%a2)
 save
 on
 beq 1f
 restore
 lea 28(%sp),%sp
 jmp 0x40019f3a
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api
 beq 2f
 move.l mm_live_api,-(%sp)
 rts
2:
#endif
 move.l %d0,-(%sp)
 jsr 0x4000f208
 jmp 0x40019eec
 .globl mm_pad_on_hook
mm_pad_on_hook:
 save
 on
 beq 1f
 restore
 lea 28(%sp),%sp
 jmp 0x4001d0f2
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api+4
 beq 2f
 move.l mm_live_api+4,-(%sp)
 rts
2:
#endif
 lea 0x400cf866,%a2
 jmp 0x4001d09a
 .globl mm_key_off_hook
mm_key_off_hook:
 save
 off
 beq 1f
 restore
 lea 16(%sp),%sp
 jmp 0x40019cf6
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api+8
 beq 2f
 move.l mm_live_api+8,-(%sp)
 rts
2:
#endif
 move.l %d4,-(%sp)
 jsr 0x40016e90
 jmp 0x40019cc2
 .globl mm_pad_off_hook
mm_pad_off_hook:
 save
 off
 beq 1f
 restore
 lea 12(%sp),%sp
 jmp 0x4001d176
1: restore
#ifdef MM_CONTROLS
 tst.l mm_live_api+12
 beq 2f
 move.l mm_live_api+12,-(%sp)
 rts
2:
#endif
 lea 0x400cf866,%a2
 jmp 0x4001d126
#ifdef MM_CONTROLS
 .data
 .globl mm_live_api
mm_live_api:
 .long 0,0,0,0
#endif


#ifdef MM_CONTROLS
/* Le producteur audio live peut aussi mettre une note dans la mailbox MIDI.
 * La machine MIDI a deja son relais direct avec port/canal captures : eviter
 * cette seconde attaque differee, tout en conservant l'enregistrement audio.
 * Entree native d2=piste, registres volatils preserves avant le delegate.
 */
 .macro producer name,resume,skip
 .globl \name
\name:
 save
 move.l %d2,-(%sp)
 clr.l -(%sp)
 jsr 0x4001e318
 addq.l #8,%sp
 cmpi.b #MM_MACHINE,%d0
 beq 1f
 restore
 jsr 0x4008a5d0
 jmp \resume
1: restore
 jmp \skip
 .endm
 producer mm_live_producer_on,0x400817b0,0x400817d8
 producer mm_live_producer_off,0x40081558,0x40081576

 .globl mm_secondary_bridge
mm_secondary_bridge:
 save
 move.l 28(%sp),-(%sp)
 move.l 28(%sp),-(%sp)
 move.l 28(%sp),-(%sp)
 jsr mm_secondary_write
 lea 12(%sp),%sp
 tst.l %d0
 beq 1f
 restore
 rts
1: restore
 lea -24(%sp),%sp
 movem.l %d2-%d4/%a2,(%sp)
 move.l mm_secondary_resume,-(%sp)
 rts
 .data
 .globl mm_secondary_resume
mm_secondary_resume: .long 0

#endif
