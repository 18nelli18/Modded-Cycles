| Sortie anticipee, exactement la meme decision aux deux seuils.
| Le linker place ce fragment dans les 38 octets du scan SRAM courant.
.text
.globl gr_scan,gr_scan_end
gr_scan:
 moveq #7,%d4
1:
 movel %a0@+,%d2
 addl %d3,%d2
.rept 3
 movel %a0@+,%d1
 addl %d3,%d1
 orl %d1,%d2
.endr
 movel %d2,%d1
 lsrl #1,%d1
 cmpl %d3,%d1
 bcc.s GR_LOUD
 subql #1,%d4
 bpl.s 1b
 nop
gr_scan_end:
