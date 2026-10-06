# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo2_project_edit_adapter.py; lines 1-438.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Project-owned host adapter for the stock LFOMenu DEPTH callback seam.

The proven stock callback ABI is ``(receiver, 0, delta)`` for descriptor 36.
This module does not patch or claim to emulate native event routing.  A caller
supplies the active track/instance/control/event identity and a selection
token. LFO1 edits are delegated to an injected stock callback/readback
service; LFO2 edits touch only an independent project bank. The default bank
is host-owned; the constructor-backed integration supplies a separate guest-
RAM sidecar and runs the original installed LFOMenu callback plus MAIN entry
setter/getter/formatter code against its alternate model root.

DEPTH's stock raw representation is offset Q8.8 around ``0x4000``.  The
selected-edit fixture observed a raw change of ``0x19`` for a callback detent
of +/-1 at its seeded values.  The host-only fallback uses that observed step;
the constructor-backed path lets original MAIN perform the scaling.  A second
fixture observed ``0x40ff → 0x4119`` (a ``0x1a`` raw delta), demonstrating that
the callback's fixed-point step depends on the starting value.  Compact units
remain prototype code steps, not semitones. The stock formatter is used for
readback; no display string is synthesized here.
"""
from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Callable

from .lfo2_extended_controls import (
    DEPTH_MAX_COMPACT_UNITS, DEPTH_MIN_COMPACT_UNITS,
    map_published_track_snapshot, project_guest_runner_config,
    stock_depth_raw_to_compact_units,
)
from .lfo2_ui_config_bank import (
    AudioPhaseBank, Lfo2ConfigBank,
)


TRACK_COUNT = 6
LFO1 = 1
LFO2 = 2
DEPTH_CONTROL = "depth"
DEPTH_DESCRIPTOR_ID = 36
DEPTH_RAW_NEUTRAL = 0x4000
DEPTH_RAW_MIN = 0x0000
DEPTH_RAW_MAX = 0x7F00
# Host-only fallback step from one selected-edit fixture. Native integration
# executes FUN_400260ca and must not substitute this fixed increment.
DEPTH_RAW_PER_CALLBACK_DETENT = 0x19
CALLBACK_SELECTOR = 0


def _event_id(value: object) -> bool:
    return (type(value) is str and value != "") or type(value) is int


@dataclass(frozen=True)
class EditorSelection:
    track_id: int
    instance_id: int
    generation: int


@dataclass(frozen=True)
class ProjectEditResult:
    accepted: bool
    status: str
    track_id: int
    instance_id: int
    control: str
    control_id: int
    event_id: str | int
    callback_arguments: tuple[object, int, int]
    selection_generation: int
    old_raw_depth: int | None = None
    new_raw_depth: int | None = None
    old_compact_depth: int | None = None
    new_compact_depth: int | None = None
    formatted_value: str | None = None
    phase_before_u32: int | None = None
    phase_after_u32: int | None = None
    stock_callback_result: object | None = None


@dataclass(frozen=True)
class ProjectDepthReadback:
    accepted: bool
    status: str
    track_id: int
    instance_id: int
    raw_depth: int | None
    compact_depth_units: int | None
    formatted_value: str | None
    selection_generation: int
    phase_u32: int | None


class Lfo2ProjectEditAdapter:
    """Selected-editor bridge with independent LFO2 state and explicit inputs.

    ``stock_lfo1_depth_edit`` is an injected service that runs the original
    ``(receiver, selector, delta)`` callback and returns the post-edit raw
    DEPTH read through the original getter.  ``original_stock_depth_formatter``
    must invoke/return the original formatter's string for a raw DEPTH value.
    Optional LFO2 native-storage services route LFO2 edits/readbacks to an
    independent constructor-backed bank using original MAIN setter/getter/
    formatter code. Without those services the LFO2 bank remains host-owned.

    ``selection_generation`` makes events from a previous editor selection
    stale even when the same track/instance is later selected again.  Track,
    instance, descriptor/control, and event ID are mandatory at every edit.
    The ``Lfo2ConfigBank`` is the single project-owned semantic config store;
    its acquired immutable snapshot is the source projected to guest controls.
    If a bank is injected, it is authoritative and is never reseeded from the
    optional native-raw fixture values. Raw values seed only a bank created by
    this adapter.
    """

    def __init__(self, *,
                 stock_lfo1_depth_edit: Callable[[object, int, int], int],
                 original_stock_depth_formatter: Callable[[int], str],
                 config_bank: Lfo2ConfigBank | None = None,
                 audio_phase_bank: AudioPhaseBank | None = None,
                 initial_depth_raws: tuple[int, ...] | None = None,
                 lfo2_depth_reader: Callable[[int], int] | None = None,
                 lfo2_depth_edit: Callable[[int, int], int] | None = None,
                 lfo2_depth_formatter: Callable[[int, int], str] | None = None):
        if not callable(stock_lfo1_depth_edit):
            raise TypeError("stock_lfo1_depth_edit must be an injected callable")
        if not callable(original_stock_depth_formatter):
            raise TypeError("original_stock_depth_formatter must be an injected callable")
        if config_bank is not None and not isinstance(config_bank, Lfo2ConfigBank):
            raise TypeError("config_bank must be Lfo2ConfigBank")
        if audio_phase_bank is not None and not isinstance(audio_phase_bank, AudioPhaseBank):
            raise TypeError("audio_phase_bank must be AudioPhaseBank")
        lfo2_services = (lfo2_depth_reader, lfo2_depth_edit,
                         lfo2_depth_formatter)
        if any(service is not None for service in lfo2_services) and not all(
                callable(service) for service in lfo2_services):
            raise TypeError(
                "LFO2 native storage requires reader, editor, and formatter services")
        raws = ((DEPTH_RAW_NEUTRAL,) * TRACK_COUNT if initial_depth_raws is None
                else tuple(initial_depth_raws))
        if len(raws) != TRACK_COUNT:
            raise ValueError("initial_depth_raws must contain six track values")
        for raw in raws:
            if type(raw) is not int or not DEPTH_RAW_MIN <= raw <= DEPTH_RAW_MAX:
                raise ValueError("initial DEPTH raw values must be integers in 0..0x7f00")

        owns_config_bank = config_bank is None
        self.config_bank = (Lfo2ConfigBank() if config_bank is None
                            else config_bank)
        self.audio_phase_bank = audio_phase_bank or AudioPhaseBank()
        self._stock_lfo1_depth_edit = stock_lfo1_depth_edit
        self._format_depth = original_stock_depth_formatter
        self._lfo2_depth_reader = lfo2_depth_reader
        self._lfo2_depth_edit = lfo2_depth_edit
        self._lfo2_depth_formatter = lfo2_depth_formatter
        self._raw_depth = list(raws)
        if self._lfo2_depth_reader is not None:
            for track_id, expected in enumerate(raws):
                observed = self._lfo2_depth_reader(track_id)
                if type(observed) is not int or observed != expected:
                    raise ValueError(
                        f"LFO2 backend track {track_id} starts at {observed!r}; "
                        f"expected {expected:#x}")
        # Import raw values only into the bank owned by this adapter. An
        # injected bank may already contain extended or otherwise independent
        # project settings, and attaching the edit bridge must not reset them.
        if owns_config_bank:
            for track_id, raw in enumerate(raws):
                compact = stock_depth_raw_to_compact_units(raw)
                current = self.config_bank.read_control(
                    track_id, LFO2, DEPTH_CONTROL).native_value
                if current != compact:
                    result = self.config_bank.apply_external_write(
                        track_id, LFO2, DEPTH_CONTROL, compact,
                        "initialization", f"initial-depth-{track_id}")
                    if result.status != "APPLIED":
                        raise ValueError(
                            "project config bank rejected initial DEPTH")
        self._selected_instance = [LFO1] * TRACK_COUNT
        self._active_track: int | None = None
        self._selection_generation = 0
        self._seen_events: set[tuple[int, int, int, str | int]] = set()
        self._lock = threading.RLock()

    def select_editor(self, track_id: int, instance_id: int) -> EditorSelection:
        """Set the explicit editor target and return its freshness token."""
        if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
            raise ValueError("track_id must be an integer in 0..5")
        if type(instance_id) is not int or instance_id not in (LFO1, LFO2):
            raise ValueError("instance_id must be exactly 1 or 2")
        with self._lock:
            self._active_track = track_id
            self._selected_instance[track_id] = instance_id
            self.config_bank.select_instance(track_id, instance_id)
            self._selection_generation += 1
            return EditorSelection(track_id, instance_id,
                                   self._selection_generation)

    def read_lfo2_depth(self, track_id: int) -> tuple[int, int, int]:
        """Return (stock raw encoding, compact units, config generation)."""
        if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
            raise ValueError("track_id must be an integer in 0..5")
        with self._lock:
            raw = self._read_lfo2_raw(track_id)
            config = self.config_bank.read_control(
                track_id, LFO2, DEPTH_CONTROL)
            return raw, int(config.native_value), config.generation

    def read_selected_lfo2_depth(self, *, track_id: int,
                                 selection_generation: int) -> ProjectDepthReadback:
        """Format LFO2's current DEPTH only when its editor selection is live.

        This is a project-adapter readback using the injected original stock
        formatter. It intentionally does not substitute for an LFO1 getter or
        imply that a native OLED draw occurred.
        """
        if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
            raise ValueError("track_id must be an integer in 0..5")
        if type(selection_generation) is not int:
            raise ValueError("selection_generation must be an integer token")
        with self._lock:
            if self._active_track != track_id:
                return ProjectDepthReadback(
                    False, "STALE_TRACK", track_id, LFO2, None, None, None,
                    selection_generation, None)
            if selection_generation != self._selection_generation:
                return ProjectDepthReadback(
                    False, "STALE_SELECTION", track_id, LFO2, None, None,
                    None, selection_generation, None)
            if self._selected_instance[track_id] != LFO2:
                return ProjectDepthReadback(
                    False, "LFO1_NATIVE_GETTER_REQUIRED", track_id, LFO1,
                    None, None, None, selection_generation, None)
            raw = self._read_lfo2_raw(track_id)
            compact = self.config_bank.read_control(
                track_id, LFO2, DEPTH_CONTROL).native_value
            phase = self.audio_phase_bank.read_audio_owned(track_id).phase_u32
            formatted = self._format_lfo2_depth(track_id, raw)
            if type(formatted) is not str:
                raise TypeError("original stock formatter must return a string")
            if self.audio_phase_bank.read_audio_owned(track_id).phase_u32 != phase:
                raise AssertionError("DEPTH readback changed audio-owned phase")
            return ProjectDepthReadback(
                True, "LFO2_FORMATTED_READBACK", track_id, LFO2, raw,
                compact, formatted, selection_generation, phase)

    def apply_depth_callback(self, *, receiver: object,
                             selector: int,
                             delta: int,
                             track_id: int,
                             instance_id: int,
                             control: str,
                             control_id: int,
                             event_id: str | int,
                             selection_generation: int) -> ProjectEditResult:
        """Route one explicit stock-ABI DEPTH edit to LFO1 or project LFO2.

        Rejected events are side-effect free. LFO1 delegates to the installed
        stock menu callback. LFO2 uses its independent project bank; when
        constructor-backed services are supplied, its edit, pointer getter,
        and formatter execute original stock MAIN code on separate records.
        """
        if receiver is None:
            raise ValueError("receiver is required")
        if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
            raise ValueError("track_id must be an integer in 0..5")
        if type(instance_id) is not int or instance_id not in (LFO1, LFO2):
            raise ValueError("instance_id must be exactly 1 or 2")
        if not _event_id(event_id):
            raise ValueError("event_id must be a nonempty string or integer")
        if type(selection_generation) is not int:
            raise ValueError("selection_generation must be an integer token")
        callback_arguments = (receiver, selector, delta)

        with self._lock:
            if self._active_track != track_id:
                return self._rejected("STALE_TRACK", track_id, instance_id,
                                      control, control_id, event_id,
                                      callback_arguments, selection_generation)
            if (self._selected_instance[track_id] != instance_id or
                    selection_generation != self._selection_generation):
                return self._rejected("STALE_SELECTION", track_id, instance_id,
                                      control, control_id, event_id,
                                      callback_arguments, selection_generation)
            if type(control) is not str or control != DEPTH_CONTROL or \
                    type(control_id) is not int or control_id != DEPTH_DESCRIPTOR_ID:
                return self._rejected("UNSUPPORTED_CONTROL", track_id, instance_id,
                                      control, control_id, event_id,
                                      callback_arguments, selection_generation)
            if type(selector) is not int or selector != CALLBACK_SELECTOR:
                return self._rejected("UNSUPPORTED_CALLBACK_SELECTOR", track_id,
                                      instance_id, control, control_id, event_id,
                                      callback_arguments, selection_generation)
            if type(delta) is not int or delta not in (-1, 0, 1):
                return self._rejected("UNSUPPORTED_CALLBACK_DELTA", track_id,
                                      instance_id, control, control_id, event_id,
                                      callback_arguments, selection_generation)

            key = (track_id, instance_id, control_id, event_id)
            if key in self._seen_events:
                return self._rejected("DUPLICATE_EVENT", track_id, instance_id,
                                      control, control_id, event_id,
                                      callback_arguments, selection_generation)
            # Claim before calling an external stock service: if that service
            # mutates LFO1 and then raises during readback, replaying the same
            # event must not apply the detent twice.
            self._seen_events.add(key)

            if instance_id == LFO1:
                raw = self._stock_lfo1_depth_edit(*callback_arguments)
                if type(raw) is not int or not DEPTH_RAW_MIN <= raw <= DEPTH_RAW_MAX:
                    raise ValueError("stock LFO1 edit service must return raw DEPTH 0..0x7f00")
                formatted = self._format_depth(raw)
                if type(formatted) is not str:
                    raise TypeError("original stock formatter must return a string")
                return ProjectEditResult(
                    True, "DELEGATED_LFO1", track_id, instance_id,
                    control, control_id, event_id, callback_arguments,
                    selection_generation, new_raw_depth=raw,
                    formatted_value=formatted,
                    stock_callback_result=raw)

            old_raw = self._read_lfo2_raw(track_id)
            old_compact = self.config_bank.read_control(
                track_id, LFO2, DEPTH_CONTROL).native_value
            phase_before = self.audio_phase_bank.read_audio_owned(track_id).phase_u32
            if self._lfo2_depth_edit is not None:
                new_raw = self._lfo2_depth_edit(track_id, delta)
                if type(new_raw) is not int or not DEPTH_RAW_MIN <= new_raw <= DEPTH_RAW_MAX:
                    raise ValueError("native LFO2 DEPTH getter returned an invalid raw word")
                observed_raw = self._lfo2_depth_reader(track_id)
                if observed_raw != new_raw:
                    raise AssertionError("native LFO2 setter/getter disagree")
                was_clamped = ((delta > 0 and new_raw == DEPTH_RAW_MAX) or
                               (delta < 0 and new_raw == DEPTH_RAW_MIN))
            else:
                candidate = old_raw + delta * DEPTH_RAW_PER_CALLBACK_DETENT
                new_raw = min(DEPTH_RAW_MAX, max(DEPTH_RAW_MIN, candidate))
                was_clamped = new_raw != candidate
            formatted = self._format_lfo2_depth(track_id, new_raw)
            if type(formatted) is not str:
                raise TypeError("original stock formatter must return a string")
            new_compact = stock_depth_raw_to_compact_units(new_raw)
            if not DEPTH_MIN_COMPACT_UNITS <= new_compact <= DEPTH_MAX_COMPACT_UNITS:
                raise AssertionError("stock raw conversion escaped bounded compact depth")

            # Commit only project-owned state after the original formatter
            # service succeeds.  Phase is separate and deliberately untouched.
            if new_raw != old_raw:
                self._raw_depth[track_id] = new_raw
                published_write = self.config_bank.apply_ui_write(
                    track_id, LFO2, DEPTH_CONTROL, new_compact, event_id)
                if published_write.status != "APPLIED":
                    raise AssertionError(
                        "native LFO2 edit did not commit to selected project bank: "
                        f"{published_write.status}")
            phase_after = self.audio_phase_bank.read_audio_owned(track_id).phase_u32
            if was_clamped:
                status = "CLAMPED"
            elif delta == 0:
                status = "NEUTRAL"
            elif new_compact == old_compact:
                status = "APPLIED_QUANTIZED_NEUTRAL"
            else:
                status = "APPLIED"
            return ProjectEditResult(
                True, status, track_id, instance_id, control, control_id,
                event_id, callback_arguments, selection_generation,
                old_raw, new_raw, old_compact, new_compact, formatted,
                phase_before, phase_after)

    def publish_guest_block_snapshot(self, track_id: int,
                                     native_rate_scalar: int):
        """Publish/acquire LFO2 config, then derive its bounded guest inputs.

        The immutable snapshot is the one and only project-bank state passed
        across this host block boundary. Python object identity here is not an
        MCU atomicity/cache-coherency guarantee.
        """
        if type(track_id) is not int or not 0 <= track_id < TRACK_COUNT:
            raise ValueError("track_id must be an integer in 0..5")
        with self._lock:
            published = self.config_bank.publish_block_boundary(
                track_id, native_rate_scalar)
            acquired = self.config_bank.acquire_block_snapshot(track_id)
            if acquired is None or acquired is not published:
                raise AssertionError("published LFO2 block snapshot is missing")
            mapped = map_published_track_snapshot(acquired)
            result = project_guest_runner_config(mapped, self.audio_phase_bank)
        if result is None:
            return acquired, None
        if result.get("destination") != 10:
            raise AssertionError("guest projection escaped proven PITCH destination")
        if result.get("depth") not in (0, 1) or acquired.lfo2.waveform != 0:
            raise AssertionError("guest projection escaped its strict square/depth subset")
        return acquired, result

    def guest_runner_config(self, track_id: int,
                            native_rate_scalar: int) -> dict | None:
        """Compatibility projection from the current project-owned snapshot."""
        _, config = self.publish_guest_block_snapshot(
            track_id, native_rate_scalar)
        return config

    def _read_lfo2_raw(self, track_id: int) -> int:
        if self._lfo2_depth_reader is None:
            return self._raw_depth[track_id]
        raw = self._lfo2_depth_reader(track_id)
        if type(raw) is not int or not DEPTH_RAW_MIN <= raw <= DEPTH_RAW_MAX:
            raise ValueError("LFO2 DEPTH backend returned an invalid raw word")
        if raw != self._raw_depth[track_id]:
            raise AssertionError(
                f"LFO2 native/host project state diverged on track {track_id}: "
                f"{raw:#x} != {self._raw_depth[track_id]:#x}")
        return raw

    def _format_lfo2_depth(self, track_id: int, raw: int) -> str:
        if self._lfo2_depth_formatter is None:
            return self._format_depth(raw)
        return self._lfo2_depth_formatter(track_id, raw)

    @staticmethod
    def _rejected(status: str, track_id: int, instance_id: int,
                  control: str, control_id: int, event_id: str | int,
                  callback_arguments: tuple[object, int, int],
                  selection_generation: int) -> ProjectEditResult:
        return ProjectEditResult(
            False, status, track_id, instance_id, control, control_id,
            event_id, callback_arguments, selection_generation)


__all__ = [
    "CALLBACK_SELECTOR", "DEPTH_CONTROL", "DEPTH_DESCRIPTOR_ID",
    "DEPTH_RAW_MAX", "DEPTH_RAW_MIN", "DEPTH_RAW_NEUTRAL",
    "DEPTH_RAW_PER_CALLBACK_DETENT", "EditorSelection", "LFO1", "LFO2",
    "Lfo2ProjectEditAdapter", "ProjectDepthReadback", "ProjectEditResult",
]
