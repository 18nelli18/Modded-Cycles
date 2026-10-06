# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/test_lfo_interposition_reference_20260918.py; lines 1-116.
# Unresolved integration bindings: see DEPENDENCIES.json.
#!/usr/bin/env python3
"""Tests for the post-conditioning compact LFO2 contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from lfo_interposition_reference_20260918 import (  # noqa: E402
    COMPACT_BASE,
    LfoState,
    PITCH_DESTINATION,
    interpose_compact,
    pitch_index,
)


class LfoInterpositionReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.compact = [0] * 0x1A0
        self.region = 2
        self.index = pitch_index(self.region)

    def stock_rebuild(self, base: int):
        def stock(values):
            values[self.index] = base
            return COMPACT_BASE

        return stock

    def test_disabled_and_zero_depth_are_exact_stock_inputs(self) -> None:
        before = list(self.compact)
        result = interpose_compact(
            self.compact,
            self.region,
            [LfoState(active=False, delta=7), LfoState(active=True, delta=0)],
            self.stock_rebuild(100),
        )
        self.assertEqual(result, COMPACT_BASE)
        expected = before
        expected[self.index] = 100
        self.assertEqual(self.compact, expected)

    def test_enabled_changes_only_post_conditioned_pitch(self) -> None:
        before = list(self.compact)
        interpose_compact(
            self.compact,
            self.region,
            [LfoState(active=True, destination=PITCH_DESTINATION, delta=1)],
            self.stock_rebuild(100),
        )
        changed = {i for i, (a, b) in enumerate(zip(before, self.compact)) if a != b}
        self.assertEqual(changed, {self.index})
        self.assertEqual(self.compact[self.index], 101)

    def test_multiple_lfos_sum_from_one_rebuilt_base(self) -> None:
        interpose_compact(
            self.compact,
            self.region,
            [
                LfoState(active=True, destination=PITCH_DESTINATION, delta=3),
                LfoState(active=True, destination=PITCH_DESTINATION, delta=-1),
            ],
            self.stock_rebuild(100),
        )
        self.assertEqual(self.compact[self.index], 102)

    def test_repeated_blocks_start_from_fresh_stock_compact(self) -> None:
        observed = []

        def stock(values):
            base = 100 + len(observed) * 10
            values[self.index] = base
            observed.append(base)
            return COMPACT_BASE

        state = [LfoState(active=True, delta=2)]
        interpose_compact(self.compact, self.region, state, stock)
        interpose_compact(self.compact, self.region, state, stock)
        self.assertEqual(observed, [100, 110])
        self.assertEqual(self.compact[self.index], 112)

    def test_disable_after_running_removes_tail(self) -> None:
        state = [LfoState(active=True, delta=2)]
        interpose_compact(self.compact, self.region, state, self.stock_rebuild(100))
        state[0] = LfoState(active=False, delta=2)
        interpose_compact(self.compact, self.region, state, self.stock_rebuild(100))
        self.assertEqual(self.compact[self.index], 100)

    def test_domain_is_explicit_and_clamps_once(self) -> None:
        interpose_compact(
            self.compact,
            self.region,
            [LfoState(active=True, delta=5)],
            self.stock_rebuild(32767),
            native_domain=(-32768, 32767),
        )
        self.assertEqual(self.compact[self.index], 32767)

    def test_non_pitch_destination_is_not_touched(self) -> None:
        interpose_compact(
            self.compact,
            self.region,
            [LfoState(active=True, destination=11, delta=99)],
            self.stock_rebuild(100),
        )
        self.assertEqual(self.compact[self.index], 100)


if __name__ == "__main__":
    unittest.main()
