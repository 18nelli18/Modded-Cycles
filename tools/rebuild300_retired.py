"""Audit conservateur des sections ChordKeys retirees et de l'ancien Vinyl.

Les unites MIT sont celles de la recette relogee PR87. Toute unite modifiee
ou referencee de l'exterieur reste conservee, ainsi que ses dependances.
Le resultat est une liste gardee par SHA, jamais une suppression heuristique.
"""
from pathlib import Path
import argparse
import bisect
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]


def audit(folder,capture):
    meta=json.loads((folder/'BUILD.json').read_text())
    areas=[(0x40000400,bytearray((capture/'native.bin').read_bytes())),
           (0x46700000,bytearray((capture/'runtime.bin').read_bytes())),
           (0x80000000,bytearray((capture/'sram.bin').read_bytes()))]
    def read(at,size):
        for base,raw in areas:
            if base<=at and at+size<=base+len(raw):return bytes(raw[at-base:at-base+size])
        raise ValueError(hex(at))
    result=[];detail={}
    if meta.get('chordkeys_removed'):
        recipe=json.loads((ROOT/'docs/flasher-own-support-test/source/integration-chord-keys.json').read_text())
        bank=json.loads((ROOT/'docs/flasher-own-support-test/source/integration-midi-bank-chord.json').read_text())
        units=sorted([dict(start=int(x['new'],16),bytes=x['size']) for x in recipe['relocation_audit']['placements']],key=lambda x:x['start'])
        starts=[x['start'] for x in units]
        def owner(at):
            i=bisect.bisect_right(starts,at)-1
            return i if i>=0 and at<units[i]['start']+units[i]['bytes'] else None
        def expected(at,size):
            for w in recipe['writes']:
                lo=0x40000400+w['off'];raw=bytes.fromhex(w['new'])
                if lo<=at and at+size<=lo+len(raw):return raw[at-lo:at-lo+size]
            for part in bank['append']['parts']:
                if 'hex' not in part:continue
                lo=int(part['dest'],16);raw=bytes.fromhex(part['hex'])
                if lo<=at and at+size<=lo+len(raw):return raw[at-lo:at-lo+size]
            raise ValueError(('no CK ownership',hex(at),size))
        roots=set();edges=[set() for _ in units];incoming=[];changed=[]
        for i,unit in enumerate(units):
            raw=read(unit['start'],unit['bytes'])
            if any(raw) and raw!=expected(unit['start'],unit['bytes']):
                roots.add(i);changed.append(unit['start'])
        for base,raw in areas:
            for offset in range(0,len(raw)-3,2):
                value=struct.unpack_from('>I',raw,offset)[0]
                if not starts[0]<=value<units[-1]['start']+units[-1]['bytes']:continue
                target=owner(value)
                if target is None:continue
                source=owner(base+offset)
                if source is None:
                    roots.add(target);incoming.append(dict(site=base+offset,target=value))
                else:edges[source].add(target)
        live=set(roots);todo=list(roots)
        while todo:
            for target in edges[todo.pop()]:
                if target not in live:live.add(target);todo.append(target)
        for i,unit in enumerate(units):
            if i in live:continue
            raw=read(unit['start'],unit['bytes'])
            if any(raw):
                assert raw==expected(unit['start'],unit['bytes'])
                result.append(dict(address=unit['start'],bytes=unit['bytes'],feature='retired ChordKeys',sha256=hashlib.sha256(raw).hexdigest()))
        detail['chordkeys']=dict(total_units=len(units),kept_units=len(live),modified_units=changed,external_incoming=incoming,
                                 removable_bytes=sum(x['bytes'] for x in result),status='conservative absolute-reference audit; relative-call audit still required')
    if meta.get('vinyl_removed'):
        fx=meta['fx_menu']['symbols'];lo=fx['fx_vinyl'];hi=fx['fx_reverb']
        assert read(lo,6)==b'\x4e\xf9'+struct.pack('>I',meta['per_track_fx']['symbols']['nv_bypass'])
        detail['vinyl']=dict(start=lo,body_start=lo+6,end=hi,bytes=hi-lo-6,status='bypass verified; old trampoline references require audit')
    return dict(reference=meta['sha256'],removals=result,detail=detail,ready_to_apply=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--capture',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=audit(args.reference,args.capture)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
    print('AUDIT',len(report['removals']),'unreferenced original CK units;',sum(x['bytes'] for x in report['removals']),'bytes; not yet applied')
