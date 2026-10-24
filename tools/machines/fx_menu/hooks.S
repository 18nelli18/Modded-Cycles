.text
#ifdef FX_BANK_SAFE
.globl fx_frame_begin
/* Avant ViewManager::draw et AVANT acquisition du mutex : services disque/UI.
 * Prologue exact rejoue ; aucun appel a present() sous le verrou de dessin. */
fx_frame_begin:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 jsr fx_frame_prepare
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 lea -36(%sp),%sp
 movem.l %d2-%d4/%a2-%a5,(%sp)
 jmp 0x40076c22
#endif
#ifdef FX_POLISH
.globl fx_stack_draw
/* Fin de ViewManager::draw, toutes vues deja dessinees ; d3=Bitmap.
 * Replay clrb d0/moveb d0,32(a2) puis epilogue natif, ABI intacte. */
fx_stack_draw:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l %d3,-(%sp)
 move.l %a2,-(%sp)
 jsr fx_stack_overlay
 addq.l #8,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 clr.b %d0
 move.b %d0,32(%a2)
 jmp 0x40076c8e
#endif
.globl fx_encoder_hook,fx_key_hook,fx_rfx,fx_mix_hook,fx_object,fx_machine_hook
fx_encoder_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 jsr fx_encoder
 addq.l #8,%sp
 tst.l %d0
 beq 1f
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #1,%d0
 rts
1:movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp fx_previous_encoder
fx_key_hook:
 lea -16(%sp),%sp
 movem.l %d1/%a0-%a1,(%sp)
 move.l 20(%sp),-(%sp)
 jsr fx_key
 addq.l #4,%sp
 tst.l %d0
 beq 2f
 move.l 20(%sp),%a0
 clr.l 12(%a0)
 movem.l (%sp),%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #0,%d0
 rts
2:movem.l (%sp),%d1/%a0-%a1
 lea 16(%sp),%sp
 jmp fx_key_original
fx_rfx:
 move.l %a5,-(%sp)
 move.l %a4,-(%sp)
 move.l %a3,-(%sp)
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 move.l 24(%sp),-(%sp)
 jsr fx_reverb
 lea 24(%sp),%sp
 move.l #0xa0,%d0
 move.l %d0,%macsr
 movclr.l %acc0,%d0
 movclr.l %acc1,%d0
 movclr.l %acc2,%d0
 movclr.l %acc3,%d0
 rts
fx_mix_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 pea 0x8000b990
 jsr fx_post
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 pea 4.w
 pea 0x8000b990
 jmp 0x40056b42
fx_object:
 move.l #fx_obj,%d0
 rts
fx_machine_hook:
 lea -16(%sp),%sp
 movem.l %d1/%a0-%a1,(%sp)
 move.l %d5,-(%sp)
 move.l %d0,-(%sp)
 jsr fx_machine_step
 addq.l #8,%sp
 movem.l (%sp),%d1/%a0-%a1
 lea 16(%sp),%sp
 moveq #-1,%d1
 jmp 0x400148bc

#ifdef FX_NEW_DELAYS
/* Signature du delay native, aucun registre a3/a4/a5 perdu : le relais legacy
 * utilise a4/a5 pour ses gains de bus. EMAC restaure comme cr_fx. */
.globl fx_dfx
fx_dfx:
 move.l %a5,-(%sp)
 move.l %a4,-(%sp)
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 jsr fx_delay
 lea 20(%sp),%sp
 move.l #0xa0,%d0
 move.l %d0,%macsr
 movclr.l %acc0,%d0
 movclr.l %acc1,%d0
 movclr.l %acc2,%d0
 movclr.l %acc3,%d0
 rts
#endif

#ifdef FX_DELAY_REPAIR
/* Native 0x40057638 : le retour wet est pret dans *0x8000b570, avant
 * feedback. Preserver d0/d1/a0/a1, tous les autres via ABI C, ACC intacts.
 * Rejouer movea.l absolu -> a1 ; reprendre au vrai chargement de out. */
.globl fx_delay_read_hook
fx_delay_read_hook:
 lea -16(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.l 0x8000b570,-(%sp)
 jsr fx_delay_return
 addq.l #4,%sp
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 16(%sp),%sp
 move.l 0x8000b570,%a1
 jmp 0x4005763e
#endif

#if defined(FX_IDLE_OPT)&&!defined(FX_NO_SHIMMER)
/* Le hook delay interne exige tous les ACC intacts. Sauver ACC0 en mode
 * entier pour ne perdre ni saturation ni bits bas ; ACCext01 inclut ACC1,
 * jamais modifie. Restaurer MACSR apres toutes les ecritures physiques. */
.globl fx_shift
fx_shift:
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
 move.l 16(%sp),-(%sp)
 jsr fx_shift_core
 addq.l #4,%sp
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
#endif
