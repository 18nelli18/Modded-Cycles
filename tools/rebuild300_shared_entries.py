"""Entrees autonomes pour trois implementations partagees, sans appel ancien+8.

Les corps viennent du propre ELF C correspondant, avec tailles et octets gardes.
Branches relatives internes seulement : memes deplacements apres deplacement.
Les pointeurs de donnees et appels externes gardent leurs adresses exactes.
"""
from pathlib import Path
import hashlib
import re
import struct
import subprocess

CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'


def apply(meta,runtime,output,native,sram):
    edition='full' if meta['activity_masks']['full'] else 'lite'
    scope='optional' if meta.get('scope')=='optional' else 'main'
    elf=Path('D:/Supermodel-workspace/CREATURE-source/pots-delay-test')/scope/edition/'build/light.elf'
    original=elf.with_suffix('.bin').read_bytes();base=0x46700000
    bounds={}
    for line in subprocess.check_output([CROSS+'nm.exe','-S',str(elf)],text=True).splitlines():
        parts=line.split()
        if len(parts)==4 and parts[2] in ('T','t'):bounds[parts[3]]=(int(parts[0],16),int(parts[1],16))
    # Lite n'a pas le moteur ACID : reutiliser son ancien producteur de
    # coefficients plutot que lui reintroduire une dependance de machine.
    pools=[x for x in meta['retired_delegates']['removed'] if x['symbol'] in ('ae_update','fast_fc_coeff')]
    pool=next((x for x in pools if x['symbol']=='ae_update'),None) or next(x for x in pools if x['symbol']=='fast_fc_coeff')
    cursor=(pool['address']+6+3)&~3;limit=pool['address']+6+pool['bytes']
    assert runtime[cursor-base:limit-base]==bytes(limit-cursor)
    moves=[]
    for name,alias in (('mf_project_encode','fp_old_encode'),('mf_pattern_copy','fp_old_copy'),('mf_pattern_init','fp_old_init')):
        old,size=bounds[name];assert meta['per_track_fx']['symbols'][name]==old
        data=original[old-0x46900000:old-0x46900000+size]
        assert runtime[old-base+6:old-base+size]==data[6:],name
        stub=meta['filter_pattern300']['symbols'][alias]
        expected=data[:8]+b'\x4e\xf9'+struct.pack('>I',old+8)
        assert runtime[stub-base:stub-base+14]==expected,(name,'trampoline mismatch')
        text=subprocess.check_output([CROSS+'objdump.exe','-d',f'--start-address={old}',f'--stop-address={old+size}',str(elf)],text=True)
        assert '%pc@' not in text,(name,'external PC-relative operand needs relocation')
        for line in text.splitlines():
            columns=line.split('\t')
            if len(columns)<3:continue
            instruction=columns[2].split()
            if len(instruction)<2:continue
            if re.fullmatch(r'b(?:ra|sr|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le)[swl]?',instruction[0]):
                assert old<=int(instruction[1],16)<old+size,(name,'external relative branch',line)
        dest=cursor;cursor=(cursor+size+3)&~3;assert cursor<=limit
        sites=[];needle=struct.pack('>I',stub)
        assert needle not in native and needle not in sram,(name,'external stored trampoline reference')
        start=0
        while (index:=runtime.find(needle,start))>=0:
            assert runtime[index-2:index] in (b'\x4e\xb9',b'\x4e\xf9'),(name,'non-call reference to old trampoline',hex(base+index))
            sites.append(base+index);start=index+4
        assert sites,(name,'no owned callers')
        for site in sites:runtime[site-base:site-base+4]=struct.pack('>I',dest)
        runtime[dest-base:dest-base+size]=data
        runtime[old-base+6:old-base+size]=bytes(size-6)
        runtime[stub-base:stub-base+14]=bytes(14)
        for profile in meta.values():
            if not isinstance(profile,dict):continue
            for key in ('symbols','aliases'):
                if profile.get(key,{}).get(alias)==stub:profile[key][alias]=dest
        moves.append(dict(name=name,old=old,bytes=size,new=dest,old_trampoline=stub,retargeted_operands=sites,sha256=hashlib.sha256(data).hexdigest()))
    return dict(moves=moves,code=moves[0]['new'],code_bytes=cursor-moves[0]['new'],symbols={'shared_'+x['name']:x['new'] for x in moves},interior_calls_removed=True,algorithm_bytes_unchanged=True,
                compiler_elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),hardware_tested=False)
