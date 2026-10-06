# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/test_lfo2_project_edit_adapter.py; lines 1-251.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Isolated tests for the project-owned LFO2 DEPTH edit adapter."""
from __future__ import annotations

import unittest

from .lfo2_extended_controls import TRIANGLE
from .lfo2_project_edit_adapter import (
    DEPTH_DESCRIPTOR_ID,
    DEPTH_RAW_MAX,
    DEPTH_RAW_NEUTRAL,
    LFO1,
    LFO2,
    Lfo2ProjectEditAdapter,
)
from .lfo2_ui_config_bank import AudioPhaseBank, Lfo2ConfigBank


class Lfo2ProjectEditAdapterTests(unittest.TestCase):
    def setUp(self):
        self.stock_calls = []
        self.format_calls = []

        def stock_edit(receiver, selector, delta):
            self.stock_calls.append((receiver, selector, delta))
            # This is the injected original callback/getter service boundary.
            return 0x4321

        def stock_formatter(raw):
            self.format_calls.append(raw)
            return f"ORIGINAL-STOCK-FORMAT:{raw:04x}"

        self.stock_edit_service = stock_edit
        self.original_formatter_service = stock_formatter
        self.adapter = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=self.stock_edit_service,
            original_stock_depth_formatter=self.original_formatter_service,
            audio_phase_bank=AudioPhaseBank((11, 22, 33, 44, 55, 66)))

    def test_attaching_adapter_preserves_prepopulated_project_bank(self):
        bank = Lfo2ConfigBank()
        bank.apply_external_write(3, LFO2, "depth", 64,
                                  "project-config", "depth-64")
        bank.apply_external_write(3, LFO2, "multiplier", 7,
                                  "project-config", "mul-7")
        bank.apply_external_write(3, LFO2, "waveform", TRIANGLE,
                                  "project-config", "triangle")
        bank.apply_external_write(5, LFO2, "depth", -12,
                                  "project-config", "depth-negative")
        before = {
            (track, control): bank.read_control(track, LFO2, control)
            for track in range(6)
            for control in ("depth", "multiplier", "waveform", "destination")
        }

        adapter = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=self.stock_edit_service,
            original_stock_depth_formatter=self.original_formatter_service,
            config_bank=bank,
            audio_phase_bank=AudioPhaseBank((1, 2, 3, 4, 5, 6)))

        self.assertIs(adapter.config_bank, bank)
        self.assertEqual(
            {
                (track, control): bank.read_control(track, LFO2, control)
                for track in range(6)
                for control in ("depth", "multiplier", "waveform", "destination")
            },
            before,
        )
        self.assertEqual(bank.read_control(3, LFO2, "depth").native_value, 64)
        self.assertEqual(bank.read_control(3, LFO2, "multiplier").native_value, 7)
        self.assertEqual(bank.read_control(3, LFO2, "waveform").native_value,
                         TRIANGLE)
        self.assertEqual(bank.read_control(5, LFO2, "depth").native_value, -12)

    def _edit(self, *, selection, track=0, instance=LFO2, receiver=0x4100,
              selector=0, delta=1, control="depth",
              control_id=DEPTH_DESCRIPTOR_ID, event_id="edit-1"):
        return self.adapter.apply_depth_callback(
            receiver=receiver, selector=selector, delta=delta,
            track_id=track, instance_id=instance, control=control,
            control_id=control_id, event_id=event_id,
            selection_generation=selection.generation)

    def test_selected_track_changes_only_lfo2_and_preserves_phase_and_string(self):
        # One stock callback detent advances this seed from just below one
        # compact unit to one; the formatter is supplied by the caller.
        self.adapter = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=self.stock_edit_service,
            original_stock_depth_formatter=self.original_formatter_service,
            audio_phase_bank=AudioPhaseBank((11, 22, 33, 44, 55, 66)),
            initial_depth_raws=(DEPTH_RAW_NEUTRAL, DEPTH_RAW_NEUTRAL,
                               0x40FF, DEPTH_RAW_NEUTRAL,
                               DEPTH_RAW_NEUTRAL, DEPTH_RAW_NEUTRAL))
        selection = self.adapter.select_editor(2, LFO2)
        before = [self.adapter.read_lfo2_depth(track) for track in range(6)]
        result = self._edit(selection=selection, track=2)

        self.assertTrue(result.accepted)
        self.assertEqual(result.status, "APPLIED")
        self.assertEqual(result.callback_arguments, (0x4100, 0, 1))
        self.assertEqual((result.old_raw_depth, result.new_raw_depth),
                         (0x40FF, 0x4118))
        self.assertEqual((result.old_compact_depth, result.new_compact_depth),
                         (0, 1))
        self.assertEqual(result.formatted_value, "ORIGINAL-STOCK-FORMAT:4118")
        self.assertEqual(result.phase_before_u32, 33)
        self.assertEqual(result.phase_after_u32, 33)
        self.assertEqual(self.stock_calls, [])
        after = [self.adapter.read_lfo2_depth(track) for track in range(6)]
        expected = list(before)
        expected[2] = (0x4118, 1, before[2][2] + 1)
        self.assertEqual(after, expected)

    def test_lfo1_is_delegated_with_original_abi_and_lfo2_remains_untouched(self):
        selection = self.adapter.select_editor(1, LFO1)
        before = [self.adapter.read_lfo2_depth(track) for track in range(6)]
        receiver = object()
        result = self._edit(selection=selection, track=1, instance=LFO1,
                            receiver=receiver, delta=-1, event_id="stock-1")

        self.assertTrue(result.accepted)
        self.assertEqual(result.status, "DELEGATED_LFO1")
        self.assertEqual(self.stock_calls, [(receiver, 0, -1)])
        self.assertEqual(result.callback_arguments, (receiver, 0, -1))
        self.assertEqual(result.new_raw_depth, 0x4321)
        self.assertEqual(result.formatted_value,
                         "ORIGINAL-STOCK-FORMAT:4321")
        self.assertEqual(self.format_calls[-1], 0x4321)
        self.assertEqual([self.adapter.read_lfo2_depth(t) for t in range(6)],
                         before)
        self.assertEqual(self.adapter.audio_phase_bank.read_audio_owned(1).phase_u32,
                         22)

    def test_neutral_and_clamp_are_explicit_and_do_not_forge_formatter(self):
        neutral_selection = self.adapter.select_editor(0, LFO2)
        neutral = self._edit(selection=neutral_selection, delta=0,
                             event_id="neutral")
        self.assertEqual(neutral.status, "NEUTRAL")
        self.assertEqual((neutral.old_raw_depth, neutral.new_raw_depth),
                         (DEPTH_RAW_NEUTRAL, DEPTH_RAW_NEUTRAL))
        self.assertEqual((neutral.old_compact_depth, neutral.new_compact_depth),
                         (0, 0))
        self.assertEqual(neutral.formatted_value,
                         "ORIGINAL-STOCK-FORMAT:4000")
        self.assertEqual(self.format_calls, [DEPTH_RAW_NEUTRAL])

        max_seeded = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=self.stock_edit_service,
            original_stock_depth_formatter=self.original_formatter_service,
            initial_depth_raws=(DEPTH_RAW_MAX,) +
            (DEPTH_RAW_NEUTRAL,) * 5)
        max_selection = max_seeded.select_editor(0, LFO2)
        clamped = max_seeded.apply_depth_callback(
            receiver=0x4200, selector=0, delta=1, track_id=0,
            instance_id=LFO2, control="depth", control_id=36,
            event_id="upper-rail", selection_generation=max_selection.generation)
        self.assertTrue(clamped.accepted)
        self.assertEqual(clamped.status, "CLAMPED")
        self.assertEqual((clamped.old_raw_depth, clamped.new_raw_depth),
                         (DEPTH_RAW_MAX, DEPTH_RAW_MAX))

        near_max = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=self.stock_edit_service,
            original_stock_depth_formatter=self.original_formatter_service,
            initial_depth_raws=(DEPTH_RAW_MAX - 1,) +
            (DEPTH_RAW_NEUTRAL,) * 5)
        near_selection = near_max.select_editor(0, LFO2)
        clipped = near_max.apply_depth_callback(
            receiver=0x4200, selector=0, delta=1, track_id=0,
            instance_id=LFO2, control="depth", control_id=36,
            event_id="partial-upper-rail",
            selection_generation=near_selection.generation)
        self.assertEqual(clipped.status, "CLAMPED")
        self.assertEqual(clipped.new_raw_depth, DEPTH_RAW_MAX)

    def test_duplicate_event_is_rejected_without_second_edit_or_format(self):
        selection = self.adapter.select_editor(3, LFO2)
        first = self._edit(selection=selection, track=3, event_id="same")
        calls_after_first = len(self.format_calls)
        second = self._edit(selection=selection, track=3, event_id="same")

        self.assertEqual(first.status, "APPLIED_QUANTIZED_NEUTRAL")
        self.assertFalse(second.accepted)
        self.assertEqual(second.status, "DUPLICATE_EVENT")
        self.assertEqual(self.adapter.read_lfo2_depth(3)[0],
                         DEPTH_RAW_NEUTRAL + 0x19)
        self.assertEqual(len(self.format_calls), calls_after_first)
        self.assertEqual(self.stock_calls, [])

    def test_stale_and_unsupported_inputs_are_rejected_without_side_effects(self):
        old_selection = self.adapter.select_editor(0, LFO2)
        current = self.adapter.select_editor(1, LFO2)
        stale = self._edit(selection=old_selection, track=0, event_id="stale")
        self.assertFalse(stale.accepted)
        self.assertEqual(stale.status, "STALE_TRACK")

        unsupported = self._edit(selection=current, track=1,
                                 control="speed", control_id=29,
                                 event_id="unsupported")
        self.assertFalse(unsupported.accepted)
        self.assertEqual(unsupported.status, "UNSUPPORTED_CONTROL")
        bad_selector = self._edit(selection=current, track=1, selector=1,
                                  event_id="selector")
        self.assertFalse(bad_selector.accepted)
        self.assertEqual(bad_selector.status, "UNSUPPORTED_CALLBACK_SELECTOR")
        bad_delta = self._edit(selection=current, track=1, delta=2,
                               event_id="delta")
        self.assertFalse(bad_delta.accepted)
        self.assertEqual(bad_delta.status, "UNSUPPORTED_CALLBACK_DELTA")
        self.assertEqual(self.stock_calls, [])
        self.assertEqual(self.format_calls, [])
        self.assertEqual(self.adapter.read_lfo2_depth(1)[0], DEPTH_RAW_NEUTRAL)

    def test_guest_projection_is_only_for_square_zero_or_one_depth_on_pitch(self):
        self.adapter.config_bank.set_native_speed(0, 0x4001)
        self.adapter.config_bank.apply_external_write(
            0, LFO2, "destination", 10, "fixture", "pitch-destination")
        zero = self.adapter.guest_runner_config(0, 0x3840)
        self.assertIsNotNone(zero)
        self.assertEqual((zero["region"], zero["destination"], zero["depth"]),
                         (0, 10, 0))
        self.assertEqual(zero["waveform"], 0)
        self.assertEqual(zero["phase"], 11)

        one_depth = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=self.stock_edit_service,
            original_stock_depth_formatter=self.original_formatter_service,
            initial_depth_raws=(0x4100,) + (DEPTH_RAW_NEUTRAL,) * 5,
            audio_phase_bank=AudioPhaseBank((0x12345678, 0, 0, 0, 0, 0)))
        one_depth.config_bank.set_native_speed(0, 0x4001)
        one_depth.config_bank.apply_external_write(
            0, LFO2, "destination", 10, "fixture", "pitch-destination")
        one = one_depth.guest_runner_config(0, 0x3840)
        self.assertIsNotNone(one)
        self.assertEqual((one["destination"], one["depth"], one["phase"]),
                         (10, 1, 0x12345678))
        self.assertIsNone(one_depth.guest_runner_config(1, 0x3840))

        one_depth.config_bank.apply_external_write(
            0, LFO2, "waveform", TRIANGLE, "fixture", "triangle")
        self.assertIsNone(one_depth.guest_runner_config(0, 0x3840))
        one_depth.config_bank.apply_external_write(
            0, LFO2, "waveform", 0, "fixture", "square")
        one_depth.config_bank.apply_external_write(
            0, LFO2, "depth", 2, "fixture", "depth-2")
        self.assertIsNone(one_depth.guest_runner_config(0, 0x3840))


if __name__ == "__main__":
    unittest.main()
