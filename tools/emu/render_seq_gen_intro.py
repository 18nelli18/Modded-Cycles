#!/usr/bin/env python3
"""Aperçu PNG des rectangles exécutés par le cartouche, sans image Elektron."""
import argparse,json,pathlib,struct,zlib
from test_seq_gen_dynamics import fixture
from test_seq_gen_menu import ROOT
from test_sdvintage import main_os_from_syx

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    base=json.loads((ROOT/'tweaks/model-cycles_OS1.13/30-model-tg.json').read_text())
    tweak=json.loads((ROOT/'tweaks/model-cycles_OS1.13/experimental/sequence-only/49-scale-gen.json').read_text())
    r=fixture(main_os_from_syx(a.cycles),base,tweak)
    r.rects.clear();r.call('sg_render',r.obj,0x93006000)
    pixels=bytearray([255])*8192
    for _,left,bottom,right,top,color in r.rects:
        for x in range(left,right+1):
            for y in range(bottom,top+1):
                p=(63-y)*128+x
                pixels[p]=255-pixels[p] if color==0xffffffff else 255
    raw=b''.join(b'\0'+bytes(v for x in range(128) for v in [pixels[y*128+x]]*4) for y in range(64) for _ in range(4))
    def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',512,256,8,0,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
    pathlib.Path(a.output).write_bytes(png)
    print('ok : aperçu du cartouche exécuté, 128×64 agrandi ×4')
if __name__=='__main__':main()
