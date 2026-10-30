"""Selection de trigs : fonctions UIStates natives, vrais evenements et chainage LED.
Tests adaptes de PPPCCC/gialloinfuso MIT, revision43b894bd14f55313cef6381af9a008acec3ed0f1.
"""
from pathlib import Path
import argparse,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_INVALID,m68k_const as mk
from machines.trig_select import upstream as G,common as C
import boot_candidate as bc
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
m=json.loads((args.build/'BUILD.json').read_text());j=m['trig_select'];sy=j['symbols'];TS=j['core_symbols'];G.TS_ON=j['bss'];al=m['direct_jump']['aliases']
IMG=next(args.build.glob('*.syx'));STOCK=args.base;BASE=0x40000400;RET=0x4e000000;STACK=0x4f000000
bc.ROOT=args.output.parent/'native-cache';CACHE={path:bc.boot(path) for path in (IMG,STOCK)}
KEEP=[getattr(mk,'UC_M68K_REG_'+n) for n in ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']]
class Emu:
 def __init__(s,img):
  u=s.u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
  main,mem=CACHE[img];u.mem_map(0x40000000,0x2400000);u.mem_write(BASE,main)
  u.hook_add(UC_HOOK_MEM_INVALID,lambda u,access,at,size,value,data:print('UNMAPPED',hex(at),'PC',hex(u.reg_read(mk.UC_M68K_REG_PC)),flush=True) or False)
  for at,raw in mem:u.mem_map(at,len(raw));u.mem_write(at,raw)
  for at,n in ((0x80000000,0x20000),(RET,0x1000),(0x4e200000,0x100000),(0x4a330000,0x10000),(STACK-0x10000,0x20000),(0x4f020000,0x30000),(0xfc070000,0x1000),(0xfc040000,0x10000)):u.mem_map(at,n)
  s.held=set();s.consumed=[]
 def w32(s,at,v):s.u.mem_write(at,struct.pack('>I',v&0xffffffff))
 def r32(s,at):return int.from_bytes(s.u.mem_read(at,4),'big')
 def r8(s,at):return s.u.mem_read(at,1)[0]
 def w8(s,at,v):s.u.mem_write(at,bytes([v&255]))
 def cstr(s,at):return bytes(s.u.mem_read(at,100)).split(bytes([0]))[0].decode()
 def call(s,entry,*args,count=2000000):
  sp=STACK-0x100;s.u.mem_write(sp,struct.pack('>I',RET)+b''.join(struct.pack('>I',v&0xffffffff) for v in args));s.u.reg_write(mk.UC_M68K_REG_A7,sp)
  for i,r in enumerate(KEEP):s.u.reg_write(r,0xc0de0000+i)
  s.u.emu_start(entry,RET,count=count);assert s.u.reg_read(mk.UC_M68K_REG_PC)==RET,hex(s.u.reg_read(mk.UC_M68K_REG_PC))
  good=s.u.reg_read(mk.UC_M68K_REG_A7)==sp+4 and all(s.u.reg_read(r)==0xc0de0000+i for i,r in enumerate(KEEP))
  return s.u.reg_read(mk.UC_M68K_REG_D0),good
checks=[]
def chk(name,cond):
 print('PASS' if cond else 'FAIL',name,flush=True);assert cond,name;checks.append(name)
e = Emu(IMG); u = e.u
UISB, FAKE, TRKO, VIEW, VVT, OBJ, OVT_ = 0x4F048000, 0x4F049000, 0x4F04A000, 0x4F04B000, 0x4F04B100, 0x4F04C000, 0x4F04C100
EV = 0x4F04D000
u.mem_write(UISB, bytes(0x200)); u.mem_write(UISB + 0x165, b'\1\1')
ST = {n: 0x4E000400 + 0x10 * i for i, n in enumerate(['VT60', 'VT80', 'VT24', 'VT28'])}
S = dict(page=0, length=64, trigs={}, log=[], grid_ret=0x55, locks={}, nudge={}, nv=[{}, {}, {}], orig=[])
sg = lambda v: struct.unpack('>i', struct.pack('>I', v & 0xffffffff))[0]
def mask(): return (e.r32(UISB + 0x15C) << 32) | e.r32(UISB + 0x160)
def steps(): m = mask(); return [i for i in range(64) if m >> i & 1]
def hold(): return e.r8(UISB + 0x164)
def focus(): return sg(e.r32(0x4014924C))

def stub(uu, addr, size, n):
    sp = uu.reg_read(mk.UC_M68K_REG_A7); arg = lambda i: e.r32(sp + 4 + 4 * i)
    r = 0
    if n == 'HELD': r = int(arg(0) in e.held)
    elif n == 'CONSUME': e.consumed.append(arg(0))
    elif n == 'POPUP': S['pop'] = e.cstr(arg(0))
    elif n == 'HEADER': r = S.get('header_object',0)
    elif n == 'TRACKNO': r = S.get('track',0)
    elif n == 'UIS': r = UISB
    elif n == 'PROJ': r = FAKE
    elif n == 'TRK': r = TRKO
    elif n == 'PG_A': r = FAKE + 0x30
    elif n == 'PG_B': r = S['page']
    elif n == 'LEN': r = S['length']
    elif n in ('HAS0', 'HAS1', 'HAS2'): r = int(S['trigs'].get(arg(1)) == int(n[3]))
    elif n == 'NOTIFY': r = 0
    elif n == 'GRID':
        ev = arg(1); S['orig'].append((e.r32(ev + 12), e.r32(ev + 16), mask(), hold())); r = S['grid_ret']
    elif n == 'VT60': r = 0 if (arg(1), arg(2)) in S['locks'] else 0xFFFFFFFF
    elif n == 'VT80': r = OBJ
    elif n == 'VT24': r = S['locks'].get((arg(2), arg(1)), 1111)
    elif n == 'VT28': S['locks'][(arg(3), arg(1))] = sg(arg(2)); S['log'].append(('lock', arg(3), sg(arg(2))))
    elif n == 'PLO':                                      # Original vt[0x74]: relativ je gehaltenem Step
        p, d = arg(1), sg(arg(2))
        for s in steps():
            if (s, p) in S['locks'] or not S.get('nocreate'): S['locks'][(s, p)] = S['locks'].get((s, p), 1000) + d
        r = 1
    elif n == 'NGET': r = S['nudge'].get(arg(1), 0) & 0xff
    elif n == 'NSET': S['nudge'][arg(1)] = sg(arg(2)) if sg(arg(2)) < 128 else sg(arg(2)) - 256
    elif n.startswith('NVG'): r = S['nv'][int(n[3])].get(arg(1), 0xff) & 0xff
    elif n.startswith('NVS'): v = arg(2) & 0xff; S['nv'][int(n[3])][arg(1)] = v if v < 128 else v - 256; S['log'].append(('nv', int(n[3]), arg(1)))
    elif n == 'NVA':                                      # Original 0x400296c4(view, Drehung): relativ je gehaltenem Step
        f = e.r32(arg(0) + 0x68); d = sg(arg(1))
        for s in (steps() if f < 3 else []): S["nv"][f][s] = max(0, min(127, S["nv"][f].get(s, 60) + d))
    for x in (mk.UC_M68K_REG_D1, mk.UC_M68K_REG_A0, mk.UC_M68K_REG_A1): uu.reg_write(x, 0xBAD0BAD0)
    uu.reg_write(mk.UC_M68K_REG_D0, r & 0xffffffff)
    uu.reg_write(mk.UC_M68K_REG_PC, e.r32(sp)); uu.reg_write(mk.UC_M68K_REG_A7, sp + 4)
HOOKS = {G.UIS: 'UIS', G.PROJ: 'PROJ', G.TRK: 'TRK', G.PG_A: 'PG_A', G.PG_B: 'PG_B', G.LEN: 'LEN', G.HAS[0]: 'HAS1',
         G.HAS[1]: 'HAS2', G.HAS[2]: 'HAS0', 0x40069B84: 'NOTIFY', G.GRID_KEY: 'GRID', G.PL_ORIG: 'PLO',
         G.NUD_GET: 'NGET', G.NUD_SET: 'NSET', G.NV_APPLY: 'NVA'}
for i in range(3): HOOKS[G.NV_GET[i]] = 'NVG%d' % i; HOOKS[G.NV_SET[i]] = 'NVS%d' % i
HOOKS.update({a: n for n, a in ST.items()})
HOOKS.update({C.HELD:'HELD',C.CONSUME:'CONSUME',al['fx_notice']:'POPUP',sy['ui_header']:'HEADER'})
HOOKS[0x40012412]='TRACKNO'
for a, n in HOOKS.items(): u.hook_add(UC_HOOK_CODE, stub, begin=a, end=a, user_data=n)
# Trig-Arten: 1 Note-Trig (0x40015c20), 2 Lock-Trig (0x40015c7c), 0 nur P-Locks (0x400158ca)
e.w32(C.TIMER, 1000)

PRESS, HOLD, REL, FPRESS = 0x1, 0x9, 0x10, 0x3
def key(code, flags, held=()):
    e.held = set(held); e.consumed = []; S['orig'] = []
    e.call(0x4007238C, EV, code, flags, 1234, 0x7F)
    d0, good = e.call(e.r32(G.GRID_VT), 0x4F04E000, EV)
    return d0 & 0xff, good, list(e.consumed), list(S['orig'])
def popup():return (2,S['pop'].split()[-1].title(),'Trig','Select')
on = lambda: int(e.r32(G.TS_ON) == G.TS_MAGIC)

chk('vtable GRID = noyau TSK et preference OFF au boot',e.r32(G.GRID_VT)==TS['TSK'] and e.r32(G.TS_ON)==0)
S['trigs'] = {0: 1, 3: 2, 4: 1, 7: 0, 12: 1, 18: 1, 33: 2, 63: 1}
good = True
for junk in (1, 0xFF, 0xFFFFFFFF, 0x5453454D):              # RAM nach dem Einschalten: beliebiger Inhalt -> Modus aus
    e.w32(G.TS_ON, junk); good &= key(20, PRESS)[3] != [] and key(16, PRESS)[3] != []
chk('nach dem Einschalten (TS_ON = Zufall, nicht TSEL): Modus aus, Trig-Tasten ans Original', good)
e.w32(G.TS_ON, 0)
# ---- Modus aus: alles geht ans Original
r = [key(20, PRESS), key(15, PRESS), key(15, PRESS, (13,)), key(9, PRESS, (13,))]
chk('Modus aus: Trig, PAGE, SETTINGS + PAGE, SETTINGS + Taste 9 -> Original, Rueckgabe des Originals, Register ok',
    all(x[0] == 0x55 and x[1] and len(x[3]) == 1 and not x[2] for x in r) and on() == 0)
# ---- TRACK + PAGE: an
d0, g, cons, orig = key(15, PRESS, (2,))
chk('TRACK + PAGE: Modus an, Popup %s, TRACK und PAGE verbraucht %s, Original nicht gerufen' % (popup(), cons),
    on() == 1 and d0 == 1 and g and orig == [] and cons == [2, 15] and popup() == (C.OV_TEXT, 'On', 'Trig', 'Select'))
# ---- Trigs waehlen
res = []
for code, fl in ((16, PRESS), (16, HOLD), (16, REL), (19, PRESS), (19, REL), (23, PRESS), (21, PRESS), (17, PRESS)):
    res.append(key(code, fl))
chk('Trig-Tasten im Modus: Steps 1, 4, 8 (P-Locks) gewaehlt, 6 (leer) und 2 (leer) nicht; Halten/Loslassen verbraucht, '
    'Original nie gerufen (%s)' % steps(), steps() == [0, 3, 7] and all(x[0] == 1 and x[1] and x[3] == [] for x in res))
chk('Halte-Merker gesetzt, Fokus = niedrigster Step (%d)' % focus(), hold() == 1 and focus() == 0)
key(16, PRESS)
chk('nochmal Step 1: abgewaehlt, Fokus -> 4 (%s, %d)' % (steps(), focus()), steps() == [3, 7] and focus() == 3)
S['page'] = 2; key(17, PRESS); S['page'] = 0
chk('Seite 3, Taste 2 -> Step 34 (Lock-Trig) gewaehlt (%s)' % steps(), steps() == [3, 7, 33])
u.mem_write(UISB + 0x166, b'\0'); d0, g, _, orig = key(20, PRESS); u.mem_write(UISB + 0x166, b'\1')
chk('nicht im Grid-Bearbeiten (0x4006b978 = 0): Trig-Taste ans Original', d0 == 0x55 and len(orig) == 1)
# ---- PAGE im Modus: Original mit verdeckter Auswahl
m0, h0 = mask(), hold()
res = [key(15, PRESS), key(15, HOLD), key(15, REL)]
chk('PAGE im Modus (Druecken, Halten, Loslassen): Original sieht keine gehaltenen Steps (%s), danach Auswahl wieder da'
    % [(o[2], o[3]) for x in res for o in x[3]], all(len(x[3]) == 1 and x[3][0][2:] == (0, 0) and x[0] == 0x55 and x[1] for x in res)
    and mask() == m0 and hold() == h0)
# ---- FUNC + PAGE: alle / keine
S['length'] = 64; d0, g, cons, orig = key(15, FPRESS)
chk('FUNC + PAGE: alle waehlbaren Steps (%s), Popup %s, PAGE verbraucht, Original nicht' % (steps(), popup()[1]),
    steps() == sorted(S['trigs']) and popup()[1] == 'All' and cons == [15] and orig == [] and d0 == 1 and g and hold() == 1)
key(15, FPRESS)
chk('FUNC + PAGE nochmal (schon alle): keine (%s), Popup %s, Halte-Merker 0, Fokus -1' % (steps(), popup()[1]),
    steps() == [] and popup()[1] == 'None' and hold() == 0 and focus() == -1)
S['length'] = 16; key(15, FPRESS)
chk('Patternlaenge 16: nur Steps < 16 (%s)' % steps(), steps() == [0, 3, 4, 7, 12])
S['length'] = 200; key(15, FPRESS)
chk('Auswahl teilweise, Laenge 200 (> 64): FUNC + PAGE waehlt den Rest dazu, kein Ueberlauf (%s, %s)' % (steps(), popup()[1]),
    steps() == sorted(S['trigs']) and popup()[1] == 'All')
S['length'] = 64
# ---- andere Tasten im Modus: Original (mit Auswahl, z. B. Locks kopieren / einfuegen)
r = key(9, PRESS | 2)
chk('andere Tasten im Modus (FUNC + Taste 9): Original, sieht die Auswahl', len(r[3]) == 1 and r[3][0][2] == mask() and mask() != 0)
# ---- TRACK + PAGE: aus
d0, g, cons, orig = key(15, PRESS, (2,))
chk('TRACK + PAGE im Modus: aus, Auswahl geloescht, Popup Off, TRACK + PAGE verbraucht',
    on() == 0 and steps() == [] and hold() == 0 and popup()[1] == 'Off' and cons == [2, 15] and orig == [] and d0 == 1 and g)
r = key(16, PRESS)
chk('danach: Trig-Tasten wieder normal (Original)', len(r[3]) == 1 and steps() == [])

# ------------------------------------------------------------------ 2. TSF (Hauptbildschirm, FUNC + PAGE)
def tsf(ts, flags):
    e.w32(G.TS_ON, G.TS_MAGIC if ts else 0x01010101); e.call(0x4007238C, EV, 15, flags, 1, 0x7F)
    sp = STACK - 0x300; u.reg_write(mk.UC_M68K_REG_A7, sp); u.reg_write(mk.UC_M68K_REG_D3, EV)
    u.emu_start(G.TSF_HOOK, G.TSF_HOOK + 10, count=2000)
    return u.reg_read(mk.UC_M68K_REG_D0) & 0xff, u.reg_read(mk.UC_M68K_REG_A7) == sp, u.reg_read(mk.UC_M68K_REG_D3) == EV
chk('TSF: Modus aus -> FUNC-Bit wie Firmware (FUNC + PAGE: %d, PAGE: %d), Stack ok' % (tsf(0, FPRESS)[0], tsf(0, PRESS)[0]),
    tsf(0, FPRESS) == (1, True, True) and tsf(0, PRESS) == (0, True, True))
chk('TSF: Modus an -> 0 (Ereignis geht ans Grid), Stack ok', tsf(1, FPRESS) == (0, True, True))


# LED : le helper slide existant reste exact pour les pas non selectionnes.
es=Emu(STOCK);ledcalls=[]
def ledstub(u,pc,size,data):
 sp=u.reg_read(mk.UC_M68K_REG_A7);ledcalls.append(struct.unpack('>4I',bytes(u.mem_read(sp+4,16))));u.reg_write(mk.UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(mk.UC_M68K_REG_A7,sp+4)
for em in (e,es):
 em.u.hook_add(UC_HOOK_CODE,ledstub,begin=0x40005f86,end=0x40005f86)
 def slide_stub(uu,pc,size,data):
  sp=uu.reg_read(mk.UC_M68K_REG_A7);uu.reg_write(mk.UC_M68K_REG_D0,int(S.get('slide',False)));uu.reg_write(mk.UC_M68K_REG_PC,int.from_bytes(uu.mem_read(sp,4),'big'));uu.reg_write(mk.UC_M68K_REG_A7,sp+4)
 em.u.hook_add(UC_HOOK_CODE,slide_stub,begin=0x400157d6,end=0x400157d6)
 em.w32(0x404a8bdc,0x4f04f800);em.u.mem_write(0x4f04f800,b''.join(struct.pack('>I',100+i) for i in range(16)))
u.mem_write(UISB+0x15c,struct.pack('>II',1<<8,(1<<5)|(1<<17)))
def led(em,step,state,on,timer):
 em.w32(G.TS_ON,G.TS_MAGIC if on else 0);em.w32(C.TIMER,timer);ledcalls.clear();sp=STACK-0x400;em.w32(sp+0x38,(step//16)*16)
 for reg,val in ((mk.UC_M68K_REG_A7,sp),(mk.UC_M68K_REG_D3,step%16),(mk.UC_M68K_REG_A5,state),(mk.UC_M68K_REG_D2,0x4f04f000),(mk.UC_M68K_REG_A3,TRKO)):
  em.u.reg_write(reg,val)
 em.u.emu_start(G.TSL_HOOK,G.TSL_HOOK+10,count=20000)
 assert em.u.reg_read(mk.UC_M68K_REG_PC)==G.TSL_HOOK+10
 assert em.u.reg_read(mk.UC_M68K_REG_A7)==sp
 return ledcalls[:]
for slide in (False,True):
 S['slide']=slide
 for step in (0,5,17,40,63):
  for state in (1,2,3,4):
   ref=led(es,step,state,False,0);assert led(e,step,state,False,0)==ref
   if step not in (5,17,40):assert led(e,step,state,True,0)==ref
for step in (5,17,40):
 assert led(e,step,3,True,0)==[(0x4f04f000,100+step%16,1,0x404a8cb8)]
 assert led(e,step,3,True,1<<24)==[(0x4f04f000,100+step%16,2,0x404a8cb8)]
chk('LED : OFF/non-selectionnes exacts, selection clignote a4Hz, pile conservee',True)
# Les pas hors Page Len ne sont pas selectionnables, y compris ALL.
S['header_object']=0x4f04e000
u.mem_write(0x4f04e000,struct.pack('>I',0x4f04e100));e.w32(0x4f04e100+40,0x4f04e200)
u.mem_write(0x4f04e200,b'\x20\x3c'+struct.pack('>I',0x4f04e400)+b'\x4e\x75')
u.mem_write(0x4f04e400+60,bytes([80,76,4,251]))
e.w32(G.TS_ON,G.TS_MAGIC);e.call(G.U_CLR,UISB);S['trigs']={0:1,3:1,4:1,16:1,19:1,20:1};S['length']=32;key(15,FPRESS)
chk('Page Len4 : ALL exclut les pas caches sur chaque page',steps()==[0,3,16,19])
e.call(G.U_CLR,UISB);S['track']=2;S['trigs']={0:1,1:1,2:1,16:1,17:1,18:1}
e.w8(0x4f04e400+25,1);e.w8(0x4f04e400+31,0xa1);key(15,FPRESS)
chk('Page Len TRK2 : ALL suit la longueur propre a la piste choisie',steps()==[0,1,16,17])
# Tous les DSP et les handlers d'edition existants sont byte-identiques en RAM.
_,base_mem=CACHE[STOCK];_,test_mem=CACHE[IMG];assert base_mem[0][0]==test_mem[0][0]
oldram,newram=base_mem[0][1],test_mem[0][1];start=j['code']-base_mem[0][0];end=start+j['code_bytes']
assert oldram[:start]==newram[:start] and oldram[end:]==newram[end:]
chk('RAM runtime : DSP, Genie, Page Len et handlers existants inchanges hors du module ajoute',True)
args.output.write_text(json.dumps(dict(sha256=m['sha256'],checks=checks,hardware_tested=False),indent=2)+'\n')
