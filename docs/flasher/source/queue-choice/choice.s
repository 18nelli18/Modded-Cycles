| Nouvelle ligne Queue at ; 0 = boucle, 1 = page de seize pas.
.section .text.avq_rows,"ax"
.globl avq_map,avq_unmap,avq_last,avq_boundary,avq_value,avq_label,avq_mode,avq_names
avq_last: moveq #21,%d0
 rts
avq_map:
 tstl %d0
 beqs 1f
 cmpil #1,%d0
 beqs 2f
 cmpil #21,%d0
 beqs 3f
 subql #2,%d0
 rts
1: moveq #20,%d0
 rts
2: moveq #19,%d0
 rts
3: moveq #21,%d0
 rts
avq_unmap:
 cmpil #20,%d0
 beqs 1f
 cmpil #19,%d0
 beqs 2f
 cmpil #21,%d0
 beqs 3f
 addql #2,%d0
 rts
1: moveq #0,%d0
 rts
2: moveq #1,%d0
 rts
3: moveq #21,%d0
 rts
| d0=index piste ; registres protégés par le hook existant.
.section .text.avq_boundary,"ax"
avq_boundary:
 moveq #0,%d1
 moveb %a0@(0,%d0:l),%d1
 tstl avq_mode
 beqs 1f
 andil #15,%d1
1: tstl %d1
 bnes 2f
 jmp Q_PHASE
2: jmp Q_OUT
.section .text.avq_value,"ax"
avq_value:
 cmpil #19,%d3
 beqs 1f
 movel %d3,%d0
 subql #5,%d0
 lsll #4,%d0
 jmp VALUE_CONT
1: lea avq_names,%a0
 movel avq_mode,%d0
 moveal %a0@(0,%d0:l:4),%a2
 jmp STRING_CONT
.section .data.avq,"aw"
.balign 4
avq_mode: .long 0
avq_names: .long avq_loop,avq_page
avq_label: .asciz "Queue at"
avq_loop: .asciz "Loop"
avq_page: .asciz "Page"
