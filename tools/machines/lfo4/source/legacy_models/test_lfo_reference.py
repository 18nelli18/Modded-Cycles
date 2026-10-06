# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/test_lfo_reference.py; lines 1-44.
# Unresolved integration bindings: see DEPENDENCIES.json.
#!/usr/bin/env python3
"""Tests for the documented LFO multiplier reference."""

import unittest

from lfo_reference import multiplier_spec, period_seconds, period_whole_notes


class LFOReferenceTests(unittest.TestCase):
    def test_twenty_four_states_and_two_families(self):
        specs = [multiplier_spec(index) for index in range(24)]
        self.assertEqual(specs[0].label, "x1")
        self.assertEqual(specs[11].label, "x2K")
        self.assertEqual(specs[12].label, "1")
        self.assertEqual(specs[23].label, "2K")
        self.assertTrue(all(spec.synchronized for spec in specs[:12]))
        self.assertTrue(all(not spec.synchronized for spec in specs[12:]))
        self.assertEqual([spec.factor for spec in specs[:12]], [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048])
        self.assertEqual([spec.factor for spec in specs[12:]], [spec.factor for spec in specs[:12]])

    def test_documented_period_and_sync_free_difference(self):
        self.assertEqual(period_whole_notes(0), 128.0)
        self.assertEqual(period_whole_notes(11), 128.0 / 2048.0)
        self.assertEqual(period_seconds(0, 120), 256.0)
        self.assertEqual(period_seconds(12, 120), 256.0)
        self.assertEqual(period_seconds(0, 60), 512.0)
        self.assertEqual(period_seconds(12, 60), 256.0)

    def test_speed_and_index_boundaries(self):
        self.assertEqual(period_whole_notes(0, 64), 2.0)
        with self.assertRaises(ValueError):
            multiplier_spec(-1)
        with self.assertRaises(ValueError):
            multiplier_spec(24)
        with self.assertRaises(ValueError):
            period_whole_notes(0, 0)
        with self.assertRaises(ValueError):
            period_whole_notes(0, 65)
        with self.assertRaises(ValueError):
            period_seconds(0, 0)


if __name__ == "__main__":
    unittest.main()
