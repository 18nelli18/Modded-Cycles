| Adaptateurs vérifiés, prototypes hors flasher. Erreur distincte de l'absence.
| lookup(parent,name,out) -> -1 I/O/guard, 0 absent, 1 présent.
| read/write(path,buffer,1616) -> 1 seulement si API ET garde réussissent.
    .ifdef ML_STORAGE2
    .equ ML_DATA_BYTES,4896
    .equ ML_RECORD_BYTES,4928
    .else
    .equ ML_DATA_BYTES,1584
    .equ ML_RECORD_BYTES,1616
    .endif
    .text
    .globl ml_store_lookup_checked,ml_store_read_checked,ml_store_write_checked
ml_store_lookup_checked:
    movel %d2,%sp@-
    jsr ml_store_io_begin
    tstl %d0
    beq .Llookup_refused
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    jsr 0x4007ad86
    lea.l %sp@(12),%sp
    movel %d0,%d2
    jsr ml_store_io_end
    tstl %d0
    beq .Llookup_refused
    movel %d2,%d0
    bra .Llookup_out
.Llookup_refused:
    moveq #-1,%d0
.Llookup_out:
    movel %sp@+,%d2
    rts
    .macro checked name,target
\name:
    movel %d2,%sp@-
    jsr ml_store_io_begin
    tstl %d0
    beq .Lchecked_out\@
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    movel %sp@(16),%sp@-
    jsr \target
    lea.l %sp@(12),%sp
    movel %d0,%d2
    jsr ml_store_io_end
    andl %d2,%d0
.Lchecked_out\@:
    movel %sp@+,%d2
    rts
    .endm
    checked ml_store_read_checked,ml_store_read
    checked ml_store_write_checked,ml_store_write
