# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_persistence_speed_join.py; lines 1-100.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Persistence-aware SPEED admission, derived over the retained UI composition.

No new state or firmware output. A check before parsing rejects unavailable
owned UI state without touching its diagnostic word. The actual extra edit
rechecks readiness after the existing writer lease, which prevents protocol
writers from changing it until the edit returns. Standalone owner resolution
is only an admission check, NOT a newly claimed pointer-lifetime lease.
"""
from dataclasses import replace

from . import lfo_four_persistence_ui_join as ui

C = ui.composition
speed = C.random.native.joined
rep = C.rep


def source(symbols, slot, context_size):
    text = speed.speed_source(symbols)
    text = rep(text, ' moveal SLOT,%a2\n tstl %a2\n beq owner_original',
        ' moveal SLOT,%a2\n tstl %a2\n beq owner_original\n'
        ' moveal %a2,%a0\n bsr speed_context_check\n tstl %d0\n beq owner_original')
    text = rep(text, ' beq consume_original\n clrl %a0@(8)',
        ' beq consume_original\n bsr speed_context_check\n tstl %d0\n'
        ' beq consume_restore\n moveal SLOT,%a0\n clrl %a0@(8)')
    text = rep(text, f' jsr {C.CORE + symbols["write_begin"]:#x}\n',
        ' bsr speed_ui_write_begin\n')
    return f'.equ SPEED_CONTEXT_SLOT,{slot:#x}\n.equ SPEED_CONTEXT_SIZE,{context_size}\n'+text+f'''
.globl speed_context_check,speed_ui_write_begin
/* A0 is the captured, boot-retained published owner. D2 and entry IPL are
 * preserved. No callbacks/allocations execute under this bounded mask. */
speed_context_check:
 movel %d2,%sp@-
 movew %sr,%d2
 movel %d2,%d1
 oril #0x700,%d1
 movew %d1,%sr
 moveq #0,%d0
 tstl %a0
 beq speed_context_done
 cmpal SLOT,%a0
 bne speed_context_done
 moveal SPEED_CONTEXT_SLOT,%a1
 cmpal #0x40000000,%a1
 bcs speed_context_done
 cmpal #(0x48000000-SPEED_CONTEXT_SIZE),%a1
 bhi speed_context_done
 movel %a1,%d0
 andil #3,%d0
 bne speed_context_bad
 cmpal %a1@(4),%a0
 bne speed_context_bad
 tstl %a1@(24)
 bne speed_context_bad
 moveq #1,%d0
 bra speed_context_done
speed_context_bad:
 moveq #0,%d0
speed_context_done:
 movew %d2,%sr
 movel %sp@+,%d2
 rts
/* Recheck AFTER taking the same lease as native edits/codec writers. The
 * early check above is not used as a TOCTOU/lifetime proof. */
speed_ui_write_begin:
 jsr {C.CORE + symbols['write_begin']:#x}
 tstl %d0
 beq speed_ui_write_done
 bsr speed_context_check
 tstl %d0
 bne speed_ui_write_done
 jsr {C.CORE + symbols['write_end']:#x}
 moveq #0,%d0
speed_ui_write_done:
 rts
'''


def join(supplied, slot, layout):
    base = list(supplied.base)
    code, symbols = C.random.native.owned.generated(source(base[0][1], slot, layout.size))
    base[3:5] = code, symbols
    names = {'owned SPEED owner': 'owner_route', 'owned SPEED edit lease': 'speed_consume',
        'stock edited controls -> supplied R before conditioning': 'root_event'}
    overlays = tuple(replace(o, replacement=b'\x4e\xf9'+ui.reader.k.words(
        speed.SPEED+symbols[names[o.label]])+b'\x4e\x71') if o.label in names else o
        for o in supplied.overlays)
    if {o.label for o in supplied.overlays if o.label in names} != set(names):
        raise ValueError('SPEED overlay inventory changed')
    base[-1] = overlays
    parts = tuple((a, code if a == speed.SPEED else data) for a,data in supplied.components)
    spans = sorted((a,a+len(data)) for a,data in parts)
    if any(a[1] > b[0] for a,b in zip(spans,spans[1:])):
        raise ValueError('SPEED admission component overlap')
    return replace(supplied, base=tuple(base), components=parts, overlays=overlays)


def compose(*, stock_owner, main=C.random.engine.f.MAIN_PATH):
    supplied, ps, layout, slot = ui.compose(stock_owner=stock_owner, main=main)
    return join(supplied,slot,layout), ps, layout, slot
