"""Port des seuls noyaux PPPCCC MIT, revision61c7432076e49b3050c7e076a5b602747d36fb8c.
Copyright(c)2026 PPPCCC/gialloinfuso ; licence jointe. Generateurs de gestes/FX
non importes. Les adresses seront fixe'es par groove_strum_assets.py.
"""
import struct
NE,EQ,PL,MI,CS,CC,LS,LE,BRA,GT,GE=6,7,10,11,5,4,3,15,0,14,12
HI=2
GMAX=7;HMAX=100;HK=77;HSH=7;HDR=0x77b2;HOFF=40;HOFF_V=6
VOICE0=0x42308828;VSTEP=0x31c;NVOICE=6;K_SP=96;SMAX=80;G0_FULL=0x20000000
M_G=0x468b2000;M_T=0x468b2200;M_ST=0x468b2800;SIZE={M_G:512,M_T:256}
def check_cf(code,base):
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);i=0
 while i<len(code):
  ins=next(cs.disasm(code[i:i+12],base+i,1),None)
  if ins is None:i+=2;continue
  assert ins.size<=6,(hex(base+i),ins.mnemonic,ins.op_str,ins.size)
  i+=ins.size

class A:
    def __init__(s, org): s.org, s.b, s.lab, s.fix = org, bytearray(), {}, []
    def w(s, *words):
        for x in words: s.b += struct.pack('>H', x)
    def l32(s, v): s.b += struct.pack('>I', v)
    def label(s, n): s.lab[n] = s.org + len(s.b)
    def bcc(s, op, n):            # Bcc.W (16-Bit-Verschiebung)
        s.w(0x6000 | (op << 8)); s.fix.append((len(s.b), n)); s.w(0)
    def done(s):
        for pos, n in s.fix:
            disp = s.lab[n] - (s.org + pos)       # relativ zur Adresse des Erweiterungsworts
            assert -32768 <= disp < 32768
            s.b[pos:pos+2] = struct.pack('>h', disp)
        return bytes(s.b)

def build_g2(t_addr, rnd):
    """G mit Humanize; Adressierung des Kopfbytes ueber lea (d16 ist zu gross fuer (d8,An,Xn))."""
    a = A(M_G); w, l = a.w, a.l32
    a.label('G')
    w(0x7E00, 0x1E39); l(GMODE)                 # moveq #0,d7 ; move.b GMODE,d7
    w(0x4A87); a.bcc(NE, 'g1')
    w(0x7E10, 0xC287, 0x4A41); a.bcc(EQ, 'HUM')  # Original-Swing (wie Firmware)
    w(0x3208, 0xC3FC, 0x000C, 0x4C00, 0x1800, 0xDA81)
    a.bcc(BRA, 'HUM')
    a.label('g1')
    w(0x0C87); l(GMAX); a.bcc(HI, 'HUM')        # ungueltig: kein Groove
    w(0x4EF9); l(t_addr)                        # T (springt am Ende nach HUM)
    a.label('HUM')
    w(0x7E05, 0xBE86); a.bcc(CS, 'ret')         # moveq #5,d7 ; cmp.l d6,d7 ; bcs ret   (Track > 5)
    w(0x41F9); l(AMOUNTS)                       # lea HDR+HOFF(a3),a0
    w(0x7000, 0x1030, 0x6800)                   # d0 = Humanize Zeit   (Kopf 40+t)
    w(0x7200, 0x1230, 0x6800 | HOFF_V)          # d1 = Humanize Velocity (Kopf 46+t)
    w(0x0C80); l(HMAX); a.bcc(LS, 'a1'); w(0x7000)   # > 100: Muell -> 0
    a.label('a1')
    w(0x0C81); l(HMAX); a.bcc(LS, 'a2'); w(0x7200)
    a.label('a2')
    w(0x7E00 | HK, 0x4C07, 0x0800, 0xEE80)      # st = (ht*77) >> 7  (0..60; v1: >> 8, 0..30)
    w(0x4C07, 0x1800, 0xEE81)                   # sv = (hv*77) >> 7
    w(0x2041)                                   # movea.l d1,a0   sv (Velocity)
    w(0x2E00, 0x8E81); a.bcc(EQ, 'ret')         # beide 0: nichts
    # ab hier wie v16-Humanize: Zeit mit st (d0), Velocity mit sv (a0)
    w(0x732F, 0x003E)                           # mvs.b 0x3e(a7),d1   Faktor
    w(0xC3FC, 0x000C, 0x4C00, 0x1800)           # d1 = Faktor*12*st = S
    w(0x2E39); l(rnd)                           # move.l RND,d7
    w(0x203C); l(1664525)
    w(0x4C00, 0x7800)                           # muls.l d0,d7
    w(0x0687); l(1013904223)
    w(0x23C7); l(rnd)                           # move.l d7,RND
    w(0x2007, 0x4840)
    w(0x0280); l(0x7FFF)
    w(0x0480); l(0x4000)
    w(0x4C01, 0x0800)
    w(0xE080, 0xE080, 0xE280)                   # -> +-S/8
    w(0xDA80)                                   # Zeit
    w(0x2007, 0xE288)
    w(0x0280); l(0x7FFF)
    w(0x0480); l(0x4000)
    w(0x2208)                                   # move.l a0,d1   s
    w(0x4C01, 0x0800)                           # r*s
    w(0x222F, 0x0034)                           # Velocity v
    w(0x4A81); a.bcc(LE, 'ret')
    w(0x4C01, 0x0800)                           # r*s*v
    w(0x2E00, 0xE588, 0xD087)                   # *5
    w(0x0680); l(0x800000)
    w(0x7E18, 0xEEA0)                           # asr.l #24
    w(0xD280, 0x7001, 0xB081); a.bcc(LE, 'v1'); w(0x2200)
    a.label('v1')
    w(0x707F, 0xB081); a.bcc(GE, 'v2'); w(0x2200)
    a.label('v2')
    w(0x2F41, 0x0034)
    a.label('ret')
    w(0x4E75)
    code = a.done(); check_cf(code, M_G); assert len(code) <= SIZE[M_G], len(code)
    return code, dict(a.lab)

def build_t(ptrs_at, hum):
    a = A(M_T); w, l = a.w, a.l32
    a.label('T')
    w(0x0C87); l(GMAX); a.bcc(HI, 'out')
    w(0x2F02)                                   # move.l d2,-(a7)  (Velocity jetzt bei 0x38(a7))
    w(0x3208)                                   # move.w a0,d1     Faktor
    w(0x5387, 0xE58F)                           # subq.l #1,d7 ; lsl.l #2,d7   (Modus 1..3)
    w(0x41F9); l(ptrs_at)
    w(0x2070, 0x7800)
    w(0x2E03, 0x0287); l(63)
    w(0x7530, 0x7800)                           # Versatz
    w(0x4C00, 0x2800, 0x4C01, 0x2800)
    w(0x2202, 0xE58A, 0xD481, 0xEC82)
    w(0xDA82)
    w(0x75B0, 0x7840)                           # Groove-Velocity g
    w(0x727F, 0x9282, 0x4C00, 0x1800)
    w(0x242F, 0x0038, 0x4A82); a.bcc(LE, 'done')
    w(0x4C02, 0x1800, 0x2E3C); l(165); w(0x4C07, 0x1800)
    w(0x7E14, 0xEEA1, 0x9481)
    w(0x7201, 0xB282); a.bcc(LE, 'vok'); w(0x2401)
    a.label('vok')
    w(0x2F42, 0x0038)
    a.label('done')
    w(0x241F)
    a.label('out')
    w(0x4EF9); l(hum)                           # weiter mit Humanize
    code = a.done(); check_cf(code, M_T)
    return code, dict(a.lab)

def build_strum_core():
    a = A(M_ST); w, l = a.w, a.l32
    # ---- ST: Ende des CHORD-Updates (a2 = Stimme). d2-d5/a2-a4 werden danach aus dem Stack geholt; d6/d7 NICHT anfassen.
    a.label('ST')
    w(0x200A, 0x0480); l(VOICE0)            # move.l a2,d0 ; subi.l #VOICE0,d0
    a.bcc(MI, 'full')
    w(0x0C80); l(NVOICE * VSTEP); a.bcc(CC, 'full')   # ausserhalb der 6 Stimmen: Schleife unten bleibt kurz
    w(0x7200)                               # moveq #0,d1   Stimmen-Index
    a.label('vi')
    w(0x0C80); l(VSTEP); a.bcc(CS, 'vf')
    w(0x0480); l(VSTEP); w(0x5281); a.bcc(BRA, 'vi')
    a.label('vf')
    w(0x4A80); a.bcc(NE, 'full')
    w(0x7006, 0xB081); a.bcc(LS, 'full')    # Index >= 6
    w(0xE589, 0x41F9); l(CNT); w(0xD1C1)    # a0 = &Zaehler
    w(0x4AAA, 0x0038); a.bcc(EQ, 'inc')     # Anschlag?
    w(0x4290); a.bcc(BRA, 'gate')
    a.label('inc')
    w(0x2010, 0x0C80); l(0xFFFF); a.bcc(CC, 'gate')
    w(0x5290)
    a.label('gate')
    w(0x7139); l(STRUM)                     # mvs.b STRUM,d0   (-80..80)
    w(0x0C80); l(SMAX); a.bcc(GT, 'bad')
    w(0x0C80); l(-SMAX & 0xFFFFFFFF); a.bcc(GE, 'sok')
    a.label('bad'); w(0x7000)
    a.label('sok')
    w(0x7A00, 0x4A80); a.bcc(PL, 'up'); w(0x4480, 0x7A01)    # d5 = Richtung (1 = von oben), d0 = |STRUM|
    a.label('up')
    w(0x7200 | K_SP, 0x4C00, 0x1800, 0xEC89)   # d1 = (|STRUM| * K) >> 6   Abstand in Bloecken
    a.bcc(EQ, 'full')
    w(0x2010, 0x43EA, 0x000C, 0x7601)       # d0 = Zaehler ; a1 = Pegel Op1 ; d3 = k = 1
    a.label('kl')
    w(0x2403, 0x4A85); a.bcc(EQ, 'su'); w(0x7403, 0x9483)    # d2 = k bzw. 3 - k
    a.label('su')
    w(0x4C01, 0x2800)                       # d2 *= Abstand  (Start)
    w(0x2800, 0x9882); a.bcc(MI, 'zero')
    a.bcc(EQ, 'quart')
    w(0x0C84); l(1); a.bcc(EQ, 'half')
    a.bcc(BRA, 'nk')
    a.label('zero'); w(0x4291); a.bcc(BRA, 'nk')
    a.label('quart'); w(0x2811, 0xE484, 0x2284); a.bcc(BRA, 'nk')    # (a1) >>= 2   (d4 als Zwischenspeicher)
    a.label('half'); w(0x2811, 0xE284, 0x2284)                         # (a1) >>= 1
    a.label('nk')
    w(0x5889, 0x5283, 0x0C83); l(4); a.bcc(NE, 'kl')
    # Grundton (Op 0): Start 0 bzw. 3 * Abstand; Einsatz in 8 Stufen
    w(0x7400, 0x4A85); a.bcc(EQ, 'o0'); w(0x2401, 0xD481, 0xD481)
    a.label('o0')
    w(0x2800, 0x9882); a.bcc(MI, 'g0z')
    w(0x0C84); l(7); a.bcc(GT, 'full')
    w(0x5284, 0x741A, 0xE5AC, 0x23C4); l(G0); a.bcc(BRA, 'out')       # G0 = (n+1) << 26
    a.label('g0z'); w(0x42B9); l(G0); a.bcc(BRA, 'out')
    a.label('full'); w(0x283C); l(G0_FULL); w(0x23C4); l(G0)
    a.label('out')
    w(0x4CEF, 0x1C3C, 0x0008, 0x4FEF, 0x0024, 0x4E75)   # Epilog des CHORD-Updates
    # ---- G0F: im CHORD-Render statt move.l #$20000000,d1 (Pegel des Grundtons)
    a.label('G0F'); w(0x2239); l(G0); w(0x4E75)
    code1 = a.done(); check_cf(code1, M_ST); assert len(code1) <= 376, len(code1); lab1 = dict(a.lab)
    return code1,lab1
