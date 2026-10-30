"""Sequenceur reel et controles PPPCCC adaptes au socle Supermodel. Note204.
Tests derives de PPPCCC/gialloinfuso MIT, revision43b894bd14f55313cef6381af9a008acec3ed0f1.
"""
from pathlib import Path
import argparse,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_INVALID,m68k_const as mk
from machines.direct_jump import upstream as G
import boot_candidate as bc
from gen_governor_recovery_test import read
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
m=json.loads((a.build/'BUILD.json').read_text());j=m['direct_jump'];sy=j['symbols'];S={**j['core_symbols']};S.update(REQ=j['code'],FIX=j['code']+4,SAVE=j['code']+8,KEEP=j['code']+14)
IMG=next(a.build.glob('*.syx'));STOCK=a.base;BASE=0x40000400;RET=0x4e000000;STACK=0x4f000000
bc.ROOT=a.output.parent/'native-cache'
CACHE={path:bc.boot(path) for path in (IMG,STOCK)}
KEEP=[getattr(mk,'UC_M68K_REG_'+n) for n in ['D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6']]
class Emu:
 def __init__(s,img):
  u=s.u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY);u.reg_write(mk.UC_M68K_REG_SR,0x2700)
  main,mem=CACHE[img];u.mem_map(0x40000000,0x2000000);u.mem_write(BASE,main)
  u.hook_add(UC_HOOK_MEM_INVALID,lambda u,access,at,size,value,data:print('UNMAPPED',hex(at),'PC',hex(u.reg_read(mk.UC_M68K_REG_PC)),flush=True) or False)
  for at,raw in mem:u.mem_map(at,len(raw));u.mem_write(at,raw)
  for at,n in ((0x42000000,0x330000),(0x42340000,0xc0000)):u.mem_map(at,n)
  for at,n in ((0x80000000,0x20000),(RET,0x1000),(0x4e200000,0x100000),(0x4a330000,0x10000),(STACK-0x10000,0x20000),(0x4f020000,0x30000),(0xfc070000,0x1000),(0xfc040000,0x10000)):u.mem_map(at,n)
  if img==IMG:s.w32(j['bss'],1)
 def w32(s,at,v):s.u.mem_write(at,struct.pack('>I',v&0xffffffff))
 def r32(s,at):return int.from_bytes(s.u.mem_read(at,4),'big')
 def r8(s,at):return s.u.mem_read(at,1)[0]
 def w8(s,at,v):s.u.mem_write(at,bytes([v&255]))
 def call(s,entry,*args,count=2000000,regs=None,stop=None):
  sp=STACK-0x100;s.u.mem_write(sp,struct.pack('>I',RET)+b''.join(struct.pack('>I',v&0xffffffff) for v in args));s.u.reg_write(mk.UC_M68K_REG_A7,sp)
  for i,r in enumerate(KEEP):s.u.reg_write(r,0xc0de0000+i)
  for r,v in (regs or {}).items():s.u.reg_write(r,v)
  s.u.emu_start(entry,stop or RET,count=count)
  assert s.u.reg_read(mk.UC_M68K_REG_PC)==(stop or RET),hex(s.u.reg_read(mk.UC_M68K_REG_PC))
  good=s.u.reg_read(mk.UC_M68K_REG_A7)==sp+4 and all(s.u.reg_read(r)==0xc0de0000+i for i,r in enumerate(KEEP) if r not in (regs or {}))
  return s.u.reg_read(mk.UC_M68K_REG_D0),good
class C:
 jmp=staticmethod(lambda at:b'\\x4e\\xf9'+struct.pack('>I',at))
PAT0,PSZ,KIT0,KSZ=0x406fa040,0x77f6,0x409c9c80,0x1bb6
ISR,ISR_END=0x40054c1e,0x40055a7a
STUBS=[0x40091770,0x40091eb6,0x4009203c,0x40082512,0x40001fba,0x40091658,0x40091fdc,0x40091f82,0x40058b5e,0x4005950e,0x40058bb4,0x40058c10,0x4009162a,G.MIDI_PC]
CH=0x4f040000
checks=[]
def chk(name,cond):
 print('PASS' if cond else 'FAIL',name,flush=True);assert cond,name;checks.append(name)
class Seq:
    def __init__(s, img):
        e = s.e = Emu(img); u = e.u
        s.calls = []
        def stub(u_, a, z, _):
            sp = u_.reg_read(mk.UC_M68K_REG_A7)
            s.calls.append((a, e.r32(sp + 4)))
            u_.reg_write(mk.UC_M68K_REG_D0, 0)
            u_.reg_write(mk.UC_M68K_REG_PC, e.r32(sp)); u_.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        for t in STUBS:
            u.hook_add(UC_HOOK_CODE, stub, begin=t, end=t)
    def pat(s, i): return PAT0 + PSZ * i
    def kit(s, i): return KIT0 + KSZ * i
    def setpat(s, i, length=16, speed=2, per_track=None):
        p = s.pat(i); u = s.e.u
        u.mem_write(p + 0x77C6, struct.pack('>h', length)); u.mem_write(p + 0x77C8, struct.pack('>h', length if per_track else 1))
        u.mem_write(p + 0x77CB, bytes([1 if per_track else 0])); u.mem_write(p + 0x77CC, bytes([speed]))
        u.mem_write(p + 0x77CA, bytes([0xFF]))
        for t in range(6):
            ln, sp = (per_track[t] if per_track else (length, speed))
            u.mem_write(p + 722 * t + 0x2C9, struct.pack('>h', ln)); u.mem_write(p + 722 * t + 0x2CB, bytes([sp]))
    def chain(s, i):
        s.e.u.mem_write(CH, struct.pack('>II', s.pat(i), s.kit(i))); s.e.call(0x40055CD6, CH, 1, count=2000000)
    def start(s):
        s.chain(0); s.e.w32(0x4230877C, 1); s.e.call(0x400542DC, count=2000000)
    def isr(s):
        s.e.u.reg_write(mk.UC_M68K_REG_A7, STACK - 0x400)
        s.e.u.emu_start(ISR, ISR_END, count=2000000)
    def snap(s):
        u = s.e.u
        return bytes(u.mem_read(0x40A78600, 0x330)) + bytes(u.mem_read(0x422FF160, 0x60)) + bytes(u.mem_read(0x42308780, 0x20))
    def st(s):
        r = s.e
        return dict(pat=r.r32(0x40A7887C), m40=r.r32(0x40A78840), tick=r.r8(0x40A78844),
                    pos=[r.r8(0x40A78860 + t) for t in range(6)], cur=[r.r8(0x40A7886C + t) for t in range(6)],
                    tp=[(r.r32(0x42308780 + 4 * t) - PAT0) // PSZ for t in range(6)])


def steps(s, n, at=None, to=1):
    """n Step-Grenzen (Tick 0) beobachten; bei Grenze 'at' Direct Jump auf Pattern 'to' anfordern (wie DJK)."""
    out = []; last = None; guard = 0
    while len(out) < n and guard < 100000:
        s.isr(); guard += 1; x = s.st()
        key = (x['pat'], tuple(x['cur']), x['m40'])
        if x['tick'] == 0 and key != last:
            last = key
            out.append(((x['pat'] - PAT0) // PSZ, x['m40'], x['cur'][:], x['pos'][:], x['tp'][:]))
            if at is not None and len(out) == at:
                s.chain(to); s.e.w32(S['REQ'], G.MAGIC)
    return out


# ---------------- 1 ohne Anforderung: bitgleich zum Original
def compare(setup, n=1500, cue_at=200):
    a, b = Seq(STOCK), Seq(IMG)
    for s in (a, b): setup(s); s.start()
    bad = 0
    for i in range(n):
        if i == cue_at: a.chain(1); b.chain(1)
        a.isr(); b.isr()
        if a.snap() != b.snap(): bad += 1
    return bad, (b.st()['pat'] - PAT0) // PSZ
for nm, setup in (('16 / 12 Steps', lambda s: (s.setpat(0, 16), s.setpat(1, 12))),
                  ('Per-Track', lambda s: (s.setpat(0, 16, per_track=[(16, 2), (7, 0), (12, 3), (16, 2), (5, 4), (16, 2)]),
                                           s.setpat(1, 12, per_track=[(12, 2), (9, 2), (3, 0), (12, 2), (12, 2), (16, 1)])))):
    bad, p = compare(setup)
    chk('ohne Direct Jump (%s, normaler Wechsel): Sequencer-Zustand nach 1500 Ticks bitgleich zum Original (%d Abweichungen), '
        'Pattern 1 erreicht' % (nm, bad), bad == 0 and p == 1)

# ---------------- 2 Direct Jump, normaler Modus
bad = []
for at in (3, 6, 10, 13, 15, 16, 17):
    s = Seq(IMG); s.setpat(0, 16); s.setpat(1, 12); s.start(); s.calls.clear()
    o = steps(s, at + 30, at=at)
    sw = next(i for i, r in enumerate(o) if r[0] == 1)
    seq = [r[2][0] for r in o]
    okc = all(seq[i + 1] == (seq[i] + 1) % (16 if o[i + 1][0] == 0 and o[i][0] == 0 else 12 if o[i][0] == 1 else 999) or
              (o[i][0] == 0 and o[i + 1][0] == 1) for i in range(len(o) - 1))
    first_new = o[sw + 1][2][0]
    cont = first_new == ((o[sw][2][0] + 1) % 16) % 12        # alte Position (modulo 16) modulo der neuen Laenge
    allt = all(o[i][2] == [o[i][2][0]] * 6 for i in range(len(o)))
    pcs = [c for c in s.calls if c[0] == G.MIDI_PC]
    if not (sw - at <= 2 and okc and cont and allt and (G.MIDI_PC, s.pat(1)) in pcs and max(seq[sw + 1:]) < 12):
        bad.append((at, sw, seq[max(0, sw - 3):sw + 5], pcs))
    if at == 6: ex = seq[at - 2:at + 6]
chk('Direct Jump 16 -> 12 an Step 3/6/10/13/15/16/17: Wechsel nach <= 2 Steps, alle Spuren lueckenlos weiter (z. B. %s), '
    'modulo 12, MIDI-Programmwechsel beim Sprung %s' % (ex, bad[:1]), not bad)
s = Seq(IMG); s.setpat(0, 16); s.setpat(1, 12); s.start()
o = steps(s, 60, at=8)
chk('danach: REQ und FIX geloescht, weiter normal im neuen Pattern (0..11)',
    s.e.r32(S['REQ']) == 0 and s.e.r32(S['FIX']) == 0 and [r[2][0] for r in o[-12:]] == sorted([r[2][0] for r in o[-12:]], key=lambda v: (v - o[-12][2][0]) % 12))
s = Seq(IMG); s.setpat(0, 16); s.setpat(1, 12); s.start()
o = steps(s, 30, at=5, to=0)
chk('Direct Jump auf dasselbe Pattern: spielt einfach weiter', [r[2][0] for r in o] == [(o[0][2][0] + i) % 16 for i in range(30)])

# ---------------- 3 Per-Track-Modus
bad = []
cases = [([(16, 2), (7, 0), (12, 3), (16, 2), (5, 4), (16, 2)], None, 12),
         (None, [(12, 2), (5, 4), (3, 0), (12, 2), (9, 2), (16, 1)], 16),
         ([(16, 2), (7, 0), (12, 3), (16, 2), (5, 4), (16, 2)], [(12, 2), (5, 4), (3, 0), (12, 2), (9, 2), (16, 1)], 12)]
for c0, c1, l1 in cases:
    for at in (4, 9, 14):
        s = Seq(IMG); s.setpat(0, 16, per_track=c0); s.setpat(1, l1, per_track=c1); s.start()
        o = steps(s, at + 40, at=at)
        sw = next(i for i, r in enumerate(o) if r[0] == 1)
        lens = [(c1[t][0] if c1 else l1) for t in range(6)]
        out = [(i, t, r[2][t]) for i, r in enumerate(o) for t in range(6) if r[4][t] == 1 and r[2][t] >= lens[t]]
        same = [t for t in range(6) if (c0[t][1] if c0 else 2) == 2 and (c1[t][1] if c1 else 2) == 2]
        contd = True
        for t in same:
            i1 = next(i for i, r in enumerate(o) if r[4][t] == 1)
            l0 = c0[t][0] if c0 else 16
            contd &= o[i1][2][t] == ((o[i1 - 1][2][t] + 1) % l0) % lens[t] and i1 - at <= 3
        if out or sw - at > 2 or not contd: bad.append((c0 is None, c1 is None, at, sw - at, out[:3], contd))
chk('Per-Track (alt / neu / beide, verschiedene Laengen und Tempi): kein Step ausserhalb der Spurlaenge, Spuren mit '
    'Tempo 1x lueckenlos %s' % bad[:2], not bad)

# ---------------- 4 DJK (Pattern-Auswahl)
e = Emu(IMG); rec = []
def st_(a_):
    def f(u, a, z, _):
        sp = u.reg_read(mk.UC_M68K_REG_A7); rec.append((a_, e.r32(sp + 4), e.r32(sp + 8)))
        u.reg_write(mk.UC_M68K_REG_PC, e.r32(sp)); u.reg_write(mk.UC_M68K_REG_A7, sp + 4)
    return f
for a_ in (0x40012518, 0x40076082, 0x4000EB90, 0x400CF866):
    e.u.hook_add(UC_HOOK_CODE, st_(a_), begin=a_, end=a_)
VIEW, EV, FR = 0x4F043000, 0x4F043200, 0x4F0434F0
def djk(func, playing, idx=21):
    e.w32(G.PLAYING, 1 if playing else 0); e.w32(S['REQ'], 0); e.w32(0x40A78638, 0)
    e.w32(EV + 0x10, 1 | (2 if func else 0)); e.w32(FR - 0x30, idx)
    sp = STACK - 0x500; e.u.reg_write(mk.UC_M68K_REG_A7, sp)
    e.u.reg_write(mk.UC_M68K_REG_A2, VIEW); e.u.reg_write(mk.UC_M68K_REG_A6, FR); e.u.reg_write(mk.UC_M68K_REG_D2, EV)
    rec.clear(); hit = []
    hs = [e.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _, t=t: (hit.append(t), u.emu_stop()), begin=t, end=t)
          for t in (G.K_NORMAL, G.K_DONE)]
    e.u.emu_start(S['DJK'], 0, count=200000)
    for h in hs: e.u.hook_del(h)
    ch = struct.unpack('>II', bytes(e.u.mem_read(0x40A7863C, 8))) if e.r32(0x40A78638) else None
    return hit, e.r32(S['REQ']) == G.MAGIC, ch, e.u.reg_read(mk.UC_M68K_REG_A7) == sp, e.u.reg_read(mk.UC_M68K_REG_D2) == EV
r = djk(False, True)
chk('TRIG ohne FUNC: Firmware-Weg 0x40020c94, keine Anforderung', r[0] == [G.K_NORMAL] and not r[1] and r[3] and r[4])
r = djk(True, False)
chk('FUNC + TRIG bei gestopptem Sequencer: wie TRIG', r[0] == [G.K_NORMAL] and not r[1] and r[3])
r = djk(True, True, idx=21)
chk('FUNC + TRIG laeuft: echte Pattern-Wahl (Kette = Pattern 21 + Kit 21), Anforderung, Ende 0x40020d5e',
    r[0] == [G.K_DONE] and r[1] and r[2] == (PAT0 + PSZ * 21, KIT0 + KSZ * 21) and r[3] and
    any(x[0] == 0x40012518 and x[2] == 21 for x in rec))


REF=STOCK
FVT,CLOSE,SEL=0x4f044000,0x4f045000,0x4f045010
UIP=0x4f046000
# ---------------- 6 FUNC im Auswahl-Fenster (nach PATTERN; echter Tasten-Handler 0x40024af0)
FVT, CLOSE, SEL = 0x4F044000, 0x4F045000, 0x4F045010
def ov_key(img, code, flags):
    e6 = Emu(img); got = []
    e6.u.mem_write(0x4E000F00, b'\x4e\x75' * 8)
    for a_ in (CLOSE, SEL):
        e6.u.mem_write(a_, b'\x4e\x75')
        e6.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _, a_=a_: got.append(a_), begin=a_, end=a_)
    for a_ in (0x4006BB50, 0x4006BB22, 0x400CF9A8):
        e6.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _, a_=a_: (got.append(a_) if a_ != 0x400CF9A8 else None, u.reg_write(mk.UC_M68K_REG_PC, e6.r32(u.reg_read(mk.UC_M68K_REG_A7))),
                                                         u.reg_write(mk.UC_M68K_REG_A7, u.reg_read(mk.UC_M68K_REG_A7) + 4)), begin=a_, end=a_)
    e6.w32(FVT + 0x28, CLOSE); e6.w32(FVT + 0x48, SEL); e6.w32(VIEW, FVT)
    e6.w32(EV + 0x0C, code); e6.w32(EV + 0x10, flags)
    hit = []
    e6.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _: (hit.append(a), u.emu_stop()), begin=0x40074A2C, end=0x40074A2C)
    d0, good = e6.call(0x40024AF0, VIEW, EV, count=200000)
    ui = e6.r32(0x400CF9A8) if False else None
    return got, (d0 & 0xFF) if not hit else 'weiter', good or bool(hit)
for fl, nm in ((1, 'Druecken'), (0, 'Loslassen')):
    o0, o1 = ov_key(STOCK, 1, fl), ov_key(IMG, 1, fl)
    chk('Fenster, FUNC %s: Original schliesst (%s); Patch: angenommen, nichts geschlossen (%s)' % (nm, o0[:2], o1[:2]),
        CLOSE in o0[0] and o1[0] == [] and o1[1] == 1 and o1[2])
o0, o1 = ov_key(STOCK, 21, 1 | 2), ov_key(IMG, 21, 1 | 2)
chk('Fenster, FUNC + TRIG: wie Original (Auswahl, Fenster zu, Ereignis weiter an die Pattern-Auswahl) %s' % (o1[:2],),
    o0 == o1 and o1[0] == [SEL, CLOSE] and o1[1] == 0)
o0, o1 = ov_key(STOCK, 3, 1), ov_key(IMG, 3, 1)
chk('Fenster, PATTERN: wie Original (schliesst)', o0 == o1 and CLOSE in o1[0])
# ---------------- 8 Auswahl bleibt nach dem Sprung offen
def ov2(img, code, flags, playing):
    e8 = Emu(img); got = []
    for a_ in (CLOSE, SEL):
        e8.u.mem_write(a_, b'\x4e\x75')
        e8.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _, a_=a_: got.append(a_), begin=a_, end=a_)
    e8.w32(FVT + 0x28, CLOSE); e8.w32(FVT + 0x48, SEL); e8.w32(VIEW, FVT); e8.w32(G.PLAYING, playing)
    e8.w32(EV + 0x0C, code); e8.w32(EV + 0x10, flags)
    d0, good = e8.call(0x40024AF0, VIEW, EV, count=200000)
    return got, d0 & 0xFF, good
r = ov2(IMG, 21, 1 | 2, 1)
chk('Fenster, FUNC + TRIG bei laufendem Sequencer: kein Abschluss, nicht geschlossen, Ereignis weiter (0) %s' % (r,),
    r[0] == [] and r[1] == 0 and r[2])
for fl, pl, nm in ((1, 1, 'TRIG'), (1 | 2, 0, 'FUNC + TRIG gestoppt')):
    r0, r1 = ov2(REF, 21, fl, pl), ov2(IMG, 21, fl, pl)
    chk('Fenster, %s: wie ohne direct-jump (Abschluss, schliessen) %s' % (nm, r1[:2]), r0 == r1 and r1[0] == [SEL, CLOSE])
# ganze Folge in der Pattern-Auswahl: FUNC + TRIG druecken, loslassen -> Modus bleibt; TRIG druecken, loslassen -> Modus aus
def seqv(img, steps_):
    e9 = Emu(img)
    e9.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _: (u.reg_write(mk.UC_M68K_REG_D0, UIP),
                  u.reg_write(mk.UC_M68K_REG_PC, e9.r32(u.reg_read(mk.UC_M68K_REG_A7))),
                  u.reg_write(mk.UC_M68K_REG_A7, u.reg_read(mk.UC_M68K_REG_A7) + 4)), begin=0x400CF9A8, end=0x400CF9A8)
    for a_ in (0x40012518, 0x40076082, 0x4000EB90, 0x4001FDE0, 0x400CF866):
        e9.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _: (u.reg_write(mk.UC_M68K_REG_PC, e9.r32(u.reg_read(mk.UC_M68K_REG_A7))),
                      u.reg_write(mk.UC_M68K_REG_A7, u.reg_read(mk.UC_M68K_REG_A7) + 4)), begin=a_, end=a_)
    e9.w8(UIP + 0x185, 1); e9.w32(G.PLAYING, 1); e9.u.mem_write(VIEW, bytes(0xA0)); e9.w32(VIEW + 0x74, 0xFFFFFFFF)
    out = []
    for code, fl in steps_:
        e9.w32(EV + 0x0C, code); e9.w32(EV + 0x10, fl)
        try: e9.call(0x40020A7A, VIEW, EV, count=200000)
        except Exception as x: out.append('Fehler'); continue
        out.append((e9.r8(UIP + 0x185), e9.r32(S['REQ']) == G.MAGIC))
    return out
o = seqv(IMG, [(21, 1 | 2), (21, 0 | 2), (22, 1 | 2), (22, 0 | 2)])
chk('Pattern-Auswahl: FUNC + TRIG, loslassen, nochmal FUNC + TRIG, loslassen: Auswahl bleibt an %s' % o,
    [x[0] for x in o] == [1, 1, 1, 1] and o[0][1])
o0 = seqv(REF, [(21, 1), (21, 0)]); o1 = seqv(IMG, [(21, 1), (21, 0)])
chk('Pattern-Auswahl: TRIG, loslassen (normaler Wechsel): Auswahl aus wie ohne direct-jump %s %s' % (o0, o1),
    [x[0] for x in o0] == [x[0] for x in o1] and o1[-1][0] == 0)
o = seqv(IMG, [(21, 1 | 2), (21, 0 | 2), (23, 1), (23, 0)])
chk('nach Direct Jumps ein normaler TRIG: Auswahl danach aus %s' % o, o[-1][0] == 0)
# ---------------- 9 ganze Folge wie am Geraet: Fenster zuerst (0x40024af0), bei Rueckgabe 0 die Pattern-Auswahl (0x40020a7a), nach
# jedem Ereignis der UIStates-Beobachter der Auswahl (0x400206c6, laeuft bei jeder Aenderung von UIStates): er schaltet den
# Auswahlmodus aus und schliesst das Fenster, wenn PATTERN nicht gehalten (+0x90) und die Auswahl nicht "wartend" ist (+0x7c;
# TRIG gedrueckt loescht das). Abschluss-Rueckruf des Fensters = echte 0x400200ee (Modus aus, +0x7c = 0).
OVL, FVT9, CLOSE9, SELC, FUN = 0x4F043800, 0x4F044400, 0x4F045100, 0x4F045200, 0x4F043600   # FUN: std::function-Speicher -> Zelle -> Auswahl
def tap_seq(img, steps_, held_pattern=False):
    e = Emu(img); log = []
    def ret(u):
        u.reg_write(mk.UC_M68K_REG_PC, e.r32(u.reg_read(mk.UC_M68K_REG_A7))); u.reg_write(mk.UC_M68K_REG_A7, u.reg_read(mk.UC_M68K_REG_A7) + 4)
    e.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _: (u.reg_write(mk.UC_M68K_REG_D0, UIP), ret(u)), begin=0x400CF9A8, end=0x400CF9A8)
    for a_ in (0x40012518, 0x40076082, 0x4000EB90, 0x4001FDE0, 0x400CF866, 0x400760BA, 0x40020730):
        e.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _, a_=a_: (log.append(a_), ret(u)), begin=a_, end=a_)
    for a_, v in ((0x400CFD0E, 0x4F047000), (0x4006A96C, 0)):                     # Projekt-Objekt, aktuelles Pattern (PATTERN gedrueckt)
        e.u.hook_add(UC_HOOK_CODE, lambda u, a, z, _, v=v: (u.reg_write(mk.UC_M68K_REG_D0, v), ret(u)), begin=a_, end=a_)
    st = {'ovl': True}
    def close(u, a, z, _): st['ovl'] = False; ret(u)
    e.u.hook_add(UC_HOOK_CODE, close, begin=CLOSE9, end=CLOSE9)
    e.u.hook_add(UC_HOOK_CODE, close, begin=0x4002063C, end=0x4002063C)           # Beobachter schliesst das Fenster
    e.u.mem_write(SELC, bytes.fromhex('2f3c') + struct.pack('>I', FUN) + bytes.fromhex('4eb9400200ee588f4e75'))
    e.w32(FUN, FUN + 0x10); e.w32(FUN + 0x10, VIEW); e.w32(FVT9 + 0x28, CLOSE9); e.w32(FVT9 + 0x48, SELC); e.w32(OVL, FVT9)
    e.w8(UIP + 0x184, 1); e.w8(UIP + 0x185, 1); e.w32(G.PLAYING, 1)
    e.u.mem_write(VIEW, bytes(0xA0)); e.w32(VIEW + 0x74, 0xFFFFFFFF); e.w8(VIEW + 0x7C, 0 if held_pattern else 1); e.w8(VIEW + 0x90, int(held_pattern))
    if held_pattern: st['ovl'] = False
    out = []
    for code, fl in steps_:
        e.w32(EV + 0x0C, code); e.w32(EV + 0x10, fl)
        try:
            r = 0
            if st['ovl']: r, _ = e.call(0x40024AF0, OVL, EV, count=200000)
            if not r & 0xFF: e.call(0x40020A7A, VIEW, EV, count=200000)
            e.call(0x400206C6, FUN, count=200000)
        except Exception as x:
            out.append(('Fehler', hex(e.u.reg_read(mk.UC_M68K_REG_PC)))); continue
        out.append((e.r8(UIP + 0x185), int(st['ovl'])))
    return out, e.r32(S['REQ']) == G.MAGIC, log
FT = [(1, 1 | 2), (21, 1 | 2), (21, 0 | 2), (1, 0)]
o, req, _ = tap_seq(IMG, FT + [(1, 1 | 2), (22, 1 | 2), (22, 0 | 2), (1, 0)])
chk('PATTERN getippt, FUNC + TRIG, los, nochmal FUNC + TRIG, los (Beobachter nach jedem Ereignis): Auswahl und Fenster bleiben %s'
    % o, all(x == (1, 1) for x in o) and req)
o, req, _ = tap_seq(IMG, FT + [(23, 1), (23, 0)])
chk('danach normaler TRIG: Auswahl aus, Fenster zu %s' % o[-2:], o[-1] == (0, 0))
o, req, _ = tap_seq(IMG, FT + [(3, 1), (3, 0)])
chk('nach Direct Jump PATTERN tippen: Auswahl aus, Fenster zu %s' % o[-2:], o[-1] == (0, 0))
o0, _, _ = tap_seq(REF, [(3, 1), (3, 0)]); o1, _, _ = tap_seq(IMG, [(3, 1), (3, 0)])
chk('PATTERN tippen im Fenster (ohne Sprung): wie ohne direct-jump %s %s' % (o0, o1), o0 == o1 and o1[-1] == (0, 0))
o0, _, _ = tap_seq(REF, [(23, 1), (23, 0)]); o1, _, _ = tap_seq(IMG, [(23, 1), (23, 0)])
chk('nur TRIG (normaler Wechsel): wie ohne direct-jump %s %s' % (o0, o1), o0 == o1 and o1[-1] == (0, 0))
o, req, log = tap_seq(IMG, [(1, 1 | 2), (21, 1 | 2), (21, 0 | 2), (1, 0), (3, 0)], held_pattern=True)
chk('PATTERN gehalten, FUNC + TRIG, los, PATTERN los: Auswahl bleibt (Fenster der Firmware wird geoeffnet) %s' % o,
    all(x[0] == 1 for x in o) and req and 0x40020730 in log)

# OFF : les trois detours du sequenceur ne modifient aucun etat natif.
oldinit=Emu.__init__
def disabled(s,img):
 oldinit(s,img)
 if img==IMG:s.w32(j['bss'],0)
Emu.__init__=disabled
bad,pat=compare(lambda s:(s.setpat(0,16),s.setpat(1,12)),n=700)
chk('JUMP OFF : 700 ticks identiques au socle, changement normal compris',bad==0 and pat==1)
for events in (FT,[(23,1),(23,0)],[(3,1),(3,0)]):
 ref,_,_=tap_seq(STOCK,events);off,_,_=tap_seq(IMG,events)
 chk('JUMP OFF : touches et fenetre comme le socle '+str(events),ref==off)
a.output.write_text(json.dumps(dict(sha256=m['sha256'],checks=checks,hardware_tested=False),indent=2)+'\\n')
