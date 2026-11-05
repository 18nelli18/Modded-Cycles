"""Reconstruction Swap : niveaux16bits, navigation4lignes, propriete du projet."""
from pathlib import Path
import copy
import struct

BASE=0x46700000

def apply(meta,native,runtime,out):
    assert meta.get('gov_inv_master380') and not meta.get('track_swap381')
    from track_swap377 import apply as build,CODE,END
    old=copy.deepcopy(meta['track_swap377'])
    before=bytes(runtime)
    # Restaurer les prologues d'origine avant de recreer les trampolines.
    for edit in old['patches']:
        at=edit['at']
        if at==CODE:continue
        raw=bytes.fromhex(edit['old'])
        runtime[at-BASE:at-BASE+len(raw)]=raw
    start=CODE-BASE;finish=END-BASE
    assert not any(runtime[start+old['code_bytes']:finish])
    runtime[start:finish]=bytes(finish-start)
    old_encoder=meta['gov_policy372']['symbols']['gp_encoder']
    new_encoder=meta['gov_inv_master380']['symbols']['gp_encoder']
    runtime[old_encoder-BASE:old_encoder-BASE+6]=b'\x4e\xf9'+struct.pack('>I',new_encoder)
    meta['gov_policy372']['symbols']['gp_encoder']=new_encoder
    del meta['track_swap377']
    meta['track_swap377']=build(meta,native,runtime,Path(out))
    changes=[];start=None
    for i,(a,b) in enumerate(zip(before,runtime)):
        if a!=b and start is None:start=i
        if start is not None and (a==b or i==len(runtime)-1):
            end=i if a==b else i+1
            changes.append(dict(at=BASE+start,old=before[start:end].hex(),new=bytes(runtime[start:end]).hex()))
            start=None
    return dict(level_storage_bits=16,track_menu_rows=4,project_ownership_checked=True,
        context_rechecked_with_IRQ_masked=True,other_patterns_untouched=True,
        symbols=meta['track_swap377']['symbols'],patches=changes,hardware_tested=False)
