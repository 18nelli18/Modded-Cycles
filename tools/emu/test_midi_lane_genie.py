#!/usr/bin/env python3
"""Adaptateur Genie B : notes vers candidat privé, validation avant écriture."""
import argparse
import pathlib
import subprocess
import tempfile
from unicorn import UC_HOOK_CODE, m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True)
    args=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    r=Rig(main_os_from_syx(args.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'io.o'),str(root/'tools/machines/midi_lanes/genie.s')],check=True)
        subprocess.run([cross+'ld','-Ttext=0x93050000','-e','ml_genie_notes','-o',str(p/'io.elf'),str(p/'io.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'io.elf'),str(p/'io.bin')],check=True)
        r.u.mem_write(0x93050000,(p/'io.bin').read_bytes())
    source,notes,candidate=0x93070000,0x93071000,0x93072000
    for length in (1,16,17,32,48,64):
        original=bytearray([1,0,6,4,length,2,0,0])+bytearray([60,0,0,2]*64)
        values=bytes([60,255,254,72][i%4] for i in range(length))
        r.u.mem_write(source,bytes(original));r.u.mem_write(notes,values)
        r.u.mem_write(candidate,bytes([0xa5])*264)
        assert r.call(0x93050000,source,notes,length,candidate)==1
        got=bytes(r.u.mem_read(candidate,264))
        assert got[:8]==original[:8] and got[8+4*length:]==original[8+4*length:]
        for step,note in enumerate(values):
            at=8+4*step
            if note==254:assert got[at:at+4]==original[at:at+4]
            elif note==255:assert got[at+3]==0
            else:assert got[at:at+4]==bytes([note,100,1,3])
        assert bytes(r.u.mem_read(source,264))==bytes(original)
        # Échec tardif : candidat entier intact, aucune modification audio.
        for bad in (0,35,97,128,253):
            r.u.mem_write(notes,values[:-1]+bytes([bad]))
            r.u.mem_write(candidate,bytes([0xa5])*264)
            assert r.call(0x93050000,source,notes,length,candidate)==0
            assert bytes(r.u.mem_read(candidate,264))==bytes([0xa5])*264
    r.u.mem_write(notes,bytes([60])*64)
    for dest in (source,source+4,source-4,notes,notes+4,notes-4):
        assert r.call(0x93050000,source,notes,64,dest)==0
    for ipl in range(1,8):
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|ipl<<8)
        assert r.call(0x93050000,source,notes,64,candidate)==0
    print('ok : conversion notes Genie vers voie MIDI privée, 1..64 pas, notes/repos/conserver, vélocité/gate audibles, flags note/slide')
    print('ok : validation avant écriture, tampons superposés et IRQ refusés, source intacte')
    print('Limites : adaptateur seul ; menu, publication, queue, undo et paramètres avancés à raccorder')


if __name__=='__main__':main()
