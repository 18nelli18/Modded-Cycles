#!/usr/bin/env python3
"""Note 57 : passage du slot de projet au chargeur natif, sans disque.

Exécute ProjectCache::load ; cache, convertisseur et callback sont observés.
Le slot persiste dans l'appel même si l'identité du contenu est renouvelée.
"""
import argparse,pathlib,subprocess,tempfile,struct
from gen_seq_gen import symbols
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    ap.add_argument('--extended',action='store_true')
    args = ap.parse_args()
    r = Rig(main_os_from_syx(args.cycles), {'writes': []},
            {'writes': [], 'symbols': {}})
    root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_STORAGE2=1'] if args.extended else []),'-o',str(p/'h.o'),str(root/'tools/machines/midi_lanes/storage_load_hook.s')],check=True)
        (p/'link.ld').write_text('SECTIONS { .text 0x93050000 : { *(.text*) *(.data*) } } ml_store_ui_cancel = 0x93064000; ml_runtime = 0x93064004; ml_clock_state = 0x93064008; ml_bank_empty = 0x9306400c; ml_bank_activate = 0x93064010; ml_play_pattern = 0x93064014; ml_pattern = 0x93064018;')
        subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','ml_store_load_hook','-o',str(p/'h.elf'),str(p/'h.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'h.elf'),str(p/'h.bin')],check=True)
        r.u.mem_write(0x93050000,(p/'h.bin').read_bytes());r.s=symbols(cross,p/'h.elf')
    cancelled=[]
    if args.extended:
        def cancel(a):
            assert r.u.reg_read(__import__('unicorn').m68k_const.UC_M68K_REG_SR)&0x700==0
            cancelled.append(True);return 0
        r.stubs[0x93064000]=cancel;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x93064000,end=0x93064000)
    assert bytes(r.u.mem_read(0x4006a660,8)).hex()=='4cd7040c4fef0020'
    r.u.mem_write(0x4006a660,b'\x4e\xf9'+struct.pack('>I',r.s['ml_store_load_hook'])+b'\x4e\x71')
    cache, dest, callback, serialized = 0x93010000, 0x93011000, 0x93012000, 0x41400000
    calls = [];load_status=[1];identity=[0x12345678]
    def retrieve(a):
        calls.append(('cache', a[0], a[1]))
        return serialized
    def convert(a):
        calls.append(('load', a[0], a[1]))
        r.w32(a[0]+8,identity[0]);return load_status[0]
    for addr, fn in ((0x4006a3ac, retrieve), (0x4005d3dc, convert),
                     (0x400d0aae, lambda a: 0), (0x400cf044, lambda a: 0)):
        r.stubs[addr] = fn
        r.u.hook_add(UC_HOOK_CODE, r.stub, begin=addr, end=addr)
    for slot in (0, 1, 95, 96):
        before=r.r32(r.s['ml_store_load_serial'])
        calls.clear()
        assert r.call(0x4006a5a0, cache, slot, dest, callback) == 1
        assert calls == [('cache', cache, slot), ('load', dest, serialized)], calls
        assert r.r32(r.s['ml_store_load_serial'])==before+1
        if slot<=96:
            assert r.r32(r.s['ml_store_load_pending_id'])==identity[0]
            assert r.r32(r.s['ml_store_load_pending_slot'])==slot
    # Un Load réussi sous IPL masqué doit notifier sans callback UI.
    from unicorn import m68k_const as mk
    before=r.r32(r.s['ml_store_load_serial']);prior=len(cancelled)
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
    assert r.call(0x4006a5a0,cache,3,dest,callback)==1
    assert r.r32(r.s['ml_store_load_serial'])==before+1
    assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0x500
    assert len(cancelled)==prior
    if args.extended:
        assert r.r32(r.s['ml_store_load_ready'])==0
        assert r.r32(r.s['ml_store_suspend_pending'])==1
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    for slot in (97, 0xfffffffe):
        calls.clear()
        assert r.call(0x4006a5a0, cache, slot, dest, callback) == 0
        assert not calls
    before=r.r32(r.s['ml_store_load_serial'])
    load_status[0]=0
    assert r.call(0x4006a5a0,cache,3,dest,callback)==0
    assert r.r32(r.s['ml_store_load_serial'])==before
    load_status[0]=1;identity[0]=0
    assert r.call(0x4006a5a0,cache,3,dest,callback)==1
    assert r.r32(r.s['ml_store_load_serial'])==before
    # La sauvegarde doit être liée au succès natif, pas au bouton seul.
    entry = 0x93014000
    storage = 0x93015000
    status = [0]
    def save(a):
        calls.append(('save', a[0], a[1], a[2], a[3]))
        return status[0]
    for addr, fn in ((0x40069f3c, lambda a: entry),
                     (0x400d0a10, lambda a: storage), (0x4008d712, save)):
        r.stubs[addr] = fn
        r.u.hook_add(UC_HOOK_CODE, r.stub, begin=addr, end=addr)
    for slot in (0, 95, 96):
        for result in (0, 2):
            calls.clear()
            r.w32(entry, slot)
            r.u.mem_write(entry+4, bytes([1, 1, 1]))
            status[0] = result
            value = r.call(0x4006a4d6, cache, slot, callback)
            assert bool(value & 255) == (result == 0), (slot, result, hex(value), calls)
            assert calls == [('save', storage, entry+12, slot, 0)], calls
            assert r.u.mem_read(entry+(6 if result == 0 else 4), 1) == b'\0'
    print('ok : Load natif -> hook compilé, identité/slot après succès, échec/zéro sans notification, slot96 différé au service UI')
    print('ok : chargeur natif transmet slot/cache/destination, bornes 0..96 et refus hors domaine')
    print('Limite : association du slot96 validée séparément ; cache/disque simulés, aucun hook de sauvegarde ajouté')


if __name__ == '__main__':
    main()
