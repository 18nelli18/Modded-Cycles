"""Preuve du tweak generative (notes/50), partie 2 : la page GEN. Lancée par test_generative.py.
Banc Unicorn au niveau des fonctions (sans démarrer l'OS), vrai code d'origine et de TG partout où il tourne sans
interface démarrée :
  1. écritures : accesseur de touche, méthode des pads, trame des voyants
  2. ouverture : vrai constructeur KeyEvent + accesseur 0x4007240c (nous -> key_hook de TG) : SETTINGS+PAGE
     construit la page (constructeur de DrumSelect et present simulés, qui enregistrent), copie des vtables,
     appui et relâchement de l'accord avalés
  3. distribution par les vtables de l'objet page : touches (emplacement 2), potards (emplacement 17 et thunk de la
     base EncoderHandler), comme l'OS les appelle
  4. pads : méthode de PadsView 0x4001d180 (jmp de TG -> nous) : pris page ouverte, la méthode d'origine jamais atteinte
  5. dessin : vrais rectangles/cadres/pixels dans un contexte 128x64, appels de texte enregistrés ; vidage ASCII
  6. voyants : la vraie trame 0x40006a4a (effacement, nos demandes, vues, extinction) avec le matériel simulé
  7. fermeture : clic sur RETURN -> vraie fermeture différée ; destructeur -> pg_gone -> destructeur d'origine
  Les actions de la page passent par le vrai code du générateur sur un faux pattern dont les données des pistes sont
  les vraies adresses de la banque : chaque réglage doit écrire exactement ce que prévoit l'exécutable hôte du cœur.
"""
import json, pathlib, struct, subprocess, sys
sys.dont_write_bytecode = True
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build                                          # noqa: E402
CYCLES = None   # le .syx officiel ; posé par test_generative.py
CLI = None      # l'exécutable hôte du cœur (machines/generative/host/gen_cli.c) ; idem
WITH = []       # autres tweaks appliqués avec model-tg et generative (--with) ; idem
BASE = 0x40000400
FAIL = []


def check(ok, msg):
    print(('  ok    ' if ok else '  FAIL  ') + msg)
    if not ok:
        FAIL.append(msg)


def image(ids):
    from mtlib import aplib, container
    from mtlib.syx import unwrap
    raw = open(CYCLES, 'rb').read()
    c = container.parse(unwrap(raw)[0]); s3 = next(s for s in c['sections'] if s['id'] == 3)
    stock = aplib.depack(c['blob'][s3['off']:s3['off'] + s3['size']])[0]
    _, tw = build.load_catalog()['model-cycles_OS1.13']
    ch = sorted((tw[i] for i in list(ids) + WITH), key=lambda t: t['order'])
    p, _ = build.apply_writes(stock, ch); pl, _ = build.build_payload(ch, stock, None)
    return p + pl, {k: int(v, 16) for k, v in tw['generative']['symbols'].items()}


STOP, STACK = 0x9f000000, 0x9e000000
APP = 0x93500000; ROOTV = APP + 64
CTX, FB = 0x93600000, 0x93600100
LIGHTS = 0x93700000
TRIGTAB, PADTAB = 0x93710000, 0x93710100
SET_HELD, MOD_USED, RTG_ON = 0x401b235c, 0x401b2360, 0x401b6d8c
VT_SRC = 0x40117918
UICTX, P, NOTE, FAKEVT = 0x93000000, 0x93100000, 0x93200000, 0x93800000
BANK = 0x406fa040; PB = BANK + 5 * 30710; SCB = PB + 30642
DEFAULTS = [[1, 16, 4, 0, 0], [1, 16, 2, 0, 4], [1, 16, 4, 0, 2], [1, 16, 5, 0, 0], [1, 16, 3, 0, 0], [1, 16, 2, 0, 0]]


class M:
    def __init__(self, img, syms):
        self.s = syms
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)              # superviseur, IPL 0 : la tâche d'interface
        uc.mem_map(0x40000000, 0x02400000); uc.mem_write(BASE, img)
        uc.mem_map(0x90000000, 0x10000000); uc.mem_map(0xfc000000, 0x100000)
        uc.mem_write(STOP, b'\x4e\x71' * 2)
        self.bad, self.heap, self.log = [], 0x92000000, []
        self.func_held = 0
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(hex(addr)) or False)
        self.stubs = {
            0x400802e0: self._new, 0x40080064: self._new,
            0x400a22b0: self._ctor,                          # constructeur de DrumSelect : demande une interface démarrée
            0x400d0974: lambda a: APP,
            0x4007700e: lambda a: self.rec('present', a[0], self.r32(a[1]), self.r32(a[1] + 4), a[2]),
            0x400cf23c: lambda a: self.rec('release', a[0]),
            0x4007faf4: lambda a: self.func_held if a[0] == 1 else 0,
            0x40071a04: self._text,
            0x400cfaf4: lambda a: LIGHTS,
            0x4008e942: lambda a: 0, 0x4008e77e: lambda a: self.rec('commit'),
            0x4008e998: lambda a: self.rec('led', a[0], 1), 0x4008e964: lambda a: self.rec('led', a[0], a[2]),
            0x40076ca2: self._views,
            0x400f4486: lambda a: self.rec('stock_dtor1', a[0]), 0x400f43ca: lambda a: self.rec('stock_dtor0', a[0]),
            0x4001d188: lambda a: self.rec('stock_pad'),     # corps de la méthode d'origine des pads, après son jmp
            0x400802ec: lambda a: 0,                          # operator delete
            0x400cf866: lambda a: UICTX, 0x4000f208: lambda a: P, NOTE: lambda a: 0,
        }
        for a in self.stubs:
            uc.hook_add(UC_HOOK_CODE, self._stub, begin=a, end=a)
        self.w32(0x40fe4178, 1)                              # TG's "view machinery up"
        self.w32(0x404a8bdc, TRIGTAB); self.w32(0x404a8ba0, PADTAB)
        for k in range(16): self.w32(TRIGTAB + 4 * k, k)     # fausses tables de voyants (remplies au démarrage sur la machine)
        for t in range(6): self.w32(PADTAB + 4 * t, 16 + t)

    def rec(self, *x):
        self.log.append(x); return 0

    def _stub(self, uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        args = struct.unpack('>8I', uc.mem_read(sp + 4, 32))
        uc.reg_write(mk.UC_M68K_REG_D0, (self.stubs[addr](args) or 0) & 0xffffffff)
        uc.reg_write(mk.UC_M68K_REG_PC, self.r32(sp)); uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def _new(self, a):
        r = self.heap; self.heap += (a[0] + 15) & ~15
        self.uc.mem_write(r, b'\0' * a[0]); return r

    def _ctor(self, a):
        o = a[0]                                             # les vptr que laisse le constructeur d'origine (0x400a22da..)
        for off, v in ((0, 0x40117920), (4, 0x40117970), (8, 0x40117984), (12, 0x40117998), (16, 0x401179ac), (0x4c, 0x401179c0)):
            self.w32(o + off, v)
        self.rec('ctor', o)

    def _text(self, a):
        s = self.cstr(a[6]) if self.cstr(a[5]) == '%s' else self.cstr(a[5])
        self.log.append(('text', a[1], s32(a[2]), s32(a[3]), a[4], s)); return 0

    def _views(self, a):
        self.log.append(('views', a[0], [self.r32(LIGHTS + 40 + 4 * i) for i in range(22)])); return 0

    def cstr(self, a):
        b = bytes(self.uc.mem_read(a, 64)); return b[:b.index(0)].decode('latin1')

    def w32(self, a, v): self.uc.mem_write(a, struct.pack('>I', v & 0xffffffff))
    def r32(self, a): return struct.unpack('>I', self.uc.mem_read(a, 4))[0]
    def r8(self, a): return self.uc.mem_read(a, 1)[0]

    def fake(self, at, data):                                # objet : vtable[4] notification, [10] données, [15] rts
        vt = FAKEVT + self.nfake * 0x100; f10 = vt + 0x80; self.nfake = getattr(self, 'nfake', 0) + 1
        self.w32(at, vt); self.w32(vt + 16, NOTE); self.w32(vt + 40, f10); self.w32(vt + 60, f10 + 8)
        self.uc.mem_write(f10, b'\x20\x3c' + struct.pack('>I', data) + b'\x4e\x75\x4e\x75')

    def pattern(self):
        """faux pattern en cours dont les données des pistes sont les vrais blocs de la banque (voir _generative_os.py)"""
        self.nfake = 0
        blk = bytearray(30710)
        for t in range(6):
            b = 722 * t
            for s in range(64): blk[b + 128 + s] = 0xff; blk[b + 192 + s] = 0xff; blk[b + 580 + s] = 0xff
            for s in range(0, 64, 3):                        # un rythme fait main : un pas sur trois
                blk[b + 2 * s:b + 2 * s + 2] = struct.pack('>H', 0x0881)
            blk[b + 710:b + 712] = struct.pack('>H', 0x680); blk[b + 712] = 60
            blk[b + 713:b + 715] = struct.pack('>H', 16)
            a = 4332 + 4385 * t
            for s in range(64): blk[a + 68 * s:a + 68 * s + 68] = b'\xff' * 66 + b'\x00\x00'
            blk[a + 4352:a + 4385] = bytes(33)
        blk[30662:30664] = struct.pack('>H', 16); blk[30667] = 0; blk[30668] = 2
        self.uc.mem_write(PB, bytes(blk))
        self.fake(P + 44, SCB)
        self.fake(P + 0x400, PB + 4332)
        for t in range(6):
            o = P + 0x70 + 88 * t
            self.fake(o, PB + 722 * t)
            self.w32(o + 44, P + 0x400); self.w32(o + 56, t); self.w32(o + 60, P)

    def bank(self):
        b = bytes(self.uc.mem_read(PB, 30710))
        rows = [''.join('1' if struct.unpack('>H', b[722 * t + 2 * s:722 * t + 2 * s + 2])[0] & 1 else '0'
                        for s in range(64)) for t in range(6)]
        lens = [struct.unpack('>H', b[722 * t + 713:722 * t + 715])[0] for t in range(6)]
        return b, rows, lens

    def controls(self):
        return list(struct.unpack('>48H', self.uc.mem_read(self.s['ours_controls'], 96)))

    def call(self, fn, *args, count=400_000_000):
        sp = STACK - 0x400
        self.uc.mem_write(sp, struct.pack('>' + 'I' * (len(args) + 1), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        try:
            self.uc.emu_start(fn, STOP, count=count)
        except Exception as x:
            pc = self.uc.reg_read(mk.UC_M68K_REG_PC)
            raise SystemExit(f'emu fault {x} at pc {pc:#x}, bad {self.bad}')
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def ev(self, code, flags, at):
        self.call(0x4007238c, at, code, flags, 0x1234, 0x7f)   # vrai constructeur KeyEvent
        return at

    def vcall(self, obj, off, *args):                        # appel virtuel : *(*(obj) + off)(obj, ...)
        return self.call(self.r32(self.r32(obj) + off), obj, *args)


def s32(v): return v - (1 << 32) if v & 0x80000000 else v


def host(cmd, seed, controls, locked):
    """l'exécutable hôte du cœur (vérifié par les vecteurs dorés)"""
    line = cmd + (f' {seed}' if seed is not None else '') + (' ' + ' '.join(map(str, list(controls) + list(locked))) if controls else '')
    return subprocess.run([str(CLI)], input=line + '\n', capture_output=True, text=True, check=True).stdout.split()


DEF = None


def defaults():
    global DEF
    DEF = [int(x) for x in host('defaults', None, [], [])]
    return DEF


def padid(m, track):
    return [m.r32(0x401001d0 + 4 * i) for i in range(7)].index(track)


def padev(m, pid, typ=1):
    at = 0x93300800
    m.uc.mem_write(at, b'\0' * 24); m.w32(at + 16, typ); m.w32(at + 20, pid)
    return at


def page_changed(m, obj):
    """choisit la piste 4 d'un appui sur son pad : la page relit ses rythmes, se redessine et demande les voyants"""
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 3)))


def sites_test(img, syms):
    m = M(img, syms)
    check(m.r32(0x4007240e) == syms['ours_key_hook'], 'écriture : jmp de l\'accesseur de touche -> ours_key_hook')
    check(m.r32(0x4001d182) == syms['ours_pad_hook'] and m.uc.mem_read(0x4001d180, 2) == b'\x4e\xf9', 'écriture : jmp de la méthode des pads de PadsView -> ours_pad_hook')
    check(bytes(m.uc.mem_read(0x40006a76, 2)) == b'\x4e\xb9' and m.r32(0x40006a78) == syms['ours_led_frame'], 'écriture : jsr 0x40076ca2 de la trame des voyants -> ours_led_frame')


def page_test(img, syms):
    defaults()
    m = M(img, syms)
    m.pattern()
    acc = lambda e: s32(m.call(0x4007240c, e))
    pg_obj = syms['pg_obj']
    # PAGE seul : TG et l'origine inchangés
    e = m.ev(15, 1, 0x93300000); check(acc(e) == 15 and m.r32(pg_obj) == 0, 'PAGE seul : code 15, pas de page')
    m.ev(15, 0x10, 0x93300000); acc(0x93300000)
    # SETTINGS+PAGE avec la page retrig de TG ouverte : pas pour nous
    s = m.ev(13, 1, 0x93300100); acc(s)
    m.w32(RTG_ON, 1); e = m.ev(15, 1, 0x93300180); r = acc(e); m.w32(RTG_ON, 0)
    check(r == 15 and m.r32(pg_obj) == 0, f'SETTINGS+PAGE page retrig de TG ouverte : laissé à TG ({r})')
    m.ev(15, 0x10, 0x93300180); acc(0x93300180)
    # SETTINGS+PAGE : ouverture
    check(m.r32(SET_HELD) == 1, 'SETTINGS enfoncé : set_held de TG = 1 (par notre accroche)')
    e = m.ev(15, 1, 0x93300200); r = [acc(e) for _ in range(3)]
    obj = m.r32(pg_obj)
    pres = [x for x in m.log if x[0] == 'present']
    check(r == [0, 0, 0] and obj and m.r32(e + 16) & 8 and m.r32(MOD_USED) == 1,
          f'SETTINGS+PAGE : pris à chaque lecture {r}, page {obj:#x}, bit 3, mod_used')
    vt = syms['pg_vt']
    check(len(pres) == 1 and pres[0][1] == ROOTV and pres[0][2] == obj and pres[0][4] == 0,
          f'present(racine = app+64, {{page, bloc}}, 0) une fois : {pres}')
    h = pres[0][3]
    check([m.r32(h + 4 * i) for i in range(4)] == [0x401000c4, 1, 1, obj], 'bloc de contrôle = {0x401000c4, 1, 1, page}, lâché après present : '
          + str([x for x in m.log if x[0] == 'release']))
    check(m.r32(obj) == vt + 8 and m.r32(obj + 4) == vt + 0x58 and m.r32(obj + 8) == 0x40117984,
          'vptr de la page : principal = copie+8, EncoderHandler = copie+0x58, autres bases d\'origine')
    stock_vt = [m.r32(VT_SRC + i) for i in range(0, 0xb0, 4)]
    ours_vt = [m.r32(vt + i) for i in range(0, 0xb0, 4)]
    changed = {i * 4: hex(v) for i, (v, w) in enumerate(zip(ours_vt, stock_vt)) if v != w}
    check(sorted(changed) == [0x08, 0x0c, 0x10, 0x18, 0x4c, 0x60], f'copie des vtables : seuls destructeurs/touches/dessin/potard/thunk remplacés {changed}')
    u = m.ev(15, 0x10, 0x93300300); r = [acc(u) for _ in range(2)]
    check(r == [0, 0], f'relâchement de PAGE après l\'accord : pris {r}')

    # --- touches par le gestionnaire de la page (emplacement 2), comme la pile de vues l'appelle ---
    key = lambda code, fl, at: s32(m.vcall(obj, 0x08, m.ev(code, fl, at)))
    before, rows0, _ = m.bank()
    m.log.clear()
    r = key(19, 1, 0x93300400); key(19, 0x10, 0x93300400)
    check(r == 1 and m.bank()[0] == before, 'touche de pas sur la page : utilisée, pattern intact (affichage seulement)')
    r = key(20, 1, 0x93300480); key(20, 0x10, 0x93300480)      # SETTINGS encore tenu : TG ferait un trig de slide
    check(r == 1 and m.bank()[0] == before, 'SETTINGS + touche de pas sur la page : à nous, pas de trig de slide de TG')
    su = m.ev(13, 0x10, 0x93300490); r = acc(su)
    check(r == 0 and m.r32(SET_HELD) == 0, f'relâchement de SETTINGS sur la page : TG l\'avale (mod_used), set_held 0 ({r})')
    m.w32(0xfc07000c, 0x5eed1234)
    r1 = key(6, 1, 0x93300500); key(6, 0x10, 0x93300500)
    _, rows1, lens1 = m.bank()
    seed = m.r32(syms['ours_seed']); ctl = m.controls()
    exp = host('rand', seed, DEF, [0] * 6)
    check(r1 == 1 and ctl == [int(x) for x in exp] and m.r32(syms['pg_owned']) == 0x3f,
          f'PUNCH : Random a tiré les six pistes (réglages = cœur hôte, graine {seed:#010x}), toutes marquées générées')
    g = host('gen', m.r32(syms['ours_seed']), ctl, [0] * 6)
    check(rows1 == [g[6 * t + 2] for t in range(6)] and lens1 == [max(2, int(g[6 * t + 1])) for t in range(6)],
          'PUNCH : trigs et longueurs écrits = cœur hôte')
    pr = struct.unpack('>6H', m.uc.mem_read(syms['pg_rhythm'], 12))
    check(list(pr) == [int(rows1[t][:min(16, lens1[t])][::-1], 2) for t in range(6)], f'pg_rhythm relu dans le pattern {[hex(x) for x in pr]}')
    r2 = key(6, 3, 0x93300580); key(6, 0x12, 0x93300580)
    check(r2 == 1 and m.bank()[0] == before and m.controls() == DEF and m.r32(syms['pg_owned']) == 0,
          'FUNC+PUNCH : Undo rend le pattern à l\'octet près, les réglages et les marques « générée »')
    r = key(2, 1, 0x93300600)
    check(r == 0, f'TRACK sur la page : distribution de base de View, non utilisée ({r})')

    # --- potards : emplacement 17 et thunk de la base +4 ---
    def enc(idx, d, fast, via_base):
        at = 0x93300700
        m.uc.mem_write(at, b'\0' * 24); m.w32(at + 12, idx); m.w32(at + 16, d); m.uc.mem_write(at + 20, bytes([fast]))
        if via_base:
            return s32(m.vcall(obj + 4, 0x08, at))
        return s32(m.vcall(obj, 0x44, at))
    r = [enc(1, 1, 0, True)]                                    # DATA +1 : piste 2 (Snare)
    r.append(enc(3, 1, 0, True))                                # densité 2 -> 3
    c1 = m.controls()
    _, rows2, lens2 = m.bank()
    g = host('gen', m.r32(syms['ours_seed']), c1, [0] * 6)
    check(m.r32(syms['pg_sel']) == 1 and c1[2 + 5 + 2] == 3 and rows2[1] == g[6 + 2] and lens2[1] == 16
          and rows2[0] == rows0[0] and rows2[2:] == rows0[2:] and m.r32(syms['pg_owned']) == 2,
          'DATA +1 choisit Snare ; potard 2 +1 : densité 3, seule cette piste réécrite (= cœur hôte), marquée générée')
    r.append(enc(2, -9, 0, False))                              # cycle 16 -> 7
    r.append(enc(4, 3, 1, True))                                # régularité +3 rapide (x4) -> bornée
    r.append(enc(5, -1, 0, True))                               # décalage 4 -> boucle dans 7
    c2 = m.controls(); _, rows3, lens3 = m.bank()
    g = host('gen', m.r32(syms['ours_seed']), c2, [0] * 6)
    n, k, e, sh = c2[2 + 5 + 1:2 + 5 + 5]
    check((n, k, sh) == (7, 3, 3) and 0 <= e and rows3[1] == g[6 + 2] and lens3[1] == 7,
          f'cycle -9 -> {n}, régularité +12 bornée -> {e}, décalage -1 boucle -> {sh} ; écrit = cœur hôte, longueur 7')
    for _ in range(2): m.call(0x4001d180, 0x93400000, padev(m, padid(m, 2)))   # deux appuis sur la piste 3 : choix, verrou
    check(m.r32(syms['pg_lock']) == 0b100 and m.r32(syms['pg_sel']) == 2, 'pad 3, deux appuis : choisie, puis verrouillée')
    r.append(enc(6, 1, 0, True))                                # style -> imbriqué
    c3 = m.controls(); _, rows4, _ = m.bank()
    g = host('gen', m.r32(syms['ours_seed']), c3, [0] * 6)
    check(c3[1] == 1 and rows4[1] == g[6 + 2] and rows4[0] == rows0[0] and rows4[2] == rows0[2],
          'potard 5 + : style imbriqué ; seules les pistes générées non verrouillées réécrites (Snare oui ; Kick jamais générée ; piste 3 verrouillée)')
    r.append(enc(13, -2, 0, True))
    check(r == [1] * len(r) and s32(m.r32(syms['pg_last_idx'])) == 13, f'chaque événement de potard consommé {r}, dernier indice 13 retenu')

    # --- pads ---
    pid = padid(m, 3)
    m.log.clear(); r = s32(m.call(0x4001d180, 0x93400000, padev(m, pid)))
    check(r == 1 and m.r32(syms['pg_sel']) == 3 and not [x for x in m.log if x[0] == 'stock_pad'],
          f'pad {pid} (piste 4) : choisie, utilisé, méthode d\'origine jamais atteinte')
    r = [s32(m.call(0x4001d180, 0x93400000, padev(m, padid(m, 0)))) for _ in range(2)]
    check(r == [1, 1] and m.r32(syms['pg_lock']) == 0b101 and m.r32(syms['pg_sel']) == 0, 'pad 1, deux appuis : choisie, puis piste 1 verrouillée')
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 2)))
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 2)))
    check(m.r32(syms['pg_lock']) == 0b001, 'pad 3, à nouveau deux appuis : piste 3 déverrouillée')
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 2)))     # piste 3 choisie : un appui la reverrouille
    m.call(0x4001d180, 0x93400000, padev(m, pid))
    check(m.r32(syms['pg_lock']) == 0b101 and m.r32(syms['pg_sel']) == 3, 'verrous 1 et 3 remis, piste 4 choisie')
    r = s32(m.call(0x4001d180, 0x93400000, padev(m, pid, 0)))
    check(r == 1, 'relâchement du pad : pris aussi')
    m.w32(0xfc07000c, 0x0badcafe)
    before_lock = m.bank()[1]
    key(6, 1, 0x93300a80); key(6, 0x10, 0x93300a80)
    after_lock = m.bank()[1]
    check(after_lock[0] == before_lock[0] and after_lock[2] == before_lock[2] and after_lock != before_lock,
          'PUNCH, pistes 1 et 3 verrouillées : ces deux intactes, le reste tiré')
    m.w32(syms['pg_sel'], 0)                                   # puis un appui sur le pad 4 la choisit (et rafraîchit)
    page_changed(m, obj)

    # --- dessin ---
    m.uc.mem_write(CTX, b'\0' * 0x100); m.w32(CTX + 4, 128); m.w32(CTX + 8, 64); m.w32(CTX + 12, 2); m.w32(CTX + 16, FB)
    m.uc.mem_write(FB, b'\x5a' * 1024)                         # du bruit : la page doit l'effacer
    rh = struct.unpack('>H', m.uc.mem_read(syms['pg_rhythm'] + 6, 2))[0]   # piste 4, telle que relue dans le pattern
    m.log.clear()
    m.vcall(obj, 0x10, CTX)
    texts = [x for x in m.log if x[0] == 'text']
    fb = bytes(m.uc.mem_read(FB, 128 * 8))
    def px(x, y):                                              # y depuis le bas, comme l'OS compte
        w = struct.unpack('>I', fb[4 * (x * 2 + (y >> 5)):4 * (x * 2 + (y >> 5)) + 4])[0]
        return (w >> (31 - (y & 31))) & 1
    rows = [''.join('#' if px(x, 63 - top) else '.' for x in range(128)) for top in range(64)]
    print('\n'.join('          ' + r for r in rows[9:58]))
    for t in texts:
        print(f'          text font {t[1]:#x} x {t[2]} y {t[3]} (top row {55 - t[3]}) flags {t[4]:#04x}: {t[5]!r}')
    strip_ok = all((rows[46][8 * i + 3] == '#') == bool((rh >> i) & 1) for i in range(16))
    outline_ok = all(rows[40][8 * i + 1:8 * i + 6] == '#####' and rows[52][8 * i + 3] == '#' for i in range(16))
    check(strip_ok and outline_ok, 'dessin : bande des 16 pas depuis le haut (plein = trig), y compté depuis le bas')
    check(all(c == '.' for r in rows[56:64] for c in r) and rows[11] == '#' * 128 and all(c == '.' for r in rows[53:55] for c in r),
          'dessin : filet sur la ligne 11 ; sous la bande, effacé (bruit parti)')
    ct = m.controls()[2 + 15:2 + 20]
    want = {'EUC', 'PERC', 'NEST', 'CYC', 'DEN', 'EVN', 'SFT', str(ct[1]), str(ct[2]), str(ct[4])}
    got = {t[5] for t in texts}
    check(not any(t.startswith(('SEED', 'K', 'PUNCH')) for t in got), 'dessin : ni graine, ni indice de potard, ni pied de page')
    boxes = [(t[2] - 3 * len(t[5]) if t[4] & 2 else t[2] - 6 * len(t[5]) if t[4] & 4 else t[2],
              55 - t[3], len(t[5]) * 6) for t in texts]          # environ 6 px par caractère, 9 lignes de haut
    clash = [(a, b) for i, a in enumerate(boxes) for b in boxes[i + 1:]
             if a[1] == b[1] and a[0] < b[0] + b[2] and b[0] < a[0] + a[2]]
    long_evn = 6 * len('123/809')
    check(not clash and 75 - long_evn // 2 > 39 + 6 and 75 + long_evn // 2 < 113 - 6,
          f'dessin : aucun texte ne chevauche un autre, la plus large valeur EVN tient dans sa colonne {clash}')
    check(want <= got and all(t[1] == 0x40ea14cc for t in texts) and any(t[5] == 'EUC' and t[4] == 8 for t in texts),
          f'dessin : appels de texte (petite police 0x40ea14cc ; mode « EUC » inversé, options 0x08) {sorted(got)}')

    # --- voyants : la vraie trame avec notre accroche ---
    m.uc.mem_write(LIGHTS, b'\xee' * 0x100)
    m.w32(ROOTV + 32, 0x00010000)                              # racine+33 : voyants à redessiner
    m.log.clear()
    m.call(0x40006a4a, APP)
    views = [x for x in m.log if x[0] == 'views']
    leds = {x[1]: x[2] for x in m.log if x[0] == 'led'}
    exp = [2 if (rh >> k) & 1 else 1 for k in range(16)] + [2 if t == 3 else 1 for t in range(6)]
    check(len(views) == 1 and views[0][2] == exp, f'trame des voyants : nos 16 voyants de pas et 6 de pads passent avant les vues')
    check(all(leds.get(k) == exp[k] for k in range(22)) and ('commit',) in m.log,
          f'trame des voyants : appels matériels allumés={sum(1 for v in exp if v == 2)} éteints={sum(1 for v in exp if v == 1)}, voyants non demandés éteints, validés')

    # --- couche 1 : le potard 6 passe Kick en MAP ; Style (tout le kit), Remplissage ; vélocités écrites ---
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 0)))      # choisit Kick (piste 1 verrouillée : réglable quand même)
    r = enc(7, 1, 0, True)
    c4 = m.controls(); b4, rows5, lens5 = m.bank()
    g = host('gen', m.r32(syms['ours_seed']), c4, [0] * 6)
    vel_bank = b4[128:192].hex()
    vel_exp = g[3]
    trig_steps = [s for s in range(64) if rows5[0][s] == '1']
    if '-v' in sys.argv:
        print('    kick', r, c4[2:7], lens5[0], rows5[0][:32], g[2][:32])
        print('    vel bank', vel_bank[:64]); print('    vel exp ', vel_exp[:64])
    check(r == 1 and c4[2] == 2 and c4[4] == 68 and rows5[0] == g[2] and lens5[0] == 64
          and all(vel_bank[2 * s:2 * s + 2] == vel_exp[2 * s:2 * s + 2] for s in trig_steps) and trig_steps,
          f'potard 6 + : Kick -> MAP (remplissage 68), trigs, longueur 64 et vélocités écrits = cœur hôte ({len(trig_steps)} coups)')
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 1)))      # Snare en MAP aussi
    enc(7, 1, 0, True)
    snare_before = m.bank()[1][1]
    r = enc(2, 80, 0, True)                                     # Style 0 -> 80 (BREAKS), depuis la page de Snare
    c5 = m.controls(); b5, rows6, _ = m.bank()
    g = host('gen', m.r32(syms['ours_seed']), c5, [0] * 6)
    check(c5[32] == 80 and rows6[1] == g[6 + 2] and rows6[1] != snare_before and rows6[0] == rows5[0],
          'potard 1 sur une piste MAP : Style 80 (tout le kit) ; Snare réécrite = cœur hôte ; Kick verrouillée garde son rythme')
    m.uc.mem_write(CTX, b'\0' * 0x100); m.w32(CTX + 4, 128); m.w32(CTX + 8, 64); m.w32(CTX + 12, 2); m.w32(CTX + 16, FB)
    m.log.clear(); m.vcall(obj, 0x10, CTX)
    got = {t[5] for t in m.log if t[0] == 'text'}
    check({'MAP', 'SNARE', 'BREAK', 'STY', 'FIL', 'CHS', 'SFT', '80', '70'} <= got,
          f'dessin sur une piste MAP : mode MAP, style BREAK, réglages STY FIL CHS SFT {sorted(got)}')
    r = enc(7, -1, 0, True)
    c6 = m.controls()
    check(c6[2 + 5] == 1 and c6[2 + 5 + 1:2 + 5 + 5] == [16, 2, 0, 4], 'potard 6 - : Snare revient en EUC avec les réglages par défaut de la couche 2')


    # --- couche 3 : réglages de notes de Tone et Chord (rangée 2), tonique et gamme ; notes et p-locks de SHAPE ---
    SHAPE = [4, 3, 17, 10, 8, 7, 19]                            # qualité d'accord -> indice SHAPE de la machine Chord
    def notes_ok(t, g):
        b = m.bank()[0]
        trig = g[6 * t + 2]; nh = g[6 * t + 4]; ch = g[6 * t + 5]
        steps = [s for s in range(64) if trig[s] == '1']
        notes = all(b[722 * t + 580 + s] == int(nh[2 * s:2 * s + 2], 16) for s in steps)
        shapes = True
        if t == 5:
            for s in steps:
                q = int(ch[2 * s:2 * s + 2], 16)
                a = PB + 4332 + 4385 * t + 68 * s + 2 * 12
                shapes &= struct.unpack('>h', m.uc.mem_read(a, 2))[0] == SHAPE[q] << 8
        return steps and notes and shapes, len(steps)
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 4)))      # choisit Tone
    r = enc(8, 10, 0, True)
    c7 = m.controls()
    g = host('gen', m.r32(syms['ours_seed']), c7, [0] * 6)
    ok, n = notes_ok(4, g)
    check(r == 1 and c7[36] == 58 and ok and m.uc.mem_read(syms['pg_rhythm'], 1) is not None,
          f'Tone, potard 7 +10 : étendue 58 ; {n} notes écrites = cœur hôte')
    m.call(0x4001d180, 0x93400000, padev(m, padid(m, 5)))      # choisit Chord
    enc(9, 100, 0, True)                                        # complexité 32 -> 127 : septièmes
    c8 = m.controls()
    g = host('gen', m.r32(syms['ours_seed']), c8, [0] * 6)
    ok, n = notes_ok(5, g)
    check(c8[41] == 127 and ok, f'Chord, potard 8 +100 : complexité 127 ; {n} fondamentales et p-locks de SHAPE (valeur << 8) = cœur hôte')
    enc(12, 2, 0, True)                                         # tonique do -> ré : Tone et Chord réécrites
    c9 = m.controls()
    g = host('gen', m.r32(syms['ours_seed']), c9, [0] * 6)
    check(c9[34] == 2 and notes_ok(4, g)[0] and notes_ok(5, g)[0], 'potard 11 +2 : tonique ré ; Tone et Chord réécrites = cœur hôte')
    enc(13, 1, 0, True); enc(13, 1, 0, True)                    # gamme (MAJ après le tour d'indice 13 plus haut) -> MIN -> DOR
    enc(11, -1, 0, True)                                        # octave de Chord 2 -> 1 (affiche -1)
    m.uc.mem_write(CTX, b'\0' * 0x100); m.w32(CTX + 4, 128); m.w32(CTX + 8, 64); m.w32(CTX + 12, 2); m.w32(CTX + 16, FB)
    m.log.clear(); m.vcall(obj, 0x10, CTX)
    got = {t[5] for t in m.log if t[0] == 'text'}
    check({'EUC', 'CHORD', 'D DOR', 'ADV', 'CPX', 'DJV', 'OCT', '-1', '127'} <= got,
          f'dessin sur Chord après un potard de la rangée 2 : tonalité « D DOR », réglages ADV CPX DJV OCT, octave -1 {sorted(got)}')
    enc(2, 1, 0, True)                                          # un potard de la rangée 1 : retour au rythme
    m.log.clear(); m.vcall(obj, 0x10, CTX)
    got = {t[5] for t in m.log if t[0] == 'text'}
    check({'CYC', 'DEN', 'EVN', 'SFT', 'D DOR'} <= got, f'un potard de la rangée 1 : réglages du rythme à nouveau {sorted(got)}')

    # --- fermeture : clic sur RETURN -> fermeture différée ; la racine lâche la vue -> notre destructeur -> l'origine ---
    r = key(12, 1, 0x93300900)
    check(r == 1 and m.r8(obj + 48) == 0, 'appui sur RETURN : utilisé, rien de fermé encore (le clic ferme)')
    r = key(12, 0x10, 0x93300900)
    check(r == 1 and m.r8(obj + 48) == 1, 'clic sur RETURN : fermeture différée 0x40076126 (vue+48 = 1)')
    m.w32(ROOTV + 32, 0); m.log.clear()
    m.vcall(obj, 0x04, )
    check(m.r32(pg_obj) == 0 and ('stock_dtor1', obj) in m.log and m.r8(ROOTV + 33) == 1,
          'destructeur : pg_gone (page oubliée, voyants à redessiner) puis l\'origine 0x400f4486')
    e = m.ev(19, 1, 0x93300a00); r = acc(e)
    check(r == 19, f'page fermée : la touche de pas revient à TG / l\'origine ({r})')
    # SETTINGS+PAGE à nouveau ferme
    s = m.ev(13, 1, 0x93300b00); acc(s)
    e = m.ev(15, 1, 0x93300b80); acc(e); obj = m.r32(pg_obj)
    m.ev(15, 0x10, 0x93300b80); acc(0x93300b80)
    e = m.ev(15, 1, 0x93300c00); r = key(15, 1, 0x93300c00)
    check(obj and r == 1 and m.r8(obj + 48) == 1 and m.r32(MOD_USED) == 1, 'SETTINGS+PAGE sur la page : fermeture différée, mod_used')
    u = m.ev(15, 0x10, 0x93300d00); r = acc(u)
    check(r == 0, f'son relâchement de PAGE avalé ({r})')
    check(not m.bad, f'aucun accès hors mémoire {m.bad[:3]}')


def run():
    img, syms = image(['model-tg', 'generative'])
    print('écritures'); sites_test(img, syms)
    print('page GEN'); page_test(img, syms)
    return FAIL
