#!/usr/bin/env python3
"""Prototype CC slide : arithmétique ColdFire réelle, sans raccordement MIDI."""
import argparse,pathlib,subprocess,tempfile,random
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'slide.o'),str(root/'tools/machines/midi_lanes/knob_cc_slide_value.s')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'slide.o'),str(p/'slide.bin')],check=True)
        code=(p/'slide.bin').read_bytes()
    r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    at=0x93050000;r.u.mem_write(at,code)
    for start,target in ((0,127),(127,0),(64,64),(1,126),(126,1)):
        for duration in (1,7,127,32768,65535,200000):
            times=sorted({0,duration//4,duration//2,3*duration//4,duration,duration+1})
            values=[r.call(at,start,target,t,duration) for t in times]
            assert values[0]==start and values[-1]==target
            assert all(min(start,target)<=v<=max(start,target) for v in values)
            assert values==sorted(values,reverse=target<start)
    rand=random.Random(824)
    for _ in range(200):
        start,target=rand.randrange(128),rand.randrange(128)
        duration=rand.randrange(1,200001);elapsed=rand.randrange(200002)
        distance=abs(target-start)*min(elapsed,duration)//duration
        expected=start+distance if target>=start else start-distance
        assert r.call(at,start,target,elapsed,duration)==expected
    for args in ((128,0,0,1),(0,128,0,1),(0,1,0,0),(0,1,0,200001),(0,1,0,0xffffffff)):
        assert r.call(at,*args)==0xffffffff
    print('ok : interpolation ColdFire montante/descendante, bornes, saturation, durées1..200000,200cas et domaines invalides')
    print('Prototype uniquement : ordonnanceur/queue CC et raccordement aux slides encore à réaliser.')

if __name__=='__main__':main()
