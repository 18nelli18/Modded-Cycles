# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/oracle.py; lines 1-129.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Independent finite-geometry oracle, NOT target instruction execution.

Sparse reads intentionally raise for unmapped published objects. Numeric checks
are not memory mapping, retained-allocation proof or an exception handler.
"""
from dataclasses import dataclass
from typing import Callable

OWNER_BYTES, M_BYTES, CONTEXT_BYTES = 6976, 0x1400, 698992
ROOT_BYTES, BANK_BASE, BANK_STRIDE = 0x37615c, 0x2cfc5c, 0x1bb6
PUBLICATION, READY, CURRENT_BANK = 10, 11, 12


@dataclass(frozen=True)
class Slots:
    # Illustrative offline fixture locations, NOT live replay bindings.
    owner: int = 0x40000304
    runtime: int = 0x40000300
    boot_status: int = 0x46e38000
    context: int = 0x46e39000
    root_binder: int = 0x404d2974

    def assembler_constants(self):
        return dict(OWNER_SLOT=self.owner, RUNTIME_SLOT=self.runtime,
                    BOOT_STATUS=self.boot_status, CONTEXT_SLOT=self.context,
                    ROOT_BINDER=self.root_binder)


@dataclass(frozen=True)
class Result:
    descriptor: int
    status: int
    stock_entry: int = 0


class Memory:
    def __init__(self):
        self.bytes = {}
        self.reads = []

    def put(self, address, value, size=4):
        for i, byte in enumerate(value.to_bytes(size, "big")):
            self.bytes[address+i] = byte

    def get(self, address, size=4):
        self.reads.append((address, size))
        return int.from_bytes(bytes(self.bytes[address+i] for i in range(size)), "big")


def pointer(value, size, alignment=4):
    return (type(value) is int and 0 < value <= 2**32-size
            and value % alignment == 0)


def geometry(owner, extra):
    """Enumeration of 18 exact addresses; no adapter quotient/shift algorithm."""
    if not pointer(owner, OWNER_BYTES) or type(extra) is not int:
        return None
    aliases = {owner+680+768*b+8*t: (b, t) for b in range(3) for t in range(6)}
    return aliases.get(extra)


def evaluate(memory: Memory, slots: Slots, extra: int, ordinal: int,
             checked_call: Callable[..., Result]) -> Result:
    """Ordered read/admission oracle, with explicit six-argument callout.

    No implicit registers, caller PC, hidden arguments or target interpreter.
    The supplied checked_call models the unchanged checked routine separately.
    """
    def fail(status):
        return Result(0, status)

    if type(ordinal) is not int or not 0 <= ordinal <= 32:
        return fail(6)
    if memory.get(slots.boot_status+4):
        return fail(PUBLICATION)
    owner = memory.get(slots.owner)
    if not owner or memory.get(slots.boot_status) != owner:
        return fail(PUBLICATION)
    pair = geometry(owner, extra)
    if pair is None:
        return fail(1)
    bank, track = pair
    if (memory.get(owner) != 0x4c464f34 or memory.get(owner+4) != 1
            or memory.get(owner+6444) != owner
            or memory.get(owner+6448) != 0x524e4731 or memory.get(owner+6440)):
        return fail(2)
    if memory.get(slots.runtime) != owner+4400:
        return fail(PUBLICATION)
    writer = memory.get(owner+72)
    if writer == 1:
        if memory.get(owner+76) != 0:
            return fail(3)
    elif writer != 0 or memory.get(owner+76) != 1:
        return fail(3)
    if (memory.get(extra) != owner+80
            or memory.get(extra+4) != owner+272+768*bank+68*track
            or memory.get(owner+44+4*bank) != owner+176+768*bank
            or memory.get(owner+56+4*bank) != owner+2508+640*bank):
        return fail(1)
    stock = memory.get(owner+40)
    if not pointer(stock, M_BYTES):
        return fail(1)
    if memory.get(stock) != 0x400fcf3c:
        return fail(4)
    context = memory.get(slots.context)
    if not pointer(context, CONTEXT_BYTES, 16):
        return fail(READY)
    if (memory.get(context) != 0x4c465347 or memory.get(context+4) != owner
            or memory.get(context+12) != stock or memory.get(context+24)):
        return fail(READY)
    root = memory.get(context+8)
    if not pointer(root, ROOT_BYTES):
        return fail(CURRENT_BANK)
    if memory.get(slots.root_binder) != root or memory.get(stock+16) != root+BANK_BASE:
        return fail(CURRENT_BANK)
    selected = memory.get(stock+68)
    if selected >= 96:
        return fail(CURRENT_BANK)
    regional = stock+96+68*track
    expected_child = root+BANK_BASE+BANK_STRIDE*selected+28+100*track
    if memory.get(regional+16) != expected_child:
        return fail(CURRENT_BANK)
    if memory.get(regional) != 0x400fef54 or memory.get(0x400fef7c) != 0x400d5632:
        return fail(4)
    stock_entry = stock+504+8*track
    if memory.get(stock_entry+4) != regional or memory.get(stock_entry) != 0x400fd134:
        return fail(4)
    return checked_call(owner, stock, extra, bank, track, ordinal)
