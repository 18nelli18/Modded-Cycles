| Entree : avant feed_isr ; d0/d1/a0/a1 sont deja scratch dans ce contrat.
| Le retour rejoue le JSR USB original puis reprend40058ca6.
.text
.globl gb_irq_start,gb_irq_end,gb_audio_end
gb_irq_start:
 move.l 0xfc07000c,%d1
 move.l %d1,gb_irq_t0
 moveq #1,%d1
 move.l %d1,gb_irq_active
 clr.l gb_budget_t0
 jmp mf_old_irq_start
| audio_end deja protege par le frame natif ; pas de registre callee-save touche.
| Native conserve ses seuils et ses moyennes, mais voit aussi prelude/queue.
gb_audio_end:
 move.l 0xfc07000c,%d0
 move.l %d0,gb_budget_t0
 tst.l gb_irq_active
 beq.s 1f
 move.l gb_irq_t0,%d1
 sub.l gb_last_tail,%d1
 move.l %d1,0x46732080
 | Ne pas falsifier la charge precedente : audio_end exige deux pics
 | consecutifs, ou une charge moyenne soutenue, avant de voler une voix.
 sub.l #90112,%d1
 move.l %d1,0x46732f00
1: jmp mf_old_audio_end
| Avant restauration EMAC et registres natifs ; a6 et les callee-save preserves.
| La mesure exclut seulement ce bilan et le court epilogue de restauration.
gb_irq_end:
 move.l 0xfc07000c,-(%sp)
 jsr gb_finish
 addq.l #4,%sp
 jmp mf_old_irq_end
