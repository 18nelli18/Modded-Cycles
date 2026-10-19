| Note135 : aucun MIDI Out dans la frame -> LFO audio natifs directement.
.text
.globl il_entry,il_seen,il_api,il_machine,il_original,il_end
il_entry:
 lea %sp@(-8),%sp
 moveml %d0/%a0,%sp@
 moveal %sp@(12),%a0
 mvzw %a0@(32),%d0
 cmpl il_machine,%d0
 beq 1f
 mvzw %a0@(98),%d0
 cmpl il_machine,%d0
 beq 1f
 mvzw %a0@(164),%d0
 cmpl il_machine,%d0
 beq 1f
 mvzw %a0@(230),%d0
 cmpl il_machine,%d0
 beq 1f
 mvzw %a0@(296),%d0
 cmpl il_machine,%d0
 beq 1f
 mvzw %a0@(362),%d0
 cmpl il_machine,%d0
 beq 1f
 moveal il_seen,%a0
 clrl %a0@
 moveml %sp@,%d0/%a0
 lea %sp@(8),%sp
 moveal il_api,%a0
 moveal %a0@,%a0
 jmp %a0@
1:
 moveml %sp@,%d0/%a0
 lea %sp@(8),%sp
 jmp il_original
.balign 4
il_seen: .long 0
il_api: .long 0
il_machine: .long 0
il_original: .space 16
il_end:
