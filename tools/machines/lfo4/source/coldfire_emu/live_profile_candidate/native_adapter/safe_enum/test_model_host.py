# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/safe_enum/test_enum.py; lines 15-21,45-48,67-75,77-83.
# Unresolved integration bindings: see DEPENDENCIES.json.
import unittest
from . import model



class Tests(unittest.TestCase):
    def run_case(self, mapping, flag=lambda d:0x600, fail=None, buffer=0x47000000, capacity=33, protected=()):
        self.words = [0xeeeeeeee]*35
        self.calls=[]
        def lookup(e,o):
            self.calls.append((e,o))
            return (0,5) if fail==o else (mapping[o],0)
        return model.enumerate_into(0x412ff2a8,buffer,capacity,self.words,lookup,flag,protected)
    def test_failure_after_partial_progress_is_not_success(self):
        self.assertEqual(self.run_case([14]*33,fail=7),model.Result(0,5))
        self.assertEqual(self.words[:8],[14]*7+[0xeeeeeeee])
        self.assertEqual(len(self.calls),8)
    def test_capacity_alignment_numeric_spans_before_call_or_write(self):
        for buf,cap,status in ((0,33,14),(3,33,14),(0xfffffffc,33,14),
                (0x47000000,32,13),(0x47000000,0xffffffff,14),
                (0xffffff7c,33,14)):
            self.assertEqual(self.run_case([14]*33,buffer=buf,capacity=cap),model.Result(0,status))
            self.assertEqual(self.calls,[])
            self.assertEqual(self.words,[0xeeeeeeee]*35)
        self.assertEqual(self.run_case([14]*33,buffer=0xffffff78),model.Result(33,0))
        self.assertEqual(self.words[33:],[0xeeeeeeee]*2)
    def test_alias_half_open_capacity_span_and_native_refusal(self):
        for start,size in ((0x47000000,4),(0x46fffffc,8),(0x47000080,8)):
            self.assertEqual(self.run_case([14]*33,protected=((start,size),)),model.Result(0,15))
            self.assertEqual(self.words,[0xeeeeeeee]*35)
        self.assertEqual(self.run_case([14]*33,protected=((0x47000084,4),)).count,33)
        self.assertEqual(self.run_case([14]*33,fail=0),model.Result(0,5))
        self.assertEqual(self.words,[0xeeeeeeee]*35)
