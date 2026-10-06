# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/test_lfo_four_menu_transaction_join.py; lines 18-22.
# Unresolved integration bindings: see DEPENDENCIES.json.
import struct
from . import word_io as k

def menu_rows(cpu,menu):
    """Stock Setup has three rows; the extra-selector Setup has four."""
    begin,end = k.read_words(cpu,menu+4,2)
    assert end-begin in (24,32), 'valid stock or extended menu vector'
    return [k.read_words(cpu,begin+8*i,1)[0] for i in range((end-begin)//8)]
