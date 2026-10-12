| Note 57 : variante bundle TG-ST uniquement. La copie arrive APRÈS
| décompression Syntakt, car la destination remplace son ancien flux.
| Le tampon nul du filesystem reste hors de notre plage préservée.
| Remise à zéro dérivée du boot_extra_hook de Model-TG (TinyGregAudio,
| MIT, LICENSE-Model-TG), même ACR1 et même reprise native.
    .section .text.ml_loader,"ax"
    .globl ml_boot_copy
ml_boot_copy:
    lea.l ML_PAYLOAD_SRC,%a0
    lea.l ML_BANK_START,%a1
    .ifdef ML_LFO_CC
    lea %sp@(-24),%sp
    moveml %d2-%d6/%a2,%sp@
    jsr ml_depack
    moveml %sp@,%d2-%d6/%a2
    lea %sp@(24),%sp
    .else
    movel #ML_BANK_SIZE,%d0
.Lcopy:
    moveb %a0@+,%a1@+
    subql #1,%d0
    bne .Lcopy
    .endif
    nop
    movel #0x000cc100,%d0
    movec %d0,%cacr
    nop
    jmp ml_boot_clear

    .text
    .globl ml_boot_clear,ml_boot_loop,ml_boot_skip,ml_boot_done
ml_boot_clear:
    lea.l %sp@(-16),%sp
    movem.l %d4-%d7,%sp@
    movel #0x4c03e000,%d4
    movec %d4,%acr1
    lea.l 0x4019b590,%a0
    moveq #0,%d4
    moveq #0,%d5
    moveq #0,%d6
    moveq #0,%d7
ml_boot_loop:
    cmpal #ML_TG_START,%a0
    bne .Lclear
ml_boot_skip:
    moveal #ML_BANK_END,%a0
.Lclear:
    cmpal #0x423380b0,%a0
    bcc ml_boot_done
    movem.l %d4-%d7,%a0@
    lea.l %a0@(16),%a0
    bra ml_boot_loop
ml_boot_done:
    movem.l %sp@,%d4-%d7
    lea.l %sp@(16),%sp
    lea.l 0xfc044000,%a0
    jmp 0x4000053a
