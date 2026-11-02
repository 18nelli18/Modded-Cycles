"""Reference de demarrage reelle, sans stubs UI ni initialisation manuelle tardive.

Execute les copies SRAM natives, les chargeurs et les installateurs jusqu'au
point natif40000542. Cette capture sert a prouver le futur chargeur, pas a
declarer une reconstruction depuis les sources terminee.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/emu')]
from gen_governor_recovery_test import read, BASE, START
from mtlib import aplib
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as C


def capture(folder, output):
    path = next(folder.glob('*.syx'))
    meta = json.loads((folder/'BUILD.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == meta['sha256']
    image = read(path)[2]
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(C.UC_CPU_M68K_ANY)
    for at, size in ((0x40000000, 0x2400000), (0x43000000, 0x800000),
                     (0x466f0000, 0x410000), (0x80000000, 0x20000),
                     (0x90000000, 0x20000), (0xfc040000, 0x10000), (0xfc070000, 0x1000)):
        uc.mem_map(at, size)
    uc.mem_write(BASE, image)
    def unmapped(u, access, address, size, value, data):
        print('UNMAPPED',hex(address),'PC',hex(u.reg_read(C.UC_M68K_REG_PC)),flush=True)
        return False
    uc.hook_add(UC_HOOK_MEM_UNMAPPED,unmapped)
    copies=[];last_read=[None]
    def observed_read(u,access,address,size,value,data):
        last_read[0]=(u.reg_read(C.UC_M68K_REG_PC),address,size,int.from_bytes(u.mem_read(address,size),'big'))
    def observed_write(u,access,address,size,value,data):
        item=last_read[0]
        if not item or item[0]!=u.reg_read(C.UC_M68K_REG_PC) or item[2]!=size or item[3]!=(value&((1<<(8*size))-1)):return
        pc,source,_,_=item
        if copies and copies[-1]['pc']==pc and copies[-1]['source']+copies[-1]['bytes']==source and copies[-1]['destination']+copies[-1]['bytes']==address:
            copies[-1]['bytes']+=size
        else:copies.append(dict(pc=pc,source=source,destination=address,bytes=size))
    uc.hook_add(UC_HOOK_MEM_READ,observed_read,begin=0x46700000,end=0x469fffff)
    uc.hook_add(UC_HOOK_MEM_WRITE,observed_write,begin=0x40000400,end=0x401fffff)
    uc.hook_add(UC_HOOK_MEM_WRITE,observed_write,begin=0x80000000,end=0x8000ffff)
    extra_regions=[]
    if image[START:START+8]==b'SMCLEAN1':
        version,entry,run,loader_source,loader_size,payload_source,payload_size,decoded_size,segments,boot=struct.unpack_from('>10I',image,START+8)
        assert version==1 and payload_size==decoded_size
        extra_regions.append((run,image[loader_source-BASE:loader_source-BASE+loader_size]))
        payload=image[payload_source-BASE:payload_source-BASE+payload_size]
        assert int.from_bytes(payload[:4],'big')==segments
        for index in range(segments):
            at,size,offset=struct.unpack_from('>III',payload,4+12*index)
            extra_regions.append((at,payload[offset:offset+size]))
    else:
        end = int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE], 'big')-BASE
        packed = image[START:end]
        runtime, _ = aplib.depack(struct.pack('>II', len(packed), sum(packed)&0xffffffff)+packed)
        extra_regions.append((0x46700000,runtime))
    privileged = set()
    for at, raw in [(BASE,image)]+extra_regions:
        privileged.update(at+i for i in range(0, len(raw)-3, 2) if raw[i:i+2] == b'\x4e\x7b')
    for at in privileged:
        uc.hook_add(UC_HOOK_CODE, lambda u, pc, size, data: u.reg_write(C.UC_M68K_REG_PC, pc+4), begin=at, end=at)
    uc.reg_write(C.UC_M68K_REG_SR, 0x2700)
    uc.reg_write(C.UC_M68K_REG_A7, 0x90010000)
    uc.emu_start(0x4000052c, 0x40000542, count=250_000_000)
    assert uc.reg_read(C.UC_M68K_REG_PC) == 0x40000542
    checked = []
    for key in ('control_all_latch', 'activity_masks', 'sidechain_manual301', 'additions_only300'):
        item = meta.get(key, {})
        for hook in item.get('hooks', item.get('late_hooks', [])):
            if not isinstance(hook, dict) or 'at' not in hook:
                continue
            expected = bytes.fromhex(hook['new']) if 'new' in hook else b'\x4e\xf9'+struct.pack('>I', hook['target'])
            actual = bytes(uc.mem_read(hook['at'], len(expected)))
            # Une edition peut remplacer un hook d'un ancetre. Consigner les
            # differences au lieu de confondre metadata historique et contrat.
            checked.append(dict(module=key, at=hook['at'], matches=actual == expected))
    output.mkdir(parents=True, exist_ok=True)
    regions = []
    for label, at, size in (('native', BASE, 0x40200000-BASE),
                            ('runtime', 0x46700000, 0x300000),
                            ('sram', 0x80000000, 0x10000)):
        raw = bytes(uc.mem_read(at, size))
        (output/(label+'.bin')).write_bytes(raw)
        regions.append(dict(label=label, address=at, bytes=size, sha256=hashlib.sha256(raw).hexdigest()))
    proof = dict(source=meta['sha256'], native_boot_continuation=True,
                 ui_stubs=False, manual_late_installer_calls=False,
                 regions=regions, historical_hooks=checked, runtime_to_final_copies=copies, hardware_tested=False)
    (output/'capture.json').write_text(json.dumps(proof, indent=2)+'\n')
    print('PASS real cold boot to40000542;', len(checked), 'hook claims inspected;',
          sum(not x['matches'] for x in checked), 'historical differences', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    capture(args.build, args.output)
