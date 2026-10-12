#!/usr/bin/env python3
"""Chemins annexes ColdFire : identité projet, 96 patterns, copies A/B et LFO.

Aucun accès disque. Refus identité nulle/indices invalides sans toucher out.
"""
import argparse,pathlib,subprocess,tempfile
from gen_seq_gen import symbols
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    a=ap.parse_args();root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'path.o'),str(root/'tools/machines/midi_lanes/storage_path.s')],check=True)
        subprocess.run([cross+'ld','-Ttext=0x93050000','-e','ml_store_path','-o',str(p/'path.elf'),str(p/'path.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'path.elf'),str(p/'path.bin')],check=True)
        r.u.mem_write(0x93050000,(p/'path.bin').read_bytes());r.s=symbols(cross,p/'path.elf')
    out=0x93070000;seen=set()
    for slot in (0,1,95):
      for identity in (1,0x12345678,0xffffffff):
        for pattern in range(96):
            for copy in (0,1):
                for kind in (0,1,2):
                    r.u.mem_write(out,bytes([165])*40)
                    assert r.call('ml_store_path',out,35,identity,pattern,copy,kind,slot)==1
                    expected='/ModdedCycles/%02d-%08X/%s-%02d-%s'%(slot,identity,('SEQ','LFO','WRK')[kind],pattern,('A','B')[copy])
                    assert r.string(out)==expected and len(expected)==34
                    assert bytes(r.u.mem_read(out+35,5))==bytes([165])*5
                    assert expected not in seen;seen.add(expected)
    for cap,identity,pattern,copy,kind in ((34,1,0,0,0),(35,0,0,0,0),(35,1,96,0,0),(35,1,0,2,0),(35,1,0,0,3),(35,1,0xffffffff,0,0)):
        r.u.mem_write(out,bytes([165])*40)
        assert r.call('ml_store_path',out,cap,identity,pattern,copy,kind,0)==0
        assert bytes(r.u.mem_read(out,40))==bytes([165])*40
    for slot in (96,0xffffffff):
        r.u.mem_write(out,bytes([165])*40)
        assert r.call('ml_store_path',out,35,1,0,0,0,slot)==0
        assert bytes(r.u.mem_read(out,40))==bytes([165])*40
    assert r.call('ml_store_path',0,35,1,0,0,0,0)==0
    print('ok : 5184 chemins uniques, projets/patterns/types/copies isolés ; bornes et sortie intacte sur erreur')
    print('Limite : stabilité Save As/renouvellement identité et création des dossiers restent à prouver')
if __name__=='__main__':main()
