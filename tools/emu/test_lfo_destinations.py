"""Note121 : bootstrap reel, noms/scan LFO2, quick assign et fermeture native differee.

python3 tools/emu/test_lfo_destinations.py --case build/lfo-destinations/0-after
L'audio et ses adresses restent strictement ceux du build de reference.
"""
import argparse,json,pathlib,sys,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,OBJ,EVENT,STACK

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();img,mem,ts=boot_case(a.case);symbols={k:v for t in ts for k,v in t.get('symbols',{}).items()};r=Rig(img,{'writes':[]},{'writes':[],'symbols':symbols});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in mem:u.mem_write(at,raw)
 flags=r.r32(r.s['ld_api']+4)
 if flags:r.call(0x40152dd4);r.call(0x40168e3c)
 else:r.call(0x4005a274)
 def bind(at,fn):
  fresh=at not in r.stubs;r.stubs[at]=fn
  if fresh:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 held=set();bind(0x4007faf4,lambda a:int(a[0] in held))
 # Kit/sons : vraies classes OS et getter de donnees brut pour six pistes.
 kit=0x93090000;vt=0x93098000;getter=0x93099000
 bind(0x400cf866,lambda a:kit);u.mem_write(getter,bytes.fromhex('206f0004202800044e75'));r.w32(vt+40,getter);r.w32(vt+16,0x93099020);u.mem_write(0x93099020,bytes.fromhex("70004e75"))
 for track in range(6):
  handle=kit+212+68*track;raw=0x930a0000+track*128;owner=kit+116+8*(63+track)
  r.w32(owner,0x400fd134);r.w32(owner+4,handle);r.w32(handle,vt);r.w32(handle+4,raw);u.mem_write(raw,bytes(100));u.mem_write(raw+38,bytes([track]))
 for track in range(6):
  for dest,label in (((23,'ATK'),(24,'FLT'),(25,'RES')) if flags==3 else ()):
   descriptor=r.call(0x4005a692,dest,track)
   assert descriptor!=0xffffffff
   assert r.string(r.call('ld_first',0,descriptor,0,dest))==label
   u.reg_write(mk.UC_M68K_REG_A2,kit+116+8*(63+track));u.reg_write(mk.UC_M68K_REG_D0,dest<<8);u.reg_write(mk.UC_M68K_REG_A7,STACK)
   u.emu_start(0x400264fc,0x40026514,count=50000)
   assert u.reg_read(mk.UC_M68K_REG_PC)==0x40026514
   assert r.string(u.reg_read(mk.UC_M68K_REG_D0))==label
   assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-16
   assert r.string(r.call('ld_second',dest))==label
 print('PASS six tracks: real descriptor lookup and both explicit label routes',flush=True)
 if 'retrosyn_labels' in r.s:
  expected=[('Timbre','TIMB'),('Oscillator','OSC'),('Pitch Sweep','PSWP'),('Chord Arp','ARP')]
  table=r.s['retrosyn_labels'];index=r.s['retrosyn_machine_index']
  for track in range(6):
   raw=0x930a0000+128*track;u.mem_write(raw+38,bytes([index]));context=kit+116+8*(63+track)
   for i,(longname,short) in enumerate(expected):
    descriptor=r.call(0x4005a692,11+i,index)
    assert r.string(r.r32(table+56*i+44))==longname
    assert r.string(r.r32(table+56*i+52))==short
    assert r.string(r.call(0x4000b208,context,descriptor))==short
   u.mem_write(raw+38,bytes([track]))
  print('PASS real Retrosyn descriptor/name lookup on six tracks: Timbre/Oscillator/Pitch Sweep/Chord Arp',flush=True)

 # Fermeture differee native : MACHINES exact, autres vues preservees.
 manager=0x930b0000;head=manager+20;node=0x930b0100;machine=0x930b1000;other=0x930b2000;node2=node+32
 bind(0x400060d8,lambda a:manager)
 r.w32(head,node2);r.w32(head+4,node);r.w32(node,head);r.w32(node+4,node2);r.w32(node+8,machine);r.w32(node2,node);r.w32(node2+4,head);r.w32(node2+8,other)
 u.mem_write(machine,bytes(208));r.w32(machine,0x40117920);r.w32(machine+44,manager);r.w32(other,0x4010052c)
 assert u.mem_read(machine+48,1)==b'\0';r.call('ld_finish');assert u.mem_read(machine+48,1)==b'\1';assert u.mem_read(manager+34,1)==b'\1';assert u.mem_read(other+48,1)==b'\0'
 before=bytes(u.mem_read(manager,8192));r.call('ld_finish');assert bytes(u.mem_read(manager,8192))==before
 # Clone B/LFO2 ne porte pas le vptr stock : aucune fermeture.
 u.mem_write(machine+48,b'\0');r.w32(machine,0x930b8000);r.call('ld_finish');assert u.mem_read(machine+48,1)==b'\0';r.w32(machine,0x40117920)
 print('PASS native deferred close only marks stock Machines selector; repeated call and B/private views safe',flush=True)
 presented=[];bind(r.s['ld_present_native'],lambda a:presented.append(tuple(a[:3])) or 71);pair=0x930b9000
 for keys,target in ((set(),other),({5},machine),({5},other)):
  held.clear();held.update(keys);u.mem_write(machine+48,b'\0');r.w32(pair,target)
  assert r.call('ld_present',manager,pair,1)==71
  assert u.mem_read(machine+48,1)==bytes([int(keys=={5} and target==other)])
  assert presented[-1]==(manager,pair,1)
 print('PASS generic Machines action screen closes only underlying selector; presentation ABI and solo Machines preserved',flush=True)
 # Vraie branche MACHINES du gestionnaire ParameterPage : LFO tenu court-circuite l'ouverture.
 allocations=r.new_count
 for keys in (set(),{5},{8},{5,8}):
  held.clear();held.update(keys)
  for event_flags in (0,1,9,33):
   r.w32(EVENT+12,5);r.w32(EVENT+16,event_flags)
   assert r.call(0x40024e0c,OBJ,EVENT)==0
   if 'lf2p_menu_key' in r.s:assert r.call('lf2p_menu_key',OBJ,EVENT)==1
   u.reg_write(mk.UC_M68K_REG_A7,STACK);u.reg_write(mk.UC_M68K_REG_D3,EVENT)
   for reg,value in ((mk.UC_M68K_REG_D0,0x12345678),(mk.UC_M68K_REG_D1,0x23456789),(mk.UC_M68K_REG_A0,0x34567890),(mk.UC_M68K_REG_A1,0x45678901)):u.reg_write(reg,value)
   stop=0x4001c2a8 if 8 in keys else 0x4001c25a
   u.emu_start(0x4001c252,stop,count=10000)
   assert u.reg_read(mk.UC_M68K_REG_PC)==stop
   assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-(0 if 8 in keys else 4)
   for reg,value in ((mk.UC_M68K_REG_D0,0x12345678),(mk.UC_M68K_REG_D1,0x23456789),(mk.UC_M68K_REG_A0,0x34567890),(mk.UC_M68K_REG_A1,0x45678901)):assert u.reg_read(reg)==value
   if 8 not in keys:assert r.r32(STACK-4)==EVENT and u.reg_read(mk.UC_M68K_REG_A3)==0x400724a0
 assert r.new_count==allocations
 print('PASS actual Machines opener: LFO held consumes press/release/hold before allocation; unmodified path and registers exact',flush=True)

 # Descripteurs des trois potards, obtenus par le vrai mapper non modifie.
 descriptors={}
 for descriptor in range(76):
  key=r.call(0x4005a4e8,descriptor)
  if key in (18,13,14) and key not in descriptors:descriptors[key]=descriptor
 for keys in (set(),{5},{8},{5,8}):
  held.clear();held.update(keys)
  for key,target in ((18,23),(13,24),(14,25)):
   assert r.call('ld_assign',descriptors[key])==(target if keys=={5,8} and (flags&(1 if key==18 else 2)) else key)
 # IRQ n'appelle pas les gestes UI, meme s'il passe accidentellement par le helper.
 held.update((5,8));u.reg_write(mk.UC_M68K_REG_SR,0x2500);assert r.call('ld_assign',descriptors[18])==18;u.reg_write(mk.UC_M68K_REG_SR,0x2000)
 print('PASS quick-assign mappings require both physical modifiers; native mapper unaffected and IRQ guarded',flush=True)
 # Slot potard : execution du vrai wrapper attaque/filtre, fermeture sans changer le descripteur.
 original=r.r32(r.s['ld_api']+8);snap=[]
 bind(original,lambda a:snap.append(tuple(a[:4])) or 13)
 for knob in range(2,9):
  for keys in (set(),{5},{5,2}):
   held.clear();held.update(keys);u.mem_write(machine+48,b'\0');assert r.call('ld_knob',OBJ,knob,0,0xffffffff)==13
   assert u.mem_read(machine+48,1)==bytes([int(bool(5 in keys and ((knob==3 and flags&1) or (4<=knob<=7 and flags&2))))])
   assert snap[-1]==(OBJ,knob,0,0xffffffff)
 print('PASS knob slot preserves all four arguments/result; plain Machines and unmodified knobs do not close',flush=True)
 if 'lf2p_enc' in r.s:
  context=0x930c0000;frame=0x930c1000;u.mem_write(frame,bytes(476));assert r.call('lf2_init',context,frame)==1;r.w32(r.s['lf2_context'],context);r.w32(r.s['lf2p_track'],0);r.w32(r.s['lf2p_obj'],OBJ)
  # Vrai scan du menu Dest : PAN -> ATTACK -> CUTOFF -> RESO, dans les deux sens.
  r.w32(r.s['lf2p_row'],4);r.w32(r.s['lf2p_edit'],1);r.w32(EVENT+12,1);r.delta=1;held.clear();r.call('lf2_edit',context,0,3,22)
  for value in (23,24,25):
   r.call('lf2p_enc',OBJ,EVENT);assert u.mem_read(context+198,1)[0]==value
  r.delta=-1
  for value in (24,23,22):r.call('lf2p_enc',OBJ,EVENT);assert u.mem_read(context+198,1)[0]==value
  print('PASS real LFO2 destination menu encoder visits ATTACK/CUTOFF/RESO both directions',flush=True)
  mapping=0x930c2000;bind(0x4004df5c,lambda a:mapping)
  for index,key,target in ((1,18,23),(4,13,24),(5,14,25)):
   r.w32(mapping+8+4*index,descriptors[key]);held.update((5,8));r.call('lf2_edit',context,0,3,127);r.call('lf2_edit',context,0,7,16384)
   prior=bytes(u.mem_read(0x40fde838,192));assert r.call('lf2p_quick_assign',index,1)==1;assert u.mem_read(context+198,1)[0]==target;assert u.mem_read(context+206,2)==b'\x40\x00'
   assert r.call('lf2p_quick_assign',index,1)==1;assert u.mem_read(context+206,2)==b'\x41\x00';assert bytes(u.mem_read(0x40fde838,192))==prior
  print('PASS actual LFO2 quick assign then depth adjustment; LFO1 phase bank unchanged',flush=True)
 print('LIMIT: physical UI/audio acceptance remains hardware testing; no DSP modification',flush=True)
if __name__=='__main__':main()
