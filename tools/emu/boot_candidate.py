"""Charge une image privee par son bootstrap natif avant les preuves."""
import pathlib, sys, struct, hashlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools'/'emu')]
from mtlib import aplib, container
from mtlib.syx import unwrap
from test_seq_gen_menu import Rig, STACK, STOP
from unicorn import UC_HOOK_CODE, m68k_const as C

def load(path):
    st, _ = unwrap(pathlib.Path(path).read_bytes())
    pkg = container.parse(st)
    sec = next(s for s in pkg['sections'] if s['id'] == 3)
    return aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0]

def boot(path):
    path=pathlib.Path(path)
    cache_dir=ROOT/'tmp'/'boot-context'/hashlib.sha256(path.read_bytes()).hexdigest()
    if (cache_dir/'complete').exists():
        return (cache_dir/'main.bin').read_bytes(),[(0x46700000,(cache_dir/'runtime.bin').read_bytes())]
    image = load(path)
    r = Rig(image, {'writes':[]}, {'writes':[], 'symbols':{}})
    u = r.u
    for addr, size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:
        u.mem_map(addr,size)
    p=image[0x401aa140-0x40000400:]
    rt,_=aplib.depack(struct.pack('>II',len(p),sum(p)&0xffffffff)+p)
    sites=set()
    for addr,raw in [(0x40000400,image),(0x46700000,rt)]:
        sites.update(addr+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
    for site in sites:
        u.hook_add(UC_HOOK_CODE,lambda u,pc,size,data:u.reg_write(C.UC_M68K_REG_PC,pc+4),begin=site,end=site)
    u.mem_write(STACK,struct.pack('>I',STOP))
    u.reg_write(C.UC_M68K_REG_A7,STACK)
    u.emu_start(0x40000530,0x4000053a,count=200_000_000)
    assert u.reg_read(C.UC_M68K_REG_PC)==0x4000053a
    print('PASS: native payload bootstrap and RAM clear reached native continuation',flush=True)
    main=bytes(u.mem_read(0x40000400,0x40200000-0x40000400))
    runtime=bytes(u.mem_read(0x46700000,0x100000))
    cache_dir.mkdir(parents=True,exist_ok=True)
    (cache_dir/'main.bin').write_bytes(main)
    (cache_dir/'runtime.bin').write_bytes(runtime)
    (cache_dir/'complete').write_text('native bootstrap reached 0x4000053a')
    return main,[(0x46700000,runtime)]

if __name__=='__main__':
    boot(sys.argv[1])
