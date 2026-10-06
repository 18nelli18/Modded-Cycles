# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/lfo_conditioned_bridge_20260922.py; lines 1-100.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Supplied-input host bridge: literal stock conditioning, then extra LFOs.

Models 58474's completed stores and 56e24's six event/source adjustments.
Does not model the unidentified stock live LFO, 91ab2, interrupts or firmware
wrapping. R/Q and six words at40fe4cdc are explicit inputs, not invented state.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct

from dsp_reference.compact_preprocess_20260918 import (
    compact_preprocess, signed_fractional_product48, movclr_signed_fractional,
)
from dsp_reference.coordinate_abi import region_slot_offset
from lfo_bank_reference import BankResult, apply_bank

R_REQUIRED_BYTES = 0x20C
Q_BYTES = 238 * 4
COMPACT_BYTES = 119 * 4


def signed32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


@dataclass(frozen=True)
class EventAdjustment:
    region: int
    slot: int
    offset: int
    before: int
    delta: int
    after: int


@dataclass(frozen=True)
class ConditionedFrame:
    compact: bytes
    history: bytes
    prefix_word: int
    event_adjustments: tuple[EventAdjustment, ...]
    stock_return_d0: int = 6


def prepare_stock(raw: bytes, history: bytes, *, weights: tuple[int, ...],
                  previous_prefix_word: int) -> ConditionedFrame:
    """Exact recovered store/value ordering with MACSR20 and cleared ACCs.

    Producer always builds the compact stream anew; Q persists separately.
    The previous root-4 word is copied back unchanged, not used as a target.
    Source slots, including LFO config, need not be assigned guessed semantics.
    These six weights are the signed halfwords read at40fe4cdc, NOT LFO depth.
    """
    if type(raw) is not bytes or len(raw) < R_REQUIRED_BYTES:
        raise ValueError("immutable R view through +0x20b required")
    if type(history) is not bytes or len(history) != Q_BYTES:
        raise ValueError("exact immutable 238-longword Q history required")
    if (type(weights) is not tuple or len(weights) != 6 or
            any(type(n) is not int or not -32768 <= n <= 32767 for n in weights)):
        raise ValueError("six explicit signed16 event/source weights required")
    out = compact_preprocess(struct.unpack_from(">120I", raw),
                             struct.unpack(">238I", history),
                             initial_work_word=previous_prefix_word,
                             initial_acc0=0, initial_acc1=0)
    compact = bytearray(struct.pack(">119I", *out.stream_words[1:]))
    # 400584dc/e0 copies R+16+42*r to compact root+16+42*r,
    # bypassing conditioning for slot4 (destination/config, not PITCH).
    for region in range(6):
        offset = region_slot_offset(region, 4)
        compact[offset:offset+2] = raw[offset:offset+2]

    adjustments = []
    # Complete 56e24: unsigned upper-clamp selector to32, signed multiply,
    # finite32 addition, then branch/clamp into0..7fff. ACC0 is cleared by
    # each MOVCLR; the preceding58474 also leaves ACC0/1 clear.
    for region, weight in enumerate(weights):
        selector = struct.unpack_from(">I", raw, 0x1DC + region*4)[0]
        slot = min(32, selector)
        offset = region_slot_offset(region, slot)
        value = struct.unpack_from(">I", raw, 0x1F4 + region*4)[0]
        scaled = signed32(2 * signed32(value - 0x4000))
        product = signed_fractional_product48(weight << 16, scaled)
        delta = signed32(movclr_signed_fractional(product))
        before = int.from_bytes(compact[offset:offset+2], "big", signed=True)
        after = min(0x7FFF, max(0, signed32(before + delta)))
        compact[offset:offset+2] = after.to_bytes(2, "big")
        adjustments.append(EventAdjustment(region, slot, offset, before, delta, after))
    return ConditionedFrame(bytes(compact), struct.pack(">238I", *out.history_after),
                            out.stream_words[0], tuple(adjustments))


def prepare_and_inject(raw: bytes, history: bytes, bank, *,
                       weights: tuple[int, ...], previous_prefix_word: int
                       ) -> tuple[ConditionedFrame, BankResult]:
    """Q receives ONLY stock conditioning; extras touch freshly built C."""
    stock = prepare_stock(raw, history, weights=weights,
                          previous_prefix_word=previous_prefix_word)
    return stock, apply_bank(stock.compact, bank)
