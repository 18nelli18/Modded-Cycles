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
 if flags&2:r.call(0x40152dd4)
 # Executer le constructeur effectivement installe, y compris Attack seul sans filtre.
 assert bytes(u.mem_read(0x4004486c,2))==bytes.fromhex('4eb9')
 r.call(r.r32(0x4004486e))
 def bind(at,fn):
  fresh=at not in r.stubs;r.stubs[at]=fn
  if fresh:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 held=set();bind(0x4007faf4,lambda a:int(a[0] in held))
 # Kit/sons : vraies classes OS et getter de donnees brut pour six pistes.
 kit=0x93090000;vt=0x93098000;getter=0x93099000
 bind(0x400cf866,lambda a:kit);u.mem_write(getter,bytes.fromhex('206f0004202800044e75'));r.w32(vt+40,getter);r.w32(kit+48,vt);r.w32(kit+52,0x9309f000);u.mem_write(0x9309f000,bytes(32));r.w32(vt+16,0x93099020);u.mem_write(0x93099020,bytes.fromhex("70004e75"))
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
 table=r.r32(0x4005a4f4);count=r.r32(r.s['ld_api']+12)
 for descriptor in (*range(count),count,0xffffffff):
  record=table+56*(descriptor if descriptor<count else 0)
  for address,offset in ((0x4000b208,52),(0x4000b22a,44)):
   assert r.call(address,0,descriptor)==r.r32(record+offset)
 print('PASS short/long native name fallback preserves every descriptor and invalid-index bounds',flush=True)

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

 # Vraie liste native, pas seulement un libelle force : ATK absent avant le masque.
 if flags&1:
  record=r.r32(0x4005a4f4)+13*56
  assert r.r32(record+36)==0x600, 'Attack eligibility not copied into active pool'
  def choices(context):
   output=0x930ef000;u.reg_write(mk.UC_M68K_REG_A0,output);r.call(0x4000bffc,context,0x600)
   vector=r.r32(r.r32(output+4)+12)
   return [r.call(0x4005a4e8,r.r32(i)) for i in range(r.r32(vector),r.r32(vector+4),4)]
  for machine_index in (0,1,2,3,4,5,6):
   u.mem_write(0x930a0000+38,bytes([machine_index]));context=kit+116+8*63
   r.w32(record+36,0);assert 23 not in choices(context)
   r.w32(record+36,0x600);assert 23 in choices(context)
  u.mem_write(0x930a0000+38,b'\0')
  print('PASS real native LFO picker: ATK excluded before eligibility correction, offered after on six stock machines and Wizard',flush=True)

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
 # Le test6 annule release-to-exit : les gardes natifs conservent les deux menus.
 lfo=0x930d0000;r.w32(lfo,0x40101644);r.w32(lfo+56,0x401016dc);r.w32(lfo+100,manager)
 lfo2=0x930d3000;r.w32(lfo2,0x40117920);r.w32(lfo2+44,manager)
 for event_flags in (0,2):
  u.mem_write(lfo+604,b'\1');u.mem_write(lfo+104,b'\0');r.w32(EVENT+12,8);r.w32(EVENT+16,event_flags)
  r.call('lf2_key' if 'lf2_key' in r.s else 0x40024e0c,lfo,EVENT)
  assert u.mem_read(lfo+104,1)==b'\0'
  if 'lf2p_assigned' in r.s:
   r.w32(r.s['lf2p_assigned'],1);u.mem_write(lfo2+48,b'\0');r.call('lf2p_menu_key',lfo2,EVENT);assert u.mem_read(lfo2+48,1)==b'\0'
 if 'lf2p_assigned' in r.s:r.w32(r.s['lf2p_assigned'],0)
 print('PASS both LFO pages retain original stay-open behavior after quick assign',flush=True)

 # Descripteurs des trois potards, obtenus par le vrai mapper non modifie.
 descriptors={}
 for descriptor in range(76):
  key=r.call(0x4005a4e8,descriptor)
  if key in (18,13,14) and key not in descriptors:descriptors[key]=descriptor
 for keys in (set(),{5},{8},{5,8}):
  held.clear();held.update(keys)
  for key,target in ((18,23),(13,24),(14,25)):
   assert r.call('ld_assign',descriptors[key])==key
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
 # Vraie entree primaire, shim CPU du corps natif : plusieurs descripteurs contradictoires
 # doivent donner la meme cible capturee, meme si la touche change entre ses lectures.
 shim=0x930d5000;outputs=0x930d6000
 native=r.s['ld_primary_quick_native'];redirect=u.hook_add(UC_HOOK_CODE,lambda u,pc,size,data:u.reg_write(mk.UC_M68K_REG_PC,shim),begin=native,end=native)
 code=bytearray()
 for i,key in enumerate((18,13,14)):
  code+=bytes.fromhex('4878')+struct.pack('>H',descriptors[key])+bytes.fromhex('4eb9')+struct.pack('>I',r.s['ld_assign'])+bytes.fromhex('588f23c0')+struct.pack('>I',outputs+4*i)
 code+=bytes.fromhex('4e75');u.mem_write(shim,bytes(code))
 flip=u.hook_add(UC_HOOK_CODE,lambda *args:held.symmetric_difference_update({5}),begin=shim,end=shim+len(code))
 for index,plain,alternate,mask in ((1,18,23,1),(4,13,24,2),(5,14,25,2)):
  for modified in (False,True):
   for turn in range(20):
    held.clear();held.add(8)
    if modified:held.add(5)
    target=alternate if modified and flags&mask else plain
    r.call(0x4001eaa2,OBJ,index,1)
    assert [r.r32(outputs+4*i) for i in range(3)]==[target]*3
    assert r.r32(r.s['ld_target_override'])==0
 if r.r32(r.s['ld_api']+32):
  u.mem_write(0x930a0000+38,b'\x06')
  for index,target in ((4,13),(5,14)):
   for modified in (False,True):
    held.clear();held.add(8)
    if modified:held.add(5)
    r.call(0x4001eaa2,OBJ,index,1)
    assert [r.r32(outputs+4*i) for i in range(3)]==[target]*3
  u.mem_write(0x930a0000+38,b'\0')
  print('PASS primary Wizard quick-assign snapshot uses native 13/14 with either modifier state',flush=True)
 u.hook_del(flip)
 held.clear();held.update((1,8));r.call(0x4001eaa2,OBJ,5,1);assert [r.r32(outputs+4*i) for i in range(3)]==[18,13,14];assert r.r32(r.s['ld_target_override'])==0
 u.hook_del(redirect)
 print('PASS primary physical knob snapshot: 120 turns, changing modifier during internal reads, no target flips or leaked aliases',flush=True)
 u.reg_write(mk.UC_M68K_REG_A7,STACK);u.reg_write(mk.UC_M68K_REG_D0,0x1234);u.emu_start(r.s['ld_primary_quick_native'],0x4001eaa8,count=100)
 assert u.reg_read(mk.UC_M68K_REG_PC)==0x4001eaa8 and u.reg_read(mk.UC_M68K_REG_A7)==STACK-60 and u.reg_read(mk.UC_M68K_REG_D0)==11
 if 'lf2p_quick_assign' in r.s:
  u.reg_write(mk.UC_M68K_REG_A7,STACK)
  for reg,value in ((mk.UC_M68K_REG_D2,31),(mk.UC_M68K_REG_D3,32),(mk.UC_M68K_REG_D4,33)):u.reg_write(reg,value)
  u.emu_start(r.s['ld_secondary_quick_native'],r.s['lf2p_quick_assign']+8,count=100)
  assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-12 and bytes(u.mem_read(STACK-12,12))==struct.pack('>III',31,32,33)
 print('PASS primary/secondary native trampoline stack/register contracts',flush=True)


 if 'lf2p_enc' in r.s:
  context=0x930c0000;frame=0x930c1000;u.mem_write(frame,bytes(476));assert r.call('lf2_init',context,frame)==1;r.w32(r.s['lf2_context'],context);r.w32(r.s['lf2p_track'],0);r.w32(r.s['lf2p_obj'],OBJ)
  # Vrai scan du menu Dest : PAN -> ATTACK -> CUTOFF -> RESO, dans les deux sens.
  r.w32(r.s['lf2p_row'],4);r.w32(r.s['lf2p_edit'],1);r.w32(EVENT+12,1);r.delta=1;held.clear();r.call('lf2_edit',context,0,3,22)
  offered=[value for value in range(23,33) if not r.string(r.call('ld_second',value)).startswith('ERR')]+[127]
  for value in offered:
   r.call('lf2p_enc',OBJ,EVENT);assert u.mem_read(context+198,1)[0]==value,(value,u.mem_read(context+198,1)[0])
  r.delta=-1
  for value in reversed([22]+offered[:-1]):r.call('lf2p_enc',OBJ,EVENT);assert u.mem_read(context+198,1)[0]==value
  print('PASS real LFO2 destination menu visits installed destinations only, both directions',offered,flush=True)
  mapping=0x930c2000;bind(0x4004df5c,lambda a:mapping)
  for index,key,target in ((1,18,23 if flags&1 else 18),(4,13,24 if flags&2 else 13),(5,14,25 if flags&2 else 14)):
   r.w32(mapping+8+4*index,descriptors[key]);held.update((5,8));r.call('lf2_edit',context,0,3,127);r.call('lf2_edit',context,0,7,16384)
   prior=bytes(u.mem_read(0x40fde838,192));assert r.call('lf2p_quick_assign',index,1)==1;assert u.mem_read(context+198,1)[0]==target;assert u.mem_read(context+206,2)==b'\x40\x00'
   assert r.call('lf2p_quick_assign',index,1)==1;assert u.mem_read(context+206,2)==b'\x41\x00';assert bytes(u.mem_read(0x40fde838,192))==prior
   settings=bytes(u.mem_read(context,1240));u.mem_write(lfo2+48,b'\0');r.w32(EVENT+12,8);r.w32(EVENT+16,0);assert r.call('lf2p_menu_key',lfo2,EVENT)==1;assert u.mem_read(lfo2+48,1)==b'\0' and r.r32(r.s['lf2p_assigned'])==0;assert bytes(u.mem_read(context,1240))==settings
  print('PASS actual LFO2 quick assign then depth adjustment; LFO1 phase bank unchanged',flush=True)
  for index,key,alternate,mask in ((1,18,23,1),(4,13,24,2),(5,14,25,2)):
   for modified in (False,True):
    for turn in range(20):
     held.clear();held.add(8)
     if modified:held.add(5)
     # La table alterne arbitrairement entre trois potards ; elle ne doit pas gagner.
     r.w32(mapping+8+4*index,descriptors[(18,13,14)[turn%3]])
     assert r.call('lf2p_quick_assign',index,1)==1
     assert u.mem_read(context+198,1)[0]==(alternate if modified and flags&mask else key)
     assert r.r32(r.s['ld_target_override'])==0
  print('PASS real LFO2 quick assign: 120 turns with stale/mixed descriptors, targets follow captured MACHINES state only',flush=True)

 # Wizard : noms propres reactualises par sa vraie recherche de potards.
 if r.r32(r.s['ld_api']+32):
  context=kit+116+8*63
  for turn in range(40):
   keys={8,5} if turn%2 else {8};held.clear();held.update(keys)
   u.mem_write(0x930a0000+38,b'\x06');r.w32(r.s['mod_held'],int(5 in held));r.call(0x4004df5c,7)
   # Reproduire le rafraichissement KICK du quick mapper : les noms partages redeviennent SWEP/CONT.
   r.w32(r.s['mod_held'],0);r.call(0x4004df5c,1)
   for key,longname,short in ((13,'Filter','FLT'),(14,'Resonance','RES')):
    descriptor=r.call(0x4005a692,key,6)
    table=r.r32(0x4005a4f4)
    native_name=r.string(r.r32(table+56*descriptor+52))
    assert native_name not in ('FLT','FLTR','RES')
    assert r.string(r.call(0x4000b208,context,descriptor))==short
    assert r.string(r.call(0x4000b22a,context,descriptor))==longname
    u.mem_write(0x930a0000+38,b'\x05')
    assert r.string(r.call(0x4000b208,context,descriptor))==native_name
    u.mem_write(0x930a0000+38,b'\x06')
   for dest,label in ((13,'FLT'),(14,'RES'),(24,'ERR'),(25,'ERR')):
    descriptor=r.call(0x4005a692,dest,6)
    assert r.string(r.call('ld_first',context,descriptor,0,dest))==label
    if 'lf2p_track' in r.s:
     r.w32(r.s['lf2p_track'],0);assert r.string(r.call('ld_second',dest))==label
   if 'lf2p_quick_assign' in r.s:
    for index,target in ((4,13),(5,14)):
     assert r.call('lf2p_quick_assign',index,1)==1
     assert u.mem_read(r.r32(r.s['lf2_context'])+198,1)[0]==target
  u.mem_write(0x930a0000+38,b'\0');r.w32(r.s['mod_held'],0)
  print('PASS Wizard native lookup and both displays: stable FLT/RES; installed secondary quick assign uses native 13/14',flush=True)

 print('LIMIT: physical UI/audio acceptance remains hardware testing; no DSP modification',flush=True)
if __name__=='__main__':main()
