# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/test_lfo_four_publication_contract.py; lines 1-86.
# Unresolved integration bindings: see DEPENDENCIES.json.
import unittest
from . import lfo_four_publication_contract as p


class PublicationTests(unittest.TestCase):
    def fixture(self):
        live = bytes((i%251 for i in range(476)))
        controls = [bytearray(16) for _ in range(6)]
        for track,row in enumerate(controls):
            row[6] = 10
            row[0] = track+1
        return live,tuple(bytes(c) for c in controls)

    def test_complete_snapshot_then_only_destination_publication(self):
        live,controls = self.fixture()
        source = p.expected_private_input(live,controls)
        result = bytearray(source)
        for track in range(6):
            result[34+66*track:36+66*track] = (2000+track).to_bytes(2,"big")
        published = p.advance_expected_publication(live,source,bytes(result))
        self.assertEqual([i for i,(a,b) in enumerate(zip(live,published)) if a != b],
                         [34+66*t+d for t in range(6) for d in (0,1)])
        self.assertEqual(p.compare_snapshot(published,controls,p.expected_private_input(published,controls)),
                         p.expected_private_input(published,controls))

    def test_stale_second_bank_is_rejected_even_if_its_numerics_match(self):
        live,controls = self.fixture()
        source = p.expected_private_input(live,controls)
        output = bytearray(source)
        output[34:36] = b"\x10\x20"
        advanced = p.advance_expected_publication(live,source,bytes(output))
        with self.assertRaisesRegex(AssertionError,"lost preceding"):
            p.compare_snapshot(advanced,controls,source)

    def test_unrelated_byte_loss_and_wrong_controls_are_rejected(self):
        live,controls = self.fixture()
        for offset in (0,16,28,35,400,475):
            corrupt = bytearray(p.expected_private_input(live,controls))
            corrupt[offset] ^= 1
            with self.subTest(offset=offset),self.assertRaises(AssertionError):
                p.compare_snapshot(live,controls,bytes(corrupt))

    def test_none_does_not_copy_private_header(self):
        live,_ = self.fixture()
        controls = (bytes(16),)*6
        source = p.expected_private_input(live,controls)
        self.assertEqual(p.advance_expected_publication(live,source,bytes(476)),live)

    def test_neutral_depth_does_not_publish_native_clamp(self):
        live,_ = self.fixture()
        for destination in range(10,23):
            controls=[]
            for _ in range(6):
                row=bytearray(16); row[6]=destination; row[14:16]=b"\x40\x00"
                controls.append(bytes(row))
            source=p.expected_private_input(live,controls)
            output=bytearray(source)
            for track in range(6):
                offset=14+66*track+2*destination
                output[offset:offset+2]=b"\x7f\x00"
            self.assertEqual(p.advance_expected_publication(live,source,bytes(output)),live)

    def test_all_expected_destination_coordinates_and_invalid_domains(self):
        live,_ = self.fixture()
        for destination in range(10,23):
            controls = []
            for _ in range(6):
                row=bytearray(16);row[6]=destination;controls.append(bytes(row))
            source=p.expected_private_input(live,controls)
            output=bytearray(source)
            for track in range(6):
                offset=14+66*track+2*destination
                output[offset:offset+2]=b"\xaa\xbb"
            published=p.advance_expected_publication(live,source,bytes(output))
            for track in range(6):
                offset=14+66*track+2*destination
                self.assertEqual(published[offset:offset+2],b"\xaa\xbb")
        for destination in (1,9,23,32,255):
            control=bytearray(16);control[6]=destination
            source=p.expected_private_input(live,(bytes(control),)*6)
            with self.assertRaises(ValueError):
                p.advance_expected_publication(live,source,source)


if __name__ == "__main__":
    unittest.main()
