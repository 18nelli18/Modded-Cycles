# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo2_ui_gesture.py; lines 1-527.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Host-side LFO editor gesture and display-selection policy.

This module intentionally stops at a view/readback descriptor.  The checked-in
OLED evidence proves the normal ParameterPageView draw/formatter path, but not
the encoder/MIDI invalidation observer or a transient-overlay timeout owner.
Consequently this module does not invent a native screen, timer, or draw call.

Time values are abstract replay ticks, not recovered firmware units. The
prototype uses seven ticks for the release threshold (approximately 700 ms
only if a future caller establishes a 100 ms tick). There is no elapsed-time
watchdog: a held press remains pending until release, explicit lost-release,
or context change. Elapsed time cannot distinguish a missing release from a
legitimate long hold.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Hashable


TRACK_COUNT = 6
INSTANCE_IDS = (1, 2)
DEFAULT_INSTANCE_ID = 1
CONTROL_NAMES = frozenset(
    {
        "speed",
        "multiplier",
        "fade",
        "destination",
        "waveform",
        "start_phase",
        "trig_mode",
        "depth",
    }
)

DEFAULT_HOLD_TICKS = 7
ABSTRACT_TICK_BASIS = (
    "Uncalibrated logical replay ticks. Seven ticks model the intended ~700 ms "
    "hold only under an explicit 100 ms/tick integration assumption; no native "
    "timer unit or cadence is proven. Lost releases require an explicit "
    "LOST_RELEASE event; no elapsed-time deadline is applied."
)


class EventKind(str, Enum):
    LFO_PRESS = "lfo_press"
    LFO_RELEASE = "lfo_release"
    FUNC_PRESS = "func_press"
    FUNC_RELEASE = "func_release"
    KNOB_TURN = "knob_turn"
    TRACK_CHANGE = "track_change"
    PAGE_CHANGE = "page_change"
    TICK = "tick"
    LOST_RELEASE = "lost_release"


class Action(str, Enum):
    PASS_THROUGH = "pass_through"
    PENDING_HOLD = "pending_hold"
    SELECTION_CHANGED = "selection_changed"
    CHORD_CONSUMED = "chord_consumed"
    GESTURE_CANCELLED = "gesture_cancelled"
    CONTEXT_CHANGED = "context_changed"
    STATE_UPDATED = "state_updated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class UiEvent:
    """Normalized event with caller-supplied monotonic sequence and tick."""

    sequence: int
    tick: int
    kind: EventKind
    track_id: int | None = None
    page_id: Hashable | None = None


@dataclass(frozen=True)
class ReadbackPolicyDescriptor:
    """Selection identity plus only the already-established normal draw path.

    ``descriptor_index`` is deliberately absent: the native mapping from the
    selected LFO bank to a ParameterPageView descriptor is not established.
    This is a host policy/readback request, not a rendered OLED screen.
    """

    track_id: int
    instance_id: int
    status: str = "POLICY_ONLY_NORMAL_READBACK"
    draw_entry: str = "ParameterPageView vtable +0x10 -> FUN_4001e40a"
    descriptor_label_source: str = "FUN_4000b22a -> registry record +0x2c"
    value_source: str = (
        "current or selected-step value chosen before parameter virtual +0x3c"
    )
    formatter: str = "selected parameter object's virtual +0x3c"
    measurement_helpers: tuple[str, ...] = ("FUN_400722b2", "FUN_40072260")
    bitmap_draw: str = "FUN_40071a04"
    descriptor_index_mapping: str = "UNRESOLVED; not inferred from bank selection"
    invalidation_edge: str = "UNRESOLVED; encoder/MIDI-to-redraw observer not proven"
    transient_overlay: str = "NOT_REQUESTED; no synthetic native overlay"
    timeout_owner: str = "UNRESOLVED; no stock UI deadline owner identified"
    blocker: str = (
        "A native UI trace must join selected LFO bank/control to the existing "
        "ParameterPageView descriptor/readback and identify the redraw observer; "
        "if a transient hint is later required, its UI timeout/dismissal owner "
        "must be independently recovered."
    )


@dataclass(frozen=True)
class ExternalTarget:
    """Explicit MIDI/p-lock destination; never derived from editor selection."""

    source: str
    track_id: int
    instance_id: int
    control: str
    event_id: int


@dataclass(frozen=True)
class PolicyResult:
    accepted: bool
    action: Action
    reason: str
    track_id: int
    selected_instance_id: int
    # The recognizer consumed/canceled its bank-toggle interpretation. A
    # recognized long-hold release is consumed before stock dispatch because
    # the observed stock release deactivates the retained parameter row.
    consumed: bool = False
    # Whether the original input event must still reach stock dispatch exactly
    # once. False for a consumed long-hold release; this is host policy, not a
    # recovered firmware callback or a device-side bank-toggle feature.
    forward_event: bool = False
    cancellation_reason: str | None = None
    readback: ReadbackPolicyDescriptor | None = None
    readback_callback_count: int = 0


def stock_tag0_code8_gesture_kind(event_code: int, flags: int) -> EventKind | None:
    """Decode only the statically recovered, unmodified code-8 button forms.

    This is a host adapter from tag-0 task records, not a physical-key label.
    Press forms 1/5 and ordinary release form 16 map to the hold recognizer.
    Bit-1/Setup variants and all other event shapes are intentionally left
    uninterpreted so stock dispatch can still receive them unchanged.
    """

    if (type(event_code) is not int or not 0 <= event_code <= 0xFFFFFFFF or
            type(flags) is not int or not 0 <= flags <= 0xFFFFFFFF):
        raise ValueError("event_code and flags must be unsigned 32-bit integers")
    if event_code != 8:
        return None
    if flags in (1, 5):
        return EventKind.LFO_PRESS
    if flags == 16:
        return EventKind.LFO_RELEASE
    return None


def _validate_track(track_id: int) -> None:
    if not isinstance(track_id, int) or isinstance(track_id, bool):
        raise ValueError("track_id must be an integer in 0..5")
    if not 0 <= track_id < TRACK_COUNT:
        raise ValueError("track_id must be an integer in 0..5")


def _validate_instance(instance_id: int) -> None:
    if (
        not isinstance(instance_id, int)
        or isinstance(instance_id, bool)
        or instance_id not in INSTANCE_IDS
    ):
        raise ValueError("instance_id must be explicitly 1 or 2")


def route_external_target(
    *, source: str, track_id: int, instance_id: int, control: str, event_id: int
) -> ExternalTarget:
    """Validate an external target without reading or changing UI selection.

    This creates routing metadata only; applying the MIDI/p-lock write belongs
    to the independent config/control path.
    """

    _validate_track(track_id)
    _validate_instance(instance_id)
    if type(source) is not str:
        raise ValueError("source must be 'midi' or 'plock'")
    normalized_source = source.lower()
    if normalized_source not in {"midi", "plock"}:
        raise ValueError("source must be 'midi' or 'plock'")
    if type(control) is not str or control not in CONTROL_NAMES:
        raise ValueError(f"unsupported LFO control: {control!r}")
    if not isinstance(event_id, int) or isinstance(event_id, bool) or event_id < 0:
        raise ValueError("event_id must be a non-negative integer")
    return ExternalTarget(
        source=normalized_source,
        track_id=track_id,
        instance_id=instance_id,
        control=control,
        event_id=event_id,
    )


class LfoUiGesturePolicy:
    """Deterministic long-hold/chord policy with per-track session selection.

    The only optional callback is a readback-policy observer.  No config-store
    or phase API is accepted here, making selection structurally view-only.
    """

    def __init__(
        self,
        *,
        initial_track_id: int = 0,
        initial_page_id: Hashable = "lfo_editor",
        hold_ticks: int = DEFAULT_HOLD_TICKS,
        on_readback_policy: Callable[[ReadbackPolicyDescriptor], None] | None = None,
    ) -> None:
        _validate_track(initial_track_id)
        if type(hold_ticks) is not int or hold_ticks < 1:
            raise ValueError("hold_ticks must be a positive integer")
        self.hold_ticks = hold_ticks
        self.current_track_id = initial_track_id
        self.current_page_id = initial_page_id
        self._selected = [DEFAULT_INSTANCE_ID] * TRACK_COUNT
        self._last_sequence = -1
        self._now_tick = -1
        self._lfo_down = False
        self._lfo_press_tick: int | None = None
        self._press_track_id: int | None = None
        self._press_page_id: Hashable | None = None
        self._lfo_consumed = False
        self._chord_reason: str | None = None
        self._func_down = False
        self._on_readback_policy = on_readback_policy

    @property
    def selected_instance_id(self) -> int:
        return self._selected[self.current_track_id]

    def selected_for_track(self, track_id: int) -> int:
        _validate_track(track_id)
        return self._selected[track_id]

    @property
    def lfo_press_pending(self) -> bool:
        return self._lfo_down

    @property
    def func_press_pending(self) -> bool:
        return self._func_down

    def readback_descriptor(
        self, *, track_id: int | None = None
    ) -> ReadbackPolicyDescriptor:
        track = self.current_track_id if track_id is None else track_id
        _validate_track(track)
        return ReadbackPolicyDescriptor(track, self._selected[track])

    def _result(
        self,
        action: Action,
        reason: str,
        *,
        accepted: bool = True,
        consumed: bool = False,
        forward_event: bool = False,
        cancellation_reason: str | None = None,
        readback: ReadbackPolicyDescriptor | None = None,
        callback_count: int = 0,
        track_id: int | None = None,
    ) -> PolicyResult:
        track = self.current_track_id if track_id is None else track_id
        return PolicyResult(
            accepted=accepted,
            action=action,
            reason=reason,
            track_id=track,
            selected_instance_id=self._selected[track],
            consumed=consumed,
            forward_event=forward_event,
            cancellation_reason=cancellation_reason,
            readback=readback,
            readback_callback_count=callback_count,
        )

    def _clear_lfo(self) -> None:
        self._lfo_down = False
        self._lfo_press_tick = None
        self._press_track_id = None
        self._press_page_id = None
        self._lfo_consumed = False
        self._chord_reason = None

    def _clear_func(self) -> None:
        self._func_down = False

    def _reject(self, reason: str) -> PolicyResult:
        return self._result(Action.REJECTED, reason, accepted=False)

    def handle(self, event: UiEvent) -> PolicyResult:
        """Apply one normalized event; rejected events do not mutate policy."""

        if not isinstance(event, UiEvent):
            raise TypeError("event must be UiEvent")
        if not isinstance(event.sequence, int) or isinstance(event.sequence, bool):
            return self._reject("INVALID_SEQUENCE")
        if not isinstance(event.tick, int) or isinstance(event.tick, bool) or event.tick < 0:
            return self._reject("INVALID_TICK")
        if event.sequence <= self._last_sequence:
            reason = (
                "DUPLICATE_SEQUENCE"
                if event.sequence == self._last_sequence
                else "OUT_OF_ORDER_SEQUENCE"
            )
            return self._reject(reason)
        if event.tick < self._now_tick:
            return self._reject("STALE_EVENT_TICK")
        if not isinstance(event.kind, EventKind):
            return self._reject("UNKNOWN_EVENT_KIND")

        # Normalized UI producers may deliver an event after focus has moved
        # to another track.  Do not reinterpret that stale event in the new
        # track's context (especially an LFO press/release pair).  A rejected
        # stale event does not consume sequence state, so the producer may
        # retry the same sequence with the corrected track identity.
        if event.kind is not EventKind.TRACK_CHANGE and event.track_id is not None:
            try:
                _validate_track(event.track_id)
            except ValueError:
                return self._reject("INVALID_EVENT_TRACK")
            if event.track_id != self.current_track_id:
                return self._reject("STALE_EVENT_TRACK")

        # The sequence is consumed once ordering is valid, even when the event
        # is a semantic duplicate (e.g. a second press with a fresh sequence).
        self._last_sequence = event.sequence
        self._now_tick = event.tick

        if event.kind is EventKind.TICK:
            return self._result(Action.STATE_UPDATED, "clock advanced")

        if event.kind is EventKind.LOST_RELEASE:
            if self._lfo_down or self._func_down:
                self._clear_lfo()
                self._clear_func()
                return self._result(
                    Action.GESTURE_CANCELLED,
                    "input source reported a lost release",
                    consumed=True,
                    cancellation_reason="EXPLICIT_LOST_RELEASE",
                )
            return self._reject("UNMATCHED_LOST_RELEASE")

        if event.kind is EventKind.TRACK_CHANGE:
            if event.track_id is None:
                return self._reject("TRACK_CHANGE_MISSING_TRACK")
            try:
                _validate_track(event.track_id)
            except ValueError:
                return self._reject("TRACK_CHANGE_INVALID_TRACK")
            changed = event.track_id != self.current_track_id
            cancelled = self._lfo_down or self._func_down
            if changed:
                self.current_track_id = event.track_id
            if cancelled:
                self._clear_lfo()
                self._clear_func()
            return self._result(
                Action.CONTEXT_CHANGED if changed else Action.STATE_UPDATED,
                "track changed" if changed else "track unchanged",
                cancellation_reason=("TRACK_CHANGE" if cancelled else None),
            )

        if event.kind is EventKind.PAGE_CHANGE:
            if event.page_id is None:
                return self._reject("PAGE_CHANGE_MISSING_PAGE")
            changed = event.page_id != self.current_page_id
            cancelled = changed and (self._lfo_down or self._func_down)
            self.current_page_id = event.page_id
            if cancelled:
                self._clear_lfo()
                self._clear_func()
            return self._result(
                Action.CONTEXT_CHANGED if changed else Action.STATE_UPDATED,
                "page changed" if changed else "page unchanged",
                cancellation_reason=("PAGE_CHANGE" if cancelled else None),
            )

        if event.kind is EventKind.FUNC_PRESS:
            if self._func_down:
                return self._reject("DUPLICATE_FUNC_PRESS")
            self._func_down = True
            if self._lfo_down:
                self._consume_lfo("FUNC_PLUS_LFO")
                return self._result(
                    Action.CHORD_CONSUMED,
                    "FUNC+LFO consumed; bank toggle cancelled",
                    consumed=True,
                    forward_event=True,
                    cancellation_reason="FUNC_PLUS_LFO",
                )
            return self._result(
                Action.PASS_THROUGH, "FUNC press recorded", forward_event=True
            )

        if event.kind is EventKind.FUNC_RELEASE:
            if not self._func_down:
                return self._reject("UNMATCHED_OR_DUPLICATE_FUNC_RELEASE")
            self._clear_func()
            return self._result(
                Action.PASS_THROUGH, "FUNC release recorded", forward_event=True
            )

        if event.kind is EventKind.LFO_PRESS:
            if self._lfo_down:
                return self._reject("DUPLICATE_LFO_PRESS")
            self._lfo_down = True
            self._lfo_press_tick = event.tick
            self._press_track_id = self.current_track_id
            self._press_page_id = self.current_page_id
            self._lfo_consumed = False
            self._chord_reason = None
            if self._func_down:
                self._consume_lfo("FUNC_PLUS_LFO")
                return self._result(
                    Action.CHORD_CONSUMED,
                    "FUNC+LFO consumed; bank toggle cancelled",
                    consumed=True,
                    forward_event=True,
                    cancellation_reason="FUNC_PLUS_LFO",
                )
            return self._result(
                Action.PENDING_HOLD,
                "LFO hold pending; original press remains routable",
                forward_event=True,
            )

        if event.kind is EventKind.KNOB_TURN:
            if self._lfo_down and not self._lfo_consumed:
                self._consume_lfo("LFO_PLUS_KNOB")
                return self._result(
                    Action.CHORD_CONSUMED,
                    "LFO press consumed; knob event remains routable",
                    consumed=True,
                    forward_event=True,
                    cancellation_reason="LFO_PLUS_KNOB",
                )
            return self._result(
                Action.PASS_THROUGH,
                "knob event is not a bank gesture",
                forward_event=True,
            )

        if event.kind is EventKind.LFO_RELEASE:
            if not self._lfo_down:
                return self._reject("UNMATCHED_OR_DUPLICATE_LFO_RELEASE")
            # PAGE_CHANGE normally cancels an in-flight press. If the
            # normalized producer misses that event but tags the release with
            # its current page, use the press-time identity as a second guard:
            # a release from another page cannot complete the bank toggle.
            # Synchronize the observed page and clear both button states so a
            # missing context event cannot leave a stale hold/ modifier stuck.
            if (event.page_id is not None
                    and event.page_id != self._press_page_id):
                self.current_page_id = event.page_id
                self._clear_lfo()
                self._clear_func()
                return self._result(
                    Action.GESTURE_CANCELLED,
                    "release arrived in a different page; bank selection unchanged",
                    consumed=True,
                    forward_event=True,
                    cancellation_reason="RELEASE_PAGE_MISMATCH",
                )
            assert self._lfo_press_tick is not None
            press_track = self._press_track_id
            duration = event.tick - self._lfo_press_tick
            if self._lfo_consumed:
                why = self._chord_reason or "CHORD"
                self._clear_lfo()
                return self._result(
                    Action.CHORD_CONSUMED,
                    "consumed press released; bank selection unchanged",
                    consumed=True,
                    forward_event=True,
                    cancellation_reason=why,
                )
            if duration < self.hold_ticks:
                self._clear_lfo()
                return self._result(
                    Action.PASS_THROUGH,
                    "short LFO press passed through; bank selection unchanged",
                    forward_event=True,
                )

            assert press_track is not None
            next_instance = 2 if self._selected[press_track] == 1 else 1
            self._selected[press_track] = next_instance
            self._clear_lfo()
            descriptor = ReadbackPolicyDescriptor(press_track, next_instance)
            callback_count = 0
            if self._on_readback_policy is not None:
                self._on_readback_policy(descriptor)
                callback_count = 1
            return self._result(
                Action.SELECTION_CHANGED,
                "long hold released; view selection toggled only",
                consumed=True,
                forward_event=False,
                readback=descriptor,
                callback_count=callback_count,
                track_id=press_track,
            )

        return self._reject("UNHANDLED_EVENT")

    def _consume_lfo(self, reason: str) -> None:
        self._lfo_consumed = True
        self._chord_reason = reason
