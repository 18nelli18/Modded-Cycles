#!/usr/bin/env python3
"""Prototype MIDI secondaire : six voies monophoniques, gates et file bornée.

Exécute l'assembleur ColdFire original en émulation. Aucune intégration à
l'horloge native ni interface ; ports déjà résolus USB/DIN/both (2/3/4).
"""
import argparse
import pathlib
import struct
import subprocess
import tempfile
from unicorn import m68k_const as mk
from unicorn import UC_HOOK_CODE
from test_midi_both import Rig, STACK, STOP
from test_sdvintage import main_os_from_syx

BANK=0x93000000
ENTRY=0x93020000
SIZE=320


def load(rig):
    root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'r.o'),str(root/'tools/machines/midi_lanes/runtime.s')],check=True)
        subprocess.run([cross+'ld','-Ttext='+hex(ENTRY),'-e','ml_step','-o',str(p/'r.elf'),str(p/'r.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary','--only-section=.text',str(p/'r.elf'),str(p/'r.bin')],check=True)
        rig.uc.mem_write(ENTRY,(p/'r.bin').read_bytes())
        return {line.split()[2]:int(line.split()[0],16) for line in subprocess.check_output([cross+'nm',str(p/'r.elf')],text=True).splitlines() if len(line.split())==3}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    r=Rig(main_os_from_syx(a.cycles),0);u=r.uc;symbols=load(r)
    instructions=[0];worst={}
    def tick(u,a,s,d):instructions[0]+=1
    u.hook_add(UC_HOOK_CODE,tick)
    def call(name,*args):
        u.reg_write(mk.UC_M68K_REG_SR,0x2505)
        u.reg_write(mk.UC_M68K_REG_A7,STACK)
        saved={reg:0x93600000+reg*4 for reg in [getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]}
        for reg,value in saved.items():u.reg_write(reg,value)
        u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args))
        instructions[0]=0
        u.emu_start(symbols[name],STOP,count=20000)
        worst[name]=max(worst.get(name,0),instructions[0])
        assert u.reg_read(mk.UC_M68K_REG_PC)==STOP
        assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
        assert u.reg_read(mk.UC_M68K_REG_SR)==0x2505
        assert all(u.reg_read(reg)==value for reg,value in saved.items())
        count,head,tail,held=struct.unpack('>4I',u.mem_read(BANK,16))
        assert count+held<=64 and head<64 and tail<64
        return u.reg_read(mk.UC_M68K_REG_D0)
    def reset():u.mem_write(BANK,bytes(SIZE))
    def packet(channel,note,velocity=100,port=4):return ((0x90|channel)<<24)|(note<<16)|(velocity<<8)|port
    def off(p):return p&0xefff00ff
    def take():return call('ml_take',BANK)
    for channel in range(16):
      for port in (2,3,4):
        reset();p=packet(channel,60,port=port)
        assert call('ml_step',BANK,0,p,3)==1
        assert take()==p and take()==0
        assert call('ml_step',BANK,0,0,0)==1 and take()==0
        assert call('ml_step',BANK,0,0,0)==1 and take()==0
        assert call('ml_step',BANK,0,0,0)==1 and take()==off(p)
        assert take()==0
    print('ok : 16 canaux × USB/DIN/both, gate trois pas, note-off exact et registres/SR')
    reset();expected=[]
    for lane in range(6):
        p=packet(lane+6,60+lane)
        assert call('ml_step',BANK,lane,p,64)==1;expected.append(p)
    for lane in range(6):call('ml_stop',BANK,lane)
    expected += [off(p) for p in expected]
    assert [take() for _ in expected]==expected and take()==0
    print('ok : six voies indépendantes, canaux 7–12 et Stop de toutes les notes')
    reset();p=packet(0,60)
    assert call('ml_step',BANK,0,p,64)==1
    before=bytes(u.mem_read(BANK,SIZE))
    assert call('ml_step',BANK,1,p,64)==0 and bytes(u.mem_read(BANK,SIZE))==before
    for bad in (packet(0,128),packet(0,60,0),packet(0,60,port=1),packet(0,60,port=5),0x803c6404):
        before=bytes(u.mem_read(BANK,SIZE));assert call('ml_step',BANK,1,bad,2)==0
        assert bytes(u.mem_read(BANK,SIZE))==before
    print('ok : collision canal/note refusée, messages invalides refusés sans modifier les voies')
    reset();accepted=[]
    for tick in range(100):
        lane=tick%6;p=packet(lane+6,40+(tick%60),port=2+lane%3)
        result=call('ml_step',BANK,lane,p,64)
        if result:accepted.append(p)
    for lane in range(6):call('ml_stop',BANK,lane)
    result=[]
    while True:
        p=take()
        if not p:break
        result.append(p)
    active=set();ons=[]
    for p in result:
        key=p&0x0fff00ff
        if p>>28==9:assert key not in active;active.add(key);ons.append(p)
        else:assert key in active;active.remove(key)
    assert not active and ons==accepted and len(result)==2*len(accepted)
    # Dépasser plusieurs fois la fin du ring sans perdre d'événement.
    for tick in range(150):
        p=packet(tick%16,tick%128)
        assert call('ml_step',BANK,0,p,1)==1 and take()==p
        call('ml_stop',BANK,0);assert take()==off(p) and take()==0
    print('ok : saturation sans note-off perdu, refus de nouveaux note-on, 150 tours de lecture/écriture')
    print('Instructions max par API',worst,'; pas une mesure du temps matériel')
    print('NOTE : horloge, page d’édition, stockage et envoi matériel non intégrés')


if __name__=='__main__':main()
