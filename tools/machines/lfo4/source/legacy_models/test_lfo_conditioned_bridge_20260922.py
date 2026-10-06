# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/test_lfo_conditioned_bridge_20260922.py; lines 1-121.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Byte-level integration tests; not a stock-LFO coexistence capture."""
from dataclasses import replace
from pathlib import Path
import struct
import unittest

from lfo_bank_reference import ExtraLfo, zero_bank
from lfo_conditioned_bridge_20260922 import (
    prepare_stock, prepare_and_inject, Q_BYTES, R_REQUIRED_BYTES,
)


def raw_fixture():
    raw = bytearray(R_REQUIRED_BYTES)
    for region in range(6):
        # Set nonzero target so +/-1 has room in the first stock block.
        struct.pack_into(">h", raw, 0x22 + region*0x42, 16000 + region)
        struct.pack_into(">I", raw, 0x1DC + region*4, 32)
        struct.pack_into(">I", raw, 0x1F4 + region*4, 0x4000)
    return raw


class ConditionedBridgeTests(unittest.TestCase):
    def prepare(self, raw, history=bytes(Q_BYTES), **kw):
        return prepare_stock(bytes(raw), history, weights=kw.get("weights", (0,)*6),
                             previous_prefix_word=0x12345678)

    def test_all_regional_pitch_coordinates_follow_independent_recurrence(self):
        raw = raw_fixture()
        for r in range(6):
            struct.pack_into(">h", raw, 0x22 + r*0x42, -15000 + r*6000)
        result = self.prepare(raw)
        self.assertEqual(result.prefix_word, 0x12345678)
        self.assertEqual(len(result.compact), 476)
        self.assertEqual(result.stock_return_d0, 6)
        for r in range(6):
            target = -15000 + r*6000
            q = (983 * 65536 * target) // 32768
            value = (q + 32768) // 65536
            self.assertEqual(struct.unpack_from(">h", result.compact, 0x22+r*0x42)[0], value)
            self.assertEqual(struct.unpack_from(">i", result.history, 2*(0x22+r*0x42))[0], q)

    def test_direct_slot4_bypass_preserves_signed_bits_after_conditioning(self):
        raw = raw_fixture()
        for r in range(6):
            struct.pack_into(">H", raw, 0x16 + 0x42*r, 0x8000 + r)
        result = self.prepare(raw)
        for r in range(6):
            offset = 0x16 + 0x42*r
            self.assertEqual(result.compact[offset:offset+2], bytes(raw[offset:offset+2]))
            # Q was still updated; the direct copy affects C alone.
            self.assertNotEqual(struct.unpack_from(">i", result.history, 2*offset)[0], 0)

    def test_event_adjustment_adds_before_extra_lfo_with_signed_scaling(self):
        raw = raw_fixture()
        struct.pack_into(">I", raw, 0x1DC, 10)
        struct.pack_into(">I", raw, 0x1F4, 0x8000)
        bank = list(zero_bank()); bank[0] = (ExtraLfo(phase=0x80000000, depth=1,
                                                   destination=10, flags=1),)
        stock, extra = prepare_and_inject(bytes(raw), bytes(Q_BYTES), bank,
                         weights=(0x4000, 0, 0, 0, 0, 0), previous_prefix_word=0)
        event = stock.event_adjustments[0]
        self.assertEqual((event.offset, event.delta), (0x22, 16384))
        self.assertEqual(event.after, event.before + 16384)
        self.assertEqual(int.from_bytes(extra.workspace[0x22:0x24], "big"), event.after+1)

    def test_event_selector_unsigned_clamp_and_negative_weight(self):
        raw = raw_fixture()
        struct.pack_into(">I", raw, 0x1DC, 0xFFFFFFFF)
        struct.pack_into(">I", raw, 0x1F4, 0x8000)
        result = self.prepare(raw, weights=(-16384, 0, 0, 0, 0, 0))
        self.assertEqual((result.event_adjustments[0].slot, result.event_adjustments[0].offset),
                         (32, 0x4E))
        self.assertEqual(result.event_adjustments[0].delta, -16384)
        self.assertEqual(result.event_adjustments[0].after, 0)

    def test_repeated_blocks_never_feed_lfo_into_q_or_previous_c(self):
        raw = raw_fixture()
        bank = list(zero_bank())
        bank[3] = (ExtraLfo(phase=0x80000000, increment=0x01000000,
                           depth=1, destination=10, flags=1),)
        control_q = injected_q = bytes(Q_BYTES)
        saved_raw = bytes(raw)
        for block in range(80):
            if block == 30:
                struct.pack_into(">h", raw, 0x22+3*0x42, 18000)
            if block == 60:
                bank = zero_bank()  # disable after running, no conditioning tail
            control = self.prepare(raw, control_q)
            stock, injected = prepare_and_inject(bytes(raw), injected_q, bank,
                          weights=(0,)*6, previous_prefix_word=0x12345678)
            self.assertEqual(stock, control)
            self.assertEqual(stock.history, control.history)
            if block < 60:
                differences = [i for i, (a, b) in enumerate(zip(injected.workspace, stock.compact)) if a != b]
                self.assertTrue(set(differences) <= {0xE8, 0xE9})
                self.assertEqual(len(differences), 1)
            else:
                self.assertEqual(injected.workspace, stock.compact)
            bank, injected_q, control_q = injected.state, stock.history, control.history
        self.assertEqual(saved_raw[:0xE8], bytes(raw)[:0xE8])

    def test_two_opposed_sources_cancel_and_zero_depth_is_identical(self):
        plus = ExtraLfo(phase=0x80000000, depth=1, destination=10, flags=1)
        minus = replace(plus, phase=0)
        for row in ((plus, minus), (replace(plus, depth=0), minus.__class__())):
            bank = list(zero_bank(2)); bank[0] = row
            stock, injected = prepare_and_inject(bytes(raw_fixture()), bytes(Q_BYTES), bank,
                              weights=(0,)*6, previous_prefix_word=0)
            self.assertEqual(stock.compact, injected.workspace)

    def test_invalid_inputs_fail_not_silently_default(self):
        for raw, history, weights in ((b"", bytes(Q_BYTES), (0,)*6),
                                     (bytes(raw_fixture()), b"", (0,)*6),
                                     (bytes(raw_fixture()), bytes(Q_BYTES), (True,)*6)):
            with self.assertRaises(ValueError):
                prepare_stock(raw, history, weights=weights, previous_prefix_word=0)


if __name__ == "__main__":
    unittest.main()
