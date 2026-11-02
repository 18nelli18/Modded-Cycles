"""Retirer des corps remplaces, apres recherche conservative des entrees internes.

Liste fermee de remplacements C complets ; les trampolines vers ancien+8 ne
sont jamais eligibles. Les appels publics gardent leur JMP de six octets.
"""
import struct
import re
import subprocess
from pathlib import Path
import hashlib


def apply(meta,areas,output,extra=False):
    selected=(('per_track_fx','ae_render'),('per_track_fx','ae_update'),
              ('per_track_fx','fast_pf_coeff'),('per_track_fx','fast_fc_coeff'),
              ('per_track_fx','li_dispatch'))
    exact={};ownership=None;data_objects=[]
    if extra:
        edition='full' if meta['activity_masks']['full'] else 'lite'
        scope='optional' if meta.get('scope')=='optional' else 'main'
        elf=Path('D:/Supermodel-workspace/CREATURE-source/pots-delay-test')/scope/edition/'build/light.elf'
        binary=elf.with_suffix('.bin');original=binary.read_bytes()
        nm='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-nm.exe'
        for line in subprocess.check_output([nm,'-S',str(elf)],text=True).splitlines():
            fields=line.split()
            if len(fields)==4 and fields[2] in ('T','t'):exact[fields[3]]=(int(fields[0],16),int(fields[1],16))
        more=('gb_finish','native_sum','pp_voice_loop','rm_step','mf_pattern_copy','mf_pattern_init','mf_project_encode')
        selected+=tuple(('per_track_fx',name) for name in more)
        ownership=dict(elf=str(elf),elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(original).hexdigest())
        table=subprocess.check_output(['H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe','-t',str(elf)],text=True)
        for line in table.splitlines():
            fields=line.split()
            if len(fields)<6 or fields[2]!='O' or fields[3]!='.text':continue
            lo,size=int(fields[0],16),int(fields[4],16)
            if not size:continue
            current=next((bytes(r[lo-b:lo-b+size]) for b,r in areas if b<=lo and lo+size<=b+len(r)),None)
            if current==original[lo-0x46900000:lo-0x46900000+size]:data_objects.append((lo,lo+size))
    removed=[];kept=[];decoded={};blobs={}
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe'
    def actual_relative(pc):
        # Ne pas prendre un immediat ou une table pour un opcode de branche.
        if any(lo<=pc<hi for lo,hi in data_objects):return False
        owners=[x for x in meta.values() if isinstance(x,dict) and isinstance(x.get('code'),int) and isinstance(x.get('code_bytes'),int) and x['code']<=pc<x['code']+x['code_bytes']]
        if not owners:return True
        item=min(owners,key=lambda x:x['code_bytes']);symbols=item.get('symbols',{})
        starts=[v for v in symbols.values() if isinstance(v,int) and item['code']<=v<=pc]
        if not starts:return True
        start=max(starts);end=min([v for v in symbols.values() if isinstance(v,int) and pc<v<item['code']+item['code_bytes']]+[item['code']+item['code_bytes']])
        key=(start,end)
        if key not in decoded:
            base,raw=next((b,r) for b,r in areas if b<=pc<b+len(r))
            if base not in blobs:
                path=output/('delegate-audit-'+hex(base)+'.bin');path.write_bytes(raw);blobs[base]=path
            text=subprocess.check_output([cross,'-D','-b','binary','-m','m68k:isa-c:emac',f'--adjust-vma={base}',f'--start-address={start}',f'--stop-address={end}',str(blobs[base])],text=True)
            parsed={}
            for line in text.splitlines():
                match=re.match(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{4}\s+)+\s*(\S+)(.*)$',line)
                if match:parsed[int(match[1],16)]=(match[2],match[3])
            decoded[key]=parsed
        instruction=decoded[key].get(pc)
        if not instruction:return False
        mnemonic,operands=instruction
        return mnemonic.startswith(('b','j','db')) or '%pc@' in operands
    for module,name in selected:
        item=meta.get(module,{})
        if name not in item.get('symbols',{}):continue
        symbols=item['symbols'];at=symbols[name];end=min([v for v in symbols.values() if isinstance(v,int) and at<v<=item['code']+item['code_bytes']]+[item['code']+item['code_bytes']])
        raw,offset=next((raw,at-base) for base,raw in areas if base<=at<base+len(raw))
        if raw[offset:offset+2]!=b'\x4e\xf9':continue
        if extra and name in more:
            address,size=exact[name];assert address==at and size>6
            end=at+size;start=at-item['code']
            assert raw[offset+6:offset+size]==original[start+6:start+size],('body ownership mismatch',name)
        lo=at+6;hi=end;references=[]
        for base,content in areas:
            # Les immediats d'adresses peuvent commencer a n'importe quel octet.
            for pos in range(len(content)-3):
                if content[pos] not in (0x40,0x46,0x80):continue
                target=int.from_bytes(content[pos:pos+4],'big')
                if lo<=target<hi and not lo<=base+pos<hi:references.append(base+pos)
            # Branches relatives, y compris les branches longues ColdFire.
            for pos in range(0,len(content)-6,2):
                pc=base+pos
                if lo<=pc<hi:continue
                op=(content[pos]<<8)|content[pos+1];target=None
                if op&0xf000==0x6000:
                    displacement=op&255
                    if displacement==0:displacement=struct.unpack_from('>h',content,pos+2)[0]
                    elif displacement==255:displacement=struct.unpack_from('>i',content,pos+2)[0]
                    elif displacement>=128:displacement-=256
                    target=pc+2+displacement
                elif op&0xf0f8==0x50c8 or op&0x3f==0x3a:
                    target=pc+2+struct.unpack_from('>h',content,pos+2)[0]
                if target is not None and lo<=target<hi and actual_relative(pc):references.append(pc)
        entry=dict(module=module,symbol=name,address=at,bytes=end-at-6,target=struct.unpack_from('>I',raw,offset+2)[0])
        if references:
            entry['possible_internal_entries']=sorted(set(references));kept.append(entry);continue
        raw[offset+6:offset+end-at]=bytes(end-at-6);removed.append(entry)
    return dict(removed=removed,kept=kept,removed_bytes=sum(x['bytes'] for x in removed),compiler_ownership=ownership,hardware_tested=False)
