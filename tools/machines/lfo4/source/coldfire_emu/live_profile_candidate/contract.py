# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/contract.py; lines 1-112.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Offline contract oracle, not an instruction interpreter or runtime proof.

Native lookup and flags are explicit callouts. No imports of existing runner,
build recipe, backend, firmware image, or mutable runtime configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable


class Status(IntEnum):
    OK = 0
    GEOMETRY = 1
    OWNER_BINDING = 2
    LEASE = 3
    STOCK_BINDING = 4
    PROFILE = 5
    DOMAIN = 6
    MISSING = 7
    FILTER = 8
    BRIDGE = 9


@dataclass(frozen=True)
class Result:
    descriptor: int
    status: Status
    stock_entry: int = 0


class Memory:
    """Sparse declared readable bytes; inaccessible memory raises, as on target.

    This deliberately does not turn an arbitrary unmapped pointer into a
    purported assembly refusal: readable/live objects are caller preconditions.
    """
    def __init__(self):
        self.bytes = {}
        self.reads = []

    def put(self, address, value, size=4):
        for i, byte in enumerate(value.to_bytes(size, "big")):
            self.bytes[address + i] = byte

    def get(self, address, size=4):
        self.reads.append((address, size))
        return int.from_bytes(bytes(self.bytes[address+i] for i in range(size)), "big")


def pointer(value, size, alignment=4):
    return type(value) is int and 0 < value <= 2**32-size and value % alignment == 0


def checked(memory: Memory, owner: int, stock: int, extra: int, bank: int,
            track: int, value: int, native_lookup: Callable[[int, int], int],
            native_flags: Callable[[int], int] | None = None) -> Result:
    """Same ordered checks as lookup.S. native_flags selects EDIT preflight.

    Python rejects non-integers explicitly; target arguments are longwords.
    Result fields model D0/D1/A0, with no target code execution.
    """
    def fail(status):
        return Result(0, status)

    edit = native_flags is not None
    if (not pointer(owner, 4688) or not pointer(stock, 552)
            or type(bank) is not int or not 0 <= bank < 3
            or type(track) is not int or not 0 <= track < 6):
        return fail(Status.GEOMETRY)
    if (memory.get(owner) != 0x4c464f34 or memory.get(owner+4) != 1
            or memory.get(owner+40) != stock):
        return fail(Status.OWNER_BINDING)
    writer = memory.get(owner+72)
    if writer == 1:
        if memory.get(owner+76) != 0:
            return fail(Status.LEASE)
    elif writer != 0 or edit or memory.get(owner+76) != 1:
        return fail(Status.LEASE)
    if type(extra) is not int or extra != owner+680+768*bank+8*track:
        return fail(Status.GEOMETRY)
    if (memory.get(extra+4) != owner+272+768*bank+68*track
            or memory.get(extra) != owner+80):
        return fail(Status.GEOMETRY)
    entry, regional = stock+504+8*track, stock+96+68*track
    if (memory.get(entry+4) != regional or memory.get(regional) != 0x400fef54
            or memory.get(0x400fef7c) != 0x400d5632):
        return fail(Status.STOCK_BINDING)
    child = memory.get(regional+16)
    if not pointer(child, 100, alignment=2):
        return fail(Status.STOCK_BINDING)
    # Unsigned comparison with six also excludes the sign-extended negatives.
    if memory.get(child+38, 1) >= 6:
        return fail(Status.PROFILE)
    if type(value) is not int or not 0 <= value <= (0x20ff if edit else 32):
        return fail(Status.DOMAIN)
    ordinal = value >> 8 if edit else value
    descriptor = native_lookup(entry, ordinal)
    if type(descriptor) is not int or not 0 <= descriptor < 2**32:
        raise ValueError("native lookup must supply a longword result")
    if edit:
        if not descriptor:
            return fail(Status.MISSING)
        flags = native_flags(descriptor)
        if type(flags) is not int or not 0 <= flags < 2**32:
            raise ValueError("native flags must supply a longword result")
        if (~flags & 0x600) != 0:
            return fail(Status.FILTER)
    return Result(descriptor, Status.OK, entry)
