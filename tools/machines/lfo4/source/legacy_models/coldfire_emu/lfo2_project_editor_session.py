# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo2_project_editor_session.py; lines 1-151.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Host-policy gesture/session adapter for the project-owned LFO2 edit port.

This joins semantic long-hold selection to :mod:`lfo2_project_edit_adapter`.
UiEvent producers are still explicit host inputs: this module does not map
physical controls or normalized stock event numbers to those semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .lfo2_project_edit_adapter import (
    DEPTH_DESCRIPTOR_ID,
    EditorSelection,
    LFO1,
    LFO2,
    Lfo2ProjectEditAdapter,
    ProjectDepthReadback,
    ProjectEditResult,
)
from .lfo2_ui_config_bank import Readback
from .lfo2_ui_gesture import (
    Action,
    EventKind,
    LfoUiGesturePolicy,
    PolicyResult,
    UiEvent,
)


@dataclass(frozen=True)
class ProjectEditorEventResult:
    policy: PolicyResult
    selected_track_id: int
    selected_instance_id: int
    selection: EditorSelection
    readback: ProjectDepthReadback | None = None


class Lfo2ProjectEditorSession:
    """Keep host gesture selection and the independent project edit port in sync."""

    def __init__(self, adapter: Lfo2ProjectEditAdapter, *,
                 policy: LfoUiGesturePolicy | None = None,
                 stock_lfo1_depth_readback: Callable[[int], tuple[int, str]] | None = None
                 ) -> None:
        if not isinstance(adapter, Lfo2ProjectEditAdapter):
            raise TypeError("adapter must be Lfo2ProjectEditAdapter")
        self.adapter = adapter
        self.policy = policy or LfoUiGesturePolicy()
        if (stock_lfo1_depth_readback is not None and
                not callable(stock_lfo1_depth_readback)):
            raise TypeError("stock_lfo1_depth_readback must be callable")
        self._stock_lfo1_depth_readback = stock_lfo1_depth_readback
        self._selection = self.adapter.select_editor(
            self.policy.current_track_id, self.policy.selected_instance_id)

    @property
    def selection(self) -> EditorSelection:
        return self._selection

    def handle_gesture(self, event: UiEvent, *,
                       refresh_depth: bool = False) -> ProjectEditorEventResult:
        """Apply host input and optionally refresh selected DEPTH readback.

        refresh_depth is an explicit host presentation request. It runs only
        after an accepted instance-selection or track-change event, and reads
        through the selected bank's getter/formatter service. It does not
        imply an OLED invalidation/draw callback.
        """
        if type(refresh_depth) is not bool:
            raise TypeError("refresh_depth must be bool")
        result = self.policy.handle(event)
        if (result.accepted and
                (result.action is Action.SELECTION_CHANGED or
                 event.kind is EventKind.TRACK_CHANGE)):
            self._selection = self.adapter.select_editor(
                self.policy.current_track_id,
                self.policy.selected_instance_id)
        readback = None
        if (refresh_depth and result.accepted and
                (result.action is Action.SELECTION_CHANGED or
                 event.kind is EventKind.TRACK_CHANGE)):
            readback = self.read_selected_depth()
        return ProjectEditorEventResult(
            result, self.policy.current_track_id,
            self.policy.selected_instance_id, self._selection, readback)

    def apply_depth_callback(self, *, receiver: object, selector: int,
                             delta: int, event_id: str | int,
                             control: str = "depth",
                             control_id: int = DEPTH_DESCRIPTOR_ID) -> ProjectEditResult:
        """Forward one callback-ABI edit to the currently selected bank."""
        return self.adapter.apply_depth_callback(
            receiver=receiver,
            selector=selector,
            delta=delta,
            track_id=self.policy.current_track_id,
            instance_id=self.policy.selected_instance_id,
            control=control,
            control_id=control_id,
            event_id=event_id,
            selection_generation=self._selection.generation,
        )

    def apply_lfo2_multiplier_edit(self, raw_value: int,
                                   event_id: str | int) -> Readback:
        """Apply one multiplier edit through the currently selected LFO2 bank.

        This is the existing editor/config-bank boundary used by the bounded
        session fixture. It does not claim a physical encoder/event producer.
        """
        if self.policy.selected_instance_id != LFO2:
            raise RuntimeError("LFO2 multiplier edit requires selected LFO2")
        track_id = self.policy.current_track_id
        return self.adapter.config_bank.apply_ui_write(
            track_id, LFO2, "multiplier", raw_value, event_id)

    def read_selected_depth(self) -> ProjectDepthReadback:
        """Read the selected instance through its owned getter/formatter.

        LFO1 is available only when a caller supplies its stock getter/formatter
        service. LFO2 continues through the project adapter's independent bank.
        Neither path claims that an OLED draw or refresh occurred.
        """
        track_id = self.policy.current_track_id
        instance_id = self.policy.selected_instance_id
        if instance_id == LFO1:
            if self._stock_lfo1_depth_readback is None:
                return ProjectDepthReadback(
                    False, "LFO1_NATIVE_GETTER_REQUIRED", track_id, LFO1,
                    None, None, None, self._selection.generation, None)
            raw, formatted = self._stock_lfo1_depth_readback(track_id)
            if type(raw) is not int or not 0 <= raw <= 0xFFFF:
                raise ValueError("stock LFO1 raw DEPTH must be an unsigned halfword")
            if type(formatted) is not str or not formatted:
                raise ValueError("stock LFO1 formatter must return nonempty text")
            return ProjectDepthReadback(
                True, "ORIGINAL_STOCK_GETTER_FORMATTER", track_id, LFO1,
                raw, None, formatted, self._selection.generation, None)
        if instance_id != LFO2:
            return ProjectDepthReadback(
                False, "UNSUPPORTED_INSTANCE", track_id, instance_id,
                None, None, None, self._selection.generation, None)
        return self.adapter.read_selected_lfo2_depth(
            track_id=track_id,
            selection_generation=self._selection.generation,
        )


__all__ = ["Lfo2ProjectEditorSession", "ProjectEditorEventResult"]
