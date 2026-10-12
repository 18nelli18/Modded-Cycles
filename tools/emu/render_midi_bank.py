#!/usr/bin/env python3
"""Aperçu du rendu MIDI actuel avec primitives et polices natives exécutées.

Sortie PNG seulement ; aucune image firmware ni donnée de police exportée.
Les données musicales et l'objet de vue viennent d'une fixture synthétique.
"""
import argparse
import pathlib
import struct
import zlib
from unicorn import UC_HOOK_CODE
import unicorn.m68k_const as mk
from test_seq_gen_menu import Rig
from test_midi_lane_page import load
from test_sdvintage import main_os_from_syx


class DrawingRig(Rig):
    def stub(self, u, addr, size, data):
        if addr == 0x40071a04:
            sp = u.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack('>8I', u.mem_read(sp+4, 32))
            self.texts.append((self.string(args[5]), args[6]))
            return
        if addr == 0x40070dea:
            return
        super().stub(u, addr, size, data)


def png(path, pixels, scale=6):
    width, height = 128*scale, 64*scale
    rows = b''.join(b'\0'+bytes(value for value in pixels[y*128:(y+1)*128]
                              for _ in range(scale))
                    for y in range(64) for _ in range(scale))
    def chunk(kind, body):
        return struct.pack('>I', len(body))+kind+body+struct.pack(
            '>I', zlib.crc32(kind+body)&0xffffffff)
    pathlib.Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(
        b'IHDR', struct.pack('>2I5B', width, height, 8, 0, 0, 0, 0))+
        chunk(b'IDAT', zlib.compress(rows))+chunk(b'IEND', b''))


def stock_fixture(r):
    # Dépendances de données synthétiques ; tout le dessin reste natif.
    values = {0x400cf9a8: 0x93010000, 0x4006b704: 0,
              0x4006b736: 0, 0x400124e8: 0, 0x400cfd0e: 0x93010000,
              0x4006a96c: 0, 0x4006aa2e: 0, 0x4006bb18: 0,
              0x4000f208: 0x93011000, 0x4000d0dc: 0x93011000,
              0x400097f0: 0x93012000, 0x4001263c: 0, 0x40053558: 0}
    r.w32(0x93012000, 0x93012080)
    for addr, value in values.items():
        r.stubs[addr] = lambda a, value=value: value
        r.u.hook_add(UC_HOOK_CODE, r.stub, begin=addr, end=addr)
    def name(a):
        r.w32(r.u.reg_read(mk.UC_M68K_REG_A0), 0x9301300c)
        return 0
    r.u.mem_write(0x93013000, struct.pack('>III', 4, 4, 0xffffffff)+b'TEST\0')
    r.stubs[0x4000ce94] = name
    r.u.hook_add(UC_HOOK_CODE, r.stub, begin=0x4000ce94, end=0x4000ce94)
    for addr, symbol in ((0x4001b28a, 'mlp_stock_track'),
                         (0x4001b774, 'mlp_stock_volume'),
                         (0x4001b722, 'mlp_stock_pan')):
        r.u.mem_write(addr, b'\x4e\xb9'+struct.pack('>I', r.s[symbol]))
    r.u.mem_write(0x4001b6ba, b'\x4e\xf9'+struct.pack('>I', r.s['mlp_stock_track_label'])+b'\x4e\x71'*2)
    for vector, start, count, mask, array in (
            (0x40fe3818, 0x4017a694, 31, 0x4017a5cc, 0x93014000),
            (0x40fe34e0, 0x40170e90, 15, 0x40170dc8, 0x93015000)):
        for i in range(count):
            r.call(0x40070172, array+28*i, 50, 9, start+200*i, mask)
        for offset, value in ((0, array), (4, array+28*count), (8, array+28*count)):
            r.w32(vector+offset, value)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--stock', action='store_true')
    ap.add_argument('--held', action='store_true')
    ap.add_argument('--lane', type=int, choices=range(1, 7), default=1)
    args = ap.parse_args()
    r = DrawingRig(main_os_from_syx(args.cycles), {'writes': []},
                   {'writes': [], 'symbols': {}})
    r.stubs[0x400802ec] = lambda a: 0
    r.u.hook_add(UC_HOOK_CODE, r.stub, begin=0x400802ec, end=0x400802ec)
    load(r, stock_display=args.stock)
    if args.stock:
        stock_fixture(r)
    pattern, bitmap, framebuffer = 0x93070000, 0x93006000, 0x93090000
    assert r.call('ml_init', pattern) == 1
    r.w32(r.s['ml_pattern'], pattern)
    r.w32(r.s['mlp_track'], args.lane-1)
    r.u.mem_write(pattern+264*(args.lane-1)+8, bytes([60, 100, 1, 1]))
    r.w32(r.s['mlp_held'], int(args.held))
    # Préfixe d'initialisation des quatre polices utilisées, sans approximation.
    r.call(0x400e7dbc)
    r.u.mem_write(framebuffer, bytes(1024))
    r.call(0x40070172, bitmap, 128, 64, framebuffer, 0)
    r.call('mlp_render', 0, bitmap)
    data = bytes(r.u.mem_read(framebuffer, 1024))
    assert any(data), 'bitmap vide'
    pixels = []
    for screen_y in range(64):
        y = 63-screen_y
        for x in range(128):
            word = struct.unpack_from('>I', data, (x*2+y//32)*4)[0]
            pixels.append(0 if word & (1 << (31-y%32)) else 255)
    png(args.output, pixels)
    print('ok : mlp_render + Bitmap/texte/rectangles/police natifs, PNG 768×384')


if __name__ == '__main__':
    main()
