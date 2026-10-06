# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/lfo_runtime_experiment_20260918.py; lines 1-108.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Pure-data plan for the bounded LFO runtime discriminator.

This module does not talk to a device.  It emits the USB-MIDI stimuli and
object-relative watch labels used by the accompanying runtime report so the
capture can be reproduced without inventing addresses or semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MidiMessage:
    controller: int
    value: int

    def bytes(self, channel: int = 0) -> tuple[int, int, int]:
        if not 0 <= channel <= 15:
            raise ValueError("channel must be in 0..15")
        if not 0 <= self.controller <= 127:
            raise ValueError("controller must be in 0..127")
        if not 0 <= self.value <= 127:
            raise ValueError("value must be in 0..127")
        return (0xB0 | channel, self.controller, self.value)


@dataclass(frozen=True)
class StimulusWindow:
    name: str
    messages: tuple[MidiMessage, ...]
    held_note: bool
    purpose: str


WATCHES = (
    "family1.owner+0x10 pointee / child+0x16 Speed",
    "family1 child+0x1c Destination",
    "family1 child+0x24 Depth",
    "family2 owner+0x10 pointee / slot+0x08",
    "R+0x10+0x42*r Speed versus R+0x16+0x42*r Destination",
    "C+0x08 compact reader",
    "0x40fde838+0x20*r derived records",
    "0x40fde854+0x20*r derived flags",
    "R+0x1dc+4*r and R+0x1f4+4*r indexed inputs",
    "C+2*q indexed compact stores",
    "S[r]+0x6c and S[r]+0x70 phase/application correlation",
)


def stimulus_windows() -> tuple[StimulusWindow, ...]:
    return (
        StimulusWindow(
            "configuration-baseline",
            (MidiMessage(105, 0), MidiMessage(105, 10), MidiMessage(105, 18),
             MidiMessage(102, 32), MidiMessage(102, 96)),
            False,
            "Separate owner-buffer writes from periodic render/state writes.",
        ),
        StimulusWindow(
            "pitch-live-output",
            (MidiMessage(105, 10), MidiMessage(109, 0), MidiMessage(110, 0),
             MidiMessage(109, 96), MidiMessage(110, 32)),
            True,
            "Test live output, Speed/Depth dependence, and Destination=Pitch.",
        ),
        StimulusWindow(
            "destination-routing",
            (MidiMessage(105, 11), MidiMessage(109, 96), MidiMessage(110, 32),
             MidiMessage(105, 18), MidiMessage(109, 96), MidiMessage(110, 32)),
            True,
            "Compare Color and Decay routing against the Pitch trace.",
        ),
        StimulusWindow(
            "phase-reset",
            (MidiMessage(108, 0), MidiMessage(107, 64), MidiMessage(107, 96),
             MidiMessage(108, 1)),
            True,
            "Separate phase/retrigger/reset behavior from static configuration.",
        ),
        StimulusWindow(
            "multiple-source",
            (MidiMessage(105, 10), MidiMessage(109, 96), MidiMessage(110, 32),
             MidiMessage(102, 48), MidiMessage(102, 80)),
            True,
            "Repeat with a known base/p-lock step to test accumulation versus overwrite.",
        ),
    )


def midi_bytes(windows: Iterable[StimulusWindow], channel: int = 0) -> tuple[tuple[int, int, int], ...]:
    return tuple(message.bytes(channel) for window in windows for message in window.messages)


def compact_address(base: int, region: int, slot: int) -> int:
    """Return C[region]+2*slot for the established compact geometry."""
    if not 0 <= region < 6:
        raise ValueError("region must be in 0..5")
    if not 0 <= slot <= 32:
        raise ValueError("slot must be in 0..32")
    return base + 0x0E + 0x42 * region + 2 * slot


if __name__ == "__main__":
    for window in stimulus_windows():
        print(window.name)
        print("  " + " ".join("%02x %02x %02x" % message.bytes() for message in window.messages))
