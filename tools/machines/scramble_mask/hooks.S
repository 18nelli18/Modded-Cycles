.text
.globl sx_bounds,sx_step_hook
sx_bounds:
 movea.l 8(%sp),%a0
 move.l 4(%sp),-(%sp)
 jsr 0x4005a65a
 addq.l #4,%sp
 rts
sx_step_hook:
 move.l %fp,72(%a2)
 move.l %a2,%d0
 lea -64(%sp),%sp
 movem.l %d0-%d7/%a0-%a6,(%sp)
 move.w %sr,%d0
 move.l %d0,60(%sp)
 move.l %a2,-(%sp)
 jsr sx_step
 addq.l #4,%sp
 move.l 60(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d7/%a0-%a6
 lea 64(%sp),%sp
 jmp 0x40054c14
