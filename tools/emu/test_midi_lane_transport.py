#!/usr/bin/env python3
"""Note 57 : prototypes Start/audio aux vrais sites OS, sans flasher.

Exécute le move d'échéance et l'appel stock 0x40053330 (branche inactive).
L'état transport, l'heure et d6 sont fournis par fixture : le chemin Play
complet, les périphériques et le délai audible ne sont pas prouvés ici.
"""
import argparse
import struct
from unicorn import UC_HOOK_CODE, m68k_const as mk
from test_midi_lane_page import make
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);args=ap.parse_args()
    r=make(main_os_from_syx(args.cycles));u=r.u
    u.mem_map(0x80000000,0x20000)
    regs=[getattr(mk,'UC_M68K_REG_'+kind+str(i)) for kind in ('D','A') for i in range(8)]
    regs.append(mk.UC_M68K_REG_SR)
    start=0x40054686;audio=0x400594a8
    original=bytes(u.mem_read(start,6));original_audio=bytes(u.mem_read(audio,6))
    assert original.hex()=='23d080001848'
    assert original_audio.hex()=='4eb940053330'
    patched=b'\x4e\xf9'+struct.pack('>I',r.s['ml_start_hook'])
    patched_audio=b'\x4e\xb9'+struct.pack('>I',r.s['ml_audio_hook'])
    def patch(address,data):
        u.mem_write(address,data)
        u.ctl_remove_cache(address,address+len(data))
    # Unicorn diffère CCR dans SR : observer Z/N/V/C par branches, sans
    # instruction qui modifie les flags (movea/lea seulement).
    capture=bytes.fromhex('4feffffc 48d74000 2c7c00000000 6604 4dee0001 6a04 4dee0002 6804 4dee0004 6404 4dee0008 23ce9300e104 4cd74000 4fef0004')
    u.mem_write(0x9300e000,capture)
    end=0x9300e000+len(capture)
    # Observer les branches dans le même emu_start, avant toute sortie JIT.
    for continuation in (start+6,audio+6):
        u.mem_write(continuation,b'\x4e\xf9'+struct.pack('>I',0x9300e000))
    def snapshot():
        values=[u.reg_read(reg) for reg in regs]
        values[-1]=(values[-1]&0xfff0)|r.r32(0x9300e104)
        return values
    def arm(due,resume=0):
        r.w32(0x40a78628,due&0xffffffff)
        u.reg_write(mk.UC_M68K_REG_A0,0x40a78628)
        u.reg_write(mk.UC_M68K_REG_D6,resume)
        u.reg_write(mk.UC_M68K_REG_SR,0x2705)
        u.emu_start(start,end,count=1000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==end
        assert r.r32(0x80001848)==due&0xffffffff
    # Contrat exact du move : registres, pile et CCR identiques au stock.
    for due in (0,12345,0x80000000,0xfffffff0):
      results=[]
      for code in (original,patched):
        patch(start,code)
        for i,reg in enumerate(regs):u.reg_write(reg,0x2705 if reg==mk.UC_M68K_REG_SR else 0x93008000 if reg==mk.UC_M68K_REG_A7 else 0x12340000+i)
        arm(due)
        results.append(snapshot())
      assert results[0]==results[1],(due,results)
    print('ok : detour Start, move natif rejoué ; registres/pile/SR identiques au stock, quatre valeurs dont rebouclage')
    # Contrat de l'appel audio : vraie fonction stock, branche inactive.
    r.w32(0x40a74544,0);r.w32(r.s['ml_context'],0)
    results=[]
    for code in (original_audio,patched_audio):
        patch(audio,code)
        for i,reg in enumerate(regs):u.reg_write(reg,0x2500 if reg==mk.UC_M68K_REG_SR else 0x93008000 if reg==mk.UC_M68K_REG_A7 else 0x12340000+i)
        u.emu_start(audio,end,count=3000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==end
        results.append(snapshot())
    assert results[0]==results[1],results
    print('ok : vrai appel audio stock conservé, contexte absent, registres/pile/SR identiques')
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    assert r.call('ml_prepare')==1
    ctx=r.r32(r.s['ml_context']);bank=ctx+1584;state=ctx+1904
    def forbidden(u,address,size,data):
        raise AssertionError('allocation ou sortie physique depuis audio : '+hex(address))
    for address in (0x400826b0,0x400802e0):
        u.hook_add(UC_HOOK_CODE,forbidden,begin=address,end=address)
    for lane in range(6):
      for step in range(16):
        assert r.call('ml_edit',ctx,lane,step,0,60+step)==1
        assert r.call('ml_edit',ctx,lane,step,3,1)==1
    def drain():
        result=[]
        while (packet:=r.call('ml_take',bank)):result.append(packet)
        return result
    def tick(now,mode=1):
        r.w32(0x8000184c,now&0xffffffff);r.w32(0x40a7883c,mode)
        u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        u.emu_start(audio,end,count=10000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==end
        assert snapshot()[-1]==0x2501  # capture : Z=1, N/V/C=0
    for due in (100000,0xfffffff0):
        serial=r.r32(r.s['ml_start_serial'])
        arm(due)
        assert r.r32(r.s['ml_start_serial'])==(serial+1)&0xffffffff
        tick(due-1);assert not drain()
        tick(due+100);ons=drain()
        assert [p>>24 for p in ons]==list(range(0x96,0x9c)),(due,ons,r.r32(state),[(key,r.r32(r.s[key])) for key in ('ml_start_due','ml_start_context','ml_start_serial','ml_start_seen')])
        assert all((p>>16)&127==60 for p in ons)
        assert r.r32(state+4)==(due+5400000)&0xffffffff
        tick(due+5400000-1);assert not drain()
        tick(due+5400000)
        assert all((p>>16)&127==61 for p in drain() if p>>28==9)
        tick(due+5400001,2)
        assert len(drain())==6 and r.r32(state)==2
        # Continue arme une nouvelle échéance sans repartir au pas 1.
        remaining=5400000-1;continued=(due+100000000)&0xffffffff
        arm(continued,1)
        tick(continued-1);assert not drain()
        tick(continued);assert not drain() and r.r32(state)==1
        tick(continued+remaining)
        assert [((p>>16)&127) for p in drain() if p>>28==9]==[62]*6
        # Restart entre deux blocs : pas besoin d'observer le Stop intermédiaire.
        restarted=(continued+remaining+100)&0xffffffff
        arm(restarted)
        tick(restarted)
        packets=drain()
        assert len(packets)==12 and [((p>>16)&127) for p in packets if p>>28==9]==[60]*6
        tick(restarted+1,0);assert len(drain())==6
        tick(restarted+2,0);assert not drain()
    print('ok : attente échéance, six voies canaux 7..12, phase ancrée malgré retard de bloc, Pause/Continue, Restart et Stop, rebouclage 32 bits')
    # Première allocation tardive : garde fermée plutôt qu'un départ libre.
    r.w32(r.s['ml_context'],0);arm(100)
    r.w32(r.s['ml_context'],ctx);tick(1000)
    assert not drain() and not r.r32(state)
    print('ok : contexte apparu après Start attend le prochain Play ; aucune sortie MIDI depuis le hook audio')
    print('NOTE : fixtures transport/heure ; Play complet, ouverture tardive synchronisée, IRQ imbriquées, charge et placement restent à prouver')


if __name__=='__main__':main()
