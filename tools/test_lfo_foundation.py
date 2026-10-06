#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Périmètre explicite : lfo_foundation/LICENSE.
"""Teste les fondations LFO sur l'hôte, sans firmware ni émulateur.

Compilation C11 temporaire par cc, ctypes et bibliothèque standard Python.
Réglages, conteneurs et résultats de modulation exclusivement synthétiques.
Les six contrôles historiques de publication sont repris puis reliés à LF4S.
Origine et limites : notes/41-fondations-lfo.md.
Exécution : python3 tools/test_lfo_foundation.py
"""

import ctypes as ct
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

sys.dont_write_bytecode = True
from lfo_foundation import publication as p

OK, INVALID, CAPACITY, MEMORY, FORMAT, BINDING = range(6)
PAYLOAD_BYTES = 48
KEYS = 6720
BASE = b"synthetic project container / version A"
ZERO = bytes(PAYLOAD_BYTES)
Allocate = ct.CFUNCTYPE(ct.c_void_p, ct.c_void_p, ct.c_size_t)
Release = ct.CFUNCTYPE(None, ct.c_void_p, ct.c_void_p)


class Options(ct.Structure):
    _fields_ = [("key_count", ct.c_uint32), ("capacity", ct.c_uint32),
                ("max_word", ct.c_uint16), ("defaults", ct.c_ubyte * PAYLOAD_BYTES),
                ("allocate", Allocate), ("release", Release),
                ("allocator_user", ct.c_void_p)]


class Edit(ct.Structure):
    _fields_ = [("key", ct.c_uint32), ("data", ct.c_ubyte * PAYLOAD_BYTES)]


def buffer(data):
    return (ct.c_ubyte * len(data)).from_buffer_copy(data)


def payload(seed):
    return struct.pack(">24H", *((seed + 17 * i) % 0x7000 for i in range(24)))


def wire(rows, defaults=ZERO, key_count=KEYS, base=BASE):
    """Encodeur indépendant du C ; zlib sert de référence pour le CRC32."""
    header = struct.pack(">4sHHIHHII", b"LF4S", 1, 52, 28 + 52 * len(rows),
                         key_count, len(rows), len(base), zlib.crc32(base))
    records = b"".join(struct.pack(">HH", key, 0)
                       + bytes(a ^ b for a, b in zip(data, defaults))
                       for key, data in rows)
    return checksum(header + records)


def checksum(prefix):
    return bytes(prefix) + struct.pack(">I", zlib.crc32(prefix))


class Native:
    def __init__(self):
        self.directory = tempfile.TemporaryDirectory(prefix="lf4s-host-")
        try:
            compiler = shutil.which("cc")
            if not compiler:
                raise RuntimeError("native host C compiler 'cc' required")
            source = Path(__file__).resolve().parent / "lfo_foundation" / "settings.c"
            suffix = ".dylib" if sys.platform == "darwin" else ".so"
            output = Path(self.directory.name) / ("settings" + suffix)
            self.command = [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-pedantic", "-O2", "-shared", "-fPIC", str(source),
                            "-o", str(output)]
            subprocess.run(self.command, check=True, capture_output=True, timeout=30)
            self.lib = ct.CDLL(str(output))
            pointer, uint, size = ct.c_void_p, ct.c_uint32, ct.c_size_t
            signatures = {
                "create": (ct.c_int, [ct.POINTER(Options), ct.POINTER(pointer)]),
                "destroy": (None, [pointer]), "count": (uint, [pointer]),
                "get": (ct.c_int, [pointer, uint, pointer]),
                "set": (ct.c_int, [pointer, uint, pointer]),
                "apply": (ct.c_int, [pointer, ct.POINTER(Edit), size]),
                "copy": (ct.c_int, [pointer, pointer, uint, uint, uint]),
                "reset": (ct.c_int, [pointer]), "encoded_size": (size, [pointer]),
                "save": (ct.c_int, [pointer, pointer, size, pointer, size,
                                    ct.POINTER(size)]),
                "load": (ct.c_int, [pointer, pointer, size, pointer, size]),
            }
            for name, (result, args) in signatures.items():
                function = getattr(self.lib, "lf4s_" + name)
                function.restype, function.argtypes = result, args
                setattr(self, name, function)
            print("Native host build: C11, warnings as errors, -O2; no firmware inputs",
                  flush=True)
        except subprocess.CalledProcessError as error:
            self.directory.cleanup()
            raise RuntimeError(error.stderr.decode()) from error
        except Exception:
            self.directory.cleanup()
            raise

    def close(self):
        self.directory.cleanup()


class FaultAllocator:
    """Échecs d'allocation sur l'hôte ; aucune adresse de l'appareil."""
    def __init__(self):
        self.heap = ct.CDLL(None)
        self.heap.malloc.argtypes, self.heap.malloc.restype = [ct.c_size_t], ct.c_void_p
        self.heap.free.argtypes, self.heap.free.restype = [ct.c_void_p], None
        self.remaining = -1
        self.calls = 0
        self.live = {}
        self.errors = []
        self.allocate = Allocate(self._allocate)
        self.release = Release(self._release)

    def _allocate(self, user, size):
        self.calls += 1
        if self.remaining == 0:
            return None
        if self.remaining > 0:
            self.remaining -= 1
        address = self.heap.malloc(size)
        if address:
            self.live[address] = size
        return address

    def _release(self, user, address):
        if address not in self.live:
            self.errors.append("unexpected allocation release")
            return
        del self.live[address]
        self.heap.free(address)


BUILD = None


def setUpModule():
    global BUILD
    BUILD = Native()


def tearDownModule():
    if BUILD is not None:
        BUILD.close()


class HostCase(unittest.TestCase):
    def setUp(self):
        self.stores = []
        self.allocators = []

    def tearDown(self):
        for store in self.stores:
            BUILD.destroy(store)
        for allocator in self.allocators:
            self.assertFalse(allocator.live, "host allocation leak")
            self.assertFalse(allocator.errors)

    def options(self, capacity=16, key_count=KEYS, defaults=ZERO, allocator=None):
        options = Options(key_count=key_count, capacity=capacity, max_word=0x7f00)
        options.defaults[:] = defaults
        if allocator is not None:
            options.allocate, options.release = allocator.allocate, allocator.release
        return options

    def store(self, **kwargs):
        result = ct.c_void_p()
        options = self.options(**kwargs)
        self.assertEqual(BUILD.create(ct.byref(options), ct.byref(result)), OK)
        self.stores.append(result)
        return result

    def allocator(self):
        allocator = FaultAllocator()
        self.allocators.append(allocator)
        return allocator

    def get(self, store, key):
        out = buffer(b"\xa5" * PAYLOAD_BYTES)
        self.assertEqual(BUILD.get(store, key, out), OK)
        return bytes(out)

    def set(self, store, key, data):
        return BUILD.set(store, key, buffer(data))

    def apply(self, store, rows):
        edits = (Edit * len(rows))()
        for edit, (key, data) in zip(edits, rows):
            edit.key, edit.data[:] = key, data
        return BUILD.apply(store, edits, len(rows))

    def save(self, store, base=BASE):
        length = BUILD.encoded_size(store)
        out = buffer(bytes(length))
        written = ct.c_size_t(0)
        self.assertEqual(BUILD.save(store, buffer(base), len(base), out, length,
                                    ct.byref(written)), OK)
        self.assertEqual(written.value, length)
        return bytes(out)

    def load(self, store, data, base=BASE):
        return BUILD.load(store, buffer(base), len(base), buffer(data), len(data))


class SettingsTests(HostCase):
    def test_sparse_defaults_sorted_rows_and_independent_wire(self):
        defaults = struct.pack(">24H", *range(24))
        store = self.store(defaults=defaults)
        for key, data in ((11, payload(10)), (2, payload(20)), (5, defaults)):
            self.assertEqual(self.set(store, key, data), OK)
        self.assertEqual(BUILD.count(store), 2)
        self.assertEqual(self.get(store, 5), defaults)
        self.assertEqual(self.save(store), wire([(2, payload(20)), (11, payload(10))],
                                               defaults=defaults))
        self.assertEqual(self.set(store, 2, defaults), OK)
        self.assertEqual(BUILD.count(store), 1)

    def test_full_6720_key_round_trip_from_independent_wire(self):
        rows = [(key, payload(key + 1)) for key in range(KEYS)]
        encoded = wire(rows)
        store = self.store(capacity=KEYS)
        self.assertEqual(self.load(store, encoded), OK)
        self.assertEqual(BUILD.count(store), KEYS)
        self.assertEqual(self.save(store), encoded)
        for key, expected in rows:
            self.assertEqual(self.get(store, key), expected)

    def test_batch_reuses_capacity_even_when_insertion_precedes_deletion(self):
        store = self.store(capacity=1)
        self.assertEqual(self.set(store, 0, payload(1)), OK)
        self.assertEqual(self.apply(store, [(1, payload(2)), (0, ZERO)]), OK)
        self.assertEqual(self.get(store, 0), ZERO)
        self.assertEqual(self.get(store, 1), payload(2))
        self.assertEqual(BUILD.count(store), 1)

    def test_failed_batch_is_atomic_for_capacity_invalid_data_and_duplicate_keys(self):
        store = self.store(capacity=1)
        self.assertEqual(self.set(store, 0, payload(1)), OK)
        before = self.save(store)
        invalid = b"\xff\xff" + bytes(46)
        cases = [(CAPACITY, [(1, payload(2))]),
                 (INVALID, [(0, ZERO), (1, invalid)]),
                 (INVALID, [(0, ZERO), (0, payload(2))]),
                 (INVALID, [(0, ZERO), (KEYS, payload(2))])]
        for status, rows in cases:
            with self.subTest(status=status, keys=[key for key, _ in rows]):
                self.assertEqual(self.apply(store, rows), status)
                self.assertEqual(self.save(store), before)

    def test_zero_capacity_empty_base_and_explicit_reset(self):
        store = self.store(capacity=0)
        self.assertEqual(self.set(store, 0, ZERO), OK)
        self.assertEqual(self.set(store, 0, payload(1)), CAPACITY)
        self.assertEqual(self.save(store, base=b""), wire([], base=b""))
        self.assertEqual(self.load(store, wire([])), OK)
        populated = self.store()
        self.assertEqual(self.set(populated, 0, payload(1)), OK)
        before = self.save(populated)
        self.assertEqual(BUILD.load(populated, buffer(BASE), len(BASE), None, 0), FORMAT)
        self.assertEqual(self.save(populated), before)
        self.assertEqual(BUILD.reset(populated), OK)
        self.assertEqual(self.get(populated, 0), ZERO)

    def test_short_save_keeps_output_length_and_state_unchanged(self):
        store = self.store()
        self.assertEqual(self.set(store, 3, payload(3)), OK)
        before = self.save(store)
        out = buffer(b"\xa5" * len(before))
        written = ct.c_size_t(12345)
        self.assertEqual(BUILD.save(store, buffer(BASE), len(BASE), out,
                                    len(before) - 1, ct.byref(written)), CAPACITY)
        self.assertEqual(bytes(out), b"\xa5" * len(before))
        self.assertEqual(written.value, 12345)
        self.assertEqual(self.save(store), before)

    def test_rejects_malformed_wire_without_changing_state_or_allocating(self):
        allocator = self.allocator()
        store = self.store(allocator=allocator)
        self.assertEqual(self.set(store, 9, payload(9)), OK)
        before = self.save(store)
        good = wire([(1, payload(1)), (2, payload(2))])
        malformed = {}
        for name, offset, replacement in (
                ("magic", 0, b"BAD!"), ("version", 4, b"\x00\x02"),
                ("stride", 6, b"\x00\x33"), ("size", 8, b"\x00\x00\x00\x1c"),
                ("domain", 12, b"\x00\x06"), ("count", 14, b"\x00\x01"),
                ("reserved", 26, b"\x00\x01"),
                ("key", 24, struct.pack(">H", KEYS)),
                ("duplicate", 76, b"\x00\x01"),
                ("default row", 28, ZERO), ("word range", 28, b"\xff\xff")):
            candidate = bytearray(good[:-4])
            candidate[offset:offset + len(replacement)] = replacement
            malformed[name] = checksum(candidate)
        malformed["unsorted"] = checksum(good[:24] + good[76:128] + good[24:76])
        malformed["trailing"] = good + b"\x00"
        malformed["CRC"] = good[:-1] + bytes([good[-1] ^ 1])
        for length in range(28):
            malformed["truncated " + str(length)] = good[:length]
        malformed["truncated row"] = good[:-5]
        for name, candidate in malformed.items():
            with self.subTest(name=name):
                calls = allocator.calls
                self.assertEqual(self.load(store, candidate), FORMAT)
                self.assertEqual(allocator.calls, calls)
                self.assertEqual(self.save(store), before)

    def test_binding_mismatch_capacity_and_empty_section_replacement(self):
        store = self.store(capacity=1)
        self.assertEqual(self.set(store, 3, payload(3)), OK)
        before = self.save(store)
        self.assertEqual(self.load(store, wire([(1, payload(1))]),
                                   base=b"X" + BASE[1:]), BINDING)
        self.assertEqual(self.load(store, wire([(1, payload(1))]), base=BASE + b"X"),
                         BINDING)
        self.assertEqual(self.load(store, wire([(1, payload(1)), (2, payload(2))])),
                         CAPACITY)
        self.assertEqual(self.save(store), before)
        self.assertEqual(self.load(store, wire([])), OK)
        self.assertEqual(BUILD.count(store), 0)

    def test_allocation_failures_preserve_existing_state_and_free_staging(self):
        allocator = self.allocator()
        store = self.store(allocator=allocator)
        peer = self.store()
        self.assertEqual(self.set(store, 1, payload(1)), OK)
        self.assertEqual(self.set(peer, 2, payload(2)), OK)
        before, peer_before = self.save(store), self.save(peer)
        live = dict(allocator.live)
        allocator.remaining = 0
        self.assertEqual(self.set(store, 3, payload(3)), MEMORY)
        self.assertEqual(self.load(store, wire([(4, payload(4))])), MEMORY)
        self.assertEqual(BUILD.copy(peer, store, 2, 3, 1), MEMORY)
        self.assertEqual(self.save(store), before)
        self.assertEqual(self.save(peer), peer_before)
        self.assertEqual(allocator.live, live)
        allocator.remaining = -1
        self.assertEqual(self.set(store, 3, payload(3)), OK)

    def test_create_failures_leave_output_unchanged_without_leaks(self):
        allocator = self.allocator()
        options = self.options(allocator=allocator)
        for remaining in (0, 1):
            allocator.remaining = remaining
            result = ct.c_void_p(12345)
            self.assertEqual(BUILD.create(ct.byref(options), ct.byref(result)), MEMORY)
            self.assertEqual(result.value, 12345)
            self.assertFalse(allocator.live)

    def test_invalid_arguments_and_options_leave_outputs_unchanged(self):
        store = self.store()
        out = buffer(b"\xa5" * PAYLOAD_BYTES)
        for invalid in (None, store):
            self.assertEqual(BUILD.get(invalid, KEYS, out), INVALID)
            self.assertEqual(bytes(out), b"\xa5" * PAYLOAD_BYTES)
        self.assertEqual(BUILD.set(store, 0, None), INVALID)
        self.assertEqual(BUILD.apply(store, None, 1), INVALID)
        self.assertEqual(BUILD.apply(store, None, 0), OK)
        self.assertEqual(BUILD.reset(None), INVALID)
        self.assertEqual(BUILD.load(store, None, 1, None, 0), INVALID)
        for change in ({"key_count": 0}, {"key_count": 65536},
                       {"capacity": KEYS + 1}):
            options = self.options()
            for key, value in change.items():
                setattr(options, key, value)
            result = ct.c_void_p(12345)
            self.assertEqual(BUILD.create(ct.byref(options), ct.byref(result)), INVALID)
            self.assertEqual(result.value, 12345)
        options = self.options(defaults=b"\xff" * PAYLOAD_BYTES)
        result = ct.c_void_p(12345)
        self.assertEqual(BUILD.create(ct.byref(options), ct.byref(result)), INVALID)
        allocator = self.allocator()
        options = self.options(allocator=allocator)
        options.release = Release()
        self.assertEqual(BUILD.create(ct.byref(options), ct.byref(result)), INVALID)

    def test_copy_uses_snapshot_for_forward_and_backward_overlap(self):
        for first, target in ((0, 1), (1, 0)):
            with self.subTest(first=first, target=target):
                store = self.store(capacity=6, key_count=6)
                original = [payload(i + 1) for i in range(6)]
                self.assertEqual(self.apply(store, list(enumerate(original))), OK)
                self.assertEqual(BUILD.copy(store, store, first, target, 5), OK)
                expected = original[:]
                expected[target:target + 5] = original[first:first + 5]
                self.assertEqual([self.get(store, key) for key in range(6)], expected)

    def test_bank_copy_reuses_capacity_and_source_stays_unchanged(self):
        source, destination = self.store(capacity=2), self.store(capacity=2)
        self.assertEqual(self.apply(source, [(0, payload(1)), (69, payload(2))]), OK)
        self.assertEqual(self.apply(destination, [(70, payload(3)), (100, payload(4))]), OK)
        before = self.save(source)
        self.assertEqual(BUILD.copy(source, destination, 0, 70, 70), OK)
        self.assertEqual(self.save(source), before)
        self.assertEqual(self.save(destination), wire([(70, payload(1)), (139, payload(2))]))

    def test_project_copy_includes_last_key_and_defaults(self):
        source, destination = self.store(capacity=2), self.store(capacity=2)
        self.assertEqual(self.apply(source, [(0, payload(1)), (KEYS - 1, payload(2))]), OK)
        self.assertEqual(self.set(destination, 2, payload(3)), OK)
        self.assertEqual(BUILD.copy(source, destination, 0, 0, KEYS), OK)
        self.assertEqual(self.save(destination), self.save(source))
        self.assertEqual(self.get(destination, 2), ZERO)

    def test_failed_copy_keeps_both_contexts_unchanged(self):
        source, destination = self.store(), self.store(capacity=1)
        self.assertEqual(self.set(source, 0, payload(1)), OK)
        self.assertEqual(self.set(destination, 2, payload(2)), OK)
        before = self.save(source), self.save(destination)
        self.assertEqual(BUILD.copy(source, destination, 0, 3, 1), CAPACITY)
        for first, target, count in ((KEYS, 0, 1), (0, KEYS, 1),
                                     (KEYS - 1, 0, 2), (0, 0, 0), (0, 0, 0xffffffff)):
            self.assertEqual(BUILD.copy(source, destination, first, target, count), INVALID)
        self.assertEqual((self.save(source), self.save(destination)), before)
        mismatched = self.store(defaults=payload(10))
        self.assertEqual(BUILD.copy(source, mismatched, 0, 0, 1), INVALID)


class PublicationTests(unittest.TestCase):
    def fixture(self):
        live = bytes(i % 251 for i in range(p.WORK_BYTES))
        controls = [bytearray(16) for _ in range(6)]
        for track, row in enumerate(controls):
            row[6], row[0] = 10, track + 1
        return live, tuple(bytes(row) for row in controls)

    def test_complete_snapshot_then_only_destination_publication(self):
        live, controls = self.fixture()
        private = p.expected_private_input(live, controls)
        output = bytearray(private)
        for track in range(6):
            output[34 + 66 * track:36 + 66 * track] = (2000 + track).to_bytes(2, "big")
        published = p.advance_expected_publication(live, private, bytes(output))
        self.assertEqual([i for i, (a, b) in enumerate(zip(live, published)) if a != b],
                         [34 + 66 * t + d for t in range(6) for d in (0, 1)])
        expected = p.expected_private_input(published, controls)
        self.assertEqual(p.compare_snapshot(published, controls, expected), expected)

    def test_stale_second_bank_is_rejected_even_if_numerics_match(self):
        live, controls = self.fixture()
        private = p.expected_private_input(live, controls)
        output = bytearray(private)
        output[34:36] = b"\x10\x20"
        advanced = p.advance_expected_publication(live, private, bytes(output))
        with self.assertRaisesRegex(AssertionError, "lost preceding"):
            p.compare_snapshot(advanced, controls, private)

    def test_unrelated_byte_loss_and_wrong_controls_are_rejected(self):
        live, controls = self.fixture()
        for offset in (0, 16, 28, 35, 400, 475):
            corrupt = bytearray(p.expected_private_input(live, controls))
            corrupt[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(AssertionError):
                p.compare_snapshot(live, controls, bytes(corrupt))

    def test_none_does_not_copy_private_header(self):
        live, _ = self.fixture()
        private = p.expected_private_input(live, (bytes(16),) * 6)
        self.assertEqual(p.advance_expected_publication(live, private, bytes(476)), live)

    def test_neutral_depth_does_not_publish_supplied_clamp(self):
        live, _ = self.fixture()
        for destination in range(10, 23):
            controls = []
            for _ in range(6):
                row = bytearray(16)
                row[6], row[14:16] = destination, b"\x40\x00"
                controls.append(bytes(row))
            private = p.expected_private_input(live, controls)
            self.assertEqual(p.advance_expected_publication(live, private, b"\x7f" * 476),
                             live)

    def test_all_destination_coordinates_and_invalid_domains(self):
        live, _ = self.fixture()
        for destination in range(10, 23):
            controls = []
            for _ in range(6):
                row = bytearray(16)
                row[6] = destination
                controls.append(bytes(row))
            private = p.expected_private_input(live, controls)
            published = p.advance_expected_publication(live, private, b"\xaa\xbb" * 238)
            for track in range(6):
                offset = 14 + 66 * track + 2 * destination
                self.assertEqual(published[offset:offset + 2], b"\xaa\xbb")
        for destination in (1, 9, 23, 32, 255):
            row = bytearray(16)
            row[6] = destination
            private = p.expected_private_input(live, (bytes(row),) * 6)
            with self.assertRaises(ValueError):
                p.advance_expected_publication(live, private, private)

    def test_incomplete_workspace_and_control_shapes_are_rejected(self):
        live, controls = self.fixture()
        for wrong in (live[:-1], bytearray(live), None):
            with self.assertRaises(ValueError):
                p.expected_private_input(wrong, controls)
            with self.assertRaises(ValueError):
                p.advance_expected_publication(live, live, wrong)
            with self.assertRaises(ValueError):
                p.compare_snapshot(live, controls, wrong)
        for wrong in (None, controls[:-1], (bytes(15),) * 6):
            with self.assertRaises(ValueError):
                p.expected_private_input(live, wrong)


class JoinedTests(HostCase):
    def test_restored_three_extra_lanes_preserve_every_preceding_publication(self):
        source = self.store(capacity=6)
        rows = []
        for track in range(6):
            extra = []
            for instance in range(3):
                control = bytearray(16)
                control[0], control[6] = instance + 1, 10
                control[14:16] = (0x4100 + track).to_bytes(2, "big")
                extra.append(bytes(control))
            rows.append((track, b"".join(extra)))
        self.assertEqual(self.apply(source, rows), OK)
        restored = self.store(capacity=6)
        self.assertEqual(self.load(restored, self.save(source)), OK)
        live = bytes(i % 251 for i in range(p.WORK_BYTES))
        for instance in range(3):
            controls = [self.get(restored, t)[16 * instance:16 * (instance + 1)]
                        for t in range(6)]
            private = p.expected_private_input(live, controls)
            self.assertEqual(p.compare_snapshot(live, controls, private), private)
            output = bytearray(private)
            for track in range(6):
                offset = 34 + 66 * track
                # Marqueur synthétique ; aucun calcul d'onde ni DSP de l'OS.
                value = int.from_bytes(private[offset:offset + 2], "big")
                output[offset:offset + 2] = ((value + instance + track + 1) % 65536).to_bytes(2, "big")
            advanced = p.advance_expected_publication(live, private, bytes(output))
            with self.assertRaises(AssertionError):
                p.compare_snapshot(advanced, controls, private)
            live = advanced
        for track in range(6):
            offset = 34 + 66 * track
            initial = int.from_bytes(bytes(i % 251 for i in range(476))[offset:offset + 2], "big")
            self.assertEqual(int.from_bytes(live[offset:offset + 2], "big"),
                             (initial + 6 + 3 * track) % 65536)

    def test_other_sound_keys_and_copied_settings_remain_independent(self):
        store = self.store(capacity=6)
        self.assertEqual(self.apply(store, [(key, payload(key + 1)) for key in range(6)]), OK)
        original = [self.get(store, key) for key in range(6)]
        self.assertEqual(BUILD.copy(store, store, 0, 1, 5), OK)
        self.assertEqual(self.get(store, 0), original[0])
        self.assertEqual([self.get(store, key) for key in range(1, 6)], original[:5])
        restored = self.store(capacity=6)
        self.assertEqual(self.load(restored, self.save(store)), OK)
        self.assertEqual([self.get(restored, key) for key in range(6)],
                         [original[0]] + original[:5])


if __name__ == "__main__":
    unittest.main(verbosity=2)
