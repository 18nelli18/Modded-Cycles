/* Seul ACC0 est utilise par MSFA. Sauver les48bits physiques et MACSR ;
 * ACC1..3 et tous les registres callee-saved restent inchanges. */
.text
.globl dx7_block
dx7_block:
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
 move.l 20(%sp),-(%sp)
 move.l 20(%sp),-(%sp)
 jsr dx7_block_c
 lea 8(%sp),%sp
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
