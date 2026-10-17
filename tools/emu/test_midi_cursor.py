"""Note115 : phase native rejointe, longueurs propres et un seul curseur B/REC."""
import argparse,pathlib,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,OBJ

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();img,memories,ts=boot_case(a.case);bank=next(t for t in ts if t['id']=='midi-out-bank');sy={**bank['symbols'],**next(t['symbols'] for t in ts if 'phase_join'in t.get('symbols',{}))};r=Rig(img,{'writes':[]},{'writes':[],'symbols':sy});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in memories:u.mem_write(at,raw)
 assert r.call('ml_prepare')==1;ctx=r.r32(r.s['ml_context']);clock=r.r32(r.s['ml_clock_state']);active=0x930b0000;r.w32(0x40a7887c,active);r.w32(active+30706,0);assert r.call('ml_bank_ui_sync')==1;pattern=r.r32(r.s['ml_pattern']);r.w32(r.s['mlp_obj'],OBJ)
 durations=[21600000,10800000,5400000,3600000,2700000,1800000,1350000];native=[3,4,6,8,12,24,48];lengths=[5,7,12,16,31,64];alloc=r.new_count
 for bspeed in range(7):
  for speed in range(7):
   for within in (0,1,449999,899999):
    now=100000000+within;r.w32(0x8000184c,now);r.w32(0x40a78628,100900000);r.w32(0x40a7883c,1);r.w32(r.s['ml_start_context'],0);r.w32(clock,0)
    for lane,length in enumerate(lengths):
     u.mem_write(pattern+264*lane+4,bytes([length,bspeed]));u.mem_write(0x40a7886c+lane,bytes([length-1]));u.mem_write(0x40a788b5+lane,bytes([speed]));u.mem_write(0x40a78866+lane,bytes([lane%native[speed]]))
    u.reg_write(mk.UC_M68K_REG_SR,0x2500);r.call('phase_join');assert r.r32(clock)==1
    for lane,length in enumerate(lengths):
     phase=((length-1)*native[speed]+lane%native[speed])*900000+within;duration=durations[bspeed];index=phase//duration
     assert r.r32(clock+4+8*lane)==(now+duration-phase%duration)&0xffffffff
     assert r.r32(clock+8+8*lane)==(index+1)%length
     r.w32(r.s['mlp_track'],lane);step=index%length;r.w32(r.s['mlp_step'],(step//16)*16);assert r.call('mlp_cursor')==step%16
    saved=bytes(u.mem_read(clock,52));r.call('phase_join');assert saved==bytes(u.mem_read(clock,52)),'reseeding existing clock'
 assert r.new_count==alloc
 print('PASS phase :7 vitesses B x7 vitesses A x4 fractions x6 longueurs(5,7,12,16,31,64), curseur/pas/deadline, pas de reseed ni allocation',flush=True)
 # Meme vitesse 1x : la position visible est exactement celle de chaque piste A.
 r.w32(clock,0)
 for lane,length in enumerate(lengths):u.mem_write(pattern+264*lane+4,bytes([length,2]));u.mem_write(0x40a788b5+lane,b'\2');u.mem_write(0x40a78866+lane,b'\0')
 r.call('phase_join')
 for lane,length in enumerate(lengths):r.w32(r.s['mlp_track'],lane);r.w32(r.s['mlp_step'],((length-1)//16)*16);assert r.call('mlp_cursor')==(length-1)%16
 # Pulse natif cible simule ; garde et vrai callback B executes.
 pulses=[];record=[0]
 for at,fn in ((0x400cfaf4,lambda a:0x930b1000),(0x4000608c,lambda a:a[0]+1),(0x400060bc,lambda a:a[0]+48),(0x40005f86,lambda a:0),(0x4008e8ce,lambda a:pulses.append((a[0],a[1])) or 0),(0x400cf9a8,lambda a:0x930b2000),(0x4006b978,lambda a:record[0])):
  r.stubs[at]=fn;u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 for mode in (0,1):
  record[0]=mode
  for lane in range(6):
   for page in range(4):
    r.w32(r.s['mlp_track'],lane);r.w32(r.s['mlp_step'],page*16);u.mem_write(pattern+lane*264+4,b'\x40');r.w32(clock+8+lane*8,page*16+6);pulses.clear()
    for led in range(1,17):r.call(0x4008e8c4,led,6)
    assert not pulses,'curseur A traverse le garde pendant B'
    r.call('mlp_led',OBJ+0x500,0,0x930b3000);assert [p for p in pulses if 1<=p[0]<=16]==[(6,6)],(mode,lane,page,pulses)
 r.w32(r.s['mlp_obj'],0);pulses.clear()
 for led in range(1,17):r.call(0x4008e8c4,led,6)
 assert pulses==[(i,6) for i in range(1,17)]
 # Le wrapper appelle le natif une fois et conserve ses resultats/SR.
 original_calls=[]
 def native(args):
  original_calls.append(1);u.reg_write(mk.UC_M68K_REG_D1,0x11223344);u.reg_write(mk.UC_M68K_REG_A0,0x930abc00);u.reg_write(mk.UC_M68K_REG_A1,0x930def00);u.reg_write(mk.UC_M68K_REG_SR,0x2500);return 0x12345678
 r.stubs[0x40053330]=native;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40053330,end=0x40053330)
 # Rejoindre de nouveau pour tester le corps C actif, pas seulement son refus.
 r.w32(r.s['mlp_obj'],OBJ);r.w32(clock,0);r.w32(r.s['ml_start_context'],0);r.w32(0x40a7883c,1)
 value=r.call('phase_tick');assert value==0x12345678 and len(original_calls)==1
 assert u.reg_read(mk.UC_M68K_REG_D1)==0x11223344 and u.reg_read(mk.UC_M68K_REG_A0)==0x930abc00 and u.reg_read(mk.UC_M68K_REG_A1)==0x930def00 and u.reg_read(mk.UC_M68K_REG_SR)==0x2500
 print('PASS wrapper audio : appel natif unique, d0/d1/a0/a1/SR preserves apres phase active',flush=True)
 print('PASS LEDs : six pistes x4pages x2modes REC/clavier, un seul curseur B ; pulses A retablis en sortant de B',flush=True)
 print('LIMITES : snapshots phase natifs simules, deadline/clock et garde executés ; alignement visuel/notes et menu REC a verifier sur appareil')
if __name__=='__main__':main()
