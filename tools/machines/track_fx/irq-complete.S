| Une decision par IRQ terminee ; ne pas assembler les queues de deux blocs.
| Memes seuils, memes fonctions de gouverneur et de diagnostic2.75.
| Entrees IRQ : scratch d0/d1/a0/a1, convention historique ; aucun EMAC touche.
.text
.globl ig_audio_end,ig_irq_end,ig_install
ig_audio_end:
 tst.l gb_irq_active
 beq.w ig_previous_audio
 move.l 0xfc07000c,%d0
 move.l %d0,gb_budget_t0
 rts
ig_irq_end:
 tst.l gb_irq_active
 beq.s .Lfinish
 tst.l gb_budget_t0
 beq.s .Lfinish
 move.l gb_irq_t0,%d0
 move.l %d0,0x46732080
 sub.l #90112,%d0
 move.l %d0,0x46732f00
 jsr mf_old_audio_end
.Lfinish:
 jmp ig_previous_irq
