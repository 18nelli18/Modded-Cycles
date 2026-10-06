# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/test_lfo2_project_editor_session.py; lines 1-178.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Semantic gesture to independent LFO2 edit/readback integration tests."""
from __future__ import annotations

import unittest

from .lfo2_extended_controls import SQUARE
from .lfo2_project_edit_adapter import (
    DEPTH_RAW_NEUTRAL,
    LFO1,
    LFO2,
    Lfo2ProjectEditAdapter,
)
from .lfo2_project_editor_session import Lfo2ProjectEditorSession
from .lfo2_ui_config_bank import AudioPhaseBank
from .lfo2_ui_gesture import Action, EventKind, LfoUiGesturePolicy, UiEvent


class ProjectEditorSessionTests(unittest.TestCase):
    def setUp(self):
        self.stock_calls = []
        self.format_calls = []
        self.phase = AudioPhaseBank((0x12345678, 2, 3, 4, 5, 6))

        def stock_edit(receiver, selector, delta):
            self.stock_calls.append((receiver, selector, delta))
            return DEPTH_RAW_NEUTRAL

        def formatter(raw):
            self.format_calls.append(raw)
            return f"stock:{raw:04x}"

        self.adapter = Lfo2ProjectEditAdapter(
            stock_lfo1_depth_edit=stock_edit,
            original_stock_depth_formatter=formatter,
            audio_phase_bank=self.phase,
            initial_depth_raws=(0x40FF, DEPTH_RAW_NEUTRAL,
                                DEPTH_RAW_NEUTRAL, DEPTH_RAW_NEUTRAL,
                                DEPTH_RAW_NEUTRAL, DEPTH_RAW_NEUTRAL),
        )
        self.policy = LfoUiGesturePolicy(initial_track_id=0, hold_ticks=7)
        self.session = Lfo2ProjectEditorSession(self.adapter, policy=self.policy)
        self.sequence = 0

    def send(self, kind, tick, *, track=None):
        self.sequence += 1
        return self.session.handle_gesture(
            UiEvent(self.sequence, tick, kind, track_id=track))

    def hold_to_lfo2(self, tick):
        self.send(EventKind.LFO_PRESS, tick)
        self.send(EventKind.TICK, tick + 100)
        return self.send(EventKind.LFO_RELEASE, tick + 101)

    def test_long_hold_edit_readback_switchback_and_phase_independence(self):
        initial_raw, initial_compact, _ = self.adapter.read_lfo2_depth(0)
        self.assertEqual((initial_raw, initial_compact), (0x40FF, 0))

        selected = self.hold_to_lfo2(0)
        self.assertEqual(selected.policy.action, Action.SELECTION_CHANGED)
        self.assertEqual(self.session.selection.instance_id, LFO2)
        self.assertEqual(self.session.selection.track_id, 0)
        self.assertFalse(self.session.policy.lfo_press_pending)

        edit = self.session.apply_depth_callback(
            receiver="semantic-test-depth-port", selector=0, delta=1,
            event_id="lfo2-depth-001")
        self.assertTrue(edit.accepted)
        self.assertEqual(edit.status, "APPLIED")
        self.assertEqual((edit.old_raw_depth, edit.new_raw_depth),
                         (0x40FF, 0x4118))
        self.assertEqual((edit.old_compact_depth, edit.new_compact_depth), (0, 1))
        self.assertEqual(edit.formatted_value, "stock:4118")
        self.assertEqual(self.stock_calls, [])
        self.assertEqual(
            self.adapter.config_bank.read_control(0, LFO2, "waveform").native_value,
            SQUARE,
        )

        readback = self.session.read_selected_depth()
        self.assertTrue(readback.accepted)
        self.assertEqual(readback.status, "LFO2_FORMATTED_READBACK")
        self.assertEqual(readback.raw_depth, 0x4118)
        self.assertEqual(readback.formatted_value, "stock:4118")
        self.assertEqual(readback.phase_u32, 0x12345678)

        # Hold duration is > 2x the toggle threshold; it remains pending until
        # release and then switches to LFO1 without altering either bank.
        switched_lfo1 = self.hold_to_lfo2(1000)
        self.assertEqual(switched_lfo1.selected_instance_id, LFO1)
        stock_boundary = self.session.read_selected_depth()
        self.assertEqual(stock_boundary.status, "LFO1_NATIVE_GETTER_REQUIRED")

        switched_lfo2 = self.hold_to_lfo2(2000)
        self.assertEqual(switched_lfo2.selected_instance_id, LFO2)
        retained = self.session.read_selected_depth()
        self.assertEqual((retained.raw_depth, retained.formatted_value),
                         (0x4118, "stock:4118"))
        self.assertEqual(self.adapter.read_lfo2_depth(1)[0], DEPTH_RAW_NEUTRAL)
        self.assertEqual(self.phase.read_audio_owned(0).phase_u32, 0x12345678)

    def test_multiplier_edit_is_selected_lfo2_only_and_readable(self):
        with self.assertRaises(RuntimeError):
            self.session.apply_lfo2_multiplier_edit(12, "mul-before-select")

        self.hold_to_lfo2(0)
        before_other = self.adapter.config_bank.read_control(1, LFO2, "multiplier")
        first = self.session.apply_lfo2_multiplier_edit(12, "mul-free-x1")
        second = self.session.apply_lfo2_multiplier_edit(13, "mul-free-x2")
        self.assertEqual((first.status, first.native_value, first.source),
                         ("APPLIED", 12, "ui"))
        self.assertEqual((second.status, second.native_value, second.source),
                         ("APPLIED", 13, "ui"))
        self.assertEqual(self.adapter.config_bank.read_control(
            0, LFO2, "multiplier").native_value, 13)
        self.assertEqual(self.adapter.config_bank.read_control(
            1, LFO2, "multiplier"), before_other)
        self.assertEqual(self.adapter.config_bank.selected_instance(0), LFO2)
        self.assertEqual(self.adapter.config_bank.selected_instance(1), LFO1)
        self.assertEqual(self.phase.read_audio_owned(0).phase_u32, 0x12345678)

    def test_track_change_keeps_independent_lfo2_banks(self):
        self.hold_to_lfo2(0)
        track0_edit = self.session.apply_depth_callback(
            receiver="track0", selector=0, delta=1, event_id="track0-edit")
        self.assertEqual(track0_edit.new_raw_depth, 0x4118)

        changed = self.send(EventKind.TRACK_CHANGE, 200,
                            track=1)
        self.assertEqual(changed.selected_track_id, 1)
        self.assertEqual(changed.selected_instance_id, LFO1)
        self.hold_to_lfo2(300)
        track1_edit = self.session.apply_depth_callback(
            receiver="track1", selector=0, delta=-1, event_id="track1-edit")
        self.assertEqual(track1_edit.new_raw_depth, DEPTH_RAW_NEUTRAL - 0x19)
        self.assertEqual(self.adapter.read_lfo2_depth(0)[0], 0x4118)

        back = self.send(EventKind.TRACK_CHANGE, 500, track=0)
        self.assertEqual(back.selected_instance_id, LFO2)
        self.assertEqual(self.session.read_selected_depth().raw_depth, 0x4118)
        self.assertEqual(self.adapter.read_lfo2_depth(1)[0],
                         DEPTH_RAW_NEUTRAL - 0x19)

    def test_chord_lost_release_duplicate_and_unsupported_control(self):
        self.send(EventKind.LFO_PRESS, 0)
        chord = self.send(EventKind.KNOB_TURN, 1)
        self.assertEqual(chord.policy.action, Action.CHORD_CONSUMED)
        self.assertTrue(chord.policy.forward_event)
        release = self.send(EventKind.LFO_RELEASE, 1000)
        self.assertEqual(release.selected_instance_id, LFO1)

        self.send(EventKind.LFO_PRESS, 1100)
        cancelled = self.send(EventKind.LOST_RELEASE, 1101)
        self.assertEqual(cancelled.policy.action, Action.GESTURE_CANCELLED)
        late = self.send(EventKind.LFO_RELEASE, 1102)
        self.assertFalse(late.policy.accepted)

        self.hold_to_lfo2(1200)
        rejected = self.session.apply_depth_callback(
            receiver="unsupported", selector=0, delta=1,
            event_id="unsupported-waveform", control="waveform",
            control_id=37)
        self.assertFalse(rejected.accepted)
        self.assertEqual(rejected.status, "UNSUPPORTED_CONTROL")
        self.assertEqual(self.adapter.read_lfo2_depth(0)[0], 0x40FF)
        self.assertEqual(self.stock_calls, [])

        valid = self.session.apply_depth_callback(
            receiver="valid", selector=0, delta=1, event_id="once")
        duplicate = self.session.apply_depth_callback(
            receiver="valid", selector=0, delta=1, event_id="once")
        self.assertEqual(valid.status, "APPLIED")
        self.assertFalse(duplicate.accepted)
        self.assertEqual(duplicate.status, "DUPLICATE_EVENT")
        self.assertEqual(self.adapter.read_lfo2_depth(0)[0], 0x4118)


if __name__ == "__main__":
    unittest.main()
