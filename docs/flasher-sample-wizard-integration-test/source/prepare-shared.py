"""Raccords partagés Wizard/performance/WAVE, désactivés sans leur option."""
from pathlib import Path
import struct
P=Path('work/sample-wizard-main');p=P/'src/model_tg.s';s=p.read_text();assert 'av_shared_key:' not in s
old='''sm_sampler_key_stock:
    moveml %sp@,%d1/%a1
    lea %sp@(8),%sp
    tstl %d0
    rts
'''
new='''sm_sampler_key_stock:
    moveml %sp@,%d1/%a1
    lea %sp@(8),%sp
    tstl av_perf_on
    bne.w av_shared_key
    tstl %d0
    rts
av_shared_key:
    cmpil #13,%d0
    beq.w kh_mod
    movel %d0,%d1
    subil #16,%d1
    cmpil #15,%d1
    bls.w kh_slide
    tstl %d0
    rts
'''
assert s.count(old)==1;s=s.replace(old,new)
# Le chemin clavier Wizard lui-même garde aussi les slides optionnelles.
s=s.replace('    blsw    kh_out\n', '    bhiw    av_shared_not_trig\n    tstl av_perf_on\n    bnew kh_slide\n    braw kh_out\nav_shared_not_trig:\n',1)
# Capturer la note une fois, juste après le constructeur de trig, avant slides.
old='''    cmpil   #MAX_TRK,%d2
    bccw    sq_out
    lea.l   SLD_BASE,%a2
'''
new='''    cmpil   #MAX_TRK,%d2
    bccw    sq_out
    tstl %sp@
    beq.w av_seq_note_done
    movel %sp@(60),%d0
    cmpil #63,%d0
    bhi.w av_seq_note_done
    moveal %sp@(52),%a0
    movel %d2,%d1
    muluw #722,%d1
    addal %d1,%a0
    lea %a0@(580),%a1
    mvsb %a1@(0,%d0:l),%d0
    bpl.w av_seq_note_store
    mvsb %a0@(712),%d0
av_seq_note_store:
    lea live_note,%a1
    moveb %d0,%a1@(0,%d2:l)
av_seq_note_done:
    lea.l   SLD_BASE,%a2
'''
assert s.count(old)==1;s=s.replace(old,new)
old='''    nop                          | slides délégués au support optionnel
    lea.l   ld_busy,%a0
'''
new='''    tstl av_perf_on
    beq.w av_ui_no_slide
    jsr sld_tick
av_ui_no_slide:
    lea.l   ld_busy,%a0
'''
assert s.count(old)==1;s=s.replace(old,new)
old='''    jsr     sm_ui_service
lh_out:'''
new='''    jsr     sm_ui_service
    moveal av_wave_tick,%a0
    tstl %a0
    beq.w lh_out
    movew %sr,%d0
    andil #0x700,%d0
    bne.w lh_out
    jsr %a0@
lh_out:'''
assert s.count(old)==1;s=s.replace(old,new)
s+='''
| Un seul propriétaire des hooks clavier, note et YES du navigateur.
 .globl av_seq_hook,av_live_hook,av_pad_hook,av_yes_hook
av_seq_hook:
 tstl av_perf_on
 bne.w sld_seq
 jmp sm_seq_capture
av_live_hook:
 tstl av_perf_on
 bne.w note_on_hook
 jmp sm_live_note_capture
av_pad_hook:
 movel %sp@(4),%d0
 bra.w av_wave_route_pad
av_yes_hook:
 movel %sp@(12),%d0
 bra.w av_wave_route_yes
av_wave_route_pad:
 lea %sp@(-16),%sp
 moveml %d0-%d1/%a0-%a1,%sp@
 bsr av_is_wave
 movel %d0,%sp@
 moveml %sp@,%d0-%d1/%a0-%a1
 lea %sp@(16),%sp
 tstl %d0
 beq.w pad_load_hook
 moveal av_wave_note,%a0
 jmp %a0@
av_wave_route_yes:
 lea %sp@(-16),%sp
 moveml %d0-%d1/%a0-%a1,%sp@
 bsr av_is_wave
 movel %d0,%sp@
 moveml %sp@,%d0-%d1/%a0-%a1
 lea %sp@(16),%sp
 tstl %d0
 beq.w preset_fail_hook
 moveal av_wave_yes,%a0
 jmp %a0@
av_is_wave:
 cmpil #5,%d0
 bhi.w av_not_wave
 moveal 0x40a78888,%a0
 tstl %a0
 beq.w av_not_wave
 muluw #100,%d0
 addal %d0,%a0
 mvzb %a0@(66),%d0
 cmpl av_wave_machine,%d0
 bne.w av_not_wave
 moveq #1,%d0
 rts
av_not_wave:
 moveq #0,%d0
 rts
 .globl av_wave_tick,av_wave_note,av_wave_yes,av_wave_machine
 .balign 4
av_wave_tick: .long 0
av_wave_note: .long 0
av_wave_yes: .long 0
av_wave_machine: .long -1
'''
p.write_text(s)
# Y du framebuffer et Y des bitmaps natifs sont orientés vers le haut.
# Retourner les pixels de l'illustration afin que la pointe soit en haut.
for suffix,w,h in [('A_48x33',48,33),('B_34x34',34,34)]:
 p=P/'src/sampler_icons'/('sampler_icon_'+suffix+'.bin');b=p.read_bytes();out=bytearray(len(b))
 for x in range(w):
  for y in range(h):
   bit=struct.unpack_from('>I',b,x*8+(y//32)*4)[0]&(1<<(31-y%32))
   if bit:
    yy=h-1-y;at=x*8+(yy//32)*4;v=struct.unpack_from('>I',out,at)[0]|(1<<(31-yy%32));struct.pack_into('>I',out,at,v)
 p.write_bytes(out)
print('PASS sources partagées préparées ; chapeau orienté pour le dessin natif.')
