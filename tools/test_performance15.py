#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests sans firmware du catalogue Performance15 ; validation du contrat public."""
import copy
import importlib.util
import pathlib
import unittest
import tempfile
import gen_performance15 as generator

SRC = pathlib.Path(__file__).resolve().parent / 'machines/performance15'
spec = importlib.util.spec_from_file_location('performance_registry', SRC / 'performance_registry.py')
registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(registry)


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.catalog = registry.load()

    def test_identites_stables(self):
        for scope, count, base in [('track', 14, 0x100), ('fx', 4, 0x200)]:
            for route in range(count):
                self.assertEqual(self.catalog.key(scope, route), base + route)
        self.assertIsNone(self.catalog.key('track', 255))
        self.assertIsNone(self.catalog.key('fx', 255))

    def test_menu_independant_des_identites(self):
        data = copy.deepcopy(self.catalog.data)
        data['profiles'][0]['track_menu'].reverse()
        changed = registry.Registry(data)
        self.assertEqual(changed.key('track', 0), 0x100)
        self.assertEqual(changed.menu(0, 'track')[0], 13)

    def test_identites_dupliquees_refusees(self):
        data = copy.deepcopy(self.catalog.data)
        data['parameters'][1]['key'] = data['parameters'][0]['key']
        with self.assertRaises(registry.RegistryError):
            registry.Registry(data)

    def test_mauvais_profil_refuse(self):
        data = copy.deepcopy(self.catalog.data)
        data['profiles'][0]['track_menu'].append(0x200)
        with self.assertRaises(registry.RegistryError):
            registry.Registry(data)

    def test_libelle_oled_borne(self):
        with self.assertRaises(registry.RegistryError):
            registry.Registry.label('TOO LONG')

    def test_aucun_moteur_supplementaire_annonce(self):
        self.assertEqual(len(self.catalog.profiles), 1)
        self.assertEqual(self.catalog.profiles[0]['name'], 'stock')
        self.assertEqual({p['instance'] for p in self.catalog.parameters}, {0, 1})


class FirmwareGuardTest(unittest.TestCase):
    def test_entree_non_officielle_refusee(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'invalid.syx'
            path.write_bytes(b'invalid')
            with self.assertRaisesRegex(SystemExit, 'officiel'):
                generator.compile_mode(path)

    def test_fichier_officiel_non_ecrase(self):
        with self.assertRaisesRegex(SystemExit, 'ecraser'):
            generator.package('same.syx', b'', 'same.syx')


if __name__ == '__main__':
    unittest.main()
