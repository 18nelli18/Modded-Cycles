"""Prototype privé : chemins stock inchangés aux deux entrées du sampler.

Ce fichier ne génère pas de recette flashable. Les autres hooks du sampler
restent à isoler ; ne pas installer le build Model-TG complet comme résultat.
"""
from pathlib import Path
import shutil
src=Path('../model-tg/src');out=Path('work/supermodel-sampler-prototype/src');shutil.copytree(src,out,dirs_exist_ok=True)
p=out/'model_tg.s';s=p.read_text()
pre='''sampler_pre:
    movel %d1,%fp@(60)
    mvsb %a2@(18),%d0
    cmpil #6,%d0
    beq.w sm_sampler_pre_full
    lea.l trk_mach,%a0
    movel %d0,%a0@(0,%d2:l:4)
    tstl %a3@
    beq.w sm_sampler_pre_idle
    jmp 0x400a7db0
sm_sampler_pre_idle:
    jmp 0x400a7de0
sm_sampler_pre_full:
'''
dispatch='''sampler_dispatch:
    cmpil #6,%d4
    beq.w sm_sampler_dispatch_full
    moveal %d6,%a0
    moveal %a0@(0,%d4:l:4),%a1
    movel %a2,%sp@-
    movel %fp,%sp@-
    movel %d1,%sp@-
    jsr %a1@
    movel %fp,%sp@-
    movel %d3,%sp@-
    lea.l 0x40118610,%a0
    moveal %a0@(0,%d4:l:4),%a1
    jsr %a1@
    lea.l %sp@(20),%sp
    jmp 0x400a7e24
sm_sampler_dispatch_full:
'''
for old,new in [('sampler_pre:\n',pre),('sampler_dispatch:\n',dispatch)]:
 assert s.count(old)==1,old;s=s.replace(old,new,1)
key='''key_hook:
    moveal %sp@(4),%a0
    movel %a0@(12),%d0
    lea %sp@(-8),%sp
    moveml %d1/%a1,%sp@
    | Les menus sampler ouverts gardent leur propre clavier.
    tstl sle_on
    bne.w sm_sampler_key_full
    | Finir une paire de touches commencée sur Wizard, même après changement de piste.
    cmpil #13,%d0
    bne.s sm_key_preset_release
    tstl set_held
    bne.w sm_sampler_key_full
sm_key_preset_release:
    cmpil #5,%d0
    bne.s sm_key_track
    tstl kh_eaten
    bne.w sm_sampler_key_full
sm_key_track:
    movel 0x40a700c4,%d1
    cmpil #5,%d1
    bhi.w sm_sampler_key_stock
    moveal 0x40a78888,%a1
    tstl %a1
    beq.w sm_sampler_key_stock
    muluw #100,%d1
    addal %d1,%a1
    moveq #0,%d1
    moveb %a1@(66),%d1
    cmpil #6,%d1
    beq.w sm_sampler_key_full
sm_sampler_key_stock:
    moveml %sp@,%d1/%a1
    lea %sp@(8),%sp
    tstl %d0
    rts
sm_sampler_key_full:
    moveml %sp@,%d1/%a1
    lea %sp@(8),%sp
'''
assert s.count('key_hook:\n')==1;s=s.replace('key_hook:\n',key,1)
# Le sampler seul n'installe pas de slides implicitement.
old='    jsr     sld_apply             | a slide moves this track s parameters,'
assert s.count(old)==1;s=s.replace(old,'    nop                          | slides délégués au support optionnel,',1)
p.write_text(s)
for old,new in [
 ('    tstl    rtg_on\n    bnew    kh_rtg                | the retrig page: the trig keys are its\n',''),
 ('    blsw    kh_slide\n','    blsw    kh_out\n'),
 ('    cmpil   #KEY_RETRIG,%d0\n    beqw    kh_rt\n    cmpil   #MM_KEY_RETURN,%d0\n    beqw    kh_rx\n',''),
 ('    jsr     sys_tick\n','    nop                          | pas de menu système Model-TG\n'),
 ('    bsr     prof_end              | the block is rendered: how long did it take\n','    nop                          | pas de profileur global\n'),
 ('    jsr     sld_tick              | slide trigs double-blink\n','    nop                          | slides délégués au support optionnel\n')]:
 assert old in s,old;s=s.replace(old,new)
# Le décodage stéréo reste nécessaire ; les effets master TG ne le sont pas.
for old in [
 '    jsr     rtg_audio             | retrig: record, and repeat, before the mix\n',
 '    moveq   #0,%d0                | retrig: the returns as the L pass hears them\n    jsr     rtg_fxpass\n',
 '    moveq   #1,%d0                | ...and the R pass\n    jsr     rtg_fxpass\n']:
 assert s.count(old)==1;s=s.replace(old,'    nop                          | pas de FX master Model-TG\n',1)
# Les deux entrées UI partagent les mêmes protections IPL/réentrance.
# Le clavier natif reste exécuté avant le service, même si celui-ci décline.
tick_start=s.index('tick_hook:\n');tick_end=s.index('\n| ---- the clock:',tick_start)
tick=s[tick_start:tick_end]
a=tick.index('    jsr     atk_watch\n');b=tick.index('    moveml  %sp@,%d0-%d7/%a0-%a3\n',a)
tick=tick[:a]+'    jsr     sm_ui_service\n'+tick[b:]
s=s[:tick_start]+tick+s[tick_end:]
led_start=s.index('led_hook:\n');led_end=s.index('\n| ================= Scale Lock',led_start)
led=s[led_start:led_end]
a=led.index('    | Only at IPL 0:');b=led.index('lh_out:\n',a)
service=led[a:b].replace('lh_out','sm_ui_out')+'sm_ui_out:\n    rts\n'
led=led[:a]+'    jsr     sm_ui_service\n'+led[b:]
s=s[:led_start]+led+'\nsm_ui_service:\n'+service+s[led_end:]
# Refuser un inode vide/surdimensionné avant le décalage en octets.
old='    movel   %d4,%d3\n    lsll    #8,%d3\n    lsll    #6,%d3                | bytes = chunks * 16384\n'
new='    tstl    %d4\n    beq.w   lb_fmt\n    cmpil   #MAX_FILE/16384,%d4\n    bhi.w   lb_fmt\n'+old
assert s.count(old)==1;s=s.replace(old,new,1)
# Device Config ne reçoit que Transfer, pas la page System/profilage TG.
old='    pea     sys_row               | and after it, System: the load page\n    movel   %a2,%sp@-\n    jsr     lm_add_row\n    addql   #8,%sp\n'
assert s.count(old)==1;s=s.replace(old,'',1)
# Le codec supplémentaire n'écrit que les sons Sampler, pas les sons stock.
for name,offset in [('snd_save_post',4),('snd_load_post',0)]:
 marker=name+':\n'
 guard=f'''{name}:
    moveal %sp@({offset}),%a1
    mvzb %a1@(38),%d1
    cmpil #6,%d1
    beq.w sm_{name}_full
    addql #8,%sp
    rts
sm_{name}_full:
'''
 assert s.count(marker)==1;s=s.replace(marker,guard,1)
p.write_text(s+'\n    .globl live_note\n')
print('Prototype source : gardes machine et dispatch stock ; aucune recette flashable.')

# Les deux petites tables d'icônes appartiennent au sampler, sans allocation
# dans le chemin de dessin ni publication d'un pointeur nul.
p=out/'phase1.s';phase=p.read_text()
for table,old in [
 ('sm_icons_a', '    movel   #196,-(%a7)            | 7 * 0x1c\n    jsr     0x40080064             | d0 = new heap buffer\n    addql   #4,%a7\n'),
 ('sm_icons_b', '    movel   #196,-(%a7)\n    jsr     0x40080064\n    addql   #4,%a7\n')]:
 assert phase.count(old)==1;phase=phase.replace(old,'    movel   #'+table+',%d0\n',1)
phase+='\n    .align 2\nsm_icons_a: .space 196\nsm_icons_b: .space 196\n'
old='    jmp     log_trampoline_tail_patch   | sampler_track_table_standalone.s:\n                                        | bsr update_sampler_table ; jmp 0x4001407a\n'
assert phase.count(old)==1;phase=phase.replace(old,'    jmp     0x4001407a          | pas de table diagnostic inutilisée\n',1)
p.write_text(phase)

# Nom court de Sample Wizard dans le panneau machine (six caractères).
p=out/'model_tg.s';text=p.read_text()
for old,new in [('nm_s_mach:     .asciz "Sample"','nm_s_mach:     .asciz "Wizard"'),('mach_nbuf:     .asciz "Sample"','mach_nbuf:     .asciz "Wizard"')]:
 assert text.count(old)==1;text=text.replace(old,new,1)
p.write_text(text)
p=out/'phase1.s';text=p.read_text();assert text.count('.ascii  "Sample"')==1;text=text.replace('.ascii  "Sample"','.ascii  "Wizard"',1);p.write_text(text)
