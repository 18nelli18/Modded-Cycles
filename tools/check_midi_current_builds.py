#!/usr/bin/env python3
"""Parite Python/navigateur des selections MIDI exportees localement."""
import argparse,hashlib,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE/'emu')]
import build
from test_sdvintage import main_os_from_syx
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--syntakt',required=True);p.add_argument('--directory',default='build/midi-current');a=p.parse_args()
    stock=main_os_from_syx(a.cycles);root=pathlib.Path(a.directory)
    for row in json.loads((root/'cases.json').read_text()):
        data=json.loads((root/(row['name']+'.json')).read_text());ts=data['tweaks']
        image,_=build.apply_writes(stock,ts);payload,_=build.build_payload(ts,stock,a.syntakt)
        digest=hashlib.sha256(bytes(image)+payload).hexdigest()
        assert digest==row['sha']==data['mainOsSha'],row['name']
        print('PASS parite Python/navigateur '+row['name'],flush=True)
if __name__=='__main__':main()
