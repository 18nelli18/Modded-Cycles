#!/usr/bin/env python3
"""Note 57 : callback LED privé, mapping/writer natifs, sortie physique simulée."""
import argparse,struct
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,PAT,key,knob
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);args=ap.parse_args()
    r=make(main_os_from_syx(args.cycles));assert r.call('mlp_open')==1
    obj=r.r32(r.s['mlp_obj']);led,claims,mapping=0x93090000,0x93090400,0x93090500
    r.w32(0x40fe4200,led);r.w32(0x404a8bdc,mapping)
    r.u.mem_write(mapping,struct.pack('>16I',*range(1,17)))
    pads=list(struct.unpack('>6I',r.u.mem_read(0x400fbc78,24)))
    r.w32(0x404a8ba0,mapping+64)
    r.u.mem_write(mapping+64,struct.pack('>6I',*pads))
    claimmask=0x1fffe|sum(1<<p for p in pads)
    rec=0x930a0000;r.u.mem_write(rec+357,b'\x01\x01')
    r.stubs[0x400cf9a8]=lambda a:rec
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400cf9a8,end=0x400cf9a8)
    for addr,fn in ((0x4008e942,lambda a:a[0]),(0x4008e964,lambda a:0),(0x4008e998,lambda a:0)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    handler=r.call(0x400f4cec,obj,0x401121c0,0x400ff970,0xfffffffe)
    assert handler==obj+0x500
    # Reproduire l'ancien défaut : RTTI DrumSelect = aucune base LedHandler.
    type_pointer=r.r32(r.r32(obj)-4)
    r.w32(r.r32(obj)-4,0x401178f8)
    assert r.call(0x400f4cec,obj,0x401121c0,0x400ff970,0xfffffffe)==0
    r.w32(r.r32(obj)-4,type_pointer)
    callback=r.r32(r.r32(handler)+8);assert callback==r.s['mlp_led']
    assert r.r32(obj+8)!=r.r32(handler) # MidiHandler natif conservé.
    for lane in range(6):
      r.w32(r.s['mlp_track'],lane)
      for bank in range(4):
        r.w32(r.s['mlp_step'],16*bank)
        for i in range(16):assert r.call('ml_edit',PAT,lane,16*bank+i,3,(i+lane+bank)%2)==1
        r.u.mem_write(led,bytes(256));r.u.mem_write(claims,bytes(8))
        before=bytes(r.u.mem_read(PAT,1584));assert r.call(callback,handler,0,claims)==1
        assert (r.r32(claims)<<32)|r.r32(claims+4)==claimmask
        actual=[r.r32(led+40+4*i) for i in range(54)]
        expected=[0]+[1+2*((i+lane+bank)%2) for i in range(16)]+[0]*37
        for i,pad in enumerate(pads):expected[pad]=3 if i==lane else 1
        assert actual==expected,actual
        assert bytes(r.u.mem_read(PAT,1584))==before
        r.w32(led+44,3);r.call(callback,handler,0,claims)
        assert r.r32(led+44)==3
    print('ok : six voies × quatre banques, mapping et writer natifs, masque de revendication ; pads sélectionnés, aucune autre LED modifiée, first-wins respecté')
    # Vrai gestionnaire de vues : RTTI, ordre des vues, revendication big-endian.
    manager,top,bottom,lower,lower_vt,fake=0x93091000,0x93091100,0x93091200,0x93092000,0x93093000,0x93094000
    r.u.mem_write(lower,bytes(r.u.mem_read(obj,0x510)))
    r.u.mem_write(lower_vt,bytes(r.u.mem_read(r.r32(handler)-8,20)))
    r.w32(lower+0x500,lower_vt+8);r.w32(lower_vt+16,fake)
    lower_calls=[]
    def audio_view(args):
        lower_calls.append(args[0])
        for i in range(16):
            address=led+40+4*(i+1)
            if not r.r32(address):r.w32(address,3 if i%2==0 else 1)
        r.w32(args[2],0);r.w32(args[2]+4,0x1fffe)
        return 1
    for addr,fn in ((fake,audio_view),(0x400e8684,lambda a:0),(0x400d08ce,lambda a:0)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    head=manager+20
    r.w32(head,bottom);r.w32(head+4,top)
    r.w32(top,head);r.w32(top+4,bottom);r.w32(top+8,obj)
    r.w32(bottom,top);r.w32(bottom+4,head);r.w32(bottom+8,lower)
    r.w32(r.s['mlp_track'],0);r.w32(r.s['mlp_step'],0)
    for i in range(16):r.call('ml_edit',PAT,0,i,3,i%2)
    r.u.mem_write(led,bytes(256));r.call(0x40076ca2,manager)
    assert lower_calls==[lower+0x500]
    assert [r.r32(led+44+4*i) for i in range(16)]==[1+2*(i%2) for i in range(16)]
    assert (r.r32(handler+4)<<32)|r.r32(handler+8)==claimmask
    # Le pas nouvellement posé et sa suppression apparaissent au cycle suivant.
    key(r,16);key(r,16,0)
    r.u.mem_write(led,bytes(256));r.call(0x40076ca2,manager);assert r.r32(led+44)==3
    key(r,16);key(r,16,0)
    r.u.mem_write(led,bytes(256));r.call(0x40076ca2,manager);assert r.r32(led+44)==1
    # Retirer la vue MIDI rétablit la vue audio sous-jacente dès le prochain cycle.
    r.w32(head+4,bottom);r.w32(bottom,head)
    r.u.mem_write(led,bytes(256));r.call(0x40076ca2,manager)
    assert [r.r32(led+44+4*i) for i in range(16)]==[3 if i%2==0 else 1 for i in range(16)]
    print('ok : vrai dispatch 0x40076ca2/RTTI, vue MIDI prioritaire, pose/retrait visibles, retour aux LEDs audio après retrait de vue ; backend audio simulé')
    # Curseur indépendant : pas précédent de la voie, longueur et page propres.
    clock=0x93095000;r.w32(r.s['ml_clock_state'],clock);r.w32(clock,1)
    cursor=[]
    r.stubs[0x4008e8c4]=lambda a:cursor.append((a[0],a[1])) or 0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4008e8c4,end=0x4008e8c4)
    r.w32(clock+8,5)
    r.u.mem_write(led,bytes(256));r.call(callback,handler,0,claims)
    assert cursor==[(5,6)]
    r.w32(obj+44,manager)
    r.u.mem_write(manager+33,b'\0')
    r.call('mlp_led_poll');assert r.u.mem_read(manager+33,1)==b'\x01'
    r.u.mem_write(manager+33,b'\0')
    for _ in range(100):r.call('mlp_led_poll')
    assert r.u.mem_read(manager+33,1)==b'\0'
    r.w32(clock+8,6);r.call('mlp_led_poll')
    assert r.u.mem_read(manager+33,1)==b'\x01'
    r.w32(r.s['mlp_step'],16);cursor.clear();r.call(callback,handler,0,claims);assert not cursor
    r.w32(r.s['mlp_step'],0);r.w32(clock,0);r.call(callback,handler,0,claims);assert not cursor
    # Chaque voie émet son pulse une seule fois après une note acceptée.
    for lane in range(6):
        cursor.clear()
        r.w32(r.s['ml_pad_serial']+4*lane,1)
        r.call('mlp_led_poll')
        r.u.mem_write(led,bytes(256));r.call(callback,handler,0,claims)
        assert cursor==[(pads[lane],6)],cursor
        cursor.clear();r.call(callback,handler,0,claims);assert not cursor
    print('ok : curseur de lecture MIDI natif mode 6, hors page/arrêt sans curseur ; 100 polls identiques sans redessin, un changement réveille les LEDs ; sortie physique simulée')

if __name__=='__main__':main()
