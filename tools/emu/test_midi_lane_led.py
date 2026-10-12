#!/usr/bin/env python3
"""Note 57 : callback LED privé, mapping/writer natifs, sortie physique simulée."""
import argparse,struct
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,PAT
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);args=ap.parse_args()
    r=make(main_os_from_syx(args.cycles));assert r.call('mlp_open')==1
    obj=r.r32(r.s['mlp_obj']);led,claims,mapping=0x93090000,0x93090400,0x93090500
    r.w32(0x40fe4200,led);r.w32(0x404a8bdc,mapping)
    r.u.mem_write(mapping,struct.pack('>16I',*range(1,17)))
    for addr,fn in ((0x4008e942,lambda a:a[0]),(0x4008e964,lambda a:0),(0x4008e998,lambda a:0)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    callback=r.r32(r.r32(obj+8)+8);assert callback==r.s['mlp_led']
    for lane in range(6):
      r.w32(r.s['mlp_track'],lane)
      for bank in range(4):
        r.w32(r.s['mlp_step'],16*bank)
        for i in range(16):assert r.call('ml_edit',PAT,lane,16*bank+i,3,(i+lane+bank)%2)==1
        r.u.mem_write(led,bytes(256));r.u.mem_write(claims,bytes(8))
        before=bytes(r.u.mem_read(PAT,1584));assert r.call(callback,obj+8,0,claims)==1
        assert r.r32(claims)==0x1fffe and r.r32(claims+4)==0
        actual=[r.r32(led+40+4*i) for i in range(54)]
        assert actual==[0]+[1+(i+lane+bank)%2 for i in range(16)]+[0]*37,actual
        assert bytes(r.u.mem_read(PAT,1584))==before
        r.w32(led+44,3);r.call(callback,obj+8,0,claims)
        assert r.r32(led+44)==3
    print('ok : six voies × quatre banques, mapping et writer natifs, masque de revendication ; aucune autre LED modifiée, first-wins respecté')
    print('NOTE : invocation du slot LedHandler vérifiée ; gestionnaire de vues complet et périphérique LED restent à tester')

if __name__=='__main__':main()
