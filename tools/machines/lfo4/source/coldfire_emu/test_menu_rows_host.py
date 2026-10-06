# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/test_lfo_four_menu_transaction_rows.py; lines 1-20.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Independent host regression for the three-row stock Setup fallback."""
import struct
import unittest
from .menu_rows import menu_rows


class RowTests(unittest.TestCase):
    def test_stock_three_and_owned_four_rows(self):
        class Memory:
            def __init__(self,count):
                self.words={0x1004:0x2000,0x1008:0x2000+8*count}
                self.words.update({0x2000+8*i:0x3000+84*i for i in range(count)})
            def read(self,address,size):
                assert size%4==0
                return b''.join(struct.pack('>I',self.words[address+i]) for i in range(0,size,4))
        for count in (3,4):
            self.assertEqual(menu_rows(Memory(count),0x1000),
                             [0x3000+84*i for i in range(count)])
        with self.assertRaises(AssertionError):
            menu_rows(Memory(2),0x1000)
