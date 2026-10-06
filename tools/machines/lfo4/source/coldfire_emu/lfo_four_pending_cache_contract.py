# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_pending_cache_contract.py; lines 1-89.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""The original pending-save cache lease, not anonymous RAM admission.

Observe the actual4006a216 return to4000f7bc and the enclosing encoder call.
Only the selected stock-sized cache data can be admitted. No append bytes,
media result, manager readiness, scheduler or hardware ownership is supplied.
This helper is preparatory until wired into and executed by the owned runner.
"""
from . import lfo_four_native_media_join as media
from .backend import MAIN_BASE, MAIN_SHA256

RETURN_PC, ENCODE_PC, ENCODE_RETURN = 0x4000f7bc, 0x4000f810, 0x4000f816
CACHES = (0x40a80b28, 0x40c90f38)
BODIES = (
    (0x4006a19c,0x4006a268,'7ab0b94fc8c7d74ffa0a03424264454f15b2d1ecd22a8af67d997bbd9a47e45b'),
    (0x4006a120,0x4006a19c,'996e8842d37fa4d4880ad63034fa5da4ad07486faac6312e1607304ad4d7b955'),
    (0x4006a4d6,0x4006a538,'1b68a50bfe1addece5a5758430d8f4d0bff57d5591815f502eafd1e02a79f75c'),
)


def contract(image):
    _require(media.sha(image)==MAIN_SHA256,'unsupported immutable MAIN')
    for lo,hi,digest in BODIES:
        _require(media.sha(image[lo-MAIN_BASE:hi-MAIN_BASE])==digest,'original cache body changed')
    _require(CACHES[0]+12+media.STOCK==CACHES[1] and
             CACHES[1]+12+media.STOCK==0x40ea1348,'stock cache extent arithmetic')
    return dict(bodies=[dict(start=hex(a),end=hex(b),sha256=h) for a,b,h in BODIES],
        caches=[dict(base=hex(a),data=hex(a+12),end=hex(a+12+media.STOCK)) for a in CACHES],
        static_cache_not_heap_slack=True,append_admitted=False,
        cache_flush_admitted=False,media_readiness_proven=False)


def _word(cpu, address):
    return int.from_bytes(cpu.read(address,4),'big')


def _require(ok, message):
    if not ok:
        raise RuntimeError('pending stock cache: '+message)


class StockCacheLease:
    def __init__(self, project, backing):
        self.project, self.backing = project, backing
        self.cache = None
        self.encoded = False
        self.witnesses = []

    def observe(self, cpu, regs):
        pc, sp = regs['pc'], regs['a7']
        if pc == RETURN_PC:
            _require(cpu.read(0x4000f7b6,6).hex()=='4eb94006a216',
                     'cache selection call changed')
            _require(regs['a4']==self.project and regs['d3']==96,
                     'not the actual Project temporary-save request')
            _require(_word(cpu,sp+4)==96, 'selection stack slot differs')
            data = regs['d0']
            self.cache = None
            self.encoded = False
            if data:
                base=data-12
                _require(base in CACHES,'selection returned an unknown cache')
                _require(_word(cpu,base)==96 and cpu.read(base+4,3)==b'\x01\x01\x01',
                         'original selected cache index/flags differ')
                self.cache=base
            self.witnesses.append(dict(pc=hex(pc),bytes=cpu.read(pc,2).hex(),
                actual_returned_data=hex(data),slot=96,Project=hex(self.project),
                stock_bytes=media.STOCK,append_admitted=False))
        elif pc == ENCODE_PC:
            _require(self.cache is not None,'encoder without observed cache selection')
            _require(cpu.read(pc,6).hex()=='4eb94005d18a', 'encoder call changed')
            args=[_word(cpu,sp+4*i) for i in range(5)]
            _require(args[:4]==[self.cache+12,self.backing,0,0xffffffff],
                     'encoder cache/backing arguments differ')
            _require(regs['a4']==self.project and regs['a3']==self.cache+12 and
                     _word(cpu,self.project+16)==self.backing,
                     'Project/cache/backing identity differs')
            self.witnesses.append(dict(pc=hex(pc),bytes=cpu.read(pc,6).hex(),
                args=[hex(a) for a in args],actual_original_encoder=True))
        elif pc == ENCODE_RETURN:
            _require(self.cache is not None and any(w['pc']==hex(ENCODE_PC) for w in self.witnesses),
                     'encoder return without entry')
            self.encoded=bool(regs['d0']&255)
            self.witnesses.append(dict(pc=hex(pc),actual_encoder_return_byte=regs['d0']&255,
                                      encoded=self.encoded))

    def admits(self, address, count):
        return (type(address) is int and type(count) is int and count>=0 and
                self.cache is not None and self.cache+12<=address and
                address+count<=self.cache+12+media.STOCK)
