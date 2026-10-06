# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/test_lfo_runtime_experiment_20260918.py; lines 1-52.
# Unresolved integration bindings: see DEPENDENCIES.json.
import unittest

from lfo_runtime_experiment_20260918 import (
    MidiMessage,
    WATCHES,
    compact_address,
    midi_bytes,
    stimulus_windows,
)


class LfoRuntimeExperimentTests(unittest.TestCase):
    def test_plan_covers_all_runtime_discriminators(self):
        names = {window.name for window in stimulus_windows()}
        self.assertEqual(
            names,
            {
                "configuration-baseline",
                "pitch-live-output",
                "destination-routing",
                "phase-reset",
                "multiple-source",
            },
        )
        self.assertTrue(all(window.messages for window in stimulus_windows()))
        self.assertTrue(any(window.held_note for window in stimulus_windows()))
        self.assertGreaterEqual(len(WATCHES), 10)

    def test_depth_pair_and_destination_values_are_encoded_as_cc(self):
        self.assertEqual(MidiMessage(109, 96).bytes(), (0xB0, 109, 96))
        self.assertEqual(MidiMessage(110, 32).bytes(), (0xB0, 110, 32))
        values = [message.value for window in stimulus_windows() for message in window.messages if message.controller == 105]
        self.assertEqual(values, [0, 10, 18, 10, 11, 18, 10])

    def test_compact_geometry_keeps_speed_destination_and_b_slots_distinct(self):
        base = 0x8000100C
        self.assertEqual(compact_address(base, 0, 1), base + 0x10)
        self.assertEqual(compact_address(base, 0, 4), base + 0x16)
        self.assertEqual(compact_address(base, 0, 10), base + 0x22)
        self.assertEqual(compact_address(base, 0, 17), base + 0x30)
        self.assertNotEqual(compact_address(base, 0, 1), compact_address(base, 0, 4))

    def test_channel_validation_and_flattened_message_count(self):
        with self.assertRaises(ValueError):
            MidiMessage(105, 0).bytes(16)
        flattened = midi_bytes(stimulus_windows())
        self.assertEqual(len(flattened), sum(len(window.messages) for window in stimulus_windows()))
        self.assertTrue(all(message[0] == 0xB0 for message in flattened))


if __name__ == "__main__":
    unittest.main()
