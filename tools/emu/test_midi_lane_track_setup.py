#!/usr/bin/env python3
"""Track Setup B compilé : raccourci, limites, indépendance A, note nommée."""
import argparse
from test_midi_lane_page import make,key,knob,PAT
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import RAW

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=make(main_os_from_syx(a.cycles));assert r.call('mlp_open')==1
 obj=r.r32(r.s['mlp_obj']);r.w32(r.s['mlp_track'],2)
 before=bytes(r.u.mem_read(RAW,722));original=bytes(r.u.mem_read(PAT,1584))
 assert key(r,1)==1 and key(r,2)==1
 assert r.r32(r.s['mlp_setup'])==3
 key(r,2,0);key(r,1,0)
 r.call('ml_toggle');assert r.r32(r.s['mlp_obj'])==obj and r.r32(r.s['mlp_setup'])==3
 r.texts.clear();r.call('mlp_render',obj,0x93006000)
 assert [t[2] for t in r.texts]==['TRACK','KbT','0','Pad','C5','>'],r.texts
 assert key(r,32,16)==1
 for i in range(70):knob(r,1)
 assert r.u.mem_read(PAT+264*2+6,1)==b'\x3c'
 for i in range(130):knob(r,-1)
 assert r.u.mem_read(PAT+264*2+6,1)==b'\xc4'
 key(r,32,16);knob(r,1);key(r,32,16)
 knob(r,1);assert r.u.mem_read(PAT+264*2+7,1)==bytes([73^72])
 r.texts.clear();r.call('mlp_render',obj,0x93006000)
 assert r.texts[-2][2]=='C#5',r.texts
 for i in range(140):knob(r,-1)
 assert r.u.mem_read(PAT+264*2+7,1)==bytes([72])
 for i in range(140):knob(r,1)
 assert r.u.mem_read(PAT+264*2+7,1)==bytes([127^72])
 assert bytes(r.u.mem_read(RAW,722))==before
 current=bytearray(r.u.mem_read(PAT,1584));current[264*2+6:264*2+8]=original[264*2+6:264*2+8]
 assert bytes(current)==original
 assert key(r,12)==1 and r.r32(r.s['mlp_setup'])==0 and r.r32(r.s['mlp_obj'])==obj
 # Pad Note est employée par la sortie MIDI privée sur le canal de la voie.
 live=r.s['ml_live_runtime'];r.u.mem_write(live,bytes(320))
 r.u.mem_write(PAT+264*2+2,bytes([12]));r.u.mem_write(PAT+264*2+7,bytes([73^72]))
 r.call('mlp_pad_note',2,1);assert r.call('ml_take',live)==0x9c496404
 r.call('mlp_pad_note',2,0);assert r.call('ml_take',live)==0x8c490004
 assert r.call('ml_take',live)==0
 # Retirer un menu conserve objet B, voie sélectionnée et table d'édition.
 assert r.r32(r.s['mlp_track'])==2 and r.r32(r.s['ml_pattern'])==PAT
 print('ok : FUNC+TRACK ouvre Track Setup B, DATA KbT-60..60/PadC-1..G9, BACK conserve B, pistes A intactes')
if __name__=='__main__':main()
