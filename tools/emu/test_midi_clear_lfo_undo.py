#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prototype B : vrais clear/Undo, frames IPL0, purge atomique et moteur natif.

--cycles OS1.13.syx --base JSON --tweak JSON
Allocateur/redraw et writer physiques simulés ; clipboard, locks, snapshots,
adaptateurs et calcul du LFO natif exécutés. Aucun test matériel implicite.
"""
import argparse
import json
import pathlib
import struct

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE, m68k_const as mk
from test_midi_bank_reclaim import load
from test_seq_gen_menu import RAW, STACK, STOP
from test_sdvintage import main_os_from_syx
import build

DEFAULT = bytes.fromhex('40000009400000800000000000004000') * 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles', required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--tweak', required=True)
    p.add_argument('--dynamic',action='store_true')
    p.add_argument('--integrated-ui',action='store_true')
    a = p.parse_args()
    base = json.loads(pathlib.Path(a.base).read_text())
    t = json.loads(pathlib.Path(a.tweak).read_text())
    meta = t['b_clear_lfo_undo']
    dest = int(t['append']['dest'], 16)
    old_raw = bytes.fromhex(base['append']['parts'][0]['hex'])
    raw = bytes.fromhex(t['append']['parts'][0]['hex'])
    allowed = {i for row in meta['edits'] for i in range(int(row['at'], 16) - dest, int(row['at'], 16) - dest + len(bytes.fromhex(row['old']))) if i >= 0}
    if a.integrated_ui:
        edits=t['play_ui']['edits']
        assert {e['role'] for e in edits}=={'record_frame','step_states','chord_pad','boot_end'}
        allowed.update(i for row in edits for i in range(int(row['at'],16)-dest,int(row['at'],16)-dest+len(bytes.fromhex(row['old']))) if i>=0)
    assert {i for i, (x, y) in enumerate(zip(old_raw, raw)) if x != y} <= allowed
    for name, value in base['symbols'].items():
        if name not in ('ML_BANK_END', 'ML_BANK_SIZE'):
            assert t['symbols'][name] == value, name
    if not a.dynamic:assert int(meta['adapter_end'], 16) <= 0x401ce400
    assert (a.dynamic or t['ram_only_rollback']) and not {0x4000f762, 0x4000f850, 0x4008b24a, 0x4008b3f6} & {build.BASE + w['off'] for w in t['writes']}
    stock = main_os_from_syx(a.cycles)
    r = load(stock, t)
    s = r.s
    pat, ctx, repeat, runtime, obj = 0x93080000, 0x93084000, 0x93088000, 0x9308a000, 0x9308b000
    r.call('ml_init', pat)
    r.call('mlcc_cfg_init', pat + 4704)
    r.u.mem_write(ctx, bytes(3020))
    for name, value in (('ml_pattern', pat), ('ml_play_pattern', pat), ('mlcc_context', ctx),
                        ('ml_runtime', runtime), ('mlp_obj', obj), ('ml_store_load_ready', 1),
                        ('ml_repeat_edit_settings', repeat), ('mlp_func', 1)):
        r.w32(s[name], value)
    for lane in range(6):
        r.u.mem_write(pat + lane * 264, bytes((1, 0, 6 + lane, 4, 16, 2, 0, 0)))
        r.u.mem_write(pat + lane * 264 + 8, bytes((60 + lane, 96, 3, 1)) * 64)
        r.u.mem_write(repeat + lane * 520, bytes((0, 4, 4, 0, 0, 1, 0, 0)))
        r.call('ml_repeat_locks_init', repeat + lane * 520 + 8)
        for lfo in range(2):
            values = (20000 + lane, 9, 16384, (0, 127, 74)[lane % 3], 3, 12000 + lane, 0, 28000)
            r.u.mem_write(pat + 4704 + lane * 32 + lfo * 16, struct.pack('>8H', *values))
    r.call('mclf_refresh')

    def stub(address, fn):
        fresh = address not in r.stubs
        r.stubs[address] = fn
        return r.u.hook_add(UC_HOOK_CODE, r.stub, begin=address, end=address) if fresh else None

    stub(s['ml_repeat_prepare_ui'], lambda args: r.w32(s['ml_repeat_edit_settings'], repeat) or 1)
    stub(0x400760ba, lambda args: 0)
    frame_calls = []

    def frame_guard(u, address, size, data):
        assert not u.reg_read(mk.UC_M68K_REG_SR) & 0x700, 'préparation frame sous IRQ'
        frame_calls.append(address)

    r.u.hook_add(UC_HOOK_CODE, frame_guard, begin=s['mlcc_frame_prepare'], end=s['mlcc_frame_prepare'])

    def allocation_guard(u, address, size, data):
        assert not u.reg_read(mk.UC_M68K_REG_SR) & 0x700, 'allocation sous IRQ'

    r.u.hook_add(UC_HOOK_CODE, allocation_guard, begin=0x400802e0, end=0x400802e0)

    def atomic_guard(u, access, address, size, value, data):
        assert u.reg_read(mk.UC_M68K_REG_SR) & 0x700 == 0x700, ('phase/queue hors IPL7', hex(address))

    r.u.hook_add(UC_HOOK_MEM_WRITE, atomic_guard, begin=ctx + 2480, end=ctx + 3007)
    audio = bytes(r.u.mem_read(RAW, 722))

    def clip(code, flags=1):
        r.u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        return r.call('mlp_clip_key', code, flags)

    def press(code):
        assert clip(code) == 1
        assert clip(code, 0) == 1

    def phase(lane):
        return bytes(r.u.mem_read(ctx + 2480 + 32 * lane, 32)) + bytes(r.u.mem_read(ctx + 2672 + 32 * lane, 32))

    def queue(lane):
        return bytes(r.u.mem_read(ctx + 2864 + 24 * lane, 24))

    def cfg(lane):
        return bytes(r.u.mem_read(pat + 4704 + lane * 32, 32))

    locks = r.call('mlkc_locks_for', pat, 1)
    assert locks
    for lane in range(6):
        r.w32(s['mlp_track'], lane)
        r.u.mem_write(ctx + 2480, b''.join(struct.pack('>8I', *range(100 * j, 100 * j + 8)) for j in range(6)))
        r.u.mem_write(ctx + 2672, b''.join(struct.pack('>8I', *range(1000 + 100 * j, 1008 + 100 * j)) for j in range(6)))
        for j in range(6):
            for lfo in range(2):
                assert r.call('mlcc_lane_put', ctx + 2864, pat, j, lfo, 74, 42 + j) == 1
        r.w32(s['mlcc_triggers'], 63)
        r.call('mlkc_lock_set', locks, lane, 19, 0, 74, 111)
        r.u.mem_write(repeat + lane * 520 + 8 + 19 * 8, bytes((1, 6, 8, 0, 2, 1, 63, 0)))
        r.w32(s['mlccp_track'], lane)
        r.w32(s['mlccp_index'], 0)
        r.w32(s['mlccp_row'], 4)
        r.call('mlccp_confirm_data')
        assert r.r32(s['mlccp_draft']) <= 127
        lanes = [bytes(r.u.mem_read(pat + 264 * j, 264)) for j in range(6)]
        configs = [cfg(j) for j in range(6)]
        phases = [phase(j) for j in range(6)]
        queues = [queue(j) for j in range(6)]
        repeated = bytes(r.u.mem_read(repeat + 520 * lane, 520))
        cc_locks = bytes(r.u.mem_read(locks, 9216))
        assert clip(10) == 1
        assert cfg(lane) == DEFAULT and phase(lane) == bytes(64) and queue(lane) == bytes(24)
        assert r.r32(s['mclf_pending']) == 0 and r.r32(s['mclf_valid']) == 1
        assert r.r32(s['mlccp_draft']) == 0xffffffff and not r.r32(s['mlccp_edit'])
        assert r.r32(s['mlcc_triggers']) == 63 & ~(1 << lane)
        assert bytes(r.u.mem_read(pat + lane * 264 + 8, 256)) == bytes.fromhex('48640100') * 64
        assert r.call('mlkc_lock_get', locks, lane, 19, 0) == 65535
        for j in range(6):
            if j != lane:
                assert bytes(r.u.mem_read(pat + 264 * j, 264)) == lanes[j]
                assert cfg(j) == configs[j] and phase(j) == phases[j] and queue(j) == queues[j]
        assert clip(10, 35) == 1 and cfg(lane) == DEFAULT  # maintien sans Undo
        assert clip(10, 0) == 1
        press(10)
        assert bytes(r.u.mem_read(pat + 264 * lane, 264)) == lanes[lane]
        assert cfg(lane) == configs[lane] and phase(lane) == phases[lane]
        assert bytes(r.u.mem_read(repeat + 520 * lane, 520)) == repeated
        assert bytes(r.u.mem_read(locks, 9216)) == cc_locks
        assert queue(lane) == bytes(24) and not r.r32(s['mclf_valid'])
    assert bytes(r.u.mem_read(RAW, 722)) == audio
    print('ok : vrais FUNC+PLAY clear/Undo sur six voies ; notes/retrig/chance/locks +32cfg+64phase restaurés, queues purgées, autres voies/audio intacts')

    # Une préparation de frame ratée laisse uniquement la voie effacée gated.
    r.w32(s['mlp_track'], 0)
    failure_hook = stub(s['mlcc_frame_prepare'], lambda args: 0)
    press(10)
    assert r.r32(s['mclf_pending']) == 1
    assert r.call('mclf_emit', ctx + 2864, pat, 0, 0, 74, 101) == 0
    assert queue(0) == bytes(24)
    assert r.call('mclf_emit', ctx + 2864, pat, 1, 0, 74, 101) == 1
    other = bytes(r.u.mem_read(pat + 264, 264))
    r.w32(s['mlp_track'], 1)
    press(10)
    assert bytes(r.u.mem_read(pat + 264, 264)) == other
    r.u.reg_write(mk.UC_M68K_REG_SR, 0x2700)
    count = len(frame_calls)
    r.call('mclf_refresh')
    assert len(frame_calls) == count and r.r32(s['mclf_pending']) == 1
    # Invalider Undo ne doit pas lever le gate avant une publication réussie.
    r.call('mlp_clip_invalidate')
    assert not r.r32(s['mclf_valid']) and r.r32(s['mclf_pending']) == 1
    foreign = 0x9308c000
    r.u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    r.call('ml_init', foreign)
    r.call('mlcc_cfg_init', foreign + 4704)
    r.w32(s['ml_pattern'], foreign)
    r.call('mclf_refresh')
    assert r.r32(s['mlcc_cfg_owner']) == pat and r.r32(s['mclf_pending']) == 1
    assert r.call('mclf_emit', ctx + 2864, pat, 0, 0, 74, 103) == 0
    r.w32(s['ml_pattern'], pat)
    del r.stubs[s['mlcc_frame_prepare']]
    if failure_hook is not None:
        r.u.hook_del(failure_hook)
    r.u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    r.call('mclf_refresh')
    assert not r.r32(s['mclf_pending']) and phase(0) == bytes(64) and queue(0) == bytes(24)
    print('ok : échec frame fail-closed, seule voie visée gated, mutation concurrente refusée ; invalidation/owner raté ne lèvent pas le gate ; reprise UI/IPL0')

    # Paste et son Undo ne restaurent pas les réglages LFO, hors demande.
    r.call('mlp_clip_invalidate')
    r.w32(s['mlp_track'], 2)
    press(9)
    r.w32(s['mlp_track'], 3)
    press(11)
    assert r.call('mlcc_cfg_edit', pat + 4704, 3, 0, 3, 11) == 1
    edited = cfg(3)
    press(11)
    assert cfg(3) == edited
    # Un projet ou changement propriétaire ne peut réutiliser l'ancien Undo.
    r.w32(s['mlp_track'], 4)
    press(10)
    assert r.r32(s['mclf_valid'])
    pat2 = 0x9308c000
    r.call('ml_init', pat2)
    r.call('mlcc_cfg_init', pat2 + 4704)
    r.w32(s['ml_pattern'], pat2)
    r.call('mclf_refresh')
    assert not r.r32(s['mclf_valid']) and not r.r32(s['mclf_pending'])
    r.w32(s['ml_pattern'], pat)
    r.call('mclf_refresh')
    r.call('mlp_clip_invalidate')
    assert not r.r32(s['mlp_clip_undo_lane']) and not r.r32(s['mlp_clip_undo_op'])
    assert not r.r32(s['mclf_valid'])
    print('ok : Paste/Undo ne modifient pas LFO ; invalidation projet/pattern, identité clear et brouillon DATA isolés')
    # Le brouillon d'une autre voie ne fait pas partie de l'effacement.
    r.w32(s['mlp_track'], 0)
    r.w32(s['mlccp_track'], 1)
    r.w32(s['mlccp_index'], 0)
    r.w32(s['mlccp_row'], 4)
    r.call('mlccp_confirm_data')
    draft = r.r32(s['mlccp_draft'])
    press(10)
    assert r.r32(s['mlccp_draft']) == draft and r.r32(s['mlccp_edit']) == 1
    press(10)
    r.call('mlccp_confirm_cancel')
    # Pas de moteur : clear/Undo restent disponibles sans allocation LFO.
    r.call('mlp_clip_invalidate')
    r.w32(s['mlcc_context'], 0)
    before_cfg = cfg(0)
    press(10)
    assert cfg(0) == DEFAULT and not r.r32(s['mclf_pending'])
    press(10)
    assert cfg(0) == before_cfg and not r.r32(s['mclf_pending'])
    r.w32(s['mlcc_context'], ctx)
    r.call('mclf_refresh')
    # Un contexte remplacé ne peut recevoir les phases de l'ancien moteur.
    r.call('mlp_clip_invalidate')
    press(10)
    replacement = 0x93090000
    r.u.mem_write(replacement, bytes(3020))
    r.w32(s['mlcc_context'], replacement)
    press(10)
    assert cfg(0) == before_cfg
    assert bytes(r.u.mem_read(replacement + 2480, 32)) == bytes(32)
    assert bytes(r.u.mem_read(replacement + 2672, 32)) == bytes(32)
    print('ok : brouillon autre voie conservé, contexte nul sans allocation, contexte remplacé refuse phases stale ; phase/queue toujours IPL7')
    boot(stock, t)
    native_audio(stock, t)


def boot(stock, t):
    r = load(stock, t)
    s = r.s
    ap = t['append']
    raw = bytes.fromhex(ap['parts'][0]['hex'])
    dest, source = int(ap['dest'], 16), int(ap['at'], 16)
    r.u.mem_write(dest, bytes(len(raw)))
    r.u.mem_write(source, bytes.fromhex(ap['compressed_hex']))
    r.u.mem_write(0x401a7750, bytes(0x4000))
    r.w32(STACK, STOP)
    r.u.reg_write(mk.UC_M68K_REG_A7, STACK)
    stop = s['ml_boot_copy'] + 42
    assert bytes(r.u.mem_read(stop, 4)).hex() == '4e7b0002'
    r.u.emu_start(s['ml_boot_copy'], stop, count=10000000)
    assert r.u.reg_read(mk.UC_M68K_REG_PC) == stop
    assert bytes(r.u.mem_read(dest, len(raw))) == raw
    assert r.u.reg_read(mk.UC_M68K_REG_A7) == STACK
    r.u.reg_write(mk.UC_M68K_REG_A0, s['ML_TG_START'])
    for reg in (mk.UC_M68K_REG_D4, mk.UC_M68K_REG_D5, mk.UC_M68K_REG_D6, mk.UC_M68K_REG_D7):
        r.u.reg_write(reg, 0)
    turns = []

    def iteration(u, address, size, data):
        turns.append(u.reg_read(mk.UC_M68K_REG_A0))
        if len(turns) == 2:
            u.emu_stop()

    hook = r.u.hook_add(UC_HOOK_CODE, iteration, begin=s['ml_boot_loop'], end=s['ml_boot_loop'])
    r.u.emu_start(s['ml_boot_loop'], STOP, count=100)
    r.u.hook_del(hook)
    assert turns == [s['ML_TG_START'], s['ML_BANK_END'] + 16]
    assert bytes(r.u.mem_read(dest, len(raw))) == raw
    assert bytes(r.u.mem_read(0x401a7750, 0x4000)) == bytes(0x4000)
    print('ok : vrai chargeur/décompresseur copie extension', len(raw), 'octets, clear saute nouvelle fin, tampon filesystem nul intact ; CACR non exécuté')


def native_audio(stock, t):
    from test_tempo_max import Rig, OBJ
    r = Rig(stock)
    u = r.uc
    r.emac.macsr = 0x20
    s = {k: int(v, 16) for k, v in t['symbols'].items()}
    for w in t['writes']:
        u.mem_write(build.BASE + w['off'], bytes.fromhex(w['new']))
    for part in t['append']['parts']:
        u.mem_write(int(part['dest'], 16), bytes.fromhex(part['hex']))
    ctx, pat = 0x93060000, 0x93070000
    u.mem_write(ctx, bytes(3020))
    u.mem_write(pat, bytes(4992))
    for key, val in (('mlcc_context', ctx), ('ml_pattern', pat), ('ml_play_pattern', pat), ('mlp_track', 2)):
        r.w32(s[key], val)
    u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    r.call(s['mlcc_cfg_init'], pat + 4704)
    for lane in range(6):
        u.mem_write(pat + lane * 264, bytes((1, 0, 6 + lane, 4)))
        for lfo in range(2):
            for field, val in enumerate((20000 + lane, 9, 16384, 74 if lfo == 0 else 1, 3, 16384, 0, 28000)):
                assert r.call(s['mlcc_cfg_edit'], pat + 4704, lane, lfo, field, val)[0] == 1
    r.call(s['mclf_refresh'])
    # Frontière A séparée ; la vraie routine native reste celle des deux LFO B.
    u.hook_add(UC_HOOK_CODE, lambda u, a, n, d: r._ret(0), begin=s['MLCC_audio_next'], end=s['MLCC_audio_next'])
    sent = []

    def send(u, address, size, data):
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        count, ptr, port = struct.unpack('>3I', u.mem_read(sp + 4, 12))
        assert not u.reg_read(mk.UC_M68K_REG_SR) & 0x700
        sent.append(bytes(u.mem_read(ptr, count)))
        r._ret(0)

    u.hook_add(UC_HOOK_CODE, send, begin=0x400826b0, end=0x400826b0)
    r.w32(0x40fe4228, 1)

    def tick(n):
        for _ in range(n):
            u.reg_write(mk.UC_M68K_REG_SR, 0x2500)
            r.call(s['mlcc_audio'], OBJ, 14400, 0)
            u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
            r.call(s['mlcc_worker'])

    tick(150)
    assert any(p[0] == 0xb8 for p in sent)
    saved_cfg = bytes(u.mem_read(pat + 4704 + 64, 32))
    saved_phase = bytes(u.mem_read(ctx + 2480 + 64, 32)) + bytes(u.mem_read(ctx + 2672 + 64, 32))

    def op(number):
        u.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        u.reg_write(mk.UC_M68K_REG_D0, number)
        u.reg_write(mk.UC_M68K_REG_D2, 1)
        r.call(s['mclf_op'])

    op(1)
    op(4)
    sent.clear()
    tick(1)  # IRQ réelle avant le refresh UI : le gate doit déjà empêcher CC.
    assert not any(p[0] == 0xb8 for p in sent)
    u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    r.call(s['mclf_refresh'])
    sent.clear()
    tick(150)
    assert sent and not any(p[0] == 0xb8 for p in sent)
    assert {p[0] for p in sent} == {0xb6, 0xb7, 0xb9, 0xba, 0xbb}
    op(2)
    u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    r.call(s['mclf_refresh'])
    assert bytes(u.mem_read(pat + 4704 + 64, 32)) == saved_cfg
    assert bytes(u.mem_read(ctx + 2480 + 64, 32)) + bytes(u.mem_read(ctx + 2672 + 64, 32)) == saved_phase
    sent.clear()
    tick(150)
    assert any(p[0] == 0xb8 for p in sent) and not r.bad
    print('ok : moteur LFO OS+EMAC réel, IRQ intercalée avant refresh, zéro CC tardif voie effacée, cinq autres continuent, Undo reprend les deux LFO')


if __name__ == '__main__':
    main()
