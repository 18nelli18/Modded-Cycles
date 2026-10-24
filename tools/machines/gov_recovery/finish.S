| Dans le padding SRAM apres voice_done : chemin ordinaire de dix instructions.
| gov_st, inutilise par le regulateur ASM release : bit7=reprise, bit0=queue valide.
.text
.globl gr_finish,gr_epilogue,gr_finish_end
gr_finish:
 tstb %a1@(0x46,%d0:l)
 bmi.s 1f
 tstb %a1@(0x58,%d0:l)
 bne.s 2f
 tstb %a1@(0x4c,%d0:l)
 bne.s 2f
gr_epilogue:
 moveml %sp@,%d2-%d4/%a2
 lea %sp@(16),%sp
 rts
1: jmp gr_recover_entry
2: jmp gr_record
gr_finish_end:
