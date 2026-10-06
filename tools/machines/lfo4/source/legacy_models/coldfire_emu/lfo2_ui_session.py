# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo2_ui_session.py; lines 1-152.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Join the LFO editor gesture policy to the two-bank configuration adapter.

This is deliberately a host-side integration seam. It accepts an explicit
native event/control result from the original-CPU UI harness; it does not
pretend to reproduce the OLED, infer a descriptor index, or turn policy replay
into native firmware evidence.
"""
from __future__ import annotations

from dataclasses import dataclass

from .lfo2_ui_config_bank import Lfo2ConfigBank, Readback
from .lfo2_ui_gesture import (
    Action,
    EventKind,
    LfoUiGesturePolicy,
    PolicyResult,
    UiEvent,
)


@dataclass(frozen=True)
class SessionEventResult:
    """One policy event plus any explicitly requested control readback."""

    policy: PolicyResult
    selected_track_id: int
    selected_instance_id: int
    readback: Readback | None = None


@dataclass(frozen=True)
class NativeControlResult:
    """Route one already-decoded UI event result to its selected bank."""

    accepted: bool
    status: str
    track_id: int
    instance_id: int
    control: str
    event_id: str | int
    readback: Readback | None


class LfoUiSession:
    """Bind per-track instance selection to config ownership.

    A caller must pass the track, control, raw native event value and stable
    event ID obtained from its event/owner trace. This class does not decode
    the encoder or invent a formatter. LFO1 remains delegated to its adapter;
    LFO2 unsupported fields remain explicit no-ops.
    """

    def __init__(self, bank: Lfo2ConfigBank,
                 policy: LfoUiGesturePolicy | None = None) -> None:
        if not isinstance(bank, Lfo2ConfigBank):
            raise TypeError("bank must be Lfo2ConfigBank")
        self.bank = bank
        self.policy = policy or LfoUiGesturePolicy()
        self._seen_native_control_events: set[tuple[int, int, str, str | int]] = set()
        # Keep the adapter's view target aligned to the policy's per-track
        # default without touching configuration or audio-owned phase.
        for track_id in range(6):
            self.bank.select_instance(
                track_id, self.policy.selected_for_track(track_id))

    def handle_gesture(self, event: UiEvent, *,
                       readback_control: str | None = None) -> SessionEventResult:
        """Apply one already-normalized semantic gesture to host session state.

        This does not translate native selector numbers 9/10/11 (whose stock
        callbacks are no-ops in the bounded probe) into physical LFO-button,
        FUNC, encoder, or release events. That producer mapping remains an
        explicit integration boundary.
        """
        result = self.policy.handle(event)
        if result.accepted and result.action is Action.SELECTION_CHANGED:
            self.bank.select_instance(result.track_id,
                                       result.selected_instance_id)
        elif (result.accepted and event.kind is EventKind.TRACK_CHANGE):
            # Each track has its own session-only selected bank. Synchronize
            # the newly active track's UI target; this is not a config write.
            track_id = self.policy.current_track_id
            self.bank.select_instance(
                track_id, self.policy.selected_for_track(track_id))

        readback = None
        if result.accepted and result.action is Action.SELECTION_CHANGED and readback_control:
            # Caller supplies a control only when the native view has proved
            # which control is currently selected; no slot mapping is guessed.
            readback = self.bank.read_control(result.track_id,
                                              result.selected_instance_id,
                                              readback_control)
        return SessionEventResult(
            result, self.policy.current_track_id,
            self.policy.selected_instance_id, readback)

    def apply_native_control(self, *, track_id: int, control: str,
                             raw_value: object,
                             event_id: str | int) -> NativeControlResult:
        """Route an original-handler-derived UI value to its selected bank.

        Stale-track events are rejected before reaching either setter. When
        accepted, the exact caller-supplied raw value is forwarded unchanged.
        """
        if type(track_id) is not int or not 0 <= track_id < 6:
            raise ValueError("track_id must be an integer in 0..5")
        if type(event_id) not in (str, int) or event_id == "":
            raise ValueError("event_id must be a nonempty string or integer")
        if track_id != self.policy.current_track_id:
            return NativeControlResult(
                False, "STALE_UI_TRACK", track_id,
                self.policy.selected_for_track(track_id), control,
                event_id, None)

        instance_id = self.policy.selected_instance_id
        dedupe_key = (track_id, instance_id, control, event_id)
        if dedupe_key in self._seen_native_control_events:
            return NativeControlResult(
                False, "DUPLICATE_NATIVE_EVENT", track_id, instance_id,
                control, event_id, None)
        # Selection has no write side effect; this only keeps the bank's
        # selected-target guard in sync with the gesture policy.
        self.bank.select_instance(track_id, instance_id)
        self._seen_native_control_events.add(dedupe_key)
        readback = self.bank.apply_ui_write(
            track_id, instance_id, control, raw_value, event_id)
        return NativeControlResult(
            readback.status in {"APPLIED", "DELEGATED",
                                "DELEGATED_MAPPING_UNRESOLVED"},
            readback.status, track_id, instance_id, control, event_id,
            readback)

    def apply_external_control(self, *, source: str, track_id: int,
                               instance_id: int, control: str,
                               raw_value: object,
                               event_id: str | int) -> NativeControlResult:
        """Apply an explicitly targeted MIDI/p-lock control independent of UI."""
        if type(source) is not str or source.lower() not in {"midi", "plock"}:
            raise ValueError("external source must be 'midi' or 'plock'")
        readback = self.bank.apply_external_write(
            track_id, instance_id, control, raw_value, source.lower(), event_id)
        accepted = readback.status in {"APPLIED", "DELEGATED",
                                      "DELEGATED_MAPPING_UNRESOLVED"}
        return NativeControlResult(
            accepted, readback.status, track_id, instance_id, control,
            event_id, readback)

    def publish_block_boundary(self, track_id: int,
                               native_rate_scalar: int):
        """Publish one complete immutable track snapshot for the audio owner."""
        return self.bank.publish_block_boundary(track_id, native_rate_scalar)
