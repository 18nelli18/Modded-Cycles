#!/usr/bin/env python3
"""Preuve du delta MIT Slice : notes, vitesse, sélection et lecture PCM TG.

Exécute le code TG réellement livré, avant/après le raccord. Le remplissage
PCM comprend la sélection de fenêtre, les trims, la phase et les 32 paires
suréchantillonnées ; les DSP et l'enveloppe natifs ne sont pas simulés ici.
--base TG.json --tweak candidat.json --elf base/_b.elf ; environ 2 secondes.
"""
import argparse
import json
import pathlib
import struct

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn import m68k_const as m

from gen_seq_gen import symbols
import sprites

VOICE = 0x93001000
TRACK = 0x93002000
PATTERN = 0x93003000
OUT = 0x9300C000
STACK = 0x9301F000
PCM = 0x94000000
REGS = ['D' + str(i) for i in range(8)] + ['A' + str(i) for i in range(8)]


class Machine:
    def __init__(self, raw, dest, syms):
        self.s = syms
        self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        self.uc.ctl_set_cpu_model(m.UC_CPU_M68K_ANY)
        for at, size in [(0x40000000, 0x200000), (0x4E2E0000, 0x10000), (0x4E3E0000, 0x10000),
                         (0x93000000, 0x20000), (PCM, 0x20000)]:
            self.uc.mem_map(at, size)
        self.uc.mem_write(dest, raw)
        for write in syms.get('_native_writes', []):
            self.uc.mem_write(0x40000400 + write['off'], bytes.fromhex(write['new']))
        # Le SR doit précéder A7 : changer S sélectionne l'autre pile du CPU.
        self.reg('SR', 0x2000)
        self.seed()

    def reg(self, name, value=None):
        r = getattr(m, 'UC_M68K_REG_' + name)
        if value is None:
            return self.uc.reg_read(r)
        self.uc.reg_write(r, value)

    def seed(self):
        for i, name in enumerate(REGS):
            self.reg(name, 0xA0200000 + 0x101 * i)
        self.reg('A7', STACK)

    def write(self, at, data):
        self.uc.mem_write(self.s.get(at, at), data)

    def w32(self, at, value):
        self.write(at, struct.pack('>I', value))

    def r32(self, at):
        return struct.unpack('>I', self.uc.mem_read(self.s.get(at, at), 4))[0]

    def lane32(self, name, lane, value):
        self.w32(self.s[name] + lane * 4, value)

    def run(self, start, end):
        start, end = self.s.get(start, start), self.s.get(end, end)
        self.uc.emu_start(start, end, count=20000)
        assert self.reg('PC') == end, (hex(self.reg('PC')), hex(end))

    def snapshot(self, names=REGS):
        return {name: self.reg(name) for name in names}

    def preserve(self, start, end, clobbered):
        before = self.snapshot()
        self.run(start, end)
        for name, value in before.items():
            if name not in clobbered:
                assert self.reg(name) == value, (start, name, hex(value), hex(self.reg(name)))


def bounded_delta(base, tweak, old, raw, dest):
    assert len(old) == len(raw)
    assert base['writes'] == tweak['writes'][:len(base['writes'])]
    assert len(tweak['writes']) == len(base['writes']) + 2
    mask = tweak['varispeed_mask']
    extra = tweak['writes'][len(base['writes']):]
    assert extra[0]['off'] == int(mask['at'], 16) - 0x40000400
    assert len(bytes.fromhex(extra[0]['new'])) == mask['used'] <= mask['size']
    assert extra[1] == sprites.redirect_write(int(mask['at'], 16))
    assert base['append']['at'] == tweak['append']['at']
    assert base['append']['parts'][0]['dest'] == tweak['append']['parts'][0]['dest']
    allowed = set()
    for site in tweak['varispeed_patch_sites']:
        at = int(site['at'], 16) - dest
        allowed.update(range(at, at + site['size']))
    table = int(tweak['varispeed_table']['at'], 16) - dest
    allowed.update(range(table, table + tweak['varispeed_table']['size']))
    assert all(x == y or i in allowed for i, (x, y) in enumerate(zip(old, raw)))
    assert all(tweak['symbols'][k] == v for k, v in base['symbols'].items())
    assert old[:0x1610] == raw[:0x1610] == bytes(0x1610)
    print('ok : taille et symboles TG inchangés ; 4 raccords + ancienne table ; un masque redirigé ; préfixe zéro intact')


def helpers(raw, dest, s):
    e = Machine(raw, dest, s)
    for lane in range(8):
        for note in (0, 35, 36, 48, 60, 83, 84, 127):
            e.seed()
            e.reg('D4', lane)
            e.write(s['slice_pending'] + lane, b'\x01')
            e.write(s['live_note'] + lane, bytes([note]))
            e.preserve('tgsv_select', 'tgsv_select_return', {'D0', 'D1', 'A0'})
            assert e.reg('D1') == (note - 52) & 0xFFFFFFFF
            e.write(s['slice_pending'] + lane, b'\x00')
            e.write(s['live_note'] + lane, b'\x30')
            e.run('tgsv_select', 'tgsv_select_return')
            assert e.reg('D1') == (note - 52) & 0xFFFFFFFF
            center = e.r32(s['tgsv_pitch_ctr'] + max(0, min(note - 36, 47)) * 4)
            for pitch in (0, center // 2, center, min(center * 2, 0x3FFFF), 0x40000):
                e.reg('D2', VOICE)
                e.w32(VOICE + 232, pitch)
                e.reg('SR', 0x2004)
                e.preserve('tgsv_speed_gate', 'sv_defstep' if pitch == 0 else 'sv_havestep', {'D0', 'D1', 'A0'})
                if pitch:
                    assert e.reg('D1') == ((min(pitch, 0x3FFFF) << 14) // center) << 2
    for lane in range(8):
        for note in (36, 60, 83, 255):
            for per_track in (0, 1):
                e.seed()
                e.reg('A1', TRACK)
                e.reg('A3', PATTERN)
                e.reg('D2', lane)
                e.reg('D3', 15)
                e.write(TRACK + 580 + 15, bytes([note]))
                e.write(TRACK + 712, b'\x48')
                e.write(PATTERN + 30667, bytes([per_track]))
                e.preserve('tgsv_seq', 'tgsv_seq_return' if per_track else 'sq_plen', {'D0', 'A5'})
                assert bytes(e.uc.mem_read(s['live_note'] + lane, 1)) == bytes([72 if note == 255 else note])
    print('ok : 8 emplacements TG, capture au trig, gamme/clamps, vitesses demi/unité/double, ABI des trois raccords')


def non_slice(old, raw, dest, s):
    for mode in (0, 1, 3, 4, 5, 6):
        for pitch in (0, 1, 45710, 172578, 262143):
            results = []
            for code in (old, raw):
                e = Machine(code, dest, s)
                e.reg('D2', VOICE)
                e.reg('D4', 3)
                e.w32(VOICE + 232, pitch)
                e.lane32('loop_mode', 3, mode)
                e.run('sv_noslice', 'sv_havestep')
                # Drapeaux morts à cette jonction : step_mod les réécrit.
                results.append(e.snapshot())
            assert results[0] == results[1], (mode, pitch)
    print('ok : calcul complet des autres modes TG identique, tous les registres vivants compris (30 cas)')


def note_hooks(old, raw, dest, s):
    for lane in range(s['MAX_TRK']):
        for code, expected in ((old, 52), (raw, 69)):
            e = Machine(code, dest, s)
            e.write('scale_state', b'\x00')
            e.lane32('loop_mode', lane, 2)
            e.reg('D0', 127)
            e.reg('D2', lane)
            e.reg('D3', 69)
            e.preserve('note_on_hook', 0x40081742, {'D1', 'A0'})
            assert bytes(e.uc.mem_read(s['live_note'] + lane, 1)) == b'\x45'
            e.reg('D3', 52)
            e.preserve('note_off_hook', 0x4008147A, {'D1', 'A0'})
            assert bytes(e.uc.mem_read(s['live_note'] + lane, 1)) == bytes([expected])
    print('ok : vrai note-on/off TG ; un note-off tardif écrasait la nouvelle note, le raccord la conserve')


def boot_clear(raw, dest, s, mask, used):
    e = Machine(raw, dest, s)
    e.uc.mem_map(0x40200000, 0x02200000)
    # Marqueurs aux deux bouts de BSS, et le vrai tampon zéro filesystem.
    for at in (0x4019B590, s['reserved_end'], 0x423380A0):
        e.write(at, b'\xA5' * 16)
    e.write(0x401A7750, b'\xA5' * 0x4000)
    helper = bytes(e.uc.mem_read(mask, used))
    for reg in ('D4', 'D5', 'D6', 'D7'):
        e.reg(reg, 0)
    e.reg('A0', 0x4019B590)
    # Vraie boucle TG complète, pas le movec ACR1 non émulé du prologue.
    e.uc.emu_start(s['clear_loop'], s['clear_done'], count=20000000)
    assert e.reg('PC') == s['clear_done']
    for at in (0x4019B590, s['reserved_end'], 0x423380A0):
        assert bytes(e.uc.mem_read(at, 16)) == bytes(16)
    assert bytes(e.uc.mem_read(0x401A7750, 0x4000)) == bytes(0x4000)
    assert bytes(e.uc.mem_read(mask, used)) == helper
    assert bytes(e.uc.mem_read(s['blob_start'], len(raw) - 0x1610)) == raw[0x1610:]
    print('ok : vraie boucle boot TG complète ; BSS et tampon filesystem zéro, helpers/table conservés, aucun raccord boot')


def render_setup(code, dest, s, lane, note, pitch, reverse=False, table=False):
    e = Machine(code, dest, s)
    for name, value in [('loop_mode', 2), ('track_slot', 0), ('dial_start', 32512 if reverse else 0),
                        ('dial_end', 0 if reverse else 32512), ('sl_S', 16 if table else 0),
                        ('sl_N', 16), ('win_wrap', 0), ('fx_sel', 0), ('slot_soff', 0), ('chn_sel', 0)]:
        e.lane32(name, lane, value)
    e.w32('slot_count', 2048)
    e.w32('slot_base', PCM)
    e.write(PCM + 64, struct.pack('>2048h', *range(2048)))
    if table:
        # Même nombre de tranches, longueurs non uniformes ; fin globale 2048.
        cuts = [i * 96 for i in range(16)] + [2048]
        for i, at in enumerate(cuts):
            e.w32(s['sl_tbl'] + lane * 33 * 4 + i * 4, at)
    e.write(s['slice_pending'] + lane, b'\x01')
    e.write(s['live_note'] + lane, bytes([note]))
    e.w32(VOICE + 232, pitch)
    e.reg('D2', VOICE)
    e.reg('D3', OUT)
    e.reg('D4', lane)
    return e


def pcm_block(e, s):
    # Jusqu'à la sauvegarde de phase originale, juste avant les DSP.
    e.run('sv_lv', s['sv_fl_mid'] + 14)
    return struct.unpack('>64i', e.uc.mem_read(s['sampler_buf'] + 32, 256))


def render_pcm(old, raw, dest, s):
    for lane in range(6):
        for note in (52, 60, 67):
            ctr = struct.unpack_from('>I', raw, s['tgsv_pitch_ctr'] - dest + (note - 36) * 4)[0]
            for reverse in (False, True):
                for table in (False, True):
                    for ratio in (1, 2):
                        e = render_setup(raw, dest, s, lane, note, ctr * ratio, reverse, table)
                        output = pcm_block(e, s)
                        base = (note - 52) * (96 if table else 128)
                        span = (2048 - base) if table and note == 67 else (96 if table else 128)
                        if reverse:
                            # Start applique l'arrondi TG à blocs de 64,
                            # contrairement à End au maximum (fin exacte).
                            span = ((span >> 6) * 32512 >> 9) + 1
                        first = base + span - 1 if reverse else base
                        expected = tuple((first + (-1 if reverse else 1) * (i // 2) * ratio) << 15
                                         for i in range(64))
                        assert output == expected, (lane, note, reverse, table, ratio)
                        assert e.r32(s['win_lo'] + lane * 4) == base
                        assert e.r32(s['win_span'] + lane * 4) == span
                        assert bytes(e.uc.mem_read(s['slice_pending'] + lane, 1)) == b'\x00'
                        assert e.reg('D3') == OUT
    # Le bouton Pitch, sur un même trig, modifie la vitesse sans déplacer la
    # fenêtre. Une future note arrivée tôt ne déplace pas la tranche non plus.
    e = render_setup(raw, dest, s, 0, 60, 45710)
    first = pcm_block(e, s)
    e.w32(VOICE + 232, 91420)
    e.write(s['live_note'], b'\x34')
    second = pcm_block(e, s)
    assert e.r32('win_lo') == 1024
    assert second == tuple((1056 + (i // 2) * 2) << 15 for i in range(64))
    assert first == tuple((1024 + i // 2) << 15 for i in range(64))
    e.w32(VOICE + 232, 28795)
    e.write(s['slice_pending'], b'\x01')
    third = pcm_block(e, s)
    assert e.r32('win_lo') == 0
    assert third == tuple((i // 2) << 15 for i in range(64))
    # Documenter la régression de la base : Pitch haut déplaçait la tranche.
    baseline = render_setup(old, dest, s, 0, 60, 91420)
    pcm_block(baseline, s)
    assert baseline.r32('win_lo') == 4 * 128
    print('ok : vrai remplissage PCM TG, 144 blocs ; 6 pistes, 3 notes, trims inverse/direct, tables égales/non uniformes')
    print('ok : Pitch modifie la vitesse sans déplacer la tranche ; note future non déclenchée sans effet')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', required=True)
    p.add_argument('--tweak', required=True)
    p.add_argument('--elf', required=True)
    a = p.parse_args()
    b = json.loads(pathlib.Path(a.base).read_text())
    t = json.loads(pathlib.Path(a.tweak).read_text())
    s = symbols('m68k-elf-', pathlib.Path(a.elf))
    # La variante Syntakt réserve la même zone TG un MiB plus bas ; ses
    # symboles privés ne sont pas exportés dans le JSON, contrairement à SLD_BASE.
    delta = int(t['symbols'].get('SLD_BASE', hex(s['SLD_BASE'])), 16) - s['SLD_BASE']
    for k, v in list(s.items()):
        if 0x4E3E0000 <= v < 0x4E3F0000:
            s[k] = v + delta
    s.update({k: int(v, 16) for k, v in t['symbols'].items()})
    s['_native_writes'] = t['writes'][len(b['writes']):]
    old = bytes.fromhex(b['append']['parts'][0]['hex'])
    raw = bytes.fromhex(t['append']['parts'][0]['hex'])
    dest = int(t['append']['parts'][0]['dest'], 16)
    bounded_delta(b, t, old, raw, dest)
    boot_clear(raw, dest, s, int(t['varispeed_mask']['at'], 16), t['varispeed_mask']['used'])
    helpers(raw, dest, s)
    non_slice(old, raw, dest, s)
    note_hooks(old, raw, dest, s)
    render_pcm(old, raw, dest, s)
    print('Limite : DSP/enveloppe et test matériel à vérifier ; sélection et lecture PCM TG exécutées sans simulation')


if __name__ == '__main__':
    main()
