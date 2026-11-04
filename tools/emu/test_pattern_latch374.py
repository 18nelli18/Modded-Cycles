"""Selecteur natif : taps, maintien, fin de chaine et observateur UI preserves."""
from pathlib import Path
import argparse,json,struct,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig,EVENT
from pattern_latch374 import apply,BASE,SITE,BSS,END
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as C
p=argparse.ArgumentParser(description=__doc__)
for key in ('build','capture','output'):p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());n=bytearray((a.capture/'native.bin').read_bytes());rt=bytearray((a.capture/'runtime.bin').read_bytes())
module=m.get('pattern_latch374') or apply(m,n,rt,a.output.parent/'module')
r=Rig(bytes(n),{'writes':[]},{'writes':[],'symbols':{}});u=r.u
u.mem_map(BASE,0x300000);u.mem_write(BASE,bytes(rt));u.mem_map(0xfc070000,0x1000)
s=module['symbols'];VIEW=0x41008000;UI=0x41009000;OBSERVER=0x4100a000;PTR=0x4100a100;POP=0x4100b000;PVT=0x4100b200
state=dict(now=100000000,mods=set(),popup=0,bank=0,closes=0);cues=[]
def install(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
def close(args):state['popup']=0;state['closes']+=1;return 0
def open_popup(args):state['popup']=1;return 0
for at,fn in [(0x4007240c,lambda a:r.r32(a[0]+12)),(0x400cf9a8,lambda a:UI),
 (0x40069b84,lambda a:0),(0x4002063c,close),(0x40020730,open_popup),
 (0x4007faf4,lambda a:int(a[0] in state['mods'])),(0x400cfd0e,lambda a:PTR),
 (0x4006a96c,lambda a:0),(0x4006bbb0,lambda a:state.update(bank=a[1]) or 0),
 (0x4006bba6,lambda a:state['bank']),(0x400760ba,lambda a:0),
 (0x4001fde0,lambda a:0),(0x4002037c,lambda a:cues.append(a[1]) or 0),
 (0x40075f2e,lambda a:0),
 (0x40075f3c,lambda a:0)]:install(at,fn)
def reset():
 u.mem_write(BSS,bytes(END-BSS));u.mem_write(VIEW,bytes(512));u.mem_write(UI,bytes(512));u.mem_write(UI+0x184,b'\1');r.w32(VIEW+0x74,0xffffffff);r.w32(VIEW+0x78,0xffffffff);r.w32(OBSERVER,PTR);r.w32(PTR,VIEW)
 state.update(now=100000000,mods=set(),popup=0,bank=0,closes=0);r.w32(POP,PVT);r.w32(PVT+0x28,0x9300d600)
install(0x9300d600,close)
def event(code,flags,advance=1000000):
 state['now']=(state['now']+advance)&0xffffffff;r.w32(0xfc07000c,state['now']);u.mem_write(EVENT,struct.pack('>6I',0x400fc20c,0,0,code,flags,0))
 if state['popup']:
  result=r.call(0x40024af0,POP,EVENT)
  if result&255:return result
 return r.call(SITE,VIEW,EVENT)
def tap(code=3):event(code,1);event(code,16)
def latched():return r.r32(s['pl_latched'])
def mode():return u.mem_read(UI+0x185,1)[0]
rows=[]
reset();tap();assert mode() and not latched() and state['popup'];rows.append('single tap uses native popup')
event(3,1);assert latched() and mode() and u.mem_read(VIEW+0x90,1)==b'\1';event(3,16);assert latched() and u.mem_read(VIEW+0x90,1)==b'\1'
# Le vrai tick TimedPopup ne doit plus decrementer jusqu a fermeture.
r.w32(POP+0x60,2);r.w32(POP+0x64,1)
for _ in range(1200):r.call(s['pl_popup_frame'],POP)
assert r.r32(POP+0x60)==2 and state['popup'] and latched() and mode();rows.append('1200 native popup frames preserve countdown while latched')
# L observateur natif ne ferme pas la selection, meme apres le delai usuel.
r.w32(0xfc07000c,state['now']+300000000);r.call(0x400206c6,OBSERVER);assert mode() and latched();rows.append('double tap survives native observer/timeout interval')
# Le vrai gate RL garde la selection lorsque held local=1.
u.reg_write(C.UC_M68K_REG_A2,VIEW);u.reg_write(C.UC_M68K_REG_A3,0x400cf9a8)
seen=[]
def boundary(uc,at,size,data):seen.append(at);uc.emu_stop()
h=u.hook_add(UC_HOOK_CODE,boundary,begin=0x40020e04,end=0x40020e04)
u.reg_write(C.UC_M68K_REG_A7,0x93008000);u.emu_start(0x40020df0,0x40020e06,count=1000);u.hook_del(h);assert seen and mode();rows.append('native last-trig release keeps selector active')
# La popup peut rester au-dessus du selecteur sur le vrai controleur.
state['popup']=1;cues.clear()
for key in (20,21,22):
 event(key,1);event(key,16);assert latched() and mode() and state['popup']
assert cues==[4,5,6],cues;rows.append('popup forwards repeated pattern selections without closing latch')
tap(12);assert not latched() and not mode() and u.mem_read(VIEW+0x90,1)==b'\0';rows.append('BACK closes and consumes its pair')
state['popup']=1;r.w32(POP+0x60,2);r.call(s['pl_popup_frame'],POP);r.call(s['pl_popup_frame'],POP);assert r.r32(POP+0x60)==0 and not state['popup'];rows.append('native popup countdown resumes when unlatched')
reset();tap();tap();assert latched();tap();assert not latched() and not mode();rows.append('third PATTERN closes and consumes its pair')
reset();tap();event(3,1,60000000);event(3,16);assert not latched();rows.append('slow double tap stays native')
reset();event(3,1);event(3,16,60000000);tap();assert not latched();rows.append('held PATTERN does not arm')
for modifier in (1,2,4,5,13):
 reset();state['mods']={modifier};tap();tap();assert not latched()
rows.append('modified taps do not latch')
reset();tap();event(3,9);event(3,16);tap();assert not latched();rows.append('repeat cancels double tap')
reset();tap();event(8,1);event(8,16);tap();assert not latched();rows.append('other key cancels double tap')
reset();state['now']=0xffffff00;tap();tap();assert latched();rows.append('timer wrap handled')
a.output.write_text(json.dumps(dict(checks=rows,module=module,native_selection_handler=True,native_observer=True,native_last_trig_gate=True,no_audio_or_physical_key_hooks=True,hardware_tested=False),indent=2)+'\n')
print('PASS',len(rows),'PATTERN latch native/UI checks')
