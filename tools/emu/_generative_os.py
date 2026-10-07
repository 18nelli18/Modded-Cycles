"""Preuve du tweak generative (notes/50), partie 1 : démarrage, accords, Random et Undo. Lancée par test_generative.py.
  1. démarrage : ours_boot étend la zone épargnée par l'effacement de la BSS de TG, l'accroche de TG efface le reste
  2. touches : vrai constructeur KeyEvent -> 0x4007240c (nous -> key_hook de TG) : SETTINGS+PATTERN pris une fois,
     posté en message de type 6
  3. tâche d'interface : les vraies fonctions d'origine sur de faux objets pattern/piste dont les données sont les
     vraies adresses de la banque ; trigs et longueurs écrits = l'exécutable hôte du cœur, pour la graine tirée
  4. Undo rend les blocs des pistes, les p-locks et le bloc d'échelle à l'octet près
"""
import json, pathlib, struct, subprocess, sys, time
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
    if not ok: FAIL.append(msg)

def image(ids):
    from mtlib import aplib, container
    from mtlib.syx import unwrap
    raw = open(CYCLES, 'rb').read()
    c = container.parse(unwrap(raw)[0]); s3 = next(s for s in c['sections'] if s['id'] == 3)
    stock = aplib.depack(c['blob'][s3['off']:s3['off'] + s3['size']])[0]
    _, tw = build.load_catalog()['model-cycles_OS1.13']
    ch = sorted((tw[i] for i in list(ids) + WITH), key=lambda t: t['order'])
    p, _ = build.apply_writes(stock, ch); pl, _ = build.build_payload(ch, stock, None)
    return p + pl, tw['generative']['symbols']

STOP, STACK = 0x9f000000, 0x9e000000
CTX, P, NOTE = 0x93000000, 0x93100000, 0x93200000
BANK = 0x406fa040; PAT = 5; PB = BANK + PAT * 30710; SCB = PB + 30642
MSGQ = 0x404a9154

class M:
    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_map(0x40000000, 0x02400000); uc.mem_write(BASE, img)
        uc.mem_map(0x90000000, 0x10000000); uc.mem_map(0xfc000000, 0x100000)
        uc.mem_write(STOP, b'\x4e\x71' * 2)
        self.bad, self.posts, self.notes, self.heap = [], [], [], 0x92000000
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(hex(addr)) or False)
        self.stubs = {0x40001fba: self._post, 0x400cf866: lambda a: CTX, 0x4000f208: lambda a: P,
                      0x40080064: self._new, 0x400802e0: self._new, 0x400802ec: lambda a: 0, NOTE: self._note}
        for a in self.stubs:
            uc.hook_add(UC_HOOK_CODE, self._stub, begin=a, end=a)
    def _stub(self, uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        args = struct.unpack('>4I', uc.mem_read(sp + 4, 16))
        uc.reg_write(mk.UC_M68K_REG_D0, self.stubs[addr](args) & 0xffffffff)
        uc.reg_write(mk.UC_M68K_REG_PC, self.r32(sp)); uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
    def _post(self, a): self.posts.append((a[0], a[1])); return 0
    def _new(self, a):
        r = self.heap; self.heap += (a[0] + 15) & ~15; return r
    def _note(self, a):
        try: k = self.r32(a[1])
        except Exception: k = None
        self.notes.append((a[0], k)); return 0
    def w32(self, a, v): self.uc.mem_write(a, struct.pack('>I', v & 0xffffffff))
    def r32(self, a): return struct.unpack('>I', self.uc.mem_read(a, 4))[0]
    def call(self, fn, *args, count=50_000_000):
        sp = STACK - 0x400
        self.uc.mem_write(sp, struct.pack('>' + 'I' * (len(args) + 1), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        try:
            self.uc.emu_start(fn, STOP, count=count)
        except Exception as x:
            pc = self.uc.reg_read(mk.UC_M68K_REG_PC)
            raise SystemExit(f'emu fault {x} at pc {pc:#x}, bad {self.bad}, regs ' + ' '.join(f'{n}={self.uc.reg_read(getattr(mk, "UC_M68K_REG_" + n)):#x}' for n in ('A0','A1','A2','A7','D0','D1','D2')))
        return self.uc.reg_read(mk.UC_M68K_REG_D0)
    def obj(self, at, data):
        """faux objet : vtable[4] (+16) notification, [10] (+40) pointeur des données, [15] (+60) rts"""
        vt = at + 0x400; f10 = at + 0x500
        self.w32(at, vt)
        self.w32(vt + 16, NOTE); self.w32(vt + 40, f10); self.w32(vt + 60, f10 + 8)
        self.uc.mem_write(f10, b'\x20\x3c' + struct.pack('>I', data) + b'\x4e\x75' + b'\x4e\x75')

def boot_test(img, syms):
    m = M(img)
    res_end, end = int(syms['ours_res_end'], 16), int(syms['ours_end'], 16)
    lo, hi = 0x4019b590, 0x423380b0
    imgend = BASE + len(img)
    m.uc.mem_write(imgend, b'\xa5' * (hi - imgend))          # du bruit dans la BSS avant l'effacement
    hit = []
    m.uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: (hit.append(a), u.emu_stop()), begin=0x4000053a, end=0x4000053a)
    m.uc.reg_write(mk.UC_M68K_REG_A7, STACK - 0x400)
    m.w32(STACK - 0x400, 0x40000536)                          # ce qu'a empilé le jsr en 0x40000530
    m.uc.emu_start(m.r32(0x40000532), 0, count=40_000_000)
    check(m.r32(0x40000532) == int(syms['ours_boot'], 16), 'démarrage : 0x40000530 appelle ours_boot')
    check(hit == [0x4000053a], 'démarrage : finit dans l\'accroche de TG -> 0x4000053a')
    mem = bytes(m.uc.mem_read(lo, hi - lo))
    keep = bytearray(img[0x401ab750 - BASE:res_end - BASE])
    keep[0x401bf402 - 0x401ab750:0x401bf406 - 0x401ab750] = struct.pack('>I', res_end)   # l'opérande que nous changeons
    check(mem[0x401ab750 - lo:res_end - lo] == keep, f'démarrage : bloc de TG et notre code gardés [0x401ab750, {res_end:#x})')
    check(not any(mem[:0x401ab750 - lo]) and not any(mem[res_end - lo:]), 'démarrage : tout le reste de la BSS à zéro, notre .bss aussi')
    check(m.r32(0x401bf402) == res_end, 'démarrage : opérande de TG modifiée en RAM')

def ev(m, code, flags, at=0x93300000):
    m.call(0x4007238c, at, code, flags, 0x1234, 0x7f)       # vrai constructeur KeyEvent
    return at

def keys_test(img, syms):
    m = M(img)
    rd = lambda e: m.call(0x4007240c, e)
    # PATTERN sans SETTINGS : intact
    e = ev(m, 3, 1); check(rd(e) == 3 and not m.posts, 'PATTERN seul : code 3, rien de posté')
    # SETTINGS enfoncé, PATTERN lu 3 fois, relâché 2 fois, SETTINGS relâché (bit 4 du clic)
    s = ev(m, 13, 1, 0x93300100); r = rd(s)
    check(r == 13 and m.r32(0x401b235c) == 1, f'SETTINGS enfoncé va à TG (code {r}), set_held = 1')
    e = ev(m, 3, 1, 0x93300200); r = [rd(e) for _ in range(3)]
    check(r == [0, 0, 0] and len(m.posts) == 1 and m.r32(e + 16) & 8, f'SETTINGS+PATTERN : pris à chaque lecture {r}, posté une fois, bit 3 posé')
    q, msg = m.posts[0]
    check(q == MSGQ and m.uc.mem_read(msg, 1)[0] == 6 and m.r32(msg + 0x18) == 1 and m.r32(msg + 0xc) == 0x4002f136,
          'message : file 0x404a9154, type 6, busy, GENERIC_MANAGER')
    u = ev(m, 3, 0x10, 0x93300300); r = [rd(u) for _ in range(2)]
    check(r == [0, 0], f'relâchement de PATTERN pris à chaque lecture {r}')
    t2 = ev(m, 2, 1, 0x93300400); r = rd(t2)
    check(r == 2, f'SETTINGS+TRACK : pas pour nous, TG le laisse passer (code {r})')
    su = ev(m, 13, 0x10, 0x93300500); r = rd(su)
    check(r == 0, f'relâchement de SETTINGS après notre accord : TG l\'avale (mod_used), code {r}')
    e = ev(m, 14, 1, 0x93300600); r = rd(e)
    check(r == 14 and len(m.posts) == 1, 'TEMPO après relâchement de SETTINGS : comme à l\'origine')
    check(not m.bad, f'aucun accès hors mémoire {m.bad[:3]}')
    return m, msg

def setup_pattern(m, rng):
    """faux objet pattern P dont les données des pistes sont les vrais blocs de la banque du pattern PAT"""
    m.obj(P + 44, SCB)                                         # objet d'échelle (0x4000d0dc(P) = P+44)
    LS = P + 0x400                                             # magasin de p-locks : données = pattern + 4332
    m.obj(LS, PB + 4332)
    for t in range(6):
        o = P + 0x70 + 88 * t                                  # 0x4000cfcc(P, t): lea a0@(0x70,d0*88)
        m.obj(o, PB + 722 * t)
        m.w32(o + 44, LS); m.w32(o + 56, t); m.w32(o + 60, P)  # magasin de p-locks ; piste ; son pattern
    # les fausses vtables sont hors des objets de 88 octets
    blk = bytearray(30710)
    for t in range(6):
        b = 722 * t
        for s in range(64):
            if rng[t][s]:
                blk[b + 2 * s:b + 2 * s + 2] = struct.pack('>H', 0x0881)   # trig, note, choisi par le pas
        for s in range(64): blk[b + 128 + s] = 0xff; blk[b + 192 + s] = 0xff
        for s in range(64): blk[b + 580 + s] = (60 + s) & 0x7f if rng[t][s] else 0xff
        blk[b + 710:b + 712] = struct.pack('>H', 0x680); blk[b + 712] = 60
        blk[b + 713:b + 715] = struct.pack('>H', 16)
    for t in range(6):                                         # magasin de p-locks vide, comme l'OS le tient :
        a = 4332 + 4385 * t                                    # 33 emplacements à -1 et un compte nul par
        for s in range(64):                                    # pas, puis 33 octets « utilisé » par emplacement
            blk[a + 68 * s:a + 68 * s + 68] = b'\xff' * 66 + b'\x00\x00'   # à zéro
        blk[a + 4352:a + 4385] = bytes(33)
    blk[30662:30664] = struct.pack('>H', 16); blk[30667] = 0; blk[30668] = 2
    m.uc.mem_write(PB, bytes(blk))
    for t in range(6):                                         # des p-locks sur quelques pas à trig, par la
        o = P + 0x70 + 88 * t                                  # vraie fonction, pour que l'OS tienne
        for s in range(0, 16, 5):                              # ses comptes par pas (mot 33)
            if rng[t][s]:
                for k, v in ((3, (s * 7) & 0x7f), (10, 64), (32, 1)):
                    m.call(0x4001646a, o, s, k, v)

def ui_test(m, msg, syms):
    import random
    rng = [[random.Random(t).random() < 0.3 for s in range(64)] for t in range(6)]
    # objets : vtables à des adresses distinctes, hors des objets de 88 octets
    def obj(at, data, slot):
        vt = 0x93400000 + slot * 0x100; f10 = vt + 0x80
        m.w32(at, vt); m.w32(vt + 16, NOTE); m.w32(vt + 40, f10); m.w32(vt + 60, f10 + 8)
        m.uc.mem_write(f10, b'\x20\x3c' + struct.pack('>I', data) + b'\x4e\x75\x4e\x75')
    m.obj = lambda at, data, _n=[0]: (obj(at, data, _n[0]), _n.__setitem__(0, _n[0] + 1))
    setup_pattern(m, rng)
    before = bytes(m.uc.mem_read(PB, 30710))
    cb, closure, arg = m.r32(msg + 0x10), m.r32(msg + 4), m.r32(msg + 0x14)
    m.notes.clear()
    m.w32(0xfc07000c, 0x5eed1234)                               # le compteur libre que la graine mélange
    t0 = time.time()
    m.call(cb, closure, arg, count=1_500_000_000)
    check(not m.bad, f'Random : aucun accès hors mémoire {m.bad[:3]} ({time.time() - t0:.1f} s d\'émulation, tables comprises)')
    after = bytes(m.uc.mem_read(PB, 30710))
    seed = m.r32(int(syms['ours_seed'], 16))
    ctl_addr = int(syms['ours_controls'], 16)
    controls = list(struct.unpack('>48H', m.uc.mem_read(ctl_addr, 96)))
    # attendu : l'exécutable hôte du même cœur C (lui-même vérifié par les vecteurs dorés)
    cli = CLI
    cli_run = lambda line: subprocess.run([str(cli)], input=line + '\n', capture_output=True, text=True, check=True).stdout.split()
    defaults = cli_run('defaults')
    exp_ctl = cli_run(f'rand {seed} ' + ' '.join(defaults) + ' 0 0 0 0 0 0')
    check(controls == [int(x) for x in exp_ctl], f'réglages tirés = cœur hôte, pour la graine {seed:#010x}')
    rows_c = cli_run(f'gen {seed} ' + ' '.join(map(str, controls)) + ' 0 0 0 0 0 0')
    lens = [struct.unpack('>H', after[722 * t + 713:722 * t + 715])[0] for t in range(6)]
    mode, mlen = after[30667], struct.unpack('>H', after[30662:30664])[0]
    rows = [''.join('1' if struct.unpack('>H', after[722 * t + 2 * s:722 * t + 2 * s + 2])[0] & 1 else '0' for s in range(64)) for t in range(6)]
    exp_rows = [rows_c[6 * t + 2] for t in range(6)]
    exp_lens = [max(2, int(rows_c[6 * t + 1])) for t in range(6)]
    check(mode == 1 and mlen == 64, f'échelle par piste {mode}, longueur maître {mlen}')
    check(lens == exp_lens, f'longueurs des pistes {lens} = attendues {exp_lens}')
    check(rows == exp_rows, 'trigs sur 64 pas = cœur hôte :\n' + '\n'.join(f'          {r[:16]}  len {L}' for r, L in zip(rows, lens)))
    check(len(m.notes) > 50, f'{len(m.notes)} notifications des observateurs (vtable[4])')
    def nlocks(b):
        return sum(1 for t in range(6) for s in range(64) for k in range(33)
                   if b[4332 + 4385 * t + 68 * s + 2 * k:4332 + 4385 * t + 68 * s + 2 * k + 2] != b'\xff\xff')
    locks_before, locks_after = nlocks(before), nlocks(after)
    check(locks_after < locks_before, f'p-locks : {locks_before} avant Random, {locks_after} après (un trig effacé perd les siens)')
    m.w32(msg + 0x18, 0)                                        # la tâche d'interface remet busy à zéro
    # Undo : posté par les touches, puis exécuté
    m.posts.clear()
    s = ev(m, 13, 1, 0x93300700); m.call(0x4007240c, s)
    e = ev(m, 14, 1, 0x93300800); m.call(0x4007240c, e)
    check(len(m.posts) == 1, 'SETTINGS+TEMPO a posté Undo')
    q, msg2 = m.posts[0]
    m.call(m.r32(msg2 + 0x10), m.r32(msg2 + 4), m.r32(msg2 + 0x14))
    undone = bytes(m.uc.mem_read(PB, 30710))
    diff = [i for i in range(30710) if undone[i] != before[i]]
    check(not diff, f'Undo : pattern identique à l\'octet près à celui d\'avant Random ({len(diff)} diffèrent : {diff[:8]})')
    if diff and '-v' in sys.argv:
        for t in range(6):
            a = 4332 + 4385 * t + 4352
            print(f'    t{t} trailer before {before[a:a + 33].hex()}')
            print(f'    t{t} trailer after  {after[a:a + 33].hex()}')
            print(f'    t{t} trailer undone {undone[a:a + 33].hex()}')
        for t in range(6):
            for s in (0, 5, 10, 15):
                a = 4332 + 4385 * t + 68 * s
                if before[a:a + 68] != undone[a:a + 68] or before[a:a+68] != b'\xff'*68:
                    print(f'    t{t} s{s} before {before[a:a + 68].hex()}')
                    print(f'    t{t} s{s} after  {after[a:a + 68].hex()}')
                    print(f'    t{t} s{s} undone {undone[a:a + 68].hex()}')

def run():
    img, syms = image(['model-tg', 'generative'])
    print('démarrage'); boot_test(img, syms)
    print('accords'); m, msg = keys_test(img, syms)
    print('tâche d\'interface : Random, Undo'); ui_test(m, msg, syms)
    return FAIL
