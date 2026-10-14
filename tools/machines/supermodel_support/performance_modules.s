| Copyright (c) 2026 TinyGregAudio, MIT ; voir LICENSE-Model-TG.
MAX_TRK=6
kh_mod:
    movel   %a0@(16),%d1
    btst    #5,%d1
    bnew    kh_eat                | the long press: no Save pattern prompt
    lea.l   set_held,%a1
    btst    #0,%d1
    beqs    kh_m_up
    btst    #3,%d1
    bnes    kh_m_dn
    clrl    mod_used              | a fresh press: no chord yet
kh_m_dn:
    moveq   #1,%d1
    movel   %d1,%a1@
    rts
kh_m_up:
    clrl    %a1@
    tstl    mod_used
    bnes    kh_eat                | after a chord: no Config Menu
    rts


kh_slide:
    lea.l   %sp@(-12),%sp
    moveml  %d2/%a2-%a3,%sp@
    movea.l %a0,%a2               | the event
    lea.l   sld_tp,%a3
    lea.l   %a3@(0,%d1:l:4),%a3   | this key s taken press; +64 its release
    moveq   #1,%d2
    lsll    %d1,%d2               | its bit in sld_keys: a press taken
    btst    #0,%a2@(19)
    beqs    ksd_up
    cmpal   %a3@,%a2              | a press: a later read of the taken one?
    bnes    ksd_fresh
    movel   sld_keys,%d0
    andl    %d2,%d0
    bnes    ksd_eat
ksd_fresh:
    clrl    %a3@(64)              | a new press: no release is ours any more
    movel   %d2,%d0
    notl    %d0
    andl    %d0,sld_keys
    clrl    %a3@
    tstl    set_held
    beqs    ksd_pass              | Settings is up: an ordinary press
    btst    #3,%a2@(19)
    bnes    ksd_pass              | auto-repeat
    movel   %a2,%a3@              | taken: this press...
    orl     %d2,sld_keys
    moveq   #1,%d0
    movel   %d0,mod_used          | ...and Settings release is no Config Menu
    movel   %d1,%d0
    jsr     sld_toggle
    bras    ksd_eat
ksd_up:
    movel   sld_keys,%d0          | a release: the taken press s, or a later
    andl    %d2,%d0               | read of that release
    bnes    ksd_rel
    cmpal   %a3@(64),%a2
    beqs    ksd_eat
    bras    ksd_pass
ksd_rel:
    movel   %d2,%d0
    notl    %d0
    andl    %d0,sld_keys
    movel   %a2,%a3@(64)
ksd_eat:
    movel   %a2@(16),%d1
    oril    #8,%d1
    movel   %d1,%a2@(16)
    moveml  %sp@,%d2/%a2-%a3
    lea.l   %sp@(12),%sp
    moveq   #0,%d0
    rts
ksd_pass:
    movel   %a2@(12),%d0          | the code, as the accessor returns it
    moveml  %sp@,%d2/%a2-%a3
    lea.l   %sp@(12),%sp
    tstl    set_held              | and on to the Settings chords, as before
    bnew    kh_out
    rts

    | ---- the slice editor is up: trig keys 1..16 play slices 1..16 of the
    | edited sample (with FUNC held, 17..32) and select them. The note starts
    | as the track pad starts one (0x4001d05e), without its recording: the core
    | note-on 0x4008171e(track, note, velocity, 0x40, 0, -1, -1), note 52 +
    | slice; the release ends it (0x4008145e(track, note, 0x40)). Every read
    | of an event carries the same flags - a key's note is kept while it
    | sounds, so each press plays once - and the key is taken, as the retrig
    | page takes it. FUNC passes on as usual.

SLIDE_BIT = 0x1000
| sld_toggle(d0 = trig key 0..15), from Settings + the key: the step it means - the grid's page
| (0x400124b8 of the UI context's track view) x 16 + the key, as the grid's
| own key handler works it out (0x4002244a) - on the selected track's pattern
| data (0x4000f23e). No trig there: one, as the grid makes it (0x40017b48),
| marked slide. A trig: its slide mark toggled. Through the stock flag setter
| 0x400179ce(data, step, mask, on), which tells the pattern's observers.
| Keeps d2-d7, a2-a6.
sld_toggle:
    lea.l   %sp@(-16),%sp
    moveml  %d2-%d4/%a2,%sp@
    movel   %d0,%d3               | the key
    jsr     0x400cf866
    movel   %d0,%d4               | the UI context
    movel   %d0,%sp@-
    jsr     0x4000eb90
    movel   %d0,%sp@-
    jsr     0x400124b8            | the page shown
    addql   #8,%sp
    lsll    #4,%d0
    addl    %d0,%d3               | the step
    movel   %d4,%sp@-
    jsr     0x4000f23e            | the selected track s pattern data
    addql   #4,%sp
    tstl    %d0
    beqw    sdt_out
    movea.l %d0,%a2
    movel   %a2,%sp@-
    jsr     0x40016402            | its length
    addql   #4,%sp
    cmpl    %d3,%d0
    blew    sdt_out               | past its last step
    pea     1
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x400157d6            | a trig there?
    lea.l   %sp@(12),%sp
    moveq   #1,%d2                | slide on...
    tstb    %d0
    bnes    sdt_has
    pea     1                     | ...on a new trig
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x40017b48
    lea.l   %sp@(12),%sp
    bras    sdt_set
sdt_has:
    pea     SLIDE_BIT
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x400157d6
    lea.l   %sp@(12),%sp
    tstb    %d0
    beqs    sdt_set
    moveq   #0,%d2                | ...or off, if it was a slide trig
sdt_set:
    movel   %d2,%sp@-
    pea     SLIDE_BIT
    movel   %d3,%sp@-
    movel   %a2,%sp@-
    jsr     0x400179ce
    lea.l   %sp@(16),%sp
    pea     msg_slon
    tstl    %d2
    bnes    sdt_pop
    addql   #4,%sp
    pea     msg_sloff
sdt_pop:
    jsr     show_popup
    addql   #4,%sp
sdt_out:
    moveml  %sp@,%d2-%d4/%a2
    lea.l   %sp@(16),%sp
    rts

| ---- the double-blink ----
| The grid's step-light painter (0x40021e..) sets each key's light through
| 0x40005f86(lights, 0x4000608c(key), mode, 0x404a8cb8), the first mode set
| in a frame winning; the frame then turns every light left unset off
| (0x40006044), and the playhead is painted after the trigs. Lights are only
| repainted when the root view's flag (+33, 0x40076bfa) asks - 0x40076c04
| sets it. So sld_led paints a slide trig as the painter would, except in
| sld_phase's off moments, when it leaves it unset (off, or the playhead);
| and sld_tick, on the LED clock, asks for a repaint whenever that phase
| changes.
| sld_led: in place of 0x40021f56..0x40021f6b - key d3's light, at mode a5,
| on the lights d2. The step is the page's first (the caller's sp@(56)) +
| the key, on the track's pattern data a3. Keeps d2-d7, a2-a6.
sld_led:
    movel   %sp@(60),%d0
    addl    %d3,%d0               | the step
    pea     SLIDE_BIT
    movel   %d0,%sp@-
    movel   %a3,%sp@-
    jsr     0x400157d6            | a slide trig?
    lea.l   %sp@(12),%sp
    tstb    %d0
    beqs    sll_set
    bsr     sld_phase
    tstl    %d0
    bnes    sll_out               | its off moment: left unset
sll_set:
    movel   %d3,%sp@-
    jsr     0x4000608c            | the key s light
    addql   #4,%sp
    pea     0x404a8cb8
    movel   %a5,%sp@-
    movel   %d0,%sp@-
    movel   %d2,%sp@-
    jsr     0x40005f86
    lea.l   %sp@(16),%sp
sll_out:
    rts
| sld_phase -> d0 = 1 in a slide trig's off moments: a quick double-blink,
| two 80-block gaps (~53 ms) 80 blocks apart, every 1024 blocks (~0.68 s).
| Keeps d1-d7.
sld_phase:
    movel   blk_clk,%d0
    andil   #1023,%d0
    cmpil   #80,%d0
    bcss    sph_off
    cmpil   #160,%d0
    bcss    sph_on
    cmpil   #240,%d0
    bcss    sph_off
sph_on:
    moveq   #0,%d0
    rts
sph_off:
    moveq   #1,%d0
    rts
| sld_tick, on the LED clock: a repaint of the lights whenever the blink's
| phase changes. Clobbers d0, d1, a0, a1.
sld_tick:
    bsr     sld_phase
    cmpl    sld_lph,%d0
    beqs    slk_out
    movel   %d0,sld_lph
    jsr     0x400d0974
    movel   %d0,%sp@-
    jsr     0x400060d8            | the root view
    addql   #4,%sp
    tstl    %d0
    beqs    slk_out
    movel   %d0,%sp@-
    jsr     0x40076c04            | its lights want repainting
    addql   #4,%sp
slk_out:
    rts

| sld_reset: in place of 0x400169f0's first two instructions - the stock reset
| of a step's trig settings, run whenever its trig goes (and when a step or
| track is cleared). Its slide mark goes too, or a new trig placed there later
| would come back as a slide trig. (data, step); d0/d1/a0/a1 are free here.
sld_reset:
    movea.l %sp@(4),%a0
    movea.l %a0@,%a1
    movel   %a0,%sp@-
    movea.l %a1@(40),%a1
    jsr     %a1@                  | its pattern data
    addql   #4,%sp
    tstl    %d0
    beqs    srs_go
    movea.l %d0,%a0
    movel   %sp@(8),%d1
    cmpil   #63,%d1
    bhis    srs_go
    addl    %d1,%d1
    movew   %a0@(0,%d1:l),%d0
    andil   #~SLIDE_BIT,%d0
    movew   %d0,%a0@(0,%d1:l)
srs_go:
    lea.l   %sp@(-12),%sp         | the two instructions the jump replaced
    moveml  %d2-%d3/%a2,%sp@
    jmp     0x400169f8

| ---- the slide ----
| A trig P whose next trig S (on, wrapping at the track s length) is a slide
| trig glides every parameter whose value differs between them, from P s value
| to S s, over the whole gap: it arrives as S plays. A value is the step s
| p-lock or, unlocked, its sound s (a sound lock s sound, as the builder takes
| it). Only continuous parameters: SLD_ELIG leaves out the LFO s multiplier,
| destination, waveform and trig mode (words 2, 4, 5, 7), the machine (9) and
| Gate (16).
| The audio side keeps each track s parameters in a table the OS smooths
| every block (0x40058474: targets -> 16.16 state at 0x800011e8 -> words);
| a trig s sound and locks jump the state (0x40058308, 0x400583da). The
| machine s parameter call reads the smoothed words - the voice loop s a2 -
| every block, and so do Attack, Filter and Resonance (sampler_pre), so
| sld_apply writes the glide over them first thing in sampler_pre. The
| state underneath is left alone, so where a glide lets go the OS s own value
| is back the next block.
| Fields, a long per track at SLD_BASE + 4 x track:
SL_PND  = 0      | a glide is armed for the track s next trig
SL_PDUR = 24     | ...its length in blocks
SL_PMSK = 48     | ...which words move
SL_PCLK = 72     | ...and when it was armed
SL_ACT  = 96     | a glide is running
SL_T0   = 120    | ...from this block
SL_DUR  = 144    | ...for this many
SL_MSK  = 168    | ...on these words
SL_LPUL = 192    | the voice s trig pulse, last block
SL_PFRE = 216    | armed while the sequencer was stopped: waits for Play
| and 26 words a buffer (64 bytes a track) at SLD_BASE + 64 x track:
SL_PST  = 256    | armed: from
SL_PEN  = 640    | armed: to
SL_AST  = 1024   | running: from
SL_AEN  = 1408   | running: to
SLD_ELIG = 0x03FEFD4A | words 1 3 6 8 10-15 17-25

| sld_seq: in place of `jsr 0x400548ce; lea %sp@(24),%sp` at both of the trig
| builder s calls, (track, pattern data, sounds, step, flag, out): the
| sequencer s, once a step for each playing track (0x400551a6), and
| 0x40055af4 s (0x40055bfa), which builds a track s current step and plays it
| at once - how the first step sounds when Play is pressed (seen in a log:
| that trig reached the voice with no sequencer build before it), and how an
| edit during playback is heard. Armed from an edit, a glide for a step that
| has already played never starts on the wrong trig: the next trig s own
| build, S s, clears it first. It runs the builder and returns what it did; meanwhile,
| when a trig fires that a slide trig follows, it arms the glide for that
| trig s voice. Pattern data per track t (722 bytes at + t x 722): step flags
| at +2 x step, sound lock at +644 + step; length at +713 and speed at +715
| when the pattern has a scale per track (+30667 = 1), else at +30662 and
| +30668. A speed is ticks a step (0x4010afa4, 24 a quarter: 6 is a 16th),
| so a step is ticks x 450,000 / tempo blocks - worked out, not measured, so
| the first round after Play glides like the rest. Locks
| at +4332 + t x 4385 + step x 68 + 2 x word (-1: none). A sound is 100 bytes,
| at sounds + 28 + t x 100 (a sound lock: sounds + 694 + lock x 100), its
| parameter words at +20.
sld_seq:
    movel   %sp@(24),%sp@-        | the builder s six arguments, again
    movel   %sp@(24),%sp@-
    movel   %sp@(24),%sp@-
    movel   %sp@(24),%sp@-
    movel   %sp@(24),%sp@-
    movel   %sp@(24),%sp@-
    jsr     0x400548ce
    lea.l   %sp@(24),%sp
    lea.l   %sp@(-44),%sp
    moveml  %d0/%d2-%d7/%a2-%a5,%sp@ | d0: the trig, or 0
    movel   %sp@(48),%d2          | the track
    cmpil   #MAX_TRK,%d2
    bccw    sq_out
    lea.l   SLD_BASE,%a2
    tstl    sld_init
    bnes    sq_go
    movea.l %a2,%a0
    moveq   #63,%d0
sq_clr:
    clrl    %a0@+
    subql   #1,%d0
    bpls    sq_clr
    moveq   #1,%d0
    movel   %d0,sld_init
sq_go:
    movel   %d2,%d7
    lsll    #2,%d7
    lea.l   %a2@(0,%d7:l),%a0     | the track s fields
    movel   %sp@(60),%d3          | the step
    movel   blk_clk,%d4
    tstl    %sp@
    beqw    sq_out                | no trig fired
    clrl    %a0@(SL_PND)
    movea.l %sp@(52),%a3          | the pattern data
    movea.l %sp@(56),%a4          | the sounds
    movel   #722,%d5
    mulsl   %d2,%d5
    lea.l   %a3@(0,%d5:l),%a1     | the track s step data
    tstb    %a3@(30667)
    beqs    sq_plen
    mvsw    %a1@(713),%d5         | its own length
    bras    sq_lok
sq_plen:
    mvsw    %a3@(30662),%d5       | the pattern s
sq_lok:
    moveq   #64,%d0
    cmpl    %d0,%d5
    blss    sq_lin
    movel   %d0,%d5
sq_lin:
    tstl    %d5
    beqw    sq_out
    movel   %d3,%d6               | the next trig: d6, d1 steps on
    moveq   #0,%d1
sq_scan:
    addql   #1,%d1
    cmpl    %d5,%d1
    bgew    sq_out                | none but this one
    addql   #1,%d6
    cmpl    %d5,%d6
    blts    sq_t
    moveq   #0,%d6
sq_t:
    movew   %a1@(0,%d6:l:2),%d0
    btst    #0,%d0
    beqs    sq_scan
    andil   #SLIDE_BIT,%d0
    beqw    sq_out                | not a slide trig
    moveq   #1,%d0
    cmpb    %a3@(30667),%d0
    bnes    sq_pspd
    mvsb    %a1@(715),%d0         | the track s speed
    bras    sq_spd
sq_pspd:
    mvsb    %a3@(30668),%d0       | the pattern s
sq_spd:
    moveq   #6,%d5
    cmpl    %d5,%d0
    blss    sq_sok
    moveq   #2,%d0                | not a speed: 1x
sq_sok:
    lea.l   0x4010afa4,%a5
    movel   %a5@(0,%d0:l:4),%d0   | ticks a step
    mulsl   %d1,%d0               | x the gap
    movel   #450000,%d5
    mulsl   %d5,%d0
    movel   0x40149310,%d5        | the tempo, 1/120 BPM
    beqw    sq_out
    divul   %d5,%d0               | -> blocks
    cmpil   #200000,%d0
    blss    sq_dok
    movel   #200000,%d0
sq_dok:
    tstl    %d0
    beqw    sq_out
    movel   %d0,%a0@(SL_PDUR)
    movel   %d4,%a0@(SL_PCLK)
    movel   %d2,%d0
    lsll    #6,%d0
    lea.l   %a2@(0,%d0:l),%a5     | the track s buffers
    lea.l   %a5@(SL_PST),%a0
    movel   %d3,%d0
    bsr     sld_vals              | from this trig s values
    lea.l   %a5@(SL_PEN),%a0
    movel   %d6,%d0
    bsr     sld_vals              | to the slide trig s
    lea.l   %a5@(SL_PST),%a0
    lea.l   %a5@(SL_PEN),%a1
    movel   #SLD_ELIG,%d5
    moveq   #0,%d6                | the words that move
    moveq   #0,%d4
sq_m:
    lsrl    #1,%d5
    bccs    sq_mn
    mvsw    %a0@(0,%d4:l:2),%d0
    mvsw    %a1@(0,%d4:l:2),%d1
    cmpl    %d1,%d0
    beqs    sq_mn
    bset    %d4,%d6
sq_mn:
    addql   #1,%d4
    tstl    %d5
    bnes    sq_m
    tstl    %d6
    beqw    sq_out                | nothing differs
    lea.l   %a2@(0,%d7:l),%a0
    movel   %d6,%a0@(SL_PMSK)
    | Armed by 0x40055af4 - which builds a track s step in advance on a project
    | load, after a stop (several times over) and on an edit - this may be the
    | trig Play sounds first, and Play itself builds nothing (logged: the load s
    | arm, minutes old by Play, was thrown away as stale). So it has no age
    | limit (SL_PFRE): it waits for its trig, and the next trig s own build
    | replaces it if that trig never sounds. The sequencer s arms keep the
    | limit, so one left over from a stop is never started by the next Play.
    moveq   #0,%d0
    movel   %sp@(44),%d1
    cmpil   #0x400551ac,%d1
    beqs    sq_fre
    moveq   #1,%d0
sq_fre:
    movel   %d0,%a0@(SL_PFRE)
    | Does this trig sound a note? Its bit 7 when bit 11 says the step chooses,
    | else the track s (+710), as the builder works it out. A trigless trig
    | has no voice trig to start on: SL_PND = 2 starts it at once.
    movel   #722,%d0
    mulsl   %d2,%d0
    lea.l   %a3@(0,%d0:l),%a1
    movew   %a1@(0,%d3:l:2),%d0
    btst    #11,%d0
    bnes    sq_own
    movew   %a1@(710),%d0
sq_own:
    moveq   #1,%d1
    btst    #7,%d0
    bnes    sq_arm
    moveq   #2,%d1
sq_arm:
    movel   %d1,%a0@(SL_PND)      | armed
sq_out:
    moveml  %sp@,%d0/%d2-%d7/%a2-%a5
    lea.l   %sp@(44),%sp
    movea.l %sp@+,%a1
    lea.l   %sp@(24),%sp          | the caller s arguments, as its lea did
    jmp     %a1@

| sld_vals(d0 = step) -> the step s 26 parameter words at a0, each its lock or
| its sound s; a1 = the track s step data, a3 = the pattern data, a4 = the
| sounds, d2 = the track. Clobbers d0, d1, a0.
sld_vals:
    lea.l   %sp@(-16),%sp
    moveml  %d3-%d4/%a2/%a5,%sp@
    movel   %d0,%d3
    lea.l   %a1@(644),%a5
    mvsb    %a5@(0,%d3:l),%d0     | its sound lock, or -1
    bmis    svl_trk
    moveq   #100,%d1
    mulsl   %d0,%d1
    lea.l   %a4@(0,%d1:l),%a5
    tstb    %a5@(698)
    beqs    svl_trk
    lea.l   %a5@(694),%a5         | the locked sound, as the builder takes it
    bras    svl_snd
svl_trk:
    moveq   #100,%d1
    mulsl   %d2,%d1
    lea.l   %a4@(0,%d1:l),%a5
    lea.l   %a5@(28),%a5          | the track s own
svl_snd:
    lea.l   %a5@(20),%a5          | its parameter words
    movel   #4385,%d0
    mulsl   %d2,%d0
    moveq   #68,%d1
    mulsl   %d3,%d1
    addl    %d1,%d0
    lea.l   %a3@(0,%d0:l),%a2
    lea.l   %a2@(4332),%a2        | the step s locks
    moveq   #25,%d4
svl_k:
    mvsw    %a2@+,%d0
    moveq   #-1,%d1
    cmpl    %d1,%d0
    bnes    svl_have
    mvsw    %a5@,%d0
svl_have:
    movew   %d0,%a0@+
    addql   #2,%a5
    subql   #1,%d4
    bpls    svl_k
    moveml  %sp@,%d3-%d4/%a2/%a5
    lea.l   %sp@(16),%sp
    rts

| sld_apply, first in sampler_pre: d2 = the track, a2 = its smoothed
| parameter words, fp = its voice. On a trig - the rising edge of +0x34, which
| can stay up for more than one block - the glide in flight has arrived and
| stops, and one armed for this trig starts (one armed on a trigless trig,
| which has no edge, starts at once). A second edge in a glide s first
| half is the same note (a pulse twice over as playback starts, a retrig)
| and leaves it running: only S, the length away, ends it. A running glide writes
| from + (to - from) x elapsed / length over its words, and holds the end
| until the next trig - a quarter of the length more at most, for a slide trig
| whose condition failed or a stopped pattern. Keeps all but d0.
sld_apply:
    tstl    sld_init
    beqw    sap_rts
    cmpil   #MAX_TRK,%d2
    bccw    sap_rts
    lea.l   %sp@(-28),%sp
    moveml  %d1/%d3-%d5/%a0-%a1/%a3,%sp@
    movel   %d2,%d0
    lsll    #2,%d0
    lea.l   SLD_BASE,%a0
    addal   %d0,%a0               | the track s fields
    movel   %d2,%d0
    lsll    #6,%d0
    lea.l   SLD_BASE,%a1
    addal   %d0,%a1               | ...and buffers
    movel   %fp@(0x34),%d1
    movel   %a0@(SL_LPUL),%d3
    movel   %d1,%a0@(SL_LPUL)
    tstl    %d1
    beqw    sap_chk
    tstl    %d3
    bnew    sap_chk               | the same pulse, still up
    tstl    %a0@(SL_ACT)
    beqs    sap_new
    movel   blk_clk,%d1
    subl    %a0@(SL_T0),%d1
    movel   %a0@(SL_DUR),%d3
    lsrl    #1,%d3
    cmpl    %d3,%d1
    bcsw    sap_chk               | early in the glide: the same note
sap_new:
    clrl    %a0@(SL_ACT)
    tstl    %a0@(SL_PND)
    beqw    sap_out
| sap_start: the armed glide starts - on its trig s edge, or (SL_PND = 2,
| armed on a trigless trig, which sounds no note) the block after it is armed.
sap_start:
    movel   blk_clk,%d1
    movel   %a0@(SL_PDUR),%d4
    tstl    %a0@(SL_PFRE)
    beqs    sap_stl
    movel   0x40a78874,%d3        | armed in advance, for Play s first trig:
    orl     0x40a7883c,%d3        | no age limit, but only while the OS says
    beqw    sap_out               | it plays (0x4005481a s test, set as Play
                                  | is pressed) - not a note played on the
                                  | keys while stopped
    bras    sap_go
sap_stl:
    movel   %d1,%d3
    subl    %a0@(SL_PCLK),%d3
    cmpl    %d4,%d3
    bcss    sap_go
    clrl    %a0@(SL_PND)
    braw    sap_out               | armed too long ago: not this trig s
sap_go:
    clrl    %a0@(SL_PND)
    movel   %d1,%a0@(SL_T0)
    movel   %d4,%a0@(SL_DUR)
    movel   %a0@(SL_PMSK),%d1
    movel   %d1,%a0@(SL_MSK)
    lea.l   %a1@(SL_PST),%a3
    lea.l   %a1@(SL_AST),%a1
    moveq   #12,%d3               | armed -> running, from and to
sap_cp:
    movel   %a3@(SL_PEN-SL_PST),%d1
    movel   %d1,%a1@(SL_AEN-SL_AST)
    movel   %a3@+,%a1@+
    subql   #1,%d3
    bpls    sap_cp
    moveq   #1,%d1
    movel   %d1,%a0@(SL_ACT)
    movel   %d2,%d0
    lsll    #6,%d0
    lea.l   SLD_BASE,%a1
    addal   %d0,%a1
    bras    sap_run
sap_chk:
    moveq   #2,%d1
    cmpl    %a0@(SL_PND),%d1
    beqw    sap_start             | armed on a trigless trig: go now
sap_run:
    tstl    %a0@(SL_ACT)
    beqw    sap_out
    movel   blk_clk,%d3
    subl    %a0@(SL_T0),%d3       | blocks since the trig
    movel   %a0@(SL_DUR),%d4
    movel   %d4,%d1
    lsrl    #2,%d1
    addl    %d4,%d1
    addil   #16,%d1
    cmpl    %d1,%d3
    bcss    sap_hold
    clrl    %a0@(SL_ACT)          | no trig came: let go
    bras    sap_out
sap_hold:
    cmpl    %d4,%d3
    bcss    sap_fr
    movel   %d4,%d3
sap_fr:
    moveq   #14,%d1
    lsll    %d1,%d3
    divul   %d4,%d3               | how far, 0..16384
    movel   %a0@(SL_MSK),%d5
    lea.l   %a1@(SL_AST),%a3
    lea.l   %a1@(SL_AEN),%a1
    moveq   #0,%d4                | 2 x the word
sap_k:
    lsrl    #1,%d5
    bccs    sap_nx
    mvsw    %a3@(0,%d4:l),%d0
    mvsw    %a1@(0,%d4:l),%d1
    subl    %d0,%d1
    mulsl   %d3,%d1
    asrl    #7,%d1
    asrl    #7,%d1
    addl    %d0,%d1
    movew   %d1,%a2@(0,%d4:l)
sap_nx:
    addql   #2,%d4
    tstl    %d5
    bnes    sap_k
sap_out:
    moveml  %sp@,%d1/%d3-%d5/%a0-%a1/%a3
    lea.l   %sp@(28),%sp
sap_rts:
    rts


show_popup:
    linkw   %fp,#-28
    moveml  %d2-%d3/%a2,%sp@
    movel   0x40fe4178,%d0
    beqw    sp_out                | popup machinery not up yet
    lea.l   0x400802e0,%a2        | operator new
    movel   %fp,%d2
    addil   #-12,%d2
    pea     %fp@(-13)
    movel   %fp@(8),%sp@-         | our text
    movel   %d2,%sp@-
    jsr     0x400f980c
    lea.l   %sp@(12),%sp
    pea     0x9c
    jsr     %a2@
    addql   #4,%sp
    movel   %d0,%d3
    movel   %d2,%sp@-
    movel   %d3,%sp@-
    jsr     0x400747c0
    addql   #8,%sp
    movel   popup_mult,%d0        | a longer stay: the fields Popup's init sets
    beqs    sp_std                | from its multiplier (0x40074676): +0x6c = N,
    movea.l %d3,%a0               | +0x60 (the ticks left, 0x400749b4 counts it
    movel   %d0,%a0@(0x6c)        | down and closes at 0) and +0x64 = 60 * N
    movel   %d0,%d1
    lsll    #6,%d0
    lsll    #2,%d1
    subl    %d1,%d0
    movel   %d0,%a0@(0x60)
    movel   %d0,%a0@(0x64)
sp_std:
    movel   %d3,%fp@(-8)
    clrl    %fp@(-4)
    pea     0x10
    jsr     %a2@
    addql   #4,%sp
    movea.l %d0,%a0
    moveq   #1,%d0
    movel   %d0,%a0@(4)
    movel   #0x400fbf40,%a0@
    movel   %d0,%a0@(8)
    movel   %d3,%a0@(12)
    movel   %a0,%fp@(-4)
    jsr     0x400d0974
    movel   %d0,%sp@-
    jsr     0x400060d8
    addql   #4,%sp
    clrl    %sp@-
    pea     %fp@(-8)
    movel   %d0,%sp@-
    jsr     0x4007700e
    lea.l   %sp@(12),%sp
    pea     %fp@(-4)
    jsr     0x400cf23c
    addql   #4,%sp
    movel   %d2,%sp@-
    jsr     0x400f7d5c
    addql   #4,%sp
sp_out:
    moveml  %fp@(-28),%d2-%d3/%a2
    unlk    %fp
    rts


snap_note:
    movel   %a5,%sp@-
    tstb    scale_state
    beqs    sn_done
    cmpil   #0x7f,%d3
    beqs    sn_done
    movel   %d3,%d5
    moveq   #52,%d6               | BASE: first trig pad's raw note
    subl    %d6,%d5               | signed offset from BASE
    moveq   #0,%d6
    moveb   scale_state,%d6
    subql   #1,%d6
    lea.l   fold_lengths,%a0
    moveb   %a0@(0,%d6:l),%d6     | N = notes in this scale
    divsw   %d6,%d5
    movel   %d5,%d1
    extl    %d1                   | quotient
    swap    %d5
    extl    %d5                   | remainder, may be negative
    tstl    %d5
    bges    sn_rem_ok
    addl    %d6,%d5               | floor-correct: remainder += N
    subql   #1,%d1                | and one octave down
sn_rem_ok:
    moveq   #0,%d6
    moveb   scale_state,%d6
    subql   #1,%d6
    muluw   #7,%d6                | fold table stride
    lea.l   fold_tables,%a5
    addal   %d6,%a5
    moveq   #0,%d6
    moveb   %a5@(0,%d5:l),%d6     | scale degree
    mulsw   #12,%d1
    addl    %d6,%d1
    addil   #48,%d1               | C_REF = C4. key_state is semitones above C,
                                  | so it MUST be added onto a multiple of 12,
                                  | not onto BASE - that was a real bug on
                                  | Samples (F major played A4 at pad 1).
    moveq   #0,%d6
    moveb   key_state,%d6
    addl    %d6,%d1               | key applied AFTER folding, so the root
    movel   %d1,%d3               | always stays on pad 1
sn_done:
    movel   %sp@+,%a5
    rts


| ---- Scale Lock menu: Samples -> Cycles address map -------------------
| Every one of these was resolved by wildcard byte matching and verified a
| second way; see docs/notes/scalelock_address_map.md.
    .equ ALLOC,            0x40080064
    .equ FREE_CLOSURE,     0x400cf044
    .equ MENUITEM_CTOR,    0x400734b0
    .equ MENUVIEW_ADDITEM, 0x40072ce6
    .equ FORMAT_STRING,    0x400f980c
    .equ TINYSTR_WRAP,     0x400f85bc
    .equ DRAW_FMT_A,       0x40072260
    .equ DRAW_FMT_B,       0x40072080
    .equ DRAW_TEXT,        0x40071a04
    .equ FREE_TINYSTR,     0x400f7d5c
    .equ SLOT2_MANAGER,    0x4002f188
    .equ SLOT2_INVOKER,    0x4002ec3a
    .equ GENERIC_MANAGER,  0x4002f136

|------------------------------------------------------------------
| slot1 invoker: label text. Clone of FUN_400300ec, own string.
| in: a0 = output buffer. out: d0 = a0.
|------------------------------------------------------------------
label_invoker:
    link.w  %a6,#-4
    move.l  %d2,-(%a7)
    pea.l   -1(%a6)
    pea.l   label_string
    move.l  %a0,%d2
    move.l  %a0,-(%a7)
    jsr     FORMAT_STRING
    lea.l   0xc(%a7),%a7
    move.l  %d2,%d0
    move.l  -8(%a6),%d2
    unlk    %a6
    rts

|------------------------------------------------------------------
| slot1 invoker for the SECOND (key) menu item. Identical shape to
| label_invoker, own string.
|------------------------------------------------------------------
label_invoker2:
    link.w  %a6,#-4
    move.l  %d2,-(%a7)
    pea.l   -1(%a6)
    pea.l   label_string2
    move.l  %a0,%d2
    move.l  %a0,-(%a7)
    jsr     FORMAT_STRING
    lea.l   0xc(%a7),%a7
    move.l  %d2,%d0
    move.l  -8(%a6),%d2
    unlk    %a6
    rts

|------------------------------------------------------------------
| slot3 invoker: value text render. Clone of FUN_400317b2's simple
| branch + shared drawing tail (params: a6+0x8..0x18 same as original).
| param_3=$10(a6) draw ctx, param_4=$14(a6) x, param_5=$18(a6) y.
|------------------------------------------------------------------
value_invoker:
    link.w  %a6,#-0x30
    move.l  #0x40fe4278,%d0
    movem.l %d2-%d4/%a2-%a5,(%a7)
    move.l  %d0,-0x10(%a6)
    lea.l   FREE_TINYSTR,%a2
    move.l  %a6,%d2
    subq.l  #8,%d2
    move.l  %a6,%d3
    addi.l  #-0x10,%d3

    moveq   #0,%d0
    move.b  scale_state,%d0
    lsl.l   #2,%d0
    lea.l   value_strings,%a0
    move.l  0(%a0,%d0.l),%d0

    move.l  %d0,-(%a7)
    move.l  %d3,-(%a7)
    jsr     TINYSTR_WRAP
    addq.l  #8,%a7

    pea.l   0x40140ab0
    move.l  %d2,-(%a7)
    move.l  -0x10(%a6),%d4
    jsr     DRAW_FMT_A
    move.l  %d4,-(%a7)
    movea.l 0x14(%a6),%a0
    pea.l   4
    move.l  0x18(%a6),-(%a7)
    lea.l   0x18(%a0),%a0
    move.l  %a0,-(%a7)
    move.l  %d2,-(%a7)
    move.l  0x10(%a6),-(%a7)
    jsr     DRAW_TEXT
    lea.l   0x1c(%a7),%a7
    move.l  %d2,(%a7)
    jsr     DRAW_FMT_B
    move.l  %d3,-(%a7)
    jsr     (%a2)
    addq.l  #8,%a7
    movem.l -0x30(%a6),%d2-%d4/%a2-%a5
    unlk    %a6
    rts

|------------------------------------------------------------------
| slot3 invoker for the SECOND (key) menu item. Identical shape to
| value_invoker, reads key_state / key_value_strings instead.
|------------------------------------------------------------------
value_invoker2:
    link.w  %a6,#-0x30
    move.l  #0x40fe4278,%d0
    movem.l %d2-%d4/%a2-%a5,(%a7)
    move.l  %d0,-0x10(%a6)
    lea.l   FREE_TINYSTR,%a2
    move.l  %a6,%d2
    subq.l  #8,%d2
    move.l  %a6,%d3
    addi.l  #-0x10,%d3

    moveq   #0,%d0
    move.b  key_state,%d0
    lsl.l   #2,%d0
    lea.l   key_value_strings,%a0
    move.l  0(%a0,%d0.l),%d0

    move.l  %d0,-(%a7)
    move.l  %d3,-(%a7)
    jsr     TINYSTR_WRAP
    addq.l  #8,%a7

    pea.l   0x40140ab0
    move.l  %d2,-(%a7)
    move.l  -0x10(%a6),%d4
    jsr     DRAW_FMT_A
    move.l  %d4,-(%a7)
    movea.l 0x14(%a6),%a0
    pea.l   4
    move.l  0x18(%a6),-(%a7)
    lea.l   0x18(%a0),%a0
    move.l  %a0,-(%a7)
    move.l  %d2,-(%a7)
    move.l  0x10(%a6),-(%a7)
    jsr     DRAW_TEXT
    lea.l   0x1c(%a7),%a7
    move.l  %d2,(%a7)
    jsr     DRAW_FMT_B
    move.l  %d3,-(%a7)
    jsr     (%a2)
    addq.l  #8,%a7
    movem.l -0x30(%a6),%d2-%d4/%a2-%a5
    unlk    %a6
    rts

|------------------------------------------------------------------
| slot4 invoker: ROTATION handler. Real precedent (objdump-verified,
| FUN_40030d74 - item1/"Len"'s own slot4) receives the rotation delta
| as a plain signed argument at $24(sp) at entry (its own prologue
| reserves+saves 24 bytes first, then reads $36(sp), i.e. entry_sp+12
| = the 3rd stack argument), takes sign(delta), and tail-jumps into
| the generic parameter-context setter (FUN_4000d3e4) to apply it -
| that setter needs a "parameter context" object (vtable+0x28/+0x10)
| our captured TrackMenuView pointer doesn't have the shape for, so
| we deliberately do NOT reuse that tail-jump (this is exactly what
| caused two real crashes earlier: assuming a captured pointer can
| stand in for that context). Instead we clone only the safe,
| argument-reading prologue, then apply the delta with our own
| already-working advance_scale (byte write, no generic-context
| machinery) and return normally.
|------------------------------------------------------------------
new_slot4_invoker:
    lea.l   -24(%a7),%a7
    movem.l %d2-%d4/%a2-%a4,(%a7)
    move.l  36(%a7),%d4
    moveq   #0,%d0
    tst.l   %d4
    beq.b   .zero
    bgt.b   .pos
    moveq   #-1,%d0
    bra.b   .apply
.pos:
    moveq   #1,%d0
.apply:
    jsr     advance_scale
.zero:
    | live redraw, take 4: FUN_40030d74 (our slot4 template) never
    | calls FUN_400750e2/FUN_40075c4e at all - those turned out to
    | just set unread "dirty" flags with no direct effect. It only
    | ever tail-jumps into the generic setter (FUN_4000d3e4), whose
    | OWN last step is "(**(code**)(*param_1+0x10))()" - calling
    | vtable slot 0x10 (notify) directly on the "current track"
    | accessor object itself. We already know this exact object has
    | a valid vtable, since its +0x28 slot (get-storage) has been
    | called successfully via this same chain throughout this whole
    | session (every getter/setter we've used does that). Call its
    | +0x10 slot the same way instead of the flag-setting functions.
    jsr     0x400cf866
    move.l  %d0,-(%a7)
    jsr     0x4000f208
    addq.l  #4,%a7
    move.l  %d0,-(%a7)
    jsr     0x4000d0dc
    addq.l  #4,%a7
    movea.l %d0,%a0
    movea.l (%a0),%a1
    movea.l 0x10(%a1),%a1
    move.l  %a0,-(%a7)
    jsr     (%a1)
    addq.l  #4,%a7
    movem.l (%a7),%d2-%d4/%a2-%a4
    lea.l   24(%a7),%a7
    rts

|------------------------------------------------------------------
| slot2 invoker: PRESS handler. Byte-identical clone of the real
| FUN_40030176 (objdump-verified) - this is confirmed (via real
| hardware test) to fire on encoder PRESS, toggling a boolean field
| on the captured object (our "a2") via a plain EOR + tail-jump to
| the real setter FUN_4007234c. We now leave this completely
| unmodified (no value-advance call): the real UX has press select
| the item without changing its value - the actual value changes
| happen in slot4 (rotation) below, matching the real framework's
| own item1 ("Len") which uses the exact same split.
|------------------------------------------------------------------
new_slot2_invoker:
    move.l  %d2,-(%a7)
    move.l  0xc(%a7),%d2
    move.l  %d2,-(%a7)
    jsr     0x400732f8
    addq.l  #4,%a7
    moveq   #1,%d1
    mvz.b   %d0,%d0
    move.l  %d2,8(%a7)
    eor.l   %d0,%d1
    move.l  %d1,12(%a7)
    move.l  (%a7)+,%d2
    jmp     0x400732ec

|------------------------------------------------------------------
| advance_scale: apply delta (d0, +1 or -1) to scale_state, wrapping
| within 0..4. note_trigger_hook reads scale_state live, so nothing
| else needs to happen here.
|------------------------------------------------------------------
advance_scale:
    moveq   #0,%d1
    move.b  scale_state,%d1
    add.l   %d0,%d1
    cmpi.l  #0,%d1
    bge.b   .not_neg
    moveq   #4,%d1
    bra.b   .store
.not_neg:
    cmpi.l  #4,%d1
    ble.b   .store
    moveq   #0,%d1
.store:
    move.b  %d1,scale_state
    rts

|------------------------------------------------------------------
| slot2 invoker for the SECOND (key) menu item: same pure-toggle
| shape as new_slot2_invoker, no value-advance call.
|------------------------------------------------------------------
new_slot2_invoker2:
    move.l  %d2,-(%a7)
    move.l  0xc(%a7),%d2
    move.l  %d2,-(%a7)
    jsr     0x400732f8
    addq.l  #4,%a7
    moveq   #1,%d1
    mvz.b   %d0,%d0
    move.l  %d2,8(%a7)
    eor.l   %d0,%d1
    move.l  %d1,12(%a7)
    move.l  (%a7)+,%d2
    jmp     0x400732ec

|------------------------------------------------------------------
| advance_key: apply delta (d0, +1 or -1) to key_state, wrapping
| within 0..11.
|------------------------------------------------------------------
advance_key:
    moveq   #0,%d1
    move.b  key_state,%d1
    add.l   %d0,%d1
    cmpi.l  #0,%d1
    bge.b   .not_neg2
    moveq   #11,%d1
    bra.b   .store2
.not_neg2:
    cmpi.l  #11,%d1
    ble.b   .store2
    moveq   #0,%d1
.store2:
    move.b  %d1,key_state
    rts

|------------------------------------------------------------------
| slot4 invoker for the SECOND (key) menu item. Same shape as
| new_slot4_invoker, calls advance_key instead of advance_scale.
|------------------------------------------------------------------
new_slot4_invoker2:
    lea.l   -24(%a7),%a7
    movem.l %d2-%d4/%a2-%a4,(%a7)
    move.l  36(%a7),%d4
    moveq   #0,%d0
    tst.l   %d4
    beq.b   .zero2
    bgt.b   .pos2
    moveq   #-1,%d0
    bra.b   .apply2
.pos2:
    moveq   #1,%d0
.apply2:
    jsr     advance_key
.zero2:
    jsr     0x400cf866
    move.l  %d0,-(%a7)
    jsr     0x4000f208
    addq.l  #4,%a7
    move.l  %d0,-(%a7)
    jsr     0x4000d0dc
    addq.l  #4,%a7
    movea.l %d0,%a0
    movea.l (%a0),%a1
    movea.l 0x10(%a1),%a1
    move.l  %a0,-(%a7)
    jsr     (%a1)
    addq.l  #4,%a7
    movem.l (%a7),%d2-%d4/%a2-%a4
    lea.l   24(%a7),%a7
    rts

|------------------------------------------------------------------
| install_scale_menu_item: hook target. Replaces the overwritten
| first instruction of FUN_40030874's epilogue. On entry, a2 still
| holds the TrackMenuView "this" pointer (unchanged from function
| entry). Builds TWO menu items (scale type, then key) and adds
| both, then resumes the original epilogue.
|
| Closure layout, stable base register a5 (0x80 bytes reserved: two
| 0x40-byte blocks, one per item):
|   item1 (scale): closure1 @ a5+0x00 (label) closure2 @ a5+0x10
|     (interact) closure3 @ a5+0x20 (value) closure4 @ a5+0x30 (null)
|   item2 (key):   same layout at a5+0x40..0x7f
| each closure: [0]=data ptr [4]=0 [8]=manager [0xc]=invoker
|------------------------------------------------------------------
install_scale_menu_item:
    lea.l   -0x30(%a7),%a7
    movem.l %d0-%d7/%a0-%a1/%a3-%a4,(%a7)
    lea.l   -0x80(%a7),%a7
    movea.l %a7,%a5

    | --- item1: SCALE LOCK ---
    move.l  #1,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    move.l  %d0,0x00(%a5)
    clr.l   0x04(%a5)
    move.l  #GENERIC_MANAGER,%d0
    move.l  %d0,0x08(%a5)
    move.l  #label_invoker,%d0
    move.l  %d0,0x0c(%a5)

    move.l  #4,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a0
    move.l  %a2,(%a0)
    move.l  %d0,0x10(%a5)
    clr.l   0x14(%a5)
    move.l  #SLOT2_MANAGER,%d0
    move.l  %d0,0x18(%a5)
    move.l  #new_slot2_invoker,%d0
    move.l  %d0,0x1c(%a5)

    move.l  #1,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    move.l  %d0,0x20(%a5)
    clr.l   0x24(%a5)
    move.l  #GENERIC_MANAGER,%d0
    move.l  %d0,0x28(%a5)
    move.l  #value_invoker,%d0
    move.l  %d0,0x2c(%a5)

    | closure4: rotation handler (slot4). Same capture (a2) and
    | manager as closure2 - proven-safe generic 4-byte-capture
    | manager, reused here since the shape is identical.
    move.l  #4,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a0
    move.l  %a2,(%a0)
    move.l  %d0,0x30(%a5)
    clr.l   0x34(%a5)
    move.l  #SLOT2_MANAGER,%d0
    move.l  %d0,0x38(%a5)
    move.l  #new_slot4_invoker,%d0
    move.l  %d0,0x3c(%a5)

    move.l  #0x54,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a3

    move.l  #8,-(%a7)
    move.l  #0xffffffff,-(%a7)
    lea.l   0x30(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x20(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x10(%a5),%a0
    move.l  %a0,-(%a7)
    move.l  %a5,-(%a7)
    move.l  %a3,-(%a7)
    jsr     MENUITEM_CTOR
    lea.l   0x1c(%a7),%a7

    move.l  %a3,-(%a7)
    move.l  %a2,-(%a7)
    jsr     MENUVIEW_ADDITEM
    addq.l  #8,%a7

    lea.l   0x30(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x20(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x10(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    move.l  %a5,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7

    | --- item2: SCALE KEY, closures at a5+0x40..0x7f ---
    move.l  #1,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    move.l  %d0,0x40(%a5)
    clr.l   0x44(%a5)
    move.l  #GENERIC_MANAGER,%d0
    move.l  %d0,0x48(%a5)
    move.l  #label_invoker2,%d0
    move.l  %d0,0x4c(%a5)

    move.l  #4,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a0
    move.l  %a2,(%a0)
    move.l  %d0,0x50(%a5)
    clr.l   0x54(%a5)
    move.l  #SLOT2_MANAGER,%d0
    move.l  %d0,0x58(%a5)
    move.l  #new_slot2_invoker2,%d0
    move.l  %d0,0x5c(%a5)

    move.l  #1,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    move.l  %d0,0x60(%a5)
    clr.l   0x64(%a5)
    move.l  #GENERIC_MANAGER,%d0
    move.l  %d0,0x68(%a5)
    move.l  #value_invoker2,%d0
    move.l  %d0,0x6c(%a5)

    | closure4: rotation handler (slot4), same pattern as item1's.
    move.l  #4,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a0
    move.l  %a2,(%a0)
    move.l  %d0,0x70(%a5)
    clr.l   0x74(%a5)
    move.l  #SLOT2_MANAGER,%d0
    move.l  %d0,0x78(%a5)
    move.l  #new_slot4_invoker2,%d0
    move.l  %d0,0x7c(%a5)

    move.l  #0x54,-(%a7)
    jsr     ALLOC
    addq.l  #4,%a7
    movea.l %d0,%a3

    move.l  #8,-(%a7)
    move.l  #0xffffffff,-(%a7)
    lea.l   0x70(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x60(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x50(%a5),%a0
    move.l  %a0,-(%a7)
    lea.l   0x40(%a5),%a0
    move.l  %a0,-(%a7)
    move.l  %a3,-(%a7)
    jsr     MENUITEM_CTOR
    lea.l   0x1c(%a7),%a7

    move.l  %a3,-(%a7)
    move.l  %a2,-(%a7)
    jsr     MENUVIEW_ADDITEM
    addq.l  #8,%a7

    lea.l   0x70(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x60(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x50(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7
    lea.l   0x40(%a5),%a0
    move.l  %a0,-(%a7)
    jsr     FREE_CLOSURE
    addq.l  #4,%a7

    lea.l   0x80(%a7),%a7
    movem.l (%a7),%d0-%d7/%a0-%a1/%a3-%a4
    lea.l   0x30(%a7),%a7

    | resume original FUN_40030874 epilogue (the instruction we overwrote)
    movem.l 0x18(%a7),%d2-%d6/%a2-%a6
    lea.l   0x80(%a7),%a7
    rts

label_string:
    .asciz "Scl"
    .even
str_off:
    .asciz "OFF"
    .even
str_major:
    .asciz "MAJ"
    .even
str_minor:
    .asciz "MIN"
    .even
str_dorian:
    .asciz "DOR"
    .even
str_penta:
    .asciz "PEN"
    .even
value_strings:
    .long str_off
    .long str_major
    .long str_minor
    .long str_dorian
    .long str_penta

label_string2:
    .asciz "Key"
    .even
key_c:
    .asciz "C"
    .even
key_cs:
    .asciz "C#"
    .even
key_d:
    .asciz "D"
    .even
key_ds:
    .asciz "D#"
    .even
key_e:
    .asciz "E"
    .even
key_f:
    .asciz "F"
    .even
key_fs:
    .asciz "F#"
    .even
key_g:
    .asciz "G"
    .even
key_gs:
    .asciz "G#"
    .even
key_a:
    .asciz "A"
    .even
key_as:
    .asciz "A#"
    .even
key_b:
    .asciz "B"
    .even
key_value_strings:
    .long key_c
    .long key_cs
    .long key_d
    .long key_ds
    .long key_e
    .long key_f
    .long key_fs
    .long key_g
    .long key_gs
    .long key_a
    .long key_as
    .long key_b                   | was missing until samplerHN: key B (11)
                                  | read the long past the table as its name


scale_state:                      | 0=OFF 1=MAJ 2=MIN 3=DOR 4=PENTA
    .byte 0                       | OFF by default; set from the menu
key_state:
    .byte 0
    .align 2
fold_lengths:
    .byte 7,7,7,5
    .align 2
fold_tables:
    .byte 0,2,4,5,7,9,11
    .byte 0,2,3,5,7,8,10
    .byte 0,2,3,5,7,9,10
    .byte 0,2,4,7,9,0,0
