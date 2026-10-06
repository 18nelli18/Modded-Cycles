# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/live_profile_candidate/native_adapter/test_adapter.py; lines 18-47,51-74,76-78,80-92,94-100,102-109,111-115,117-126,128-136,138-143,145-149,151-161,163-169,171-177,179-187,189-194,196-201,203-213,215-224,226-239,242-247,249-253,255-258,260-267,269-277,279-281.
# Unresolved integration bindings: see DEPENDENCIES.json.
from dataclasses import replace
import unittest
from ..contract import checked
from .oracle import (BANK_BASE, BANK_STRIDE, CONTEXT_BYTES, CURRENT_BANK, M_BYTES, OWNER_BYTES, PUBLICATION, READY, ROOT_BYTES, Memory, Result, Slots, evaluate, geometry)
_EXTRA_UNSET = object()

def fixture(bank=0, track=0, profile=0, writer=1, reader=0, selected=0,
            owner=0x412ff000, stock=0x45000000, context=0x43000000,
            root=0x406fa024, slots=Slots()):
    """Sparse declared readable fixture, NOT firmware allocation evidence."""
    memory = Memory()
    extra = owner+680+768*bank+8*track
    regional = stock+96+68*track
    entry = stock+504+8*track
    child = root+BANK_BASE+BANK_STRIDE*selected+28+100*track
    pairs = [(slots.boot_status, owner), (slots.boot_status+4, 0),
             (slots.owner, owner), (slots.runtime, owner+4400),
             (slots.context, context), (slots.root_binder, root),
             (owner, 0x4c464f34), (owner+4, 1), (owner+40, stock),
             (owner+72, writer), (owner+76, reader), (owner+6440, 0),
             (owner+6444, owner), (owner+6448, 0x524e4731),
             (extra, owner+80), (extra+4, owner+272+768*bank+68*track),
             (stock, 0x400fcf3c), (stock+16, root+BANK_BASE), (stock+68, selected),
             (entry, 0x400fd134), (entry+4, regional),
             (regional, 0x400fef54), (regional+16, child),
             (0x400fef7c, 0x400d5632), (context, 0x4c465347),
             (context+4, owner), (context+8, root), (context+12, stock),
             (context+24, 0)]
    pairs += [(owner+44+4*b, owner+176+768*b) for b in range(3)]
    pairs += [(owner+56+4*b, owner+2508+640*b) for b in range(3)]
    for address, value in pairs:
        memory.put(address, value)
    memory.put(child+38, profile, 1)
    return dict(memory=memory, slots=slots, owner=owner, stock=stock,
                context=context, root=root, extra=extra, child=child,
                regional=regional, entry=entry, bank=bank, track=track)


class OracleTests(unittest.TestCase):
    def call(self, f, ordinal=18, extra=_EXTRA_UNSET, descriptor=None):
        self.contexts, self.native_calls = [], []
        memory = f["memory"]
        before = dict(memory.bytes)

        def checked_call(*args):
            self.contexts.append(args)

            def native(entry, index):
                # Explicit native lookup ORACLE. Reads actual current stored
                # child; this neither executes A830 nor fabricates CPU registers.
                child = memory.get(memory.get(entry+4)+16)
                profile = memory.get(child+38, 1)
                self.native_calls.append((entry, index, profile))
                value = (14 if index == 0 else 0 if index == 32 else index+5*profile)
                return value if descriptor is None else descriptor

            result = checked(memory, *args, native)
            return Result(result.descriptor, int(result.status), result.stock_entry)

        result = evaluate(memory, f["slots"], f["extra"] if extra is _EXTRA_UNSET else extra,
                          ordinal, checked_call)
        self.assertEqual(memory.bytes, before, "adapter/oracles must not write object bytes")
        return result
    def assert_refuses(self, f, status, **kwargs):
        self.assertEqual(self.call(f, **kwargs), Result(0, status))
        self.assertEqual(self.native_calls, [])
    def test_all18_six_profiles_both_leases_and33_ordinals(self):
        for bank in range(3):
            for track in range(6):
                for profile in range(6):
                    for writer, reader in ((1, 0), (0, 1)):
                        for ordinal in range(33):
                            f = fixture(bank, track, profile, writer, reader, selected=94)
                            result = self.call(f, ordinal)
                            self.assertEqual(result.status, 0)
                            self.assertEqual(result.stock_entry, f["entry"])
                            self.assertEqual(self.contexts, [(f["owner"], f["stock"],
                                f["extra"], bank, track, ordinal)])
                            self.assertEqual(self.native_calls, [(f["entry"], ordinal, profile)])
    def test_geometry_enumerates_exact18_and_rejects_all_holes(self):
        owner = 0x412ff000
        valid = {owner+680+768*b+8*t: (b, t) for b in range(3) for t in range(6)}
        for extra in range(owner+670, owner+2270):
            self.assertEqual(geometry(owner, extra), valid.get(extra))
        for extra in (0, -1, 0xffffffff, True, None, "entry", 1.5):
            self.assertIsNone(geometry(owner, extra))
    def test_unadmitted_e_refuses_before_owner_or_entry_dereference(self):
        for extra in (0, 3, 0xffffffff, -1, True, None, "entry", 1.5,
                      0x412ff000+679, 0x412ff000+728, 0x412ff000+2257):
            f = fixture()
            self.assert_refuses(f, 1, extra=extra)
            self.assertEqual(f["memory"].reads,
                [(f["slots"].boot_status+4, 4), (f["slots"].owner, 4),
                 (f["slots"].boot_status, 4)])
    def test_bad_ordinal_refuses_without_even_publication_reads(self):
        for ordinal in (-1, 33, 0xffffffff, True, None, "18", 1.5):
            f = fixture()
            self.assert_refuses(f, 6, ordinal=ordinal)
            self.assertEqual(f["memory"].reads, [])
    def test_terminal_latch_null_and_foreign_publication(self):
        for field, value in (("terminal", 1), ("slot", 0), ("identity", 0),
                             ("identity", 0x412ff004)):
            f = fixture()
            address = {"terminal": f["slots"].boot_status+4,
                       "slot": f["slots"].owner,
                       "identity": f["slots"].boot_status}[field]
            f["memory"].put(address, value)
            self.assert_refuses(f, PUBLICATION)
            self.assertNotIn((f["owner"], 4), f["memory"].reads)
    def test_owner_alignment_wrap_and_full_not_prefix_bound(self):
        for owner in (3, 0xfffffff0, 2**32-4688):
            f = fixture()
            f["memory"].put(f["slots"].owner, owner)
            f["memory"].put(f["slots"].boot_status, owner)
            self.assert_refuses(f, 1)
            self.assertNotIn((owner, 4), f["memory"].reads)
        f = fixture(owner=2**32-OWNER_BYTES)
        self.assertEqual(self.call(f).status, 0)  # numeric boundary only
    def test_header_constructor_binding_marker_quarantine(self):
        for offset, value in ((0, 0), (4, 2), (6444, 0), (6448, 0), (6440, 1)):
            f = fixture()
            f["memory"].put(f["owner"]+offset, value)
            self.assert_refuses(f, 2)
            self.assertNotIn((f["extra"], 4), f["memory"].reads)
    def test_runtime_publication_alias(self):
        f = fixture()
        f["memory"].put(f["slots"].runtime, f["owner"]+4404)
        self.assert_refuses(f, PUBLICATION)
        self.assertNotIn((f["extra"], 4), f["memory"].reads)
    def test_mixed_missing_wrong_and_foreign_lease(self):
        for writer, reader in ((0, 0), (1, 1), (2, 0), (0, 2), (2, 1),
                               (1, 2), (0xffffffff, 0), (0, 0xffffffff)):
            f = fixture(writer=writer, reader=reader)
            self.assert_refuses(f, 3)
            self.assertNotIn((f["extra"], 4), f["memory"].reads)
        # A lease on published O never admits an E of another retained owner.
        f = fixture()
        self.assert_refuses(f, 1, extra=f["extra"]+0x10000)
        # No task token exists: valid gate words cannot authenticate the holder.
        self.assertEqual(self.call(fixture(writer=1)).status, 0)
    def test_exact_private_vptr_region_and_selected_bank_aliases(self):
        for field in ("vptr", "region", "route", "config"):
            f = fixture(bank=2, track=5)
            address = {"vptr": f["extra"], "region": f["extra"]+4,
                       "route": f["owner"]+44+8, "config": f["owner"]+56+8}[field]
            f["memory"].put(address, 0)
            self.assert_refuses(f, 1)
    def test_invalid_m_before_dereference_and_full_extent(self):
        for stock in (0, 7, 0xfffffffc, 2**32-552):
            f = fixture()
            f["memory"].put(f["owner"]+40, stock)
            self.assert_refuses(f, 1)
            self.assertNotIn((stock, 4), f["memory"].reads)
        self.assertEqual(self.call(fixture(stock=2**32-M_BYTES)).status, 0)
    def test_stock_constructor_entry_region_getter_bindings(self):
        for field in ("parent", "entry", "region", "entry_region", "getter"):
            f = fixture()
            address = {"parent": f["stock"], "entry": f["entry"],
                       "region": f["regional"], "entry_region": f["entry"]+4,
                       "getter": 0x400fef7c}[field]
            f["memory"].put(address, 0)
            self.assert_refuses(f, 4)
            self.assertNotIn((f["child"]+38, 1), f["memory"].reads)
    def test_invalid_context_pointer_before_dereference(self):
        for context in (0, 4, 0xfffffffc, 2**32-16):
            f = fixture()
            f["memory"].put(f["slots"].context, context)
            self.assert_refuses(f, READY)
            self.assertNotIn((context, 4), f["memory"].reads)
    def test_context_tag_owner_m_and_readiness(self):
        for offset, value in ((0, 0), (4, 0), (12, 0), (24, 1)):
            f = fixture()
            f["memory"].put(f["context"]+offset, value)
            self.assert_refuses(f, READY)
            self.assertNotIn((f["regional"]+16, 4), f["memory"].reads)
    def test_bank_root_binder_array_and_selected_domain(self):
        for field, value in (("root", 0), ("root", 3), ("root", 0xfffffff0),
                             ("binder", 0), ("array", 0),
                             ("selected", 96), ("selected", 0xffffffff)):
            f = fixture()
            address = {"root": f["context"]+8, "binder": f["slots"].root_binder,
                       "array": f["stock"]+16, "selected": f["stock"]+68}[field]
            f["memory"].put(address, value)
            self.assert_refuses(f, CURRENT_BANK)
            self.assertNotIn((f["child"]+38, 1), f["memory"].reads)
        self.assertLessEqual(BANK_BASE+96*BANK_STRIDE, ROOT_BYTES)
    def test_wrong_track_stale_bank_or_arbitrary_child_never_read_profile(self):
        for child in (0, 3, 0xfffffffc, 0x47000000):
            f = fixture(track=2, selected=1)
            f["memory"].put(f["regional"]+16, child)
            self.assert_refuses(f, CURRENT_BANK)
            self.assertNotIn((child+38, 1), f["memory"].reads)
        f = fixture(track=2)
        for child in (f["child"]+100, f["child"]+BANK_STRIDE):
            f["memory"].put(f["regional"]+16, child)
            self.assert_refuses(f, CURRENT_BANK)
    def test_sequential_current_bank_child_rebind_and_profile(self):
        f = fixture(track=2, profile=1)
        self.assertEqual(self.call(f, 18).descriptor, 23)
        old = f["child"]
        new = old+2*BANK_STRIDE
        f["memory"].put(f["stock"]+68, 2)
        f["memory"].reads.clear()
        self.assert_refuses(f, CURRENT_BANK)  # stale stored binding
        f["memory"].put(f["regional"]+16, new)
        f["memory"].put(new+38, 5, 1)
        f["memory"].reads.clear()
        self.assertEqual(self.call(f, 18).descriptor, 43)
        self.assertNotIn((old+38, 1), f["memory"].reads)
        self.assertIn((new+38, 1), f["memory"].reads)
    def test_native_word_aligned_children_accept_all96_bank_parities(self):
        for selected in range(96):
            f = fixture(track=5, selected=selected)
            self.assertEqual(f["child"] % 4, 2*(selected%2))
            self.assertEqual(self.call(f).status, 0)
            self.assertIn((f["child"]+38, 1), f["memory"].reads)
    def test_all250_invalid_signed_profile_bytes(self):
        for profile in range(6, 256):
            f = fixture(profile=profile)
            self.assert_refuses(f, 5)
            self.assertEqual(len(self.contexts), 1)
    def test_native_zero_unavailable_is_distinct_from_refusal(self):
        f = fixture()
        self.assertEqual(self.call(f, descriptor=0), Result(0, 0, f["entry"]))
        self.assert_refuses(fixture(profile=255), 5)
    def test_no_extra_child_profile_or_configuration_reads(self):
        f = fixture(bank=2, track=5, profile=4)
        self.assertEqual(self.call(f).status, 0)
        extra_region = f["owner"]+272+768*2+68*5
        extra_child = f["owner"]+2508+640*2+100*5
        self.assertNotIn((extra_region+16, 4), f["memory"].reads)
        self.assertFalse(any(extra_child <= address < extra_child+100
                             for address, _ in f["memory"].reads))
    def test_unmapped_published_objects_are_retention_contract_violations(self):
        f = fixture()
        f["memory"].put(f["owner"]+40, 0x46000000)
        with self.assertRaises(KeyError):
            self.call(f)
        f = fixture()
        f["memory"].put(f["slots"].context, 0x46000000)
        with self.assertRaises(KeyError):
            self.call(f)
    def test_declared_slots_are_read_only_and_rebindable(self):
        slots = Slots(0x47000000, 0x47000004, 0x47000008, 0x47000010, 0x47000014)
        self.assertEqual(self.call(fixture(slots=slots)).status, 0)
