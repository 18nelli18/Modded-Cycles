# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/scale_native_keyboard.py; lines 33-34.
# Unresolved integration bindings: see DEPENDENCIES.json.
import struct

def read_words(cpu,address,count):
    return list(struct.unpack('>'+str(count)+'I',cpu.read(address,4*count)))
