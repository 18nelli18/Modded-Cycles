# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/test_candidate.py; lines 11-23,27-39,41-52,54-60,62-66,68-77,80-90,92-94,98-102,104-115,117-127,129-135,137-140,142-148,150-153,155-161,163-166,168-174.
# Unresolved integration bindings: see DEPENDENCIES.json.
from dataclasses import replace
import unittest
from .contract import Memory, Result, Status, checked

def fixture(bank=0, track=0, profile=0, writer=1, reader=0,
            owner=0x41000000, stock=0x42000000):
    memory = Memory()
    extra = owner+680+768*bank+8*track
    regional = stock+96+68*track
    child = 0x43000000+100*track
    for address, value in ((owner, 0x4c464f34), (owner+4, 1), (owner+40, stock),
            (owner+72, writer), (owner+76, reader), (extra, owner+80),
            (extra+4, owner+272+768*bank+68*track), (stock+504+8*track+4, regional),
            (regional, 0x400fef54), (0x400fef7c, 0x400d5632), (regional+16, child)):
        memory.put(address, value)
    memory.put(child+38, profile, 1)
    return memory, (owner, stock, extra, bank, track), child


class ContractTests(unittest.TestCase):
    def call(self, fixture_args, value=18, descriptor=53, flags=None):
        memory, args, _ = fixture_args
        self.calls = []
        def lookup(entry, ordinal):
            self.calls.append(("lookup", entry, ordinal))
            return descriptor
        def flag_call(value):
            self.calls.append(("flags", value))
            return flags
        before = dict(memory.bytes)
        result = checked(memory, *args, value, lookup, flag_call if flags is not None else None)
        self.assertEqual(memory.bytes, before, "oracle must not change object bytes")
        return result
    def test_all_geometry_and_valid_profiles_forward_current_stock_entry(self):
        for bank in range(3):
            for track in range(6):
                for profile in range(6):
                    with self.subTest(bank=bank, track=track, profile=profile):
                        f = fixture(bank, track, profile)
                        result = self.call(f)
                        entry = f[1][1]+504+8*track
                        self.assertEqual(result, Result(53, Status.OK, entry))
                        self.assertEqual(self.calls, [("lookup", entry, 18)])
                        # No extra backing/profile getter is read or synchronized.
                        self.assertNotIn((f[1][0]+272+768*bank+68*track+16, 4), f[0].reads)
    def test_lookup_native_zero_is_valid_and_distinct_from_refusal(self):
        result = self.call(fixture(), descriptor=0)
        self.assertEqual((result.descriptor, result.status), (0, Status.OK))
        self.assertNotEqual(result.stock_entry, 0)
        result = self.call(fixture(profile=255), descriptor=0)
        self.assertEqual(result, Result(0, Status.PROFILE))
        self.assertEqual(self.calls, [])
    def test_every_invalid_signed_profile_byte_refuses_before_forward(self):
        for byte in range(6, 256):
            with self.subTest(byte=byte):
                self.assertEqual(self.call(fixture(profile=byte)).status, Status.PROFILE)
                self.assertEqual(self.calls, [])
    def test_current_stored_child_rebind_changes_context_without_config_copy(self):
        memory, args, old = fixture(track=2)
        regional = args[1]+96+68*2
        new = 0x44000000
        memory.put(regional+16, new)
        memory.put(new+38, 5, 1)
        result = self.call((memory, args, new), value=11)
        self.assertEqual(result.status, Status.OK)
        self.assertIn((new+38, 1), memory.reads)
        self.assertNotIn((old+38, 1), memory.reads)
    def test_numeric_geometry_rejects_before_dereferencing(self):
        for index, value in ((0, 0), (0, 3), (0, 0xfffffff0), (1, 0),
                (1, 7), (1, 0xfffffffc), (3, -1), (3, 3), (4, -1), (4, 6),
                (0, True), (3, 1.5), (4, "2")):
            memory, args, child = fixture()
            args = list(args); args[index] = value
            with self.subTest(index=index, value=value):
                result = self.call((memory, args, child))
                self.assertEqual(result.status, Status.GEOMETRY)
                self.assertEqual(memory.reads, [])
                self.assertEqual(self.calls, [])
    def test_prefix_wrap_bounds_are_not_allocation_sizes(self):
        f = fixture(owner=2**32-4688, stock=2**32-552)
        self.assertEqual(self.call(f).status, Status.OK)
    def test_owner_identity_version_and_retained_m(self):
        for offset, value in ((0, 0), (4, 2), (40, 0x42000004)):
            f = fixture(); f[0].put(f[1][0]+offset, value)
            self.assertEqual(self.call(f).status, Status.OWNER_BINDING)
            self.assertEqual(self.calls, [])
    def test_exact_extra_geometry_and_private_entry_vptr(self):
        for variant in ("entry", "regional", "vptr"):
            memory, args, child = fixture(bank=2, track=5)
            args = list(args)
            if variant == "entry":
                args[2] += 8
            elif variant == "regional":
                memory.put(args[2]+4, args[0]+272)
            else:
                memory.put(args[2], 0x400fd134)
            self.assertEqual(self.call((memory, args, child)).status, Status.GEOMETRY)
            self.assertEqual(self.calls, [])
    def test_exact_stock_region_vptr_getter_and_child_pointer(self):
        for offset_kind, value in (("entry", 0), ("vptr", 0x400fcf3c),
                ("getter", 0x400d5634), ("child", 0), ("child", 3),
                ("child", 0xfffffffc)):
            f = fixture(track=4)
            m = f[1][1]; region = m+96+68*4
            address = {"entry": m+504+8*4+4, "vptr": region,
                       "getter": 0x400fef7c, "child": region+16}[offset_kind]
            f[0].put(address, value)
            self.assertEqual(self.call(f).status, Status.STOCK_BINDING)
            self.assertEqual(self.calls, [])
    def test_native_word_aligned_child_does_not_need_long_alignment(self):
        f=fixture(track=2,profile=3)
        memory,args,old_child=f
        current_child=old_child+2
        memory.put(args[1]+96+68*2+16,current_child)
        memory.put(current_child+38,3,1)
        self.assertEqual(self.call((memory,args,current_child)).status,Status.OK)
    def test_unmapped_live_pointer_is_a_caller_contract_violation(self):
        f = fixture(); f[0].put(f[1][1]+96+16, 0x45000000)
        with self.assertRaises(KeyError):
            self.call(f)
    def test_read_or_write_lease_lookup_but_only_writer_preflight(self):
        self.assertEqual(self.call(fixture(writer=0, reader=1)).status, Status.OK)
        self.assertEqual(self.call(fixture(writer=0, reader=1), value=0, flags=0x600).status,
                         Status.LEASE)
        for writer, reader in ((0, 0), (1, 1), (2, 0), (0, 2), (0xffffffff, 0)):
            self.assertEqual(self.call(fixture(writer=writer, reader=reader)).status, Status.LEASE)
            self.assertEqual(self.calls, [])
    def test_lookup_domain_and_python_malformed_arguments(self):
        for value in (-1, 33, 0xffffffff, True, None, "18", 1.5):
            self.assertEqual(self.call(fixture(), value=value).status, Status.DOMAIN)
            self.assertEqual(self.calls, [])
    def test_preflight_exact_mask_inclusion_exhaustive(self):
        for flags in range(0x800):
            result = self.call(fixture(), value=0x0aff, flags=flags)
            expected = Status.OK if (flags & 0x600) == 0x600 else Status.FILTER
            self.assertEqual(result.status, expected)
            self.assertEqual(self.calls[0][2], 10)
        self.assertEqual(self.call(fixture(), value=0x1200, flags=0xffffffff).status, Status.OK)
    def test_preflight_missing_descriptor_skips_native_flags(self):
        self.assertEqual(self.call(fixture(), value=0x0b00, descriptor=0, flags=0x600).status,
                         Status.MISSING)
        self.assertEqual(len(self.calls), 1)
    def test_raw_dst_signed_8_8_domain_and_fractional_byte(self):
        for raw in (0, 0xff, 0x0a00, 0x0aff, 0x1200, 0x2000, 0x20ff):
            self.assertEqual(self.call(fixture(), value=raw, flags=0x600).status, Status.OK)
            self.assertEqual(self.calls[0][2], raw >> 8)
        for raw in (-1, -32768, 0x2100, 0x7f00, 0x8000, 0xffff, 0xffffffff, True):
            self.assertEqual(self.call(fixture(), value=raw, flags=0x600).status, Status.DOMAIN)
            self.assertEqual(self.calls, [])
