#!/usr/bin/env python3
"""Prototype retrigger B : cadence bornée, wrap, annulation et saturation."""
import argparse,pathlib,struct,subprocess,tempfile
from unicorn import m68k_const as mk,UC_HOOK_CODE
from test_midi_both import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx

ENTRY=0x93020000
BANK=0x93000000
STATE=0x93001000

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);ap.add_argument('--chance',action='store_true');ap.add_argument('--conditions',action='store_true');a=ap.parse_args();a.chance=a.chance or a.conditions
 root=pathlib.Path(__file__).resolve().parents[2]
 cross=str(root.parent/'toolchain/bin/m68k-elf-')
 r=Rig(main_os_from_syx(a.cycles),0);u=r.uc
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objects=[]
  for name in ('runtime','pattern','retrigger','retrigger_locks','retrigger_service','integration','arp','arp_tick','retrigger_patterns','retrigger_step') + (('chance',) if a.chance else ()) + (('conditions','condition_history','condition_decode','condition_run') if a.conditions else ()):
   obj=p/(name+'.o');objects.append(str(obj))
   subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_REPEAT=1','--defsym','ML_PATTERN_BANKS=1',*(['--defsym','ML_CHANCE=1'] if a.chance else []),*(['--defsym','ML_CONDITIONS=1'] if a.conditions else []),'-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  elf=p/'r.elf';binary=p/'r.bin'
  bindings={'mlp_track':0x93006010,'mlp_step':0x93006014,'ml_runtime':0x93006018,'ml_context':0x93006000,'ml_play_pattern':0x93006004,'ml_pattern':0x93006008,
            'ml_clock_durations':0x93006100,'ml_pad_serial':0x93006200,'ml_live_runtime':0x93007000,
            'ml_bank_ui_sync':0x93018000,'ml_bank_follow':0x93018000,'ml_clock':0x93018002,'ml_prepare':0x93018000,
            'ml_service':0x93018000,'mlp_led_poll':0x93018000}
  if a.conditions:bindings.update(ml_cond_history=0x93006400,ml_cond_fill=0x93006480)
  subprocess.run([cross+'ld','-Ttext='+hex(ENTRY),'-e','ml_repeat_tick',
                  *['--defsym='+name+'='+hex(value) for name,value in bindings.items()],
                  '-o',str(elf),*objects],check=True)
  subprocess.run([cross+'objcopy','-O','binary','--only-section=.text','--only-section=.rodata','--only-section=.data',str(elf),str(binary)],check=True)
  u.mem_write(ENTRY,binary.read_bytes())
  u.mem_map(0x80000000,0x10000)
  symbols={s[2]:int(s[0],16) for line in subprocess.check_output([cross+'nm',str(elf)],text=True).splitlines() if len(s:=line.split())==3}
 def call(name,*args,sr=0x2505):
  u.reg_write(mk.UC_M68K_REG_SR,sr);u.reg_write(mk.UC_M68K_REG_A7,STACK)
  u.mem_write(STACK,struct.pack('>'+'I'*(1+len(args)),STOP,*args))
  u.emu_start(symbols[name],STOP,count=20000)
  assert u.reg_read(mk.UC_M68K_REG_PC)==STOP
  assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
  if name in ('ml_repeat_tick','ml_repeat_cancel','ml_repeat_arm','ml_repeat_service','ml_repeat_service_with_arp','ml_repeat_cancel_all','ml_repeat_audio','ml_audio_tick','ml_repeat_resolve','ml_repeat_arp_tick','ml_repeat_pattern_prepare','ml_repeat_locked_step','ml_pattern_tick'):
   assert u.reg_read(mk.UC_M68K_REG_SR)==sr
  count,_,_,held=struct.unpack('>4I',u.mem_read(BANK,16));assert count+held<=64
  return u.reg_read(mk.UC_M68K_REG_D0)
 def state(start=100,end=140,packet=0x96486403):
  u.mem_write(BANK,bytes(320));u.mem_write(STATE,struct.pack('>5I',1,start,10,end,packet))
 def tick(now):return call('ml_repeat_tick',BANK,STATE,0,now)
 def take():return call('ml_take',BANK)
 state();assert tick(99)==0 and take()==0
 assert tick(100)==1 and take()==0x96486403 and take()==0
 assert tick(109)==0 and take()==0
 assert tick(110)==1 and [take(),take(),take()]==[0x86480003,0x96486403,0]
 assert tick(135)==1 and [take(),take()]==[0x86480003,0x96486403]
 assert tick(135)==0 and take()==0
 assert tick(140)==0 and take()==0x86480003 and take()==0
 assert u.mem_read(STATE,4)==bytes(4)
 # Un léger retard conserve la phase ; gros retard saute sans rafale.
 state();tick(101);take()
 assert struct.unpack('>I',u.mem_read(STATE+4,4))[0]==110
 tick(112);take();take()
 assert struct.unpack('>I',u.mem_read(STATE+4,4))[0]==120
 state(0xfffffff8,20);assert tick(0xfffffff8)==1;take()
 assert tick(1)==0;assert tick(2)==1;take();take()
 call('ml_repeat_cancel',BANK,STATE,0)
 assert take()==0x86480003 and take()==0 and tick(12)==0
 # Producteur sans consommateur : les Off restent réservés, aucun débordement.
 state(0,1000)
 for now in range(0,1000,10):tick(now)
 tick(1000)
 messages=[]
 while (packet:=take()):messages.append(packet)
 assert messages and messages[-1]==0x86480003
 assert sum((p>>24)==0x96 for p in messages)==sum((p>>24)==0x86 for p in messages)
 # Table de vitesse OS réelle, sans copie des constantes dans le mod.
 for rate in range(17):
  interval=struct.unpack('>I',u.mem_read(0x4010ce4c+rate*4,4))[0]
  state()
  assert call('ml_repeat_arm',BANK,STATE,0,0,0x96486403,rate,interval*3)==1
  assert take()==0x96486403
  assert struct.unpack('>5I',u.mem_read(STATE,20))==(1,interval,interval,interval*3,0x96486403)
  assert tick(interval-1)==0 and take()==0
  assert tick(interval)==1 and [take(),take()]==[0x86480003,0x96486403]
  assert tick(interval*3)==0 and take()==0x86480003
 state();before=bytes(u.mem_read(STATE,20))
 for lane,rate,duration,packet in ((6,0,10,0x96486403),(0,17,10,0x96486403),(0,0,0,0x96486403),(0,0,0x40000000,0x96486403),(0,0,10,0x96480003),(0,0,10,0x86486403)):
  assert call('ml_repeat_arm',BANK,STATE,lane,0,packet,rate,duration)==0
  assert bytes(u.mem_read(STATE,20))==before and take()==0
 # File pleine : aucune répétition armée après refus de la première note.
 state()
 u.mem_write(BANK,struct.pack('>4I',64,0,0,0)+bytes(304))
 assert call('ml_repeat_arm',BANK,STATE,0,0,0x96486403,16,100)==0
 assert u.mem_read(STATE,4)==bytes(4)
 u.mem_write(BANK,bytes(320))
 # Conversion Len native, y compris INF distinct d'un délai fini.
 for length in range(128):
  for gate in (0,5400001,345600000):
   for latency in (0,800):
    if length==127:expected=0xffffffff
    else:
     half=(gate>>1)+struct.unpack('>I',u.mem_read(0x4010d814+4*(length+1),4))[0]-latency
     expected=half*2 if 0<half<=0x1fffffff else 0
    assert call('ml_repeat_duration',length,gate,latency)==expected
 for args in ((128,0,0),(0,0x40000000,0),(0,0,0xffffffff)):
  assert call('ml_repeat_duration',*args)==0
 state();start=0xfffffff0
 assert call('ml_repeat_arm',BANK,STATE,0,start,0x96486403,16,0xffffffff)==1
 assert take()==0x96486403 and struct.unpack('>I',u.mem_read(STATE,4))[0]==2
 for index in (1,2,3,100):
  assert tick((start+index*1080000)&0xffffffff)==1
  assert [take(),take()]==[0x86480003,0x96486403] and take()==0
 call('ml_repeat_cancel',BANK,STATE,0)
 assert take()==0x86480003 and take()==0
 print('ok : conversion des128 Len natives, INF sans échéance artificielle, wrap et annulation avec Off')
 print('ok : armement atomique, 17 vitesses natives, première note/Off réservés, refus sans répétition fantôme')
 locks=0x93002000
 u.mem_write(locks-4,b'ABCD'+bytes(512)+b'EFGH')
 assert call('ml_repeat_locks_init',locks)==1
 for step in range(64):
  assert bytes(u.mem_read(locks+step*8,8))==b'\0\0\0\0\0\1\0\0'
  for field,values in enumerate(((0,1),(0,16),(0,127),(-128,127),(0,5),(1,4))):
   for value in values:assert call('ml_repeat_lock',locks,step,field,value&0xffffffff)==1
 before=bytes(u.mem_read(locks,512))
 for step,field,value in ((64,0,1),(0,6,1),(0,0,2),(0,1,17),(0,2,128),(0,3,128),(0,3,-129),(0,4,6),(0,5,0),(0,5,5)):
  assert call('ml_repeat_lock',locks,step,field,value&0xffffffff)==0
  assert bytes(u.mem_read(locks,512))==before
 assert bytes(u.mem_read(locks-4,4))==b'ABCD' and bytes(u.mem_read(locks+512,4))==b'EFGH'
 print('ok : 64 verrous privés retrigger/arp, six champs bornés, valeurs invalides sans écriture')
 # Locks partiels : le masque distingue « hériter » de « désactiver ».
 defaults=locks+0x400;resolved=defaults+0x40
 base=bytes((1,8,32,0,0,1,0,0));override=bytes((0,16,127,128,5,4))
 u.mem_write(defaults,base)
 call('ml_repeat_locks_init',locks)
 for mask in range(64):
  step=mask
  u.mem_write(locks+step*8,override+bytes((mask,0)))
  u.mem_write(resolved-4,b'ABCD'+b'\xa5'*8+b'EFGH')
  assert call('ml_repeat_resolve',defaults,locks,step,resolved)==1
  expected=bytes(override[i] if mask&(1<<i) else base[i] for i in range(6))+bytes(2)
  assert bytes(u.mem_read(resolved,8))==expected
  assert bytes(u.mem_read(resolved-4,4))==b'ABCD' and bytes(u.mem_read(resolved+8,4))==b'EFGH'
 assert bytes(u.mem_read(defaults,8))==base
 for field,bad in ((0,2),(1,17),(2,128),(4,6),(5,0),(5,5)):
  broken=bytearray(base);broken[field]=bad;broken[6]=1<<field
  u.mem_write(locks,bytes(broken));u.mem_write(resolved,b'\xa5'*8)
  assert call('ml_repeat_resolve',defaults,locks,0,resolved)==0
  assert bytes(u.mem_read(resolved,8))==b'\xa5'*8
 for mask in (64,128,255):
  u.mem_write(locks,base[:6]+bytes((mask,0)))
  assert call('ml_repeat_resolve',defaults,locks,0,resolved)==0
  assert bytes(u.mem_read(resolved,8))==b'\xa5'*8
 assert call('ml_repeat_resolve',defaults,locks,64,resolved)==0
 assert bytes(u.mem_read(resolved,8))==b'\xa5'*8
 call('ml_repeat_locks_init',locks)
 assert call('ml_repeat_lock',locks,0,0,0)==1
 assert bytes(u.mem_read(locks,8))==bytes((0,0,0,0,0,1,1,0))
 assert call('ml_repeat_resolve',defaults,locks,0,resolved)==1
 assert bytes(u.mem_read(resolved,8))==bytes((0,8,32,0,0,1,0,0))
 print('ok : 64 combinaisons de locks partiels, héritage/arrêt explicite, validation avant publication')
 # Six voies simultanées ; le service ne touche pas le pattern ni ses gardes.
 pattern=0x93003000
 def six(duration=4000000):
  u.mem_write(BANK,bytes(320));u.mem_write(STATE,bytes(120))
  data=bytearray(1584)
  for lane in range(6):
   data[lane*264:lane*264+6]=bytes((1,0,6+lane,3,16,2))
  u.mem_write(pattern-4,b'ABCD'+data+b'EFGH')
  for lane in range(6):
   assert call('ml_repeat_arm',BANK,STATE+lane*20,lane,0,((0x96+lane)<<24)|0x486403,16,duration)==1
  assert len([take() for _ in range(6)])==6
  return bytes(u.mem_read(pattern-4,1592))
 before=six()
 assert call('ml_repeat_service',BANK,pattern,STATE,1080000,1)==6
 packets=[take() for _ in range(12)]
 for lane in range(6):
  assert packets[lane*2:lane*2+2]==[((0x86+lane)<<24)|0x480003,((0x96+lane)<<24)|0x486403]
 assert take()==0 and bytes(u.mem_read(pattern-4,1592))==before
 # Annulation immédiate, avec Off sur l'ancien canal/port, jamais le nouveau.
 for lane,offset,value in ((0,1,1),(1,0,0),(2,2,15),(3,3,2),(4,2,16),(5,3,1)):
  u.mem_write(pattern+lane*264+offset,bytes((value,)))
 assert call('ml_repeat_service',BANK,pattern,STATE,2160000,1)==0
 assert [take() for _ in range(6)]==[((0x86+lane)<<24)|0x480003 for lane in range(6)]
 assert take()==0 and all(u.mem_read(STATE+lane*20,4)==bytes(4) for lane in range(6))
 for mode in (0,2):
  six()
  assert call('ml_repeat_service',BANK,pattern,STATE,1,mode)==0
  assert [take() for _ in range(6)]==[((0x86+lane)<<24)|0x480003 for lane in range(6)]
  assert take()==0
  assert call('ml_repeat_service',BANK,pattern,STATE,2160000,1)==0 and take()==0
 six()
 call('ml_repeat_cancel_all',BANK,STATE)
 assert [take() for _ in range(6)]==[((0x86+lane)<<24)|0x480003 for lane in range(6)]
 assert take()==0 and bytes(u.mem_read(STATE,120))==b''.join(struct.pack('>5I',0,1080000,1080000,4000000,((0x96+lane)<<24)|0x486403) for lane in range(6))
 assert call('ml_repeat_service',BANK,pattern,STATE,2160000,1)==0 and take()==0
 for offset,value in ((4,0),(4,65),(5,7)):
  six()
  for lane in range(6):u.mem_write(pattern+lane*264+offset,bytes((value,)))
  assert call('ml_repeat_service',BANK,pattern,STATE,2160000,1)==0
  assert [take() for _ in range(6)]==[((0x86+lane)<<24)|0x480003 for lane in range(6)]
  assert take()==0
 # Consommateur DIN bloqué : six producteurs ne perdent jamais leurs Off.
 six(200000000)
 for now in range(1080000,108000001,1080000):
  call('ml_repeat_service',BANK,pattern,STATE,now,1)
 assert struct.unpack('>I',u.mem_read(BANK,4))[0]>=58
 call('ml_repeat_cancel_all',BANK,STATE)
 packets=[]
 while (packet:=take()):packets.append(packet)
 for lane in range(6):
  # Les six On initiaux ont déjà été consommés par six().
  assert sum(p>>24==0x86+lane for p in packets)==1+sum(p>>24==0x96+lane for p in packets)
 assert all(u.mem_read(STATE+lane*20,4)==bytes(4) for lane in range(6))
 # Une voie inactive ne possède pas la note ordinaire : ne pas la couper.
 u.mem_write(BANK,bytes(320));u.mem_write(STATE,bytes(120))
 assert call('ml_step',BANK,0,0x96486403,8)==1 and take()==0x96486403
 held=bytes(u.mem_read(BANK+272,8))
 assert call('ml_repeat_service',BANK,pattern,STATE,2160000,0)==0 and take()==0
 assert bytes(u.mem_read(BANK+272,8))==held
 # Adaptateur appelé par l'audio : un autre pattern annule avant de répéter.
 u.mem_write(BANK,bytes(320))
 assert call('ml_repeat_audio',BANK,pattern,0,1)==0
 before=six()
 private=symbols['ml_repeat_states']
 u.mem_write(private,bytes(u.mem_read(STATE,120)))
 assert call('ml_repeat_audio',BANK,pattern,1080000,1)==6
 assert len([take() for _ in range(12)])==12 and take()==0
 alternate=pattern+0x1000
 u.mem_write(alternate,bytes(u.mem_read(pattern,1584)))
 assert call('ml_repeat_audio',BANK,alternate,2160000,1)==0
 assert [take() for _ in range(6)]==[((0x86+lane)<<24)|0x480003 for lane in range(6)]
 assert take()==0 and bytes(u.mem_read(pattern-4,1592))==before
 assert call('ml_repeat_audio',BANK,alternate,3240000,1)==0 and take()==0
 print('ok : adaptateur audio, changement de propriétaire pattern avant répétition, anciens canaux libérés')
 # Vrai wrapper firmware compilé ML_REPEAT : service avant ml_clock.
 # Le corps de ml_clock est un témoin ici ; le service et la file sont réels.
 context=0x93008000;runtime=context+1584
 u.mem_write(0x93018000,b'\x4e\x75\x4e\x75')
 u.mem_write(symbols['ml_context'],struct.pack('>I',context))
 u.mem_write(symbols['ml_play_pattern'],struct.pack('>I',pattern))
 u.mem_write(runtime,bytes(320));u.mem_write(private,bytes(120))
 observed=[]
 def clock_witness(uc,address,size,user):
  sp=uc.reg_read(mk.UC_M68K_REG_A7)
  args=struct.unpack('>5I',uc.mem_read(sp+4,20))
  observed.append((args,struct.unpack('>I',uc.mem_read(runtime,4))[0]))
 hook=u.hook_add(UC_HOOK_CODE,clock_witness,begin=0x93018002,end=0x93018002)
 call('ml_audio_tick',0,1)
 assert observed[-1][0]==(runtime,pattern,context+1904,0,1)
 for lane in range(6):
  assert call('ml_repeat_arm',runtime,private+lane*20,lane,0,((0x96+lane)<<24)|0x486403,16,4000000)==1
 def drain_runtime():
  result=[]
  while (packet:=call('ml_take',runtime)):result.append(packet)
  return result
 assert len(drain_runtime())==6
 call('ml_audio_tick',1080000,1)
 assert observed[-1][1]==12 and len(drain_runtime())==12
 u.mem_write(symbols['ml_play_pattern'],struct.pack('>I',alternate))
 call('ml_audio_tick',2160000,1)
 assert observed[-1][0][1]==alternate and observed[-1][1]==6
 assert drain_runtime()==[((0x86+lane)<<24)|0x480003 for lane in range(6)]
 call('ml_audio_tick',3240000,1)
 assert observed[-1][1]==0 and drain_runtime()==[]
 u.hook_del(hook)
 print('ok : wrapper audio compilé, service avant ordonnanceur, arguments/IRQ préservés, changement de pattern sans répétition tardive')
 # Comparaison des six modes avec l'algorithme MIT arp.c, sur notes non triées.
 arp=0x9300a000
 def reference(s,notes,mode,octs):
  last,pos,direction,seed=s
  if mode==5:return last,s
  if mode>=3:
   length=len(notes)*octs
   if mode==3:
    seed=(seed*1103515245+12345)&0xffffffff
    p=(seed>>16)%length
    if length>1 and p==pos:p=(p+1)%length
   else:p=(pos+1)%length
   v=notes[p%len(notes)]+12*(p//len(notes))
   if v>127:v=notes[p%len(notes)]
   return v,(v,p,direction,seed)
  up=direction>0 if mode==2 else mode==0
  values=[n+12*o for o in range(octs) for n in notes if n+12*o<=127]
  def beyond(up,ref):
   choices=[v for v in values if (v>ref if up else v<ref)]
   return (min(choices) if up else max(choices)) if choices else -1
  v=beyond(up,last)
  if v<0 and mode==2:
   direction=-direction;up=not up;v=beyond(up,last)
  if v<0 and mode!=2:v=beyond(up,-1 if up else 128)
  if v<0:v=last
  return v,(v,pos,direction,seed)
 for notes in ((67,60,64),(120,127),(72,),(60,72,60),(0,12,24,36,48,60,72,84,96,108,120,127)):
  for mode in range(6):
   for octs in range(1,5):
    u.mem_write(arp-4,b'ABCD'+bytes(32)+b'EFGH')
    call('ml_arp_init',arp)
    for note in notes:assert call('ml_arp_held',arp,note,1)==1
    unique=list(dict.fromkeys(notes));s=(unique[0],0,1,0x2545f491)
    for _ in range(80):
     expected,s=reference(s,unique,mode,octs)
     assert call('ml_arp_next',arp,mode,octs)==expected,(notes,mode,octs,s)
     count,last,pos,direction,seed=struct.unpack('>IIIiI',u.mem_read(arp,20))
     assert count==len(unique) and (last,pos,direction,seed)==s
    assert bytes(u.mem_read(arp-4,4))==b'ABCD' and bytes(u.mem_read(arp+32,4))==b'EFGH'
 # Relâchement d'un accord, doublons et limites sans corruption.
 call('ml_arp_init',arp)
 for note in range(60,72):assert call('ml_arp_held',arp,note,1)==1
 before=bytes(u.mem_read(arp,32))
 assert call('ml_arp_held',arp,72,1)==0 and bytes(u.mem_read(arp,32))==before
 for note in (60,65,71):assert call('ml_arp_held',arp,note,0)==1
 assert struct.unpack('>I',u.mem_read(arp,4))[0]==9
 assert bytes(u.mem_read(arp+20,9))==bytes(n for n in range(60,72) if n not in (60,65,71))
 before=bytes(u.mem_read(arp,32))
 for mode,octs in ((6,1),(0,0),(0,5)):
  assert call('ml_arp_next',arp,mode,octs)==0xffffffff and bytes(u.mem_read(arp,32))==before
 assert call('ml_arp_held',arp,128,1)==0 and bytes(u.mem_read(arp,32))==before
 call('ml_arp_init',arp)
 assert call('ml_arp_next',arp,0,1)==0xffffffff
 print('ok : arp B compilé, six modes/quatre octaves comparés à arp.c, ordre de jeu, limites MIDI et touches relâchées')
 # Vraie file MIDI : progression transactionnelle, pas une simple sélection.
 state(packet=0x963c6403);call('ml_arp_init',arp)
 for note in (60,64,67):call('ml_arp_held',arp,note,1)
 def arp_tick(now,mode=0,octs=1):return call('ml_repeat_arp_tick',BANK,STATE,arp,0,now,mode,octs)
 before=bytes(u.mem_read(arp,32))
 assert arp_tick(99)==0 and take()==0 and bytes(u.mem_read(arp,32))==before
 assert arp_tick(100)==1 and take()==0x96406403 and take()==0
 assert arp_tick(110)==1 and [take(),take()]==[0x86400003,0x96436403]
 assert arp_tick(120)==1 and [take(),take()]==[0x86430003,0x963c6403]
 before=bytes(u.mem_read(arp,32))
 assert arp_tick(140)==0 and take()==0x863c0003 and take()==0
 assert bytes(u.mem_read(arp,32))==before
 for mode in (0,3,4):
  state(packet=0x963c6403);call('ml_arp_init',arp)
  for note in (60,64,67):call('ml_arp_held',arp,note,1)
  before=bytes(u.mem_read(arp,32));packet=bytes(u.mem_read(STATE+16,4))
  u.mem_write(BANK,struct.pack('>4I',64,0,0,0)+bytes(304))
  assert arp_tick(100,mode)==0
  assert bytes(u.mem_read(arp,32))==before and bytes(u.mem_read(STATE+16,4))==packet
 # OFF garde le paquet courant et n'avance aucun état d'arp.
 state(packet=0x963c6403);before=bytes(u.mem_read(arp,32))
 assert arp_tick(100,5)==1 and take()==0x963c6403
 assert bytes(u.mem_read(arp,32))==before
 call('ml_repeat_cancel',BANK,STATE,0);assert take()==0x863c0003
 state(packet=0x963c6403);call('ml_arp_init',arp)
 for note in (60,64):call('ml_arp_held',arp,note,1)
 assert call('ml_repeat_arm',BANK,STATE,0,0,0x963c6403,16,0xffffffff)==1
 assert take()==0x963c6403
 assert arp_tick(1080000)==1 and [take(),take()]==[0x863c0003,0x96406403]
 call('ml_repeat_cancel',BANK,STATE,0);assert take()==0x86400003 and take()==0
 print('ok : arp/retrigger transactionnel, Off/On réels, refus de file sans progression/seed consommée, OFF et fin')
 # Raccordement réel au service six voies : mode/état propres à chaque voie.
 arpbank=0x9300b000
 u.mem_write(arpbank-4,b'ABCD'+b'\xa5'*240+b'EFGH')
 assert call('ml_arp_bank_init',arpbank)==1
 for lane in range(6):
  record=arpbank+lane*40
  assert struct.unpack('>2I',u.mem_read(record,8))==(5,1)
  assert bytes(u.mem_read(record+8,32))==struct.pack('>5I',0,0,0,1,0x2545f491)+bytes(12)
  u.mem_write(record,struct.pack('>I',lane))
  for note in (60,64,67):call('ml_arp_held',record+8,note,1)
 u.mem_write(symbols['ml_repeat_arp_bank'],struct.pack('>I',arpbank))
 six()
 refs=[(60,0,1,0x2545f491) for _ in range(6)]
 for now in (1080000,2160000,3240000):
  assert call('ml_repeat_service',BANK,pattern,STATE,now,1)==6
  packets=[take() for _ in range(12)]
  for lane in range(6):
   if lane==5:note=72
   else:note,refs[lane]=reference(refs[lane],(60,64,67),lane,1)
   assert packets[lane*2+1]==((0x96+lane)<<24)|(note<<16)|0x6403
   count,last,pos,direction,seed=struct.unpack('>IIIiI',u.mem_read(arpbank+lane*40+8,20))
   assert count==3 and (last,pos,direction,seed)==refs[lane]
  assert take()==0
 assert bytes(u.mem_read(arpbank-4,4))==b'ABCD' and bytes(u.mem_read(arpbank+240,4))==b'EFGH'
 call('ml_repeat_cancel_all',BANK,STATE)
 assert len([take() for _ in range(6)])==6 and take()==0
 # Mode corrompu et octave invalide annulent, au lieu de retenir une note.
 for offset,value in ((0,6),(4,0),(4,5),(8,13)):
  six();u.mem_write(arpbank,struct.pack('>2I',0,1))
  u.mem_write(arpbank+offset,struct.pack('>I',value))
  assert call('ml_repeat_service',BANK,pattern,STATE,1080000,1)==5
  assert u.mem_read(STATE,4)==bytes(4) and take()==0x86480003
  while take():pass
  u.mem_write(arpbank+8,struct.pack('>I',3))
  call('ml_repeat_cancel_all',BANK,STATE)
  while take():pass
 u.mem_write(symbols['ml_repeat_arp_bank'],bytes(4))
 print('ok : six arpèges dans le vrai service, modes indépendants, Note Off anciens, réglages invalides annulés')
 # Deux propriétaires explicites : aucun échange de global pour le live.
 otherbank=0x9300c000;otherstate=0x9300c100;otherruntime=0x9300c200
 for pointer,mode,notes in ((arpbank,0,(60,64)),(otherbank,1,(70,74))):
  call('ml_arp_bank_init',pointer);u.mem_write(pointer,struct.pack('>I',mode))
  for note in notes:call('ml_arp_held',pointer+8,note,1)
 u.mem_write(STATE,bytes(120));state(packet=0x963c6403)
 assert call('ml_repeat_service_with_arp',BANK,pattern,STATE,100,1,arpbank)==1
 assert take()==0x96406403 and take()==0
 firststate=bytes(u.mem_read(arpbank,240));firstruntime=bytes(u.mem_read(BANK,320))
 u.mem_write(otherstate,bytes(120));u.mem_write(otherruntime,bytes(320))
 assert call('ml_repeat_arm',otherruntime,otherstate,0,0,0x96466403,16,4000000)==1
 assert call('ml_take',otherruntime)==0x96466403
 assert call('ml_repeat_service_with_arp',otherruntime,pattern,otherstate,1080000,1,otherbank)==1
 assert [call('ml_take',otherruntime) for _ in range(2)]==[0x86460003,0x964a6403]
 assert bytes(u.mem_read(arpbank,240))==firststate and bytes(u.mem_read(BANK,320))==firstruntime
 # Changer le pattern du séquenceur efface ses touches, pas celles du live.
 secondstate=bytes(u.mem_read(otherbank,240));secondruntime=bytes(u.mem_read(otherruntime,320))
 u.mem_write(symbols['ml_repeat_arp_bank'],struct.pack('>I',arpbank))
 call('ml_repeat_audio',BANK,pattern,110,1)
 for lane in range(6):
  record=arpbank+lane*40
  assert struct.unpack('>2I',u.mem_read(record,8))==((0 if lane==0 else 5),1)
  assert bytes(u.mem_read(record+8,32))==struct.pack('>5I',0,0,0,1,0x2545f491)+bytes(12)
 assert bytes(u.mem_read(otherbank,240))==secondstate and bytes(u.mem_read(otherruntime,320))==secondruntime
 u.mem_write(symbols['ml_repeat_arp_bank'],bytes(4))
 print('ok : propriétaires clavier/séquenceur distincts, reset de pattern sans toucher au live ni aux modes/Oct')
 # Allocation des réglages par pattern : aucun new depuis l'interruption.
 alloc={'next':0x94000000,'fail':False,'calls':0}
 def new_witness(uc,address,size,user):
  if address!=0x400802e0:return
  assert uc.reg_read(mk.UC_M68K_REG_SR)&0x700==0
  sp=uc.reg_read(mk.UC_M68K_REG_A7)
  assert struct.unpack('>I',uc.mem_read(sp+4,4))[0]==3120
  alloc['calls']+=1;pointer=0 if alloc['fail'] else alloc['next']
  if pointer:alloc['next']+=3120
  ret=struct.unpack('>I',uc.mem_read(sp,4))[0]
  uc.reg_write(mk.UC_M68K_REG_D0,pointer);uc.reg_write(mk.UC_M68K_REG_A7,sp+4);uc.reg_write(mk.UC_M68K_REG_PC,ret)
 hook=u.hook_add(UC_HOOK_CODE,new_witness,begin=0x400802e0,end=0x400802e0)
 assert call('ml_repeat_pattern_lookup',0)==0
 assert call('ml_repeat_pattern_prepare',pattern)==0 and alloc['calls']==0
 for pointer in (0,pattern+1):assert call('ml_repeat_pattern_prepare',pointer,sr=0x2005)==0
 alloc['fail']=True
 assert call('ml_repeat_pattern_prepare',pattern,sr=0x2005)==0
 assert call('ml_repeat_pattern_lookup',pattern)==0
 alloc['fail']=False
 first=call('ml_repeat_pattern_prepare',pattern,sr=0x2005);assert first==0x94000000
 n=alloc['calls'];assert call('ml_repeat_pattern_prepare',pattern,sr=0x2005)==first and alloc['calls']==n
 for lane in range(6):
  record=first+lane*520
  assert bytes(u.mem_read(record,8))==bytes((0,8,0,0,5,1,0,0))
  for step in range(64):assert bytes(u.mem_read(record+8+step*8,8))==bytes((0,0,0,0,0,1,0,0))
 assert call('ml_repeat_lock',first+8,15,1,16)==1
 pointers=[first]
 for index in range(1,96):
  ptr=call('ml_repeat_pattern_prepare',pattern+index*0x10000,sr=0x2005)
  assert ptr and ptr not in pointers;pointers.append(ptr)
  assert bytes(u.mem_read(ptr+8+15*8,8))==bytes((0,0,0,0,0,1,0,0))
 n=alloc['calls'];assert call('ml_repeat_pattern_prepare',pattern+96*0x10000,sr=0x2005)==0
 assert alloc['calls']==n and call('ml_repeat_pattern_lookup',pattern)==first
 assert bytes(u.mem_read(first+8+15*8,8))==bytes((0,16,0,0,0,1,2,0))
 u.hook_del(hook)
 print('ok : 96 extensions privées par pattern, locks isolés, allocation UI seule, échec/réessai et table pleine')
 # Vrai ml_pattern_tick -> locks -> armement -> service arp/retrigger.
 u.mem_write(BANK,bytes(320));u.mem_write(private,bytes(120))
 u.mem_write(symbols['ml_play_pattern'],struct.pack('>I',pattern))
 u.mem_write(symbols['ml_repeat_play_settings'],struct.pack('>I',first))
 u.mem_write(symbols['ml_repeat_arp_bank'],struct.pack('>I',arpbank))
 call('ml_arp_bank_init',arpbank)
 u.mem_write(symbols['ml_clock_durations'],struct.pack('>7I',21600000,10800000,5400000,3600000,2700000,1800000,1350000))
 u.mem_write(0x8000184c,bytes(4));u.mem_write(0x40149310,bytes(4))
 u.mem_write(first,bytes((1,16,0,0,0,2,0,0)))
 u.mem_write(pattern+8,bytes((72,100,1,1)))
 u.mem_write(pattern+12,bytes((72,100,1,0)))
 u.mem_write(pattern+16,bytes((67,100,1,1)))
 assert call('ml_pattern_tick',BANK,pattern,0,0)==1
 assert take()==0x96486403 and take()==0
 assert struct.unpack('>5I',u.mem_read(private,20))==(1,1080000,1080000,6075000,0x96486403)
 assert struct.unpack('>2I',u.mem_read(arpbank,8))==(0,2)
 assert call('ml_repeat_service',BANK,pattern,private,1080000,1)==1
 assert [take(),take()]==[0x86480003,0x96546403]
 # Le repos n'abrège pas Len ; un pas explicitement désactivé revient au stock.
 assert call('ml_pattern_tick',BANK,pattern,0,1)==1 and take()==0
 assert u.mem_read(private,4)==struct.pack('>I',1)
 assert call('ml_repeat_lock',first+8,2,0,0)==1
 assert call('ml_pattern_tick',BANK,pattern,0,2)==1
 assert [take(),take()]==[0x86540003,0x96436403] and take()==0
 assert u.mem_read(private,4)==bytes(4)
 assert call('ml_repeat_service',BANK,pattern,private,2160000,1)==0 and take()==0
 if a.chance:
  # Refus explicite : Off de l'ancienne note, pas de nouvelle note/repeat.
  call('ml_chance_set',first+8,0,0)
  assert call('ml_pattern_tick',BANK,pattern,0,0)==1
  assert take()==0x86430003 and take()==0
  assert u.mem_read(private,4)==bytes(4)
  call('ml_chance_set',first+8,0,100)
  assert call('ml_pattern_tick',BANK,pattern,0,0)==1
  assert take()==0x96486403 and take()==0
  assert u.mem_read(private,4)==struct.pack('>I',1)
  print('ok : chance dans le vrai pattern_tick, refus libère Off, 100 % arme retrigger, aucun On refusé')
 if a.conditions:
  hist=symbols['ml_cond_history'];call('ml_cond_init',hist)
  u.mem_write(first+15,bytes((102,)))
  u.mem_write(symbols['ml_cond_fill'],bytes(4))
  call('ml_pattern_tick',BANK,pattern,0,0)
  assert take()==0x86480003 and take()==0
  u.mem_write(symbols['ml_cond_fill'],struct.pack('>I',1))
  call('ml_pattern_tick',BANK,pattern,0,0)
  assert take()==0x96486403 and take()==0
  u.mem_write(first+15,bytes((104,)))
  call('ml_pattern_tick',BANK,pattern,0,0)
  assert [take(),take()]==[0x86480003,0x96486403] and take()==0
  u.mem_write(first+15,bytes((105,)))
  call('ml_pattern_tick',BANK,pattern,0,0)
  assert take()==0x86480003 and take()==0
  assert call('ml_cond_previous',hist,0)==1
  assert u.mem_read(private,4)==bytes(4)
  call('ml_chance_set',first+8,0,0)
  call('ml_pattern_tick',BANK,pattern,0,0)
  assert take()==0 and call('ml_cond_previous',hist,0)==0
  u.mem_write(first+15,bytes((104,)))
  call('ml_pattern_tick',BANK,pattern,0,0)
  assert take()==0 and call('ml_cond_previous',hist,0)==0
  print('ok : conditions stock pilotent vrai pattern_tick, FILL/PRE/inverse, Off conservés sans On refusé')
 u.mem_write(symbols['ml_repeat_play_settings'],bytes(4));u.mem_write(symbols['ml_repeat_arp_bank'],bytes(4))
 print('ok : vrai pattern_tick -> locks -> retrigger/arp, Len sur repos, lock OFF et retour au chemin MIDI normal')
 print('ok : service six voies, répétitions bornées, mute/stop/pause/changement canal-port sans note résiduelle')
 print('ok : retrigger B compilé, cadence/wrap/retard borné, fin/annulation, file saturée sans Note Off perdu')
if __name__=='__main__':main()
